from starling_sim.basemodel.agent.persons.person import Person


class User(Person):
    """
    This class describes a simple station-based vehicle-sharing user
    """

    SCHEMA = {
        "properties": {
            "has_station_info": {
                "title": "Station stock information",
                "description": "Indicate if user has access to vehicle availability of the stations",
                "type": "boolean",
                "default": True,
            },
            "patience": {
                "advanced": True,
                "title": "Patience when requesting a station",
                "description": "user patience while waiting for a vehicle. "
                "Caution, None means infinite patience",
                "type": ["integer", "null"],
                "minimum": 0,
                "default": None,
            },
            "closest_station_evaluation": {
                "advanced": True,
                "title": "Station distance evaluation",
                "description": "Determine how the distance to the stations is evaluated",
                "type": "string",
                "oneOf": [{"const": "euclidean"}, {"const": "shortest_path"}],
                "default": "euclidean",
            },
        },
        "required": ["has_station_info", "closest_station_evaluation"],
    }

    def __init__(self, simulation_model, agent_id, origin, destination, **kwargs):

        super().__init__(simulation_model, agent_id, origin, destination, **kwargs)

        # remember the failed stations
        self.failed_stations_ids = []

    def loop_(self):
        """
        Main loop of a station-based vehicle-sharing user
        """

        # loop on trying to get vehicle at closest station
        yield self.execute_process(self.request_loop_(self.maxTries))

        if self.vehicle is None:
            # if failed to get a vehicle, leave the system
            self.leave_simulation("FAIL_GET")
        else:
            # loop on trying to leave vehicle at station closest to dest
            yield self.execute_process(self.request_loop_())

            # should not have a vehicle
            if self.vehicle is not None:
                self.simulation_error("Did not return its vehicle")
            else:
                # end trip
                yield self.execute_process(self.walk_to_destination_())

            return

    def try_new_request_(self):
        """
        Try to request the best station according to user's state.

        The best station is the closest to agent. According to their
        has_station_info attribute, users may ignore the stations that can't
        offer them the service they look for. If no station is found, they wait
        30 seconds and try again.

        :return: StationRequest object, completed according to request result
        """

        # find the best station according to current state
        best_station = self.best_station_for()

        while best_station is None:
            yield self.execute_process(self.spend_time_(30))
            best_station = self.best_station_for()

        # go to chosen station and request it
        self.tempDestination = best_station.position

        if self.vehicle is None:
            # GET request
            yield self.execute_process(self.move_())
            request = self.station_get_request(best_station)
            yield self.execute_process(self.request_tries(request))

            if request.success:
                self.get_vehicle(request.result)
                self.failed_stations_ids = []
            else:
                self.failed_stations_ids.append(best_station.id)

        else:
            # PUT request
            yield self.execute_process(self.move_shortest_with_vehicle_())
            request = self.station_put_request(best_station)
            yield self.execute_process(self.request_tries(request))

            if request.success:
                self.leave_vehicle()
            else:
                self.failed_stations_ids.append(best_station.id)

        # return request to loop
        self.sim.scheduler.env.exit(request)

    def request_tries(self, station_request):
        """
        Execute a sequence of attempts for the given request.

        Each time the waiting time exceeds the agent's patience,
        they reevaluate their decision of staying in the queue.
        This evaluation is done by the quit_decision method.
        This results in a Request with a sequence of waiting times

        :param station_request: StationRequest object
        """

        # request event
        wait_sequence = []

        # quit boolean
        quitting = False

        while not quitting:
            start = self.sim.scheduler.now()
            result = yield self.execute_process(
                self.wait_for_request_(station_request, self.profile["patience"])
            )

            # trace wait event
            wait_sequence += [self.sim.scheduler.now() - start]

            # result of the request
            if station_request.event_ in result:
                # complete request
                station_request.waitSequence = wait_sequence
                station_request.success = True
                station_request.result = result[station_request.event_]

                # end request
                station_request.event_.cancel()

                # return result of request
                return
                # self.sim.scheduler.env.exit(result[station_request.event_])
            else:
                quitting = self.quit_decision(station_request)

        if quitting:
            # complete request
            station_request.waitSequence = wait_sequence
            station_request.success = False

            # end request
            station_request.event_.cancel()

            # return 0 in case of failed request
            # self.sim.scheduler.env.exit(0)

    def best_station_for(self):
        """
        Return the best station according to the agent's state.

        It corresponds to the closest station to either current position
        or destination, depending on the agent having a vehicle or not.
        Some stations may be ignored (e.g. empty stations), depending on the information
        detained by the agent

        :return: Station object, or None if no station is found
        """

        # compute stations to consider for closest search
        considered_stations = []

        for station in self.sim.agentPopulation["station"].values():

            # don't consider the stations where the request already failed
            if station.id in self.failed_stations_ids:
                continue

            if self.profile["has_station_info"]:
                # don't consider empty stations if looking for a vehicle, and vice-versa
                if (self.vehicle is None and station.nb_products() == 0) or (
                    self.vehicle is not None and station.nb_products() == station.capacity
                ):
                    continue

            considered_stations.append(station)

        # compute closest station to either current position or destination
        if self.profile["closest_station_evaluation"] == "euclidean":

            if self.vehicle is None:
                best_station = self.sim.environment.euclidean_n_closest(
                    self.position, considered_stations, 1
                )[0]
            else:
                best_station = self.sim.environment.euclidean_n_closest(
                    self.destination, considered_stations, 1
                )[0]

        # TODO : return path and use it
        elif self.profile["closest_station_evaluation"] == "shortest_path":

            if self.vehicle is None:

                best_station = self.sim.environment.closest_object(
                    self.position, considered_stations, True, "walk", n=3
                )
            else:
                best_station = self.sim.environment.closest_object(
                    self.destination, considered_stations, False, "walk", n=3
                )
        else:
            raise ValueError(
                "Unsupported value {} for 'closest_station_evaluation' option.".format(
                    self.profile["closest_station_evaluation"]
                )
            )

        return best_station

    def quit_decision(self, request):
        """
        Decide if user should quit after exceeding its request patience

        :param request: StationRequest object
        :return: boolean, True for quitting the request queue
        """

        return True
