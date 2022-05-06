from starling_sim.basemodel.agent.vehicles.vehicle import Vehicle
from starling_sim.basemodel.trace.events import (
    IdleEvent,
    RequestEvent,
    StopEvent,
    StaffOperationEvent,
)
from starling_sim.basemodel.agent.requests import Stop

from copy import copy


class ServiceVehicle(Vehicle):
    """
    This class describes a vehicle providing transport services (pickup, dropoff)
    """

    SCHEMA = {
        "properties": {
            "dwell_time": {
                "title": "Dwell time",
                "description": "Time spent when serving stops",
                "type": "integer",
                "minimum": 0,
                "default": 30,
            },
            "trip_id": {
                "advanced": True,
                "title": "Initial trip ID",
                "description": "Identifier of the vehicle's initial trip",
                "type": "string",
            },
            "operator_id": {
                "title": "Operator ID",
                "description": "ID of the operator managing this agent",
                "type": "string",
            },
        },
        "required": ["operator_id"],
    }

    def __init__(
        self,
        simulation_model,
        agent_id,
        origin,
        seats,
        operator_id,
        dwell_time=30,
        trip_id=None,
        **kwargs
    ):

        super().__init__(simulation_model, agent_id, origin, seats, **kwargs)

        # list of trip ids to be realised by the service vehicle (chronological order)
        self.tripList = None

        # id of the trip realised by the service vehicle, used to match user stops
        self.tripId = trip_id

        # halt duration while processing a stop
        self.dwellTime = dwell_time

        # service operator, managing the fleet
        self.operator = self.sim.agentPopulation.get_agent(operator_id)

        # planning of the service vehicle, consists in a list of Stop objects
        self.planning = []

        # boolean indicating if the vehicle is idle
        self.isIdle = False

        # event triggered to send a signal to service vehicle
        self.signalEvent_ = self.sim.scheduler.new_event_object()

    # signaling

    def trigger_signal(self):

        former_event = self.signalEvent_

        self.signalEvent_ = self.sim.scheduler.new_event_object()

        former_event.succeed()

    # event tracing

    def trace_event(self, event):

        if isinstance(event, StopEvent):
            for request in event.pickups + event.dropoffs:
                request.agent.trace_event(event)

        if isinstance(event, StaffOperationEvent):
            if event.structure is not None:
                event.structure.trace_event(event)
            for target in event.targets:
                target.trace_event(event)

        # add event to own trace
        super().trace_event(event)

    # stop processing

    def process_stop_(self, stop):

        # get the stops to process
        dropoff = None
        pickup = None

        if stop.type == Stop.STOP_POINT:
            dropoff = stop.dropoffList
            pickup = stop.pickupList
        elif stop.type == Stop.PUT_REQUEST:
            dropoff = stop
        elif stop.type == Stop.GET_REQUEST:
            pickup = stop
        elif stop.type is None:
            self.planning.remove(stop)
            return
        else:
            self.log_message("Unknown stop type {} to process".format(stop.type))

        # trace a stop event
        stop_event = StopEvent(self.sim.scheduler.now(), self.operator, self, self.tripId, stop)

        # compute the dwell time duration
        dwell_time = self.compute_dwell_time(stop)
        # set the effective departure time of the current stop
        if stop.type == Stop.STOP_POINT:
            stop.effectiveDepartureTime[self.tripId] = self.sim.scheduler.now() + dwell_time
        else:
            stop.effectiveDepartureTime = self.sim.scheduler.now() + dwell_time

        # process the dropoffs
        processed_dropoff = []
        if dropoff is not None:
            if isinstance(dropoff, list):
                processed_dropoff = self.process_stop_list(dropoff)
            else:

                # remove stop from planning
                self.planning.remove(stop)

                processed_dropoff = self.process_user_stop(dropoff)

            if processed_dropoff is not None and processed_dropoff != []:
                self.log_message("Dropped off {}".format(processed_dropoff))

        # trace dropoffs
        stop_event.set_dropoffs(processed_dropoff, self.sim.scheduler.now())

        yield self.execute_process(self.spend_time_(dwell_time))

        # process the pickups
        processed_pickup = []
        if pickup is not None:

            # remove stop from planning
            self.planning.remove(stop)

            if isinstance(pickup, list):

                processed_pickup = self.process_stop_list(pickup)
            else:
                processed_pickup = self.process_user_stop(pickup)

            if processed_pickup is not None and processed_pickup != []:
                self.log_message("Picked up {}".format(processed_pickup))

        # trace pickups
        stop_event.set_pickups(processed_pickup, self.sim.scheduler.now())

        self.trace_event(stop_event)

    def process_stop_list(self, stop_list):
        """
        Method called for processing the stop point pickup or dropoff list

        :param stop_list: list of user stops to be processed
        :return: list of agent ids that where processed
        """

        # list of ids of the agents that were processed
        processed = []

        # make a copy of the list so stops can be removed from the original
        list_copy = copy(stop_list)

        # process all user stops of the list
        for user_stop in list_copy:

            # process user stop and get the agent id
            result = self.process_user_stop(user_stop)

            # if an agent was indeed processed
            if result is not None:

                # remove the user stop from the list
                stop_list.remove(user_stop)

                # add the agent id to the list of processed agents
                processed.append(result)

        # return the list of processed agents
        return processed

    def process_user_stop(self, user_stop):
        """
        Process the user stop if it is relevant,
        by calling either the pickup or dropoff method.

        The stop is processed if its trip matches the service vehicle,
        and if it respects the capacity constraints of the service vehicle

        :param user_stop: UserStop object
        :return: Boolean indicating if the user stop has been processed
        """

        # test if stop should be processed by this service vehicle
        if not self.serve_stop(user_stop):
            return

        # TODO : remove when dynamic travel times are added
        # log if process time is not now
        process_time = user_stop.get_process_time()
        if process_time is not None and process_time != self.sim.scheduler.now():
            self.log_message(
                "Stop {} should be processed at {}".format(user_stop, process_time), 30
            )

        request = self.operator.requests[user_stop.requestId]
        agent_id = request.agent.id
        agent = self.sim.agentPopulation.get_agent(agent_id)

        if user_stop.type == Stop.GET_REQUEST:

            # for the pickup requests, check the service vehicle capacity
            if self.load() + request.number <= self.seats:
                self.pickup(user_stop)
                return request
            else:
                self.exceeds_capacity(user_stop)
                return None

        elif user_stop.type == Stop.PUT_REQUEST:

            # cannot dropoff user if not in vehicle
            if agent not in self.occupants:
                return None
            else:
                self.dropoff(user_stop)
                return request

        else:
            self.log_message(
                "Unknown stop type for service vehicle : {}".format(user_stop.type), 30
            )
            return None

    def pickup(self, stop):
        """
        Realise the pickup of the given stop request.

        If the request has been cancelled, remove all the
        related stops of the planning

        :param stop: UserStop object, with type GET
        """

        # get the user's request from operator
        request = self.operator.requests[stop.requestId]

        # test if request has been cancelled
        if request.success is not None and not request.success:

            self.log_message("Request {} was dismissed, cannot pickup".format(request.id))
            # remove all related stops
            for stop in self.planning:
                if stop.type == stop.GET_REQUEST and stop.requestId == request.id:
                    self.planning.remove(stop)
            return

        # update request success
        request.success = True
        request.result = self
        if stop.requestedTime is not None:
            request.waitSequence += [self.sim.scheduler.now() - stop.requestedTime]

        # trace request event
        request_event = RequestEvent(self.sim.scheduler.now(), request)
        request.agent.trace_event(request_event)

        # get service vehicle
        request.agent.get_vehicle(self)

        # wake-up user
        request.pickup_succeed()

    def dropoff(self, stop):
        """
        Realise the dropoff of the given stop request

        :param stop: UserStop object, with type PUT
        """

        # get the user's request from operator
        request = self.operator.requests[stop.requestId]

        # trace detour
        if request.directTravelTime is not None:
            detour = int(
                (request.dropoff.arrivalTime - request.pickup.departureTime)
                - request.directTravelTime
            )
            request.waitSequence += [detour]

        # leave service vehicle
        request.agent.leave_vehicle()

        # wake-up user
        request.dropoff_succeed()

        # move the request to the fulfilled collection
        # del self.operator.requests[stop.requestId]
        self.operator.fulfilled[stop.requestId] = request

    def serve_stop(self, user_stop):
        """
        Determine if the stop should be processed by the service vehicle.

        By default, use the trip id.

        :param user_stop: UserStop
        :return: boolean indicating if the stop should be processed
        """

        return user_stop.trip == self.tripId

    def exceeds_capacity(self, user_stop):
        """
        Execute the procedure for stops that cannot be picked up because of capacity.

        This method is called when a GET request cannot be served because
        of the capacity constraint.

        For instance, trigger the stop pickup event, or let the agent wait for another vehicle.

        :param user_stop: UserStop object
        """

        self.log_message("Cannot serve stop {}, the vehicle is full".format(user_stop))

    def compute_dwell_time(self, stop):
        """
        Compute the dwell time of the vehicle when processing the stop.

        The dwell time is spent between the dropoffs and the pickups.
        The computation method may differ depending if the stop is a StopPoint or
        a UserStop, or on the number of pickups and dropoffs.

        :param stop: Stop object

        :return: stop dwell time
        """

        # TODO : change, not very satisfying
        # get the dwell time for the stop
        if stop.type == Stop.STOP_POINT:
            arrival_time = stop.arrivalTime[self.tripId].pop(0)
            departure_time = stop.departureTime[self.tripId].pop(0)
            dwell_time = departure_time - arrival_time
        else:
            dwell_time = self.dwellTime

        return dwell_time

    # planning management and idle behaviour

    def set_planning(self, new_planning):
        """
        Set a new planning for the service vehicle.

        The planning change can imply a redirection or change the idle state
        of the service vehicle

        :param new_planning: list of Stop objects
        """

        # set the new planning
        self.planning = new_planning

        # change tempDestination, allowing dynamic redirection
        if len(self.planning) != 0:
            self.tempDestination = self.planning[0].position
        else:
            self.tempDestination = self.position

        # wake up the service vehicle if it was idle
        if self.isIdle and len(self.planning) != 0:
            try:
                self.current_process.succeed()
            except RuntimeError:
                self.log_message("Was already awake but had empty planning", 30)

    def insert_in_planning(self, request, indexes):
        """
        Insert the stops of the given request in the planning.

        :param request: TripRequest
        :param indexes: tuple of indexes for the insertion
        """

    def test_idle_(self):
        """
        Execute a certain behavior if the vehicle is idle.

        The vehicle is considered idle if its planning is empty. The idle
        behaviour is provided by the vehicle's operator.

        :return: yield the idle behaviour process
        """

        # if planning is empty
        if not self.planning:

            # vehicle starts being idle
            self.isIdle = True
            start_time = self.sim.scheduler.now()
            yield self.signalEvent_ | self.execute_process(
                self.operator.idle_behaviour_(self), True
            )

            # trace idle time
            self.isIdle = False
            idle_duration = self.sim.scheduler.now() - start_time
            if idle_duration > 0:
                self.trace_event(IdleEvent(self.sim.scheduler.now(), idle_duration))
