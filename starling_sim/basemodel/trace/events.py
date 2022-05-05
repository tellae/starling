"""
This module contains event classes that compose agents' traces
"""


class Event:
    """
    This class represents the events contained in the trace

    It should be extended to describe the different kinds of events of the agents
    """

    def __init__(self, time, message=""):
        """

        :param time: timestamp of the traced event
        :param message: eventual message to be added to the event
        """
        self.timestamp = time
        self.message = message

    def __str__(self):
        """
        Gives a string display to the event
        """

        if self.message == "":
            return "[{}, {}]: ".format(self.timestamp, self.__class__.__name__)
        else:
            return "[{}, {}, {}]: ".format(self.message, self.__class__.__name__, self.timestamp)


class InputEvent(Event):
    """
    This event describes the generation of a traced element.
    """

    def __init__(self, time, element, message=""):
        """
        Creates a generation event
        :param time: timestamp of the generation
        :param element: generated element
        :param message: eventual message to be added to the event
        """
        super().__init__(time, message=message)
        self.element = element

    def __str__(self):

        return super().__str__() + "generatedElement={}, type={}".format(
            self.element, type(self.element)
        )


class MoveEvent(Event):
    """
    This event describes an agent moving
    """

    def __init__(self, time, move_distance, move_duration, mode, message=""):
        """
        Creates a moving event
        :param time: timestamp of departure
        :param move_distance: move distance
        :param move_duration: time spent moving
        :param mode: transport mode ("walk", "bike", "drive",..)
        :param message: eventual message to be added to the event
        """

        super().__init__(time, message=message)

        self.distance = move_distance
        self.duration = move_duration
        self.mode = mode


class RouteEvent(MoveEvent):
    """
    This event describes the route of an agent
    """

    def __init__(self, time, route_data, mode, message=""):
        """
        Creates a route event.

        :param time: timestamp of the route departure
        :param route_data: {"route": list of nodes,
            "length": list of link lengths, "time": list of link durations}
        :param mode: transport mode ("walk", "bike", "drive",..)
        :param message: eventual message to be added to the event
        :return:
        """

        super().__init__(
            time, sum(route_data["length"]), sum(route_data["time"]), mode, message=message
        )

        self.data = route_data

    def set_route_data(self, route_data):

        self.data = route_data
        self.distance = sum(route_data["length"])
        self.duration = sum(route_data["time"])

    def __str__(self):

        return super().__str__() + "mode={}, start={}, end={}, duration={}, distance={}".format(
            self.mode, self.data["route"][0], self.data["route"][-1], self.duration, self.distance
        )


class PositionChangeEvent(MoveEvent):
    """
    This event describes a position change of an agent
    """

    def __init__(self, time, origin, destination, distance, duration, mode, message=""):
        """
        Creates a position change event
        :param destination:
        :param distance:
        :param duration:
        :param time: timestamp of the traced event
        :param origin: describes a position, e.g. a node id
        :param mode: transport mode used to reach this position
        :param message: eventual message to be added to the event
        """
        super().__init__(time, distance, duration, mode, message)

        self.origin = origin
        self.destination = destination

    def __str__(self):
        return super().__str__() + "mode={}, start={}, end={}, duration={}, distance={}".format(
            self.mode, self.origin, self.destination, self.duration, self.distance
        )


class WaitEvent(Event):
    """
    This event describes the a waiting agent
    """

    def __init__(self, time, reason, waiting_time, message=""):
        """
        Creates a wait event
        :param time: timestamp of the waiting start
        :param reason: reason of the waiting event
        :param waiting_time: waited duration
        :param message: eventual message to be added to the event
        """
        super().__init__(time, message)
        self.reason = reason
        self.waiting_time = waiting_time

    def __str__(self):

        return super().__str__() + "waitedTime={}, reason={}".format(self.waiting_time, self.reason)


class IdleEvent(Event):
    """
    This event describes an idle agent
    """

    def __init__(self, time, idle_duration, message=""):
        """
        Creates an idle event
        :param time: start of the idle period
        :param idle_duration: duration of the idle period
        :param message: eventual message to be added to the event
        """

        super().__init__(time, message)
        self.duration = idle_duration

    def __str__(self):

        return super().__str__() + "idleDuration={}".format(self.duration)


class RequestEvent(Event):
    """
    This event describes a user request
    """

    def __init__(self, time, request, message=""):
        """
        Creates a request event
        :param time: timestamp of the request
        :param request: Request object
        :param message: eventual message to be added to the event
        """
        super().__init__(time, message)
        self.request = request

    def __str__(self):

        return super().__str__() + str(self.request)


class StopEvent(Event):
    """
    This event describes the processing of a Stop
    """

    def __init__(self, time, operator, service_vehicle, trip, stop, message=""):

        super().__init__(time, message)

        self.operator = operator
        self.serviceVehicle = service_vehicle
        self.stop = stop
        self.trip = trip

        # list of requests served during dropoff
        self.dropoffs = []
        self.dropoff_time = None

        # list of requests served during pickup
        self.pickups = []
        self.pickup_time = None

    def set_dropoffs(self, dropoffs, dropoff_time):

        if dropoffs is None:
            dropoffs = []
        elif not isinstance(dropoffs, list):
            dropoffs = [dropoffs]

        self.dropoffs = dropoffs
        self.dropoff_time = dropoff_time

    def set_pickups(self, pickups, pickup_time):

        if pickups is None:
            pickups = []
        elif not isinstance(pickups, list):
            pickups = [pickups]

        self.pickups = pickups
        self.pickup_time = pickup_time

    def __str__(self):

        return super().__str__() + "stop={}, trip={}, serviceVehicle={}".format(
            self.stop, self.trip, self.serviceVehicle.id
        )


# deprecated, use StopEvent
# class PickupEvent(StopEvent):
#     """
#     This event describes the processing of a pickup
#     """
#
#     def __init__(self, time, operator, service_vehicle, trip, stop, pickups, message=""):
#
#         super().__init__(time, operator, service_vehicle, trip, stop, message=message)
#
#         if not isinstance(pickups, list):
#             pickups = [pickups]
#
#         self.pickups = pickups
#
#     def __str__(self):
#
#         return super().__str__() + "serviceVehicle={}, stop={}, trip={}, pickups={}"\
#             .format(self.serviceVehicle.id, str(self.stop), self.trip, self.pickups)
#
#
# # deprecated, use StopEvent
# class DropoffEvent(StopEvent):
#     """
#     This event describes the processing of a dropoff
#     """
#
#     def __init__(self, time, operator, service_vehicle, trip, stop, dropoffs, message=""):
#
#         super().__init__(time, operator, service_vehicle, trip, stop, message=message)
#
#         if not isinstance(dropoffs, list):
#             dropoffs = [dropoffs]
#
#         self.dropoffs = dropoffs
#
#     def __str__(self):
#
#         return super().__str__() + "serviceVehicle={}, stop={}, trip={}, dropoffs={}"\
#             .format(self.serviceVehicle.id, str(self.stop), self.trip, self.dropoffs)
#


class StaffOperationEvent(Event):
    """
    This event describes a staff operation
    """

    def __init__(self, time, staff, total, goal, targets=None, structure=None, message=""):
        """
        Create a staff operation event.

        :param time: timestamp of the staff operation event
        :param staff: staff realising the operation
        :param total: relative number corresponding to operations realised
        :param goal: objective of operation to realise
        :param targets: list of operation targets
        :param structure: structure where the operation is realised
        """

        super().__init__(time, message)

        self.staff = staff
        self.total = total
        self.goal = goal
        self.targets = targets
        if targets is None:
            self.targets = []
        self.structure = structure

    def __str__(self):
        if self.structure is None:
            struct = None
        else:
            struct = self.structure.id
        return super().__str__() + "staff={}, total={}, structure={}".format(
            self.staff.id, self.total, struct
        )


class GetVehicleEvent(Event):
    """
    This event describes an agent getting a vehicle
    """

    def __init__(self, time, agent, vehicle, message=""):
        """
        Creates a get vehicle event
        :param time: timestamp of the get event
        :param agent: new occupant
        :param vehicle: concerned vehicle
        :param message: eventual message to be added to the event
        """
        super().__init__(time, message)
        self.agent = agent
        self.vehicle = vehicle

    def __str__(self):

        return super().__str__() + "agent={}, getVehicle={}".format(self.agent.id, self.vehicle.id)


class LeaveVehicleEvent(Event):
    """
    This event describes an agent returning a vehicle
    """

    def __init__(self, time, agent, vehicle, message=""):
        """
        Creates a leave vehicle event
        :param time: timestamp of the return event
        :param agent: agent returning vehicle
        :param vehicle: concerned vehicle
        :param message: eventual message to be added to the event
        """
        super().__init__(time, message)
        self.agent = agent
        self.vehicle = vehicle

    def __str__(self):

        return super().__str__() + "agent={}, leaveVehicle={}".format(
            self.agent.id, self.vehicle.id
        )


class LeaveSystemEvent(Event):
    """
    This event describes an agent leaving the simulation
    """

    def __init__(self, time, message=""):
        super().__init__(time, message=message)

    def __str__(self):

        return super().__str__() + "leavingSystem={}".format(self.timestamp)


class DestinationReachedEvent(Event):
    """
    This event describes an agent reaching its destination
    """

    def __init__(self, time, message=""):
        super().__init__(time, message=message)

    def __str__(self):

        return super().__str__() + "arrivalTime={}".format(self.timestamp)


class LeaveSimulationEvent(Event):
    """
    This event describes an agent leaving the simulation.
    """

    def __init__(self, time, agent, cause, message=""):

        super().__init__(time, message=message)

        # agent leaving the simulation
        self.agent = agent

        #
        self.cause = cause

    def __str__(self):

        return super().__str__() + "agent={}, cause={}".format(self.agent, self.cause)


# class EndOfSimulationEvent(Event):
#     """
#     This event describes the end of the simulation
#     """
#
#     def __init__(self, time, message=""):
#         """
#         Creates an end of simulation event
#         :param time: timestamp of simulation end
#         :param message: eventual message to be added to the event
#         """
#         super().__init__(time, message=message)
#
#     def __str__(self):
#
#         return super().__str__() + "simulationEndTime={}" \
#             .format(self.timestamp)
