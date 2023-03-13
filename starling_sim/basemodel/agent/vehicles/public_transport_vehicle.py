from starling_sim.basemodel.agent.vehicles.service_vehicle import ServiceVehicle
from networkx.exception import NetworkXNoPath


class PublicTransportVehicle(ServiceVehicle):
    """
    This class describes a public transport vehicle that follows
    a time table often described with a GTFS.
    """

    SCHEMA = {"x-display": "hidden"}

    def __init__(self, simulation_model, agent_id, origin, seats, **kwargs):
        super().__init__(simulation_model, agent_id, origin, seats, **kwargs)

        # route id, describes the line of the current trip
        self.routeId = None

        # direction id, indicates if the trip is in the direct way (0) or not (1)
        self.directionId = None

    def loop_(self):
        # execute each trip assigned to the vehicle
        for trip_id in self.tripList:
            # set the vehicle trip id
            self.tripId = trip_id
            self.routeId, self.directionId = self.operator.get_route_and_direction_of_trip(trip_id)

            # get the planning associated to the trip
            self.planning = self.operator.trips[trip_id][1].copy()

            yield self.execute_process(self.execute_trip_())

    def execute_trip_(self):
        """
        Execute and follow the current trip.

        It is assumed that the tripId, routeId, directionId
        and planning attributes are already set.
        """

        # teleport to the trip start position
        next_trip_start = self.planning[0].position
        self.move_to_(next_trip_start, 0)

        # wait for the trip departure
        wait_time = self.planning[0].arrivalTime[self.tripId][0] - self.sim.scheduler.now()
        yield self.execute_process(self.spend_time_(wait_time))

        # follow the planning
        current_stop = self.planning[0]
        while self.planning:
            # go to next stop
            next_stop = self.planning[0]
            move_duration = next_stop.arrivalTime[self.tripId][0] - self.sim.scheduler.now()
            yield self.execute_process(
                self.public_transport_move_(self.operator, move_duration, current_stop, next_stop)
            )

            # process the next stop of the planning
            yield self.execute_process(self.process_stop_(next_stop))
            current_stop = next_stop

    # move method for public transports
    def public_transport_move_(self, operator, move_duration, from_stop, to_stop):
        """
        Move from one stop to another following the provided line shape if possible.

        If no line shape is available, execute a normal move or fly,
        depending on the operator parameters.

        :param operator:
        :param move_duration:
        :param from_stop:
        :param to_stop:
        :return:
        """

        # set the effective arrival time of the destination stop
        to_stop.effectiveArrivalTime[self.tripId] = self.sim.scheduler.now() + move_duration

        # try to use the line_shape file
        if from_stop is not None and to_stop is not None and operator.line_shapes is not None:
            # get the line shapes table
            line_shapes_table = operator.line_shapes

            # filter the table to get the right OD
            OD_shape = line_shapes_table[
                (line_shapes_table["stop_id_A"] == from_stop.id)
                & (line_shapes_table["stop_id_B"] == to_stop.id)
            ].iloc[
                1:,
            ]

            if not OD_shape.empty:
                # print(self.tripId)

                route_data = self.sim.environment.compute_shaped_route(
                    operator, OD_shape, from_stop.id, to_stop.id, move_duration
                )
                mode = self.mode
                check_dest = False

                # execute route data
                yield self.execute_process(
                    self.follow_route_data_(route_data, check_dest, mode, verb=False)
                )
                return

        # otherwise, use base methods
        if to_stop is not None:
            self.tempDestination = to_stop.position

        if self.operator.operationParameters["use_shortest_path"]:
            try:
                # compute and use shortest path
                yield self.execute_process(self.move_(duration=move_duration, verb=False))
                return
            except NetworkXNoPath:
                pass

        # compute approximate distance and cut in the environment
        yield self.execute_process(self.fly_(duration=move_duration, distance_factor=1, verb=False))

    def serve_stop(self, user_stop):
        """
        Determine if the stop should be processed by the service vehicle.

        For public transport, all users waiting at the current stop point are evaluated,
        so only those going with the right route, direction and destination stop
        should be picked up. For the dropoff, only the ones in the vehicle
        are processed.

        :param user_stop: UserStop object
        :return: boolean indicating if the stop should be processed
        """

        # get the stop request
        request = self.operator.requests[user_stop.requestId]

        # get the request trip id
        stop_trip = user_stop.trip

        # pickup stop
        if user_stop.type == user_stop.GET_REQUEST:
            # None/Nan trips are considered having good route and direction
            if isinstance(stop_trip, str):
                # check route and direction
                route_id, direction_id = self.operator.get_route_and_direction_of_trip(stop_trip)
                if not (route_id == self.routeId and direction_id == self.directionId):
                    return False

            # check that the destination stop is served
            destination_stop = self.operator.stopPoints[user_stop.twin.stopPoint]
            if destination_stop in self.planning:
                return True
            else:
                return False

        # dropoff stop
        elif user_stop.type == user_stop.PUT_REQUEST:
            return request.agent in self.occupants

    def exceeds_capacity(self, user_stop):
        # if the user expects this vehicle (ie this trip)
        # remove the stop from the stop point list and signal the failed pickup
        if isinstance(user_stop.tripId, str) and user_stop.tripId == self.tripId:
            request = self.operator.requests[user_stop.requestId]
            self.operator.stopPoints[request.dropoff.stopPoint].dropoffList.remove(request.dropoff)
            request.success = False
            request.pickupEvent_.succeed()
