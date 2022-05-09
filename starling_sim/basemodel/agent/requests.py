"""
This module regroups the classes describing
the requests made by an agent during the simulation.

Requests are used for the interaction between users and operators.

Stops describe the action of a service vehicle, for instance picking up a user.
"""


class Request:
    """
    Class describing a request made by an agent.
    """

    GET_REQUEST = "GET"
    PUT_REQUEST = "PUT"
    TAXI_REQUEST = "TAXI"

    STR_LIST = ["structure", "position", "type"]

    def __init__(
        self, agent, timestamp, structure=None, position=None, request_type=None, prebooked=None
    ):
        """
        Creation of a new request.

        :param agent: agent making the request
        :param timestamp: time when the request was made
        :param structure: structure requested by the agent
        :param position: request's position
        :param request_type: type of request
        """

        # requesting agent
        self.agent = agent

        # timestamp of the request
        self.timestamp = timestamp

        # requested structure
        self.structure = structure

        # target position of the request
        self.position = position

        # request type
        self.type = request_type

        # prebooked request
        self.prebooked = prebooked

        # SimPy Event, can be used by the agent as a callback
        self.event_ = None

        # request success
        self.success = None

        # request result
        self.result = None

        # sequence of waiting times due to request
        self.waitSequence = []

    def set_request_event(self, event=None):
        """
        Set the event attribute with the given SimPy event.

        By default, the a basic Event object is added, which can be triggered
        using the succeed method.

        If the request has no agent, try to get the scheduler from the structure.

        :param event: SimPy Event object
        """

        if event is None:
            if self.agent is None:
                event = self.structure.sim.scheduler.new_event_object()
            else:
                event = self.agent.sim.scheduler.new_event_object()

        self.event_ = event

    def succeed(self, new_event=None):
        """
        Trigger the request event as successful and replace it with the new event.

        :param new_event: SimPy Event object
        """

        former_event = self.event_

        self.set_request_event(new_event)

        former_event.succeed()

    def fail(self, new_event=None):
        """
        Trigger the request event as failed and replace it with the new event.

        :param new_event: SimPy Event object
        """
        former_event = self.event_

        self.set_request_event(new_event)

        # TODO : need an exception argument ?
        former_event.fail()

    def cancel(self):
        """
        Set success to false and call the structure cancel method.
        """

        self.success = False

        self.structure.cancel_request(self)

    def __str__(self):
        """
        Give string display to the request.

        :return: string with some of the request information
        """

        fill_string = "requestTime=" + str(self.timestamp) + ", agent=" + str(self.agent.id)

        for attr_name in self.STR_LIST:
            attribute = self.__getattribute__(attr_name)
            if attribute is not None:
                if attr_name == "structure":
                    attribute = attribute.id
                fill_string += ", " + attr_name + "=" + str(attribute)

        fill_string += ", success={}, result={}, waitDurations={}"

        return fill_string.format(self.success, self.result, self.waitSequence)

    def __repr__(self):

        return self.__str__()


class StationRequest(Request):
    """
    Class describing a request made to a vehicle station.
    """

    def __init__(self, agent, timestamp, station, request_type):
        """
        Creation of a new station request

        :param agent: agent making the request
        :param timestamp: time when the request was made
        :param station: station requested by the agent
        :param request_type: type of the request
        """

        super().__init__(agent, timestamp, structure=station, request_type=request_type)


class TripRequest(Request):
    """
    Class describing a trip request made to a service operator.
    """

    STR_LIST = ["structure", "id", "position", "type"]

    def __init__(self, agent, timestamp, operator, number, request_id, trip_id=None):
        """
        Creation of a new trip request.

        :param agent: agent making the request
        :param timestamp: time when the request was made
        :param operator: operator requested by the agent
        :param number: number of seats requested
        :param request_id: id of the trip request, stored by the operator
        :param trip_id: if of the request trip, or None
        """

        super().__init__(agent, timestamp, structure=operator)

        # trip request id
        self.id = request_id

        # store the id of the request trip, if there is one
        self.tripId = trip_id

        # store the agent number
        self.number = number

        # store the direct travel time
        self.directTravelTime = None

        # trip stops

        # pickup stop
        self.pickup = None

        # dropoff stop
        self.dropoff = None

        # stops events

        # pickup event
        self.pickupEvent_ = self.structure.sim.scheduler.new_event_object()

        # dropoff event
        self.dropoffEvent_ = self.structure.sim.scheduler.new_event_object()

    def set_stops(self, pickup_request, dropoff_request):
        """
        Set the pickup and dropoff attributes of the request.

        :param pickup_request: UserStop object with type "GET"
        :param dropoff_request: UserStop object with type "PUT"
        """

        # set agent number
        pickup_request.number = self.number
        dropoff_request.number = self.number

        # set pickup twin stop
        pickup_request.set_twin_stop(dropoff_request)

        # set pickup stop
        self.pickup = pickup_request

        # set dropoff twin stop
        dropoff_request.set_twin_stop(pickup_request)

        # set dropoff stop
        self.dropoff = dropoff_request

    def set_trip(self, trip_id):
        """
        Set the pickup and dropoff trip id, if they are UserStops.

        :param trip_id:
        """

        self.tripId = trip_id

        if isinstance(self.pickup, UserStop) and isinstance(self.dropoff, UserStop):
            self.pickup.tripId = trip_id
            self.dropoff.tripId = trip_id

    def pickup_succeed(self):

        self.pickupEvent_.succeed()

    def dropoff_succeed(self):

        self.dropoffEvent_.succeed()


class Stop:
    """
    Class describing a stop in a service vehicle planning
    """

    GET_REQUEST = "GET"
    PUT_REQUEST = "PUT"
    TAXI_REQUEST = "TAXI"
    STOP_POINT = "STOP_POINT"
    REPOSITIONING = "REPOSITIONING"

    def __init__(self, position, stop_type):
        """
        Creation of a new stop.

        As we make copies (deepcopy) of the stops for testing plannings,
        they cannot contain attributes such as Agent or SimPy.Event objects.

        :param position: position of the stop in the environment
        :param stop_type: type of stop, either "GET", "PUT" or "STOP_POINT"
        """

        # Indicates the way to process the stop
        self.type = stop_type

        # position of the stop in the environment
        self.position = position

        # planned or effective arrival time
        self.arrivalTime = None

        # planned or effective departure time
        self.departureTime = None

        # effective arrival time
        self.effectiveArrivalTime = None

        # effective departure time
        self.effectiveDepartureTime = None


class UserStop(Stop):
    """
    Class describing the stop of a user, either a pickup or dropoff.

    User stops can be used as is in the plannings, or grouped in stop points.

    User stops should be grouped by pair (pickup and dropoff) in TripRequest objects,
    using the setup_stops method.
    """

    def __init__(
        self,
        stop_type,
        position,
        request_id,
        requested_time=None,
        max_time=None,
        max_travel_time=None,
        stop_point_id=None,
        trip_id=None,
    ):
        """
        Creation of a new user stop.

        :param stop_type: type of user stop, either "GET" or "PUT"
        :param position: position of the user stop in the environment
        :param request_id: id of the corresponding TripRequest
        :param requested_time: time requested for the stop.
            Default is None, no min constraint on the stop service time.
        :param max_time: maximum service time accepted.
            Default is None, no max constraint on the stop service time.
        :param max_travel_time: maximum duration of the TripRequest travel.
            Default is None, no constraint on the trip travel time.
        :param stop_point_id: id of the stop point, if relevant
        :param trip_id: id of the requested trip, if relevant
        """

        super().__init__(position, stop_type)

        # id of the request made to the service operator
        self.requestId = request_id

        # twin user stop, the other stop of the same trip request
        self.twin = None

        # store the agent number
        self.number = None

        # id of the stop point if the user stop is part of a stop point
        self.stopPoint = stop_point_id

        # id of the requested trip, used to match the service vehicle. None matches all trips
        self.trip = trip_id

        # constraints on the service time

        # requested stop time (and then minimum stop time)
        # if None, the stop can be processed up as soon as possible
        self.requestedTime = requested_time

        # maximum process time
        # if None, the stop can be processed as late as wanted
        self.maxTime = max_time

        # maximum travel time
        # if None, no constraint on the trip travel time
        self.maxTravelTime = max_travel_time

    def get_process_time(self):
        """
        Get the time of the effective stop processing.

        Pickups are processed at departure time, and dropoffs
        are processed at arrival time.

        :return: process time of the stop
        """

        if self.type == self.GET_REQUEST:
            return self.departureTime
        elif self.type == self.PUT_REQUEST:
            return self.arrivalTime
        else:
            raise ValueError("Unsupported type {} for UserStop".format(self.type))

    def set_twin_stop(self, twin_stop):
        """
        Set the user stop twin stop.

        :param twin_stop: UserStop object
        """

        self.twin = twin_stop

    def is_feasible(self):
        """
        Check if the stop point is feasible, ie if the time constraints are respected.

        :return: Boolean indicating if the user stop is feasible
        """

        travel_time = None

        # compute the stop service time and travel time if relevant
        if self.type == self.GET_REQUEST:

            service_time = self.departureTime

            if service_time is not None and self.twin.arrivalTime is not None:
                travel_time = self.twin.arrivalTime - service_time

        elif self.type == self.PUT_REQUEST:

            service_time = self.arrivalTime

            if service_time is not None and self.twin.arrivalTime is not None:
                travel_time = service_time - self.twin.departureTime

        else:
            return False

        # check the min service time constraint
        if self.requestedTime is None:
            after_requested = True
        else:
            after_requested = self.requestedTime <= service_time

        # check the max service time constraint
        if self.maxTime is None:
            before_max = True
        else:
            before_max = service_time <= self.maxTime

        # check the max travel time constraint
        if self.maxTravelTime is None or travel_time is None:
            not_too_long = True
        else:
            not_too_long = travel_time <= self.maxTravelTime

        return after_requested and before_max and not_too_long

    def __str__(self):
        """
        Give a string display to the user stop.

        :return: string with some of the user stop information
        """

        fill_string = (
            "[requestId={}, stopType={}, position={}, arrivalTime={}, "
            "departureTime={}, requestedTime={}, maxTime={}]"
        )

        return fill_string.format(
            self.requestId,
            self.type,
            self.position,
            self.arrivalTime,
            self.departureTime,
            self.requestedTime,
            self.maxTime,
        )

    def __repr__(self):

        return self.__str__()


class StopPoint(Stop):
    """
    Class describing a stop point, where several user stops can be grouped.

    Stop points may be serviced by several vehicles following different trips.
    Servicing a stop point means servicing all the user stops that correspond
    to the service vehicle trip
    """

    def __init__(self, position, stop_id, name="unnamed_stop"):
        """
        Creation of a new stop point.

        :param position: position of the stop in the environment
        :param stop_id: id of the stop point, stored by the operator
        :param name: name of the stop point, for instance "République"
        """

        super().__init__(position, self.STOP_POINT)

        # id of the stop point, used for describing the service trips
        self.id = stop_id

        # name of the stop point, for a better readability
        self.name = name

        # list of user pickups at this stop
        self.pickupList = []

        # list of user dropoffs at this stop
        self.dropoffList = []

        # dict of the arrival times of this stop point, of the form {trip_id: arrival_time}
        self.arrivalTime = dict()

        # dict of the departure times of this stop point, of the form {trip_id: departure_time}
        self.departureTime = dict()

        # dict of the effective arrival times of this stop point, of the form {trip_id: arrival_time}
        self.effectiveArrivalTime = dict()

        # dict of the effective departure times of this stop point, of the form {trip_id: departure_time}
        self.effectiveDepartureTime = dict()

    def __str__(self):
        """
        Give a string display to the stop point.

        :return: string with some of the stop point information
        """
        return "[name={}, id={}, position={}]".format(self.name, self.id, self.position)

    def __repr__(self):

        return self.__str__()


class Operation(Stop):
    def __init__(self, stop_type, position, total, targets=None, station_id=None):
        """
        Creation of a new operation.

        :param stop_type: type of the operation (REPOSITIONING, ..)
        :param position: position in the environment
        :param total: relative number corresponding to operations realised
        :param targets: list of operation targets, or None
        :param station_id: id of the target station, or None
        """

        super().__init__(position, stop_type)

        # operations realised at this stop (may be negative, for instance when picking up vehicles)
        self.total = total

        # targets of the operation (None if there are no specific targets)
        self.targets = targets

        # id of the station, if there is one
        self.station = station_id

    def __str__(self):
        """
        Give a string display to the operation.

        :return: string with some of the operation information
        """

        return "[type={}, total={}, position={}, station={}]".format(
            self.type, self.total, self.position, self.station
        )

    def __repr__(self):

        return self.__str__()
