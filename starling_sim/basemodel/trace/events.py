"""
This module contains event classes that compose agents' traces
"""

from abc import ABC, abstractmethod
from builtins import hasattr
from xml.etree.ElementTree import Element


class Event:
    """
    This class represents the events contained in the trace.

    It should be extended to describe the different kinds of events of the simulation.
    """

    def __init__(self, time):

        # simulation time at which the event occurred
        self.timestamp = time

        # message from the simulation environment at event tracing
        self.message = ""

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def xml_attrib(self):
        attributes = self._get_xml_attrib()
        to_delete = []
        for key in attributes.keys():
            if hasattr(attributes[key], "id"):
                attributes[key] = getattr(attributes[key], "id", "")
            if key.endswith("_"):
                to_delete.append(key)

        for key in to_delete:
            del attributes[key]

        attributes = {k: str(v) for k, v in attributes.items()}

        if "message" in attributes:
            del attributes["message"]

        return attributes

    def to_xml(self) -> Element:
        # create XML Element
        element = Element(self.name, attrib=self.xml_attrib)

        # add eventual message
        if self.message:
            element.text = self.message

        # add eventual sub elements
        sub_elements = self._xml_sub_elements()
        if sub_elements:
            for sub_element in sub_elements:
                element.append(sub_element)

        return element

    def _get_xml_attrib(self) -> dict:
        return self.__dict__.copy()

    def _xml_sub_elements(self) -> list | None:
        return None

    def __str__(self):
        # get attributes without timestamp
        attributes = self.xml_attrib
        del attributes["timestamp"]
        str_attributes = ", ".join([f"{k}={v}" for k, v in attributes.items()])

        # get message
        message = f", {self.message}" if self.message else ""

        # format
        res = "[{timestamp}, {event}{message}]: {attributes}"
        return res.format(
            timestamp=self.timestamp, event=self.name, message=message, attributes=str_attributes
        )


class DurationEvent(Event, ABC):
    """
    This abstract event describes an event that takes place over several time steps.
    """

    @property
    def total_duration(self):
        """
        Get the total duration of the event.

        :return: integer describing the total event duration
        """
        return self._total_duration()

    @abstractmethod
    def _total_duration(self) -> int:
        raise NotImplementedError


class InputEvent(Event):
    """
    This event describes the generation of a traced element.
    """

    def __init__(self, time, agent):
        """
        Creates a generation event.

        :param time: timestamp of the generation
        :param agent: generated agent
        """
        super().__init__(time)

        self.id = agent.id
        self.agentType = agent.type
        self.mode = agent.mode
        self.icon = agent.icon


class MoveEvent(DurationEvent):
    """
    This event describes an agent moving
    """

    def __init__(self, time, origin, destination, move_distance, move_duration, mode):
        """
        Creates a moving event
        :param time: timestamp of departure
        :param origin: origin position
        :param destination: destination position
        :param move_distance: move distance
        :param move_duration: time spent moving
        :param mode: transport mode ("walk", "bike", "drive",..)
        """

        super().__init__(time)
        self.origin = origin
        self.destination = destination
        self.distance = move_distance
        self.duration = move_duration
        self.mode = mode

    def _total_duration(self) -> int:
        return self.duration


class RouteEvent(MoveEvent):
    """
    This event describes the route of an agent
    """

    def __init__(self, time, route_data, mode):
        """
        Creates a route event.

        :param time: timestamp of the route departure
        :param route_data: {"route": list of nodes,
            "length": list of link lengths, "time": list of link durations}
        :param mode: transport mode ("walk", "bike", "drive",..)
        :return:
        """

        super().__init__(
            time,
            route_data["route"][0],
            route_data["route"][-1],
            sum(route_data["length"]),
            sum(route_data["time"]),
            mode,
        )

        self.data = route_data

    def set_route_data(self, route_data):
        self.data = route_data
        self.origin = route_data["route"][0]
        self.destination = route_data["route"][-1]
        self.distance = sum(route_data["length"])
        self.duration = sum(route_data["time"])

    def get_route_data_in_interval(self, start_time, end_time):
        durations = self.data["time"]
        distances = self.data["length"]

        index = 0

        interval_durations = []
        interval_distances = []

        current_timestamp = self.timestamp

        while index < len(durations) and (
            current_timestamp < end_time
            or (current_timestamp == end_time and durations[index] == 0)
        ):
            segment_duration = durations[index]
            segment_distance = distances[index]

            if current_timestamp < start_time:
                # current segment is before the interval
                if current_timestamp + segment_duration <= start_time:
                    current_timestamp += segment_duration
                # current segment steps over the interval start
                else:
                    # evaluate part that is in the interval
                    duration_in_interval = current_timestamp + segment_duration - start_time
                    interval_durations.append(duration_in_interval)
                    interval_distances.append(
                        round(segment_distance * duration_in_interval / segment_duration)
                    )
                    current_timestamp += segment_duration
            else:
                # current segment is in the interval
                if current_timestamp + segment_duration <= end_time:
                    interval_durations.append(segment_duration)
                    interval_distances.append(segment_distance)
                    current_timestamp += segment_duration
                # current segment steps over the interval end
                else:
                    # evaluate part that is in the interval
                    duration_in_interval = end_time - current_timestamp
                    interval_durations.append(duration_in_interval)
                    interval_distances.append(
                        round(segment_distance * duration_in_interval / segment_duration)
                    )
                    current_timestamp = end_time

            index += 1

        return {"time": interval_durations, "length": interval_distances}

    def _xml_sub_elements(self) -> list | None:
        sub_elements = []

        route = self.data["route"]
        length = self.data["length"]
        time = self.data["time"]
        from_position = route[0]

        for i in range(1, len(self.data["route"])):
            to_position = route[i]
            edge_element = Element(
                "edge",
                attrib={
                    "from": str(from_position),
                    "to": str(to_position),
                    "length": str(length[i]),
                    "time": str(time[i]),
                },
            )

            sub_elements.append(edge_element)
            from_position = to_position

        return sub_elements

    def _get_xml_attrib(self):
        res = {k: str(v) for k, v in self.__dict__.items()}
        del res["data"]
        return res


class PositionChangeEvent(MoveEvent):
    """
    This event describes a position change of an agent
    """

    def __init__(self, time, origin, destination, distance, duration, mode):
        """
        Creates a position change event
        :param destination:
        :param distance:
        :param duration:
        :param time: timestamp of the traced event
        :param origin: describes a position, e.g. a node id
        :param mode: transport mode used to reach this position
        """
        super().__init__(time, origin, destination, distance, duration, mode)


class WaitEvent(DurationEvent):
    """
    This event describes the a waiting agent
    """

    def __init__(self, time, reason, waiting_time):
        """
        Creates a wait event
        :param time: timestamp of the waiting start
        :param reason: reason of the waiting event
        :param waiting_time: waited duration
        """
        super().__init__(time)
        self.reason = reason
        self.waiting_time = waiting_time

    def _total_duration(self):
        return self.waiting_time


class IdleEvent(Event):
    """
    This event describes an idle agent
    """

    def __init__(self, time, idle_duration):
        """
        Creates an idle event
        :param time: start of the idle period
        :param idle_duration: duration of the idle period
        """

        super().__init__(time)
        self.duration = idle_duration


class ServiceEvent(Event):
    """
    This event describes a status change of an agent service.
    """

    def __init__(self, time, former_status, new_status):
        super().__init__(time)
        # former and new status values
        self.former = former_status
        self.new = new_status


class RequestEvent(DurationEvent):
    """
    This event describes a user request
    """

    def __init__(self, time, request):
        """
        Creates a request event
        :param time: timestamp of the request
        :param request: Request object
        """
        super().__init__(time)

        self.agent = request.agent
        self.requestTime = request.timestamp
        self.type = request.type
        self.structure = request.structure
        self.success = request.success
        self.result = request.result
        self.waitSequence = request.waitSequence

    def _total_duration(self):
        return sum(self.waitSequence)


class StopEvent(Event):
    """
    This event describes the processing of a Stop
    """

    def __init__(self, time, operator, service_vehicle, trip, stop):
        super().__init__(time)

        self.operator = operator
        self.serviceVehicle = service_vehicle
        self.stop = ""
        if stop.type == stop.STOP_POINT:
            self.stop = stop.id
        elif hasattr(stop, "stopPoint"):
            self.stop = stop.stopPoint

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

    def _xml_sub_elements(self) -> list | None:

        sub_elements = []

        for request in self.dropoffs:
            element = Element(
                "dropoff",
                attrib={
                    "timestamp": str(self.dropoff_time),
                    "agent": request.agent.id,
                },
            )
            sub_elements.append(element)

        for request in self.pickups:
            element = Element(
                "pickup",
                attrib={
                    "timestamp": str(self.pickup_time),
                    "agent": request.agent.id,
                },
            )
            sub_elements.append(element)

        return sub_elements

    def _get_xml_attrib(self):
        attrib = super()._get_xml_attrib()
        del attrib["pickups"]
        del attrib["dropoffs"]

        return attrib


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

    def __init__(self, time, staff, total, goal, targets=None, structure=None):
        """
        Create a staff operation event.

        :param time: timestamp of the staff operation event
        :param staff: staff realising the operation
        :param total: relative number corresponding to operations realised
        :param goal: objective of operation to realise
        :param targets: list of operation targets
        :param structure: structure where the operation is realised
        """

        super().__init__(time)

        self.staff = staff
        self.total = total
        self.goal = goal
        self.targets = targets
        if targets is None:
            self.targets = []
        self.structure = structure


class GetVehicleEvent(Event):
    """
    This event describes an agent getting a vehicle
    """

    def __init__(self, time, agent, vehicle):
        """
        Creates a get vehicle event
        :param time: timestamp of the get event
        :param agent: new occupant
        :param vehicle: concerned vehicle
        """
        super().__init__(time)
        self.agent = agent
        self.vehicle = vehicle


class LeaveVehicleEvent(Event):
    """
    This event describes an agent returning a vehicle
    """

    def __init__(self, time, agent, vehicle):
        """
        Creates a leave vehicle event
        :param time: timestamp of the return event
        :param agent: agent returning vehicle
        :param vehicle: concerned vehicle
        """
        super().__init__(time)
        self.agent = agent
        self.vehicle = vehicle


class LeaveSystemEvent(Event):
    """
    This event describes an agent leaving the simulation
    """

    def __init__(self, time):
        super().__init__(time)


class DestinationReachedEvent(Event):
    """
    This event describes an agent reaching its destination
    """

    def __init__(self, time):
        super().__init__(time)


class LeaveSimulationEvent(Event):
    """
    This event describes an agent leaving the simulation.
    """

    def __init__(self, time, cause):
        super().__init__(time)

        # leave code
        self.cause = cause


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
