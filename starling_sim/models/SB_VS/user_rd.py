from starling_sim.models.SB_VS.user import User as SB_VS_user


class User(SB_VS_user):
    """
    This class describes a station-based vehicle-sharing user with possibility of round trips
    """

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

            # if round trip, move to current position with duration equal to round_trip parameter
            if "origin_station" in self.profile and "destination_station" in self.profile \
                     and self.profile["origin_station"] == self.profile["destination_station"]:
                self.log_message("Round trip !")
                self.tempDestination = self.sim.agentPopulation["station"][self.profile["destination_station"]].position
                # yield self.execute_process(self.move_shortest_with_vehicle_(duration=self.profile["round_trip"]))
                yield self.execute_process(self.move_shortest_with_vehicle_(duration=30*60))

            # loop on trying to leave vehicle at station closest to dest
            yield self.execute_process(self.request_loop_())

            # should not have a vehicle
            if self.vehicle is not None:
                self.simulation_error("Did not return its vehicle")
            else:
                # end trip
                yield self.execute_process(self.walk_to_destination_())

            return

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
            # if station.id in self.failed_stations_ids:
            #     continue

            if self.profile["has_station_info"]:
                # don't consider empty stations if looking for a vehicle, and vice-versa
                if (self.vehicle is None and station.nb_products() == 0) or \
                        (self.vehicle is not None and station.nb_products() == station.capacity):
                    continue

            considered_stations.append(station)

        dist_dict = {}

        # get the total travel time for each station
        for station in considered_stations:

            # if user doesn't have a vehicle : walk to station and bike to destination
            if self.vehicle is None:
                destination_station = self.sim.agentPopulation.get_agent(self.profile["destination_station"], "station")
                dist_dict[station.id] = self.sim.environment.topologies[self.mode].shortest_path_length(
                    self.position, station.position, None) \
                    + self.sim.environment.topologies[station.mode].shortest_path_length(
                    station.position, destination_station.position, None)
            # if user has a vehicle : bike to station and walk to destination
            else:
                destination_station = self.sim.agentPopulation.get_agent(self.profile["destination_station"], "station")
                dist_dict[station.id] = self.sim.environment.topologies[station.mode].shortest_path_length(
                    self.position, station.position, None) + self.sim.environment.topologies[
                                            self.mode].shortest_path_length(
                    station.position, destination_station.position, None)

        # get the minimal travel time station
        best_station = min(dist_dict, key=dist_dict.get)
        best_station = self.sim.agentPopulation.get_agent(best_station, "station")

        return best_station
