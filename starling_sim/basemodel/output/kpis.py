from starling_sim.basemodel.trace.events import *
from starling_sim.basemodel.agent.requests import UserStop, StopPoint, StationRequest
from starling_sim.utils.constants import (
    SERVICE_INIT,
    SERVICE_UP,
    SERVICE_PAUSE,
    SERVICE_END,
)
import inspect
from abc import ABC, abstractmethod
import math


class KPI(ABC):
    """
    Generic structure of a KPI class

    Its sub-classes compute and update specific indicator
    from given events
    """

    # indicates if this KPI is compatible with time profiling
    PROFILE_COMPATIBILITY = True

    #: **agentId**: id of the agent
    KEY_ID = "agentId"

    def __init__(self, export_keys: list = None):
        """
        The indicator_dict associates values to the indicators names

        The keys attribute correspond to the keys of the indicator_dict
        """

        self.kpi_output = None

        # list of indicator names of this KPI
        self.keys = []
        self._export_keys = export_keys

        # current agent on which KPI is evaluated
        self.agent = None

        # event time follow up
        self.current_timestamp = None

        # indicators evaluation attributes
        self.indicator_dict = None

        # time profiling
        self.profile = None
        self.current_profile_index = 0

    @property
    def export_keys(self):
        return self._export_keys if self._export_keys is not None else self.keys

    def _init_keys(self):
        # return class attributes starting with "KEY_"
        keys = list(
            map(
                lambda x: x[1],
                filter(
                    lambda x: x[0].startswith("KEY_"),
                    inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a))),
                ),
            )
        )
        keys.remove(self.KEY_ID)
        return keys

    def new_indicator_dict(self):
        """
        Evaluate indicators starting values

        :return: dict with keys in self.keys
        """
        return {key: 0 for key in self.keys}

    def setup(self, kpi_output, simulation_model):
        """
        Setup method called during simulation setup.

        After calling this method, the `keys` attribute should be set.

        :param kpi_output: parent KpiOutput
        :param simulation_model:
        """
        self.kpi_output = kpi_output
        time_profile = self.kpi_output.sim.scenario["kpi_time_profile"]
        if self.PROFILE_COMPATIBILITY and time_profile:
            if isinstance(time_profile, bool):
                # default profile is one hour intervals until simulation ends
                self.profile = [
                    hour * 3600
                    for hour in range(math.ceil(self.kpi_output.sim.scenario["limit"] / 3600))
                ]
            else:
                # otherwise, use provided time profile (add missing 0)
                self.profile = time_profile if time_profile[0] == 0 else [0] + time_profile

        self._indicators_setup(simulation_model)
        self.keys = self._init_keys()

    def _indicators_setup(self, simulation_model):
        """
        Setup attributes that need the simulation model to be initialised.
        """
        pass

    def evaluate_for_agent(self, agent):
        """
        Evaluate KPI indicators for the given agent.

        Indicators are evaluated by browsing the agent's
        events in chronological and updating values according
        to the KPI description.

        :param agent: Traced agent
        """
        # reset kpi
        self.reset_for_agent(agent)

        # browse agent's events in chronological order
        events = sorted(agent.trace.eventList, key=lambda x: x.timestamp)
        for event in events:
            self.update_from_event(event)

        # signal end of events
        self.end_of_events()

    def reset_for_agent(self, agent):
        """
        Reset indicators of the KPI in preparation of a new evaluation.

        :param agent:
        """
        # set studied agent
        self.agent = agent
        # reset indicators attributes
        self.current_timestamp = 0
        self.indicator_dict = self.new_indicator_dict()
        self.current_profile_index = 0

    def end_of_events(self):
        """
        Execute certain actions when the event list evaluation has ended.
        """
        if self.profile:
            # if profiling is on, fill rows until the last profile interval
            while self.current_profile_index < len(self.profile):
                self.end_of_profile_range()
        else:
            # otherwise, just add a row containing the KPI evaluation
            self.new_kpi_row()

    def end_of_profile_range(self):
        """
        Add a new row with indicators of current interval and jump to the next one.
        """
        self.current_profile_index += 1
        self.new_kpi_row()

    def new_kpi_row(self):
        """
        Add a new row to the output table.

        Indicators are reset after their data has been added to a row.
        """
        # add kpi row
        for key in self.export_keys:
            self.kpi_output.kpi_rows[key].append(self.indicator_dict[key])

        # reset indicators
        self.indicator_dict = self.new_indicator_dict()

    def is_in_later_profile(self, timestamp):
        """
        Test if time profiling is enabled and if the given timestamp is in a later profile interval.

        :param timestamp:
        :return: boolean indicating if timestamp in a later profile interval
        """
        return (
            self.profile
            and self.current_profile_index < len(self.profile) - 1
            and timestamp >= self.profile[self.current_profile_index + 1]
        )

    def update_from_event(self, event: Event):
        """
        Update indicators based on the event contents.

        If event is in a later profile interval, jump
        to the right interval before processing the event.

        :param event: Event instance
        """
        assert (
            event.timestamp >= self.current_timestamp
        ), "Event list should be ordered chronologically"

        # if event is in a later profile range, jump to it
        while self.is_in_later_profile(event.timestamp):
            self.end_of_profile_range()

        # update timestamp
        self.current_timestamp = event.timestamp

        self._update(event)

    def add_proportioned_indicators(self, event):
        # evaluate total duration of event
        if not isinstance(event, DurationEvent):
            raise ValueError(
                "add_proportioned_indicators should be called on DurationEvent instances"
            )
        total_duration = event.total_duration

        # while current profile does not contain profile end, add proportioned indicators and jump to next profile
        current_timestamp = event.timestamp
        while self.is_in_later_profile(event.timestamp + total_duration):
            # evaluate the duration spent in the current profile
            duration_current = self.profile[self.current_profile_index + 1] - current_timestamp

            # evaluate indicators for the current profile range
            self.evaluate_indicators_on_profile_range(event, current_timestamp, duration_current)

            self.end_of_profile_range()
            current_timestamp = self.profile[self.current_profile_index]

        duration_last = event.timestamp + total_duration - current_timestamp
        self.evaluate_indicators_on_profile_range(event, current_timestamp, duration_last)

    def evaluate_indicators_on_profile_range(self, event, current_timestamp, duration_on_range):
        """
        Evaluate and update KPI indicators for the given event on the specified time interval.

        :param event:
        :param current_timestamp:
        :param duration_on_range:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def _update(self, event):
        """
        Update the kpi values according to the event content and the agent.

        :param event: processed event
        :return:
        """


class MoveKPI(KPI):
    """
    This KPI evaluates the distance and spent time for each one of the simulation modes
    """

    #: **{mode}Distance**: distance travelled in <mode> [meters]
    SUFFIX_KEY_DISTANCE = "{mode}Distance"
    #: **{mode}Time**: time travelled in <mode> [seconds]
    SUFFIX_KEY_TIME = "{mode}Time"

    def __init__(self, **kwargs):
        self.modes = []
        super().__init__(**kwargs)

    def _indicators_setup(self, simulation_model):
        self.modes = list(simulation_model.environment.topologies.keys())

    def _init_keys(self):
        keys = []
        for mode in self.modes:
            keys.append(self.SUFFIX_KEY_DISTANCE.format(mode=mode))
            keys.append(self.SUFFIX_KEY_TIME.format(mode=mode))
        return keys

    def _update(self, event):
        if isinstance(event, MoveEvent):
            self.add_proportioned_indicators(event)

    def evaluate_indicators_on_profile_range(self, event, current_timestamp, duration_on_range):
        if duration_on_range == 0:
            duration = 0
            distance = event.distance
        else:
            if isinstance(event, RouteEvent):
                route_data = event.get_route_data_in_interval(
                    current_timestamp, current_timestamp + duration_on_range
                )
                duration = sum(route_data["time"])
                distance = sum(route_data["length"])
            else:
                duration = duration_on_range
                distance = round(event.distance * duration_on_range / event.duration)
        self.indicator_dict[self.SUFFIX_KEY_TIME.format(mode=event.mode)] += duration
        self.indicator_dict[self.SUFFIX_KEY_DISTANCE.format(mode=event.mode)] += distance


class WaitKPI(KPI):
    """
    This KPI evaluates the time spent waiting
    """

    #: **waitTime**: total traced wait time [seconds]
    KEY_WAIT = "waitTime"

    def _update(self, event):
        if isinstance(event, WaitEvent) or isinstance(event, RequestEvent):
            self.add_proportioned_indicators(event)

    def evaluate_indicators_on_profile_range(self, event, current_timestamp, duration_on_range):
        self.indicator_dict[self.KEY_WAIT] += duration_on_range


class GetVehicleKPI(KPI):
    """
    This KPI evaluates the number of vehicle uses
    """

    #: **nbGetVehicle**: number of uses of the vehicle
    KEY_GET_VEHICLE = "nbGetVehicle"

    def _update(self, event):
        """
        Add a new use for each GetVehicleEvent

        :param event:
        """

        if isinstance(event, GetVehicleEvent):
            self.indicator_dict[self.KEY_GET_VEHICLE] += event.agent.number


class SuccessKPI(KPI):
    """
    This KPI evaluates the number of failed/successful requests
    """

    #: **nbFailedGet**: number of failed get requests
    KEY_FAILED_GET = "nbFailedGet"
    #: **nbSuccessGet**: number successful get requests
    KEY_SUCCESS_GET = "nbSuccessGet"
    #: **nbFailedPut**: number of failed put requests
    KEY_FAILED_PUT = "nbFailedPut"
    #: **nbSuccessPut**: number of successful put requests
    KEY_SUCCESS_PUT = "nbSuccessPut"
    #: **nbFailedRequest**: number of failed requests
    KEY_FAILED_REQUEST = "nbFailedRequest"
    #: **nbSuccessRequest**: number of successful requests
    KEY_SUCCESS_REQUEST = "nbSuccessRequest"

    def _init_keys(self):
        return [
            self.KEY_FAILED_GET,
            self.KEY_SUCCESS_GET,
            self.KEY_FAILED_PUT,
            self.KEY_SUCCESS_PUT,
            self.KEY_FAILED_REQUEST,
            self.KEY_SUCCESS_REQUEST,
        ]

    def _update(self, event):
        """
        Add request events according to their success

        :param event:
        """

        if isinstance(event, RequestEvent):
            if event.request.success:
                self.indicator_dict[self.KEY_SUCCESS_REQUEST] += 1
                if event.request.type == StationRequest.GET_REQUEST:
                    self.indicator_dict[self.KEY_SUCCESS_GET] += 1
                else:
                    self.indicator_dict[self.KEY_SUCCESS_PUT] += 1
            else:
                self.indicator_dict[self.KEY_FAILED_REQUEST] += 1
                if event.request.type == StationRequest.GET_REQUEST:
                    self.indicator_dict[self.KEY_FAILED_GET] += 1
                else:
                    self.indicator_dict[self.KEY_FAILED_PUT] += 1


class StaffOperationKPI(KPI):
    """
    This KPI evaluates the number of staff operations
    """

    #: **nbFailedGetStaff**: number of failed gets by staff
    KEY_FAILED_GET_STAFF = "nbFailedGetStaff"
    #: **nbSuccessGetStaff**: number of successful gets by staff
    KEY_SUCCESS_GET_STAFF = "nbSuccessGetStaff"
    #: **nbFailedPutStaff**: number of failed puts by staff
    KEY_FAILED_PUT_STAFF = "nbFailedPutStaff"
    #: **nbSuccessPutStaff**: number of successful puts by staff
    KEY_SUCCESS_PUT_STAFF = "nbSuccessPutStaff"

    def _init_keys(self):
        return [
            self.KEY_FAILED_GET_STAFF,
            self.KEY_SUCCESS_GET_STAFF,
            self.KEY_FAILED_PUT_STAFF,
            self.KEY_SUCCESS_PUT_STAFF,
        ]

    def _update(self, event):
        """
        Add operations to the total

        :param event:
        """

        if isinstance(event, StaffOperationEvent):
            goal = event.goal
            total = event.total
            if goal < 0:
                self.indicator_dict[self.KEY_SUCCESS_GET_STAFF] += abs(total)
                self.indicator_dict[self.KEY_FAILED_GET_STAFF] += total - goal
            elif goal > 0:
                self.indicator_dict[self.KEY_SUCCESS_PUT_STAFF] += total
                self.indicator_dict[self.KEY_FAILED_PUT_STAFF] += goal - total


class OccupationKPI(KPI):
    """
    This KPI evaluates the empty and full time and distance
    and the stock relative time/distance
    """

    #: **emptyTime**: time spent empty [seconds]
    KEY_EMPTY_TIME = "emptyTime"
    #: **emptyDistance**: distance travelled empty [meters]
    KEY_EMPTY_DISTANCE = "emptyDistance"
    #: **fullTime**: time spent full [seconds]
    KEY_FULL_TIME = "fullTime"
    #: **fullDistance**: distance travelled full [meters]
    KEY_FULL_DISTANCE = "fullDistance"
    #: **stockTime**: stock relative time (stock*time) [seconds]
    KEY_STOCK_TIME = "stockTime"
    #: **stockDistance**: stock relative distance (stock*distance) [meters]
    KEY_STOCK_DISTANCE = "stockDistance"
    #: **maxStock**: maximum stock
    KEY_MAX_STOCK = "maxStock"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.capacity = None
        self.currentStock = None
        self.previousTime = -1
        self.currentDistance = None

    def _init_keys(self):
        return [
            self.KEY_EMPTY_TIME,
            self.KEY_EMPTY_DISTANCE,
            self.KEY_FULL_TIME,
            self.KEY_FULL_DISTANCE,
            self.KEY_STOCK_TIME,
            self.KEY_STOCK_DISTANCE,
            self.KEY_MAX_STOCK,
        ]

    def reset_for_agent(self, agent):
        super().reset_for_agent(agent)
        self.capacity = None
        self.currentStock = None
        self.previousTime = -1
        self.currentDistance = None

    def get_capacity(self, element):
        """
        Get the capacity of the agent, according to its type.

        :param element:

        :return: agent's capacity
        """
        return self.capacity

    def get_initial_stock(self, element):
        """
        Get the initial stock of the agent, according to its type.

        :param element:

        :return: agent's initial stock
        """
        return self.currentStock

    def end_of_profile_range(self):
        if self.current_profile_index < len(self.profile) - 1:
            self.update_timestamp(self.profile[self.current_profile_index + 1] - 1)
        super().end_of_profile_range()

    def update_timestamp(self, timestamp):
        # compute time spent with last stock
        duration = int(timestamp - self.previousTime)

        # add time to relevant time count
        if self.currentStock is not None:
            if self.currentStock == 0:
                self.indicator_dict[self.KEY_EMPTY_TIME] += duration
                if self.currentDistance is not None:
                    self.indicator_dict[self.KEY_EMPTY_DISTANCE] += self.currentDistance
            elif self.currentStock == self.capacity:
                self.indicator_dict[self.KEY_FULL_TIME] += duration
                if self.currentDistance is not None:
                    self.indicator_dict[self.KEY_FULL_DISTANCE] += self.currentDistance

            # add stock relative time and distance
            self.indicator_dict[self.KEY_STOCK_TIME] += duration * self.currentStock
            if self.currentDistance is not None:
                self.indicator_dict[self.KEY_STOCK_DISTANCE] += (
                    self.currentDistance * self.currentStock
                )

        # set time of last update
        self.previousTime = timestamp

    def add_to_stock(self, value, timestamp):
        """
        Update the full and empty time and distance counts, according to the previous
        stock value, then updates the stock and time.

        :param value: stock change (negative for stock loss)
        :param timestamp: timestamp of the stock change event
        """
        # update indicators for previous period
        self.update_timestamp(timestamp)

        # update current stock
        self.currentStock += value
        if self.currentStock > self.indicator_dict[self.KEY_MAX_STOCK]:
            self.indicator_dict[self.KEY_MAX_STOCK] = self.currentStock

        # reset distance count
        if self.currentDistance is not None:
            self.currentDistance = 0

    def _update(self, event):
        """
        Update the stock and time counts from traced events

        :param event:
        """

        if isinstance(event, InputEvent):
            self.capacity = self.get_capacity(event.element)
            self.currentStock = self.get_initial_stock(event.element)
            self.indicator_dict[self.KEY_MAX_STOCK] = self.currentStock

        if isinstance(event, LeaveSimulationEvent):
            self.update_timestamp(event.timestamp - 1)
            self.currentStock = None


class StationOccupationKPI(OccupationKPI):
    """
    This KPI evaluates the time spent in the empty and full states (of a station),
    and the stock relative time spent in the station
    """

    def _init_keys(self):
        return [self.KEY_EMPTY_TIME, self.KEY_FULL_TIME, self.KEY_STOCK_TIME]

    def new_indicator_dict(self):
        return {
            key: 0
            for key in [
                self.KEY_EMPTY_TIME,
                self.KEY_FULL_TIME,
                self.KEY_STOCK_TIME,
                self.KEY_MAX_STOCK,
            ]
        }

    def get_capacity(self, element):
        return element.capacity

    def get_initial_stock(self, element):
        return element.initial_stock

    def _update(self, event):
        """
        Update the stock and time counts from request events

        :param event:
        """

        super()._update(event)

        if isinstance(event, RequestEvent) and event.request.success:
            request = event.request

            # update time counts and current time
            if request.type == StationRequest.GET_REQUEST:
                self.add_to_stock(-1, request.timestamp)
            elif request.type == StationRequest.PUT_REQUEST:
                self.add_to_stock(1, request.timestamp)

        if isinstance(event, StaffOperationEvent):
            if event.total != 0:
                self.add_to_stock(event.total, event.timestamp)


class VehicleOccupationKPI(OccupationKPI):
    """
    This KPI evaluates the time and distance in the empty and full states (of vehicle),
    and a passenger relative distance and time.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currentDistance = 0

    def reset_for_agent(self, agent):
        super().reset_for_agent(agent)
        self.currentDistance = 0

    def end_of_profile_range(self):
        super().end_of_profile_range()
        self.currentDistance = 0

    def get_capacity(self, element):
        return element.seats

    def get_initial_stock(self, element):
        # for now, initial stock is always 0 in our simulation
        return 0

    def _update(self, event):
        """
        Update the stock and time/distance counts from
        get/leave vehicle and move events

        :param event:
        """

        super()._update(event)

        if isinstance(event, GetVehicleEvent):
            self.add_to_stock(event.agent.number, event.timestamp)

        elif isinstance(event, LeaveVehicleEvent):
            self.add_to_stock(-event.agent.number, event.timestamp)

        if isinstance(event, MoveEvent):
            self.add_proportioned_indicators(event)

    def evaluate_indicators_on_profile_range(self, event, current_timestamp, duration_on_range):
        if isinstance(event, RouteEvent):
            route_data = event.get_route_data_in_interval(
                current_timestamp, current_timestamp + duration_on_range
            )
            self.currentDistance += sum(route_data["length"])
        else:
            if duration_on_range == 0:
                self.currentDistance += event.distance
            else:
                self.currentDistance += round(event.distance * duration_on_range / event.duration)


class ChargeKPI(KPI):
    """
    This KPI evaluates the trips's boards and un-boards
    """

    PROFILE_COMPATIBILITY = False

    #: **tripId**: gtfs trip id
    KEY_TRIP_ID = "tripId"
    #: **time**: simulation timestamp of board/un-board
    KEY_TIME = "time"
    #: **stopId**: stop id of board/un-board
    KEY_STOP_ID = "stopId"
    #: **boardType**: (+1) for boards, (-1) for un-boards
    KEY_BOARD_TYPE = "boardType"
    #: **value**: numeric value of the charge change
    KEY_VALUE = "value"

    def __init__(self, non_empty_only=True, **kwargs):
        # boolean indicating if only non empty pickups and dropoffs should be traced
        self.non_empty_only = non_empty_only

        super().__init__(**kwargs)

    def new_indicator_dict(self):
        return dict()

    def _init_keys(self):
        return [
            self.KEY_TRIP_ID,
            self.KEY_TIME,
            self.KEY_STOP_ID,
            self.KEY_BOARD_TYPE,
            self.KEY_VALUE,
        ]

    def end_of_events(self):
        pass

    def _update(self, event):
        """
        Add stop information to the list

        :param event:
        """

        if isinstance(event, StopEvent):
            # add a row for each stop type
            if event.dropoffs:
                self.update_stop_information(event)
                self.indicator_dict[self.KEY_TIME] = event.dropoff_time
                self.indicator_dict[self.KEY_BOARD_TYPE] = -1
                self.indicator_dict[self.KEY_VALUE] = len(event.dropoffs)
                self.new_kpi_row()
            if event.pickups:
                self.update_stop_information(event)
                self.indicator_dict[self.KEY_TIME] = event.pickup_time
                self.indicator_dict[self.KEY_BOARD_TYPE] = 1
                self.indicator_dict[self.KEY_VALUE] = len(event.pickups)
                self.new_kpi_row()

            # add a row even if stop is empty if asked
            if not event.pickups and not event.dropoffs and not self.non_empty_only:
                self.update_stop_information(event)
                self.indicator_dict[self.KEY_TIME] = event.timestamp
                self.indicator_dict[self.KEY_BOARD_TYPE] = 0
                self.indicator_dict[self.KEY_VALUE] = 0
                self.new_kpi_row()

    def update_stop_information(self, event):
        """
        Update the indicator with the information common to dropoffs and pickups.

        :param event:
        """

        trip_id = event.trip

        self.indicator_dict[self.KEY_TRIP_ID] = trip_id

        self.indicator_dict[self.KEY_STOP_ID] = get_stop_id_of_event(event)


class PublicTransportChargeKPI(ChargeKPI):
    """
    This KPI evaluates the public transport trips's boards and un-boards
    """

    #: **routeId**: gtfs route id
    KEY_ROUTE_ID = "routeId"
    #: **tripDirection**: gtfs trip direction
    KEY_TRIP_DIRECTION = "tripDirection"

    def __init__(self, **kwargs):
        self.trips = None
        self.routes = None

        super().__init__(**kwargs)

    def _init_keys(self):
        return [self.KEY_ROUTE_ID, self.KEY_TRIP_DIRECTION] + super()._init_keys()

    def _indicators_setup(self, simulation_model):
        self.trips = simulation_model.gtfs.trips
        self.routes = simulation_model.gtfs.routes

    def update_stop_information(self, event):
        super().update_stop_information(event)

        self.indicator_dict[self.KEY_ROUTE_ID] = get_route_id_of_trip(self.trips, event.trip, event)
        self.indicator_dict[self.KEY_TRIP_DIRECTION] = get_direction_of_trip(self.trips, event.trip)


class ServiceKPI(KPI):
    """
    This KPI describes the service time of a vehicle.
    """

    #: **serviceDuration**: vehicle service duration [seconds]
    KEY_SERVICE_DURATION = "serviceDuration"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_service_marker = None

    def reset_for_agent(self, agent):
        self.last_service_marker = None
        super().reset_for_agent(agent)

    def end_of_profile_range(self):
        if self.current_profile_index < len(self.profile) - 1:
            self.update_indicator(self.profile[self.current_profile_index + 1] - 1)
        super().end_of_profile_range()

    def update_indicator(self, timestamp):
        if self.last_service_marker is not None:
            self.indicator_dict[self.KEY_SERVICE_DURATION] += timestamp - self.last_service_marker
            self.last_service_marker = timestamp

    def _update(self, event):
        if isinstance(event, ServiceEvent):
            if event.new == SERVICE_UP:
                self.start_service(event.timestamp)
            elif event.new in [SERVICE_PAUSE, SERVICE_END]:
                self.close_service(event.timestamp)
            elif event.new == SERVICE_INIT:
                raise ValueError("Service state shouldn't change to {} status".format(SERVICE_INIT))
            else:
                raise ValueError("Unsupported service status " + event.new)

    def start_service(self, timestamp):
        if self.last_service_marker is not None:
            raise ValueError("Service starts but has not ended")
        else:
            self.last_service_marker = timestamp

    def close_service(self, timestamp):
        if self.last_service_marker is None:
            raise ValueError("Service ends but has not started")
        else:
            self.update_indicator(timestamp)
            self.last_service_marker = None


class TransferKPI(KPI):
    """
    This KPI lists the transfers realised by a user,
    with additional information such as walk distance and duration,
    wait duration, from/to trip/stop
    """

    PROFILE_COMPATIBILITY = False

    #: **walkDistance**: walk distance of transfer [meters]
    KEY_WALK_DIST = "walkDistance"
    #: **walkTime**: walk time of transfer [seconds]
    KEY_WALK_DURATION = "walkDuration"
    #: **waitTime**: wait time of transfer [seconds]
    KEY_WAIT_TIME = "waitTime"
    #: **fromRoute**: origin route of transfer
    KEY_FROM_ROUTE = "fromRoute"
    #: **fromTrip**: origin trip of transfer
    KEY_FROM_TRIP = "fromTrip"
    #: **fromStop**: origin stop point of transfer
    KEY_FROM_STOP = "fromStop"
    #: **toRoute**: destination route of transfer
    KEY_TO_ROUTE = "toRoute"
    #: **toTrip**: destination trip of transfer
    KEY_TO_TRIP = "toTrip"
    #: **toStop**: destination stop of transfer
    KEY_TO_STOP = "toStop"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.trips = None
        self.routes = None

        # transfer variables
        self.current_walk_distance = 0
        self.current_walk_duration = 0
        self.current_wait_time = 0
        self.from_route = None
        self.from_trip = None
        self.from_stop = None
        self.to_route = None
        self.to_trip = None
        self.to_stop = None

    def _indicators_setup(self, simulation_model):
        if simulation_model.gtfs is not None:
            self.trips = simulation_model.gtfs.trips
            self.routes = simulation_model.gtfs.routes

    def _init_keys(self):
        return [
            self.KEY_WALK_DIST,
            self.KEY_WALK_DURATION,
            self.KEY_WAIT_TIME,
            self.KEY_FROM_ROUTE,
            self.KEY_FROM_TRIP,
            self.KEY_FROM_STOP,
            self.KEY_TO_ROUTE,
            self.KEY_TO_TRIP,
            self.KEY_TO_STOP,
        ]

    def end_of_events(self):
        pass

    def new_indicator_dict(self):
        return dict()

    def _update(self, event):
        if isinstance(event, InputEvent):
            self.reset_variables()

        if isinstance(event, WaitEvent):
            self.current_wait_time += event.waiting_time

        elif isinstance(event, MoveEvent) and event.mode == "walk":
            self.current_walk_distance += event.distance
            self.current_walk_duration += event.duration

        elif isinstance(event, RequestEvent):
            self.current_wait_time += sum(event.request.waitSequence)

        elif isinstance(event, StopEvent):
            if isinstance(event.stop, StopPoint):
                stop_id = event.stop.id
            elif isinstance(event.stop, UserStop):
                stop_id = event.stop.stopPoint
            else:
                stop_id = None

            dropoff_agents = [request.agent.id for request in event.dropoffs]
            pickup_agents = [request.agent.id for request in event.pickups]

            if self.agent.id in dropoff_agents:
                self.from_trip = event.trip
                self.from_stop = stop_id

            elif self.agent.id in pickup_agents:
                self.to_trip = event.trip
                self.to_stop = stop_id

                self.write_variables()
                self.reset_variables()

        elif isinstance(event, DestinationReachedEvent):
            self.write_variables()
            self.reset_variables()

    def reset_variables(self):
        self.current_walk_distance = 0
        self.current_walk_duration = 0
        self.current_wait_time = 0
        self.from_trip = None
        self.from_stop = None
        self.to_trip = None
        self.to_stop = None

    def write_variables(self):
        self.indicator_dict[self.KEY_WALK_DIST] = self.current_walk_distance
        self.indicator_dict[self.KEY_WALK_DURATION] = self.current_walk_duration
        self.indicator_dict[self.KEY_WAIT_TIME] = self.current_wait_time
        self.indicator_dict[self.KEY_FROM_ROUTE] = get_route_short_name_of_trip(
            self.trips, self.routes, self.from_trip
        )

        self.indicator_dict[self.KEY_FROM_TRIP] = self.from_trip
        self.indicator_dict[self.KEY_FROM_STOP] = self.from_stop
        self.indicator_dict[self.KEY_TO_ROUTE] = get_route_short_name_of_trip(
            self.trips, self.routes, self.to_trip
        )

        self.indicator_dict[self.KEY_TO_TRIP] = self.to_trip
        self.indicator_dict[self.KEY_TO_STOP] = self.to_stop
        self.new_kpi_row()


# TODO : remove ? useless with TransferKPI
# class JourneyKPI(KPI):
#     """
#     This KPI evaluates the sequence of lines that compose a user journey
#     """
#
#     #: **journeySequence**: sequence of trip ids of the journey
#     KEY_JOURNEY_SEQUENCE = "journeySequence"
#
#     def __init__(self):
#
#         super().__init__()
#
#         self.keys = [self.KEY_JOURNEY_SEQUENCE]
#
#         self.trips_table = None
#         self.routes_table = None
#
#     def setup(self, simulation_model):
#
#         operator = simulation_model.agentPopulation["operators"]["OPR"]
#
#         feed = operator.service_info
#
#         self.trips_table = feed.trips
#         self.routes_table = feed.routes
#
#     def new_indicator_dict(self):
#
#         self.indicator_dict = {self.KEY_JOURNEY_SEQUENCE: ""}
#
#     def update(self, event, agent):
#         """
#         Add a new route for each PickupEvent
#         :param agent:
#         :param event:
#         :return:
#         """
#
#         super().update(event, agent)
#
#         if isinstance(event, PickupEvent):
#
#             route_id = self.trips_table.loc[self.trips_table["trip_id"] == event.trip, "route_id"].iloc[0]
#
#             route_name = self.routes_table.loc[self.routes_table["route_id"] == route_id, "route_short_name"].iloc[0]
#
#             self.indicator_dict[self.KEY_JOURNEY_SEQUENCE] += route_name + "-"
#
#         if isinstance(event, DestinationReachedEvent):
#
#             self.indicator_dict[self.KEY_JOURNEY_SEQUENCE] = self.indicator_dict[self.KEY_JOURNEY_SEQUENCE][:-1]
#


class DestinationReachedKPI(KPI):
    """
    This KPI evaluates the destination reach time
    """

    #: **destinationReachedTime**: time when destination is reached, "NA" otherwise [seconds or NA]
    KEY_DESTINATION_REACHED = "destinationReachedTime"

    def new_indicator_dict(self):
        return {self.KEY_DESTINATION_REACHED: "NA"}

    def _update(self, event):
        """
        Add total wait duration of the request

        :param event:
        """

        if isinstance(event, DestinationReachedEvent):
            self.indicator_dict[self.KEY_DESTINATION_REACHED] = event.timestamp


class LeaveSimulationKPI(KPI):
    """
    This KPI evaluates the cause of the simulation leave.
    """

    #: **leaveSimulation**: code used when leaving the simulation (see model doc)
    KEY_LEAVE_SIMULATION = "leaveSimulation"

    def new_indicator_dict(self):
        return {self.KEY_LEAVE_SIMULATION: None}

    def _update(self, event):
        """
        Add the cause of the LeaveSimulationEvent.

        :param event:
        """

        if isinstance(event, LeaveSimulationEvent):
            self.indicator_dict[self.KEY_LEAVE_SIMULATION] = event.cause


def get_route_id_of_trip(trips, trip_id, event):
    if trips is None:
        return event.serviceVehicle.operator

    trip_table = trips.loc[trips["trip_id"] == trip_id, "route_id"]

    # if trips is not in the gtfs (on-demand trips for instance)
    # try to get operator id
    if trip_table.empty:
        return event.serviceVehicle.operator

    return trip_table.iloc[0]


def get_direction_of_trip(trips, trip_id):
    if trips is None:
        return ""

    trip_table = trips.loc[trips["trip_id"] == trip_id, "direction_id"]

    # ignore trips that are not in the gtfs (on-demand trips for instance)
    if trip_table.empty:
        return ""

    return trip_table.iloc[0]


def get_route_short_name_of_trip(trips, routes, trip_id):
    if trips is None or routes is None or trip_id is None:
        return None

    trip_table = trips.loc[trips["trip_id"] == trip_id, "route_id"]

    # ignore trips that are not in the gtfs (on-demand trips for instance)
    if trip_table.empty:
        return ""

    route_id = trip_table.iloc[0]
    route_short_name = routes.loc[routes["route_id"] == route_id, "route_short_name"].iloc[0]

    return route_short_name


def get_stop_id_of_event(event):
    stop_id = None

    if isinstance(event.stop, StopPoint):
        stop_id = event.stop.id
    elif isinstance(event.stop, UserStop):
        stop_id = event.stop.stopPoint

    if stop_id is None:
        stop_id = ""

    return stop_id
