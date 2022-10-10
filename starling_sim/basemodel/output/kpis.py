from starling_sim.basemodel.trace.events import *
from starling_sim.basemodel.agent.requests import UserStop, StopPoint, StationRequest
from starling_sim.utils.constants import PUBLIC_TRANSPORT_TYPE


class KPI:
    """
    Generic structure of a KPI class

    Its sub-classes compute and update specific indicator
    from given events
    """

    #: **agentId**: id of the agent
    KEY_ID = "agentId"

    def __init__(self):
        """
        The indicator_dict associates values to the indicators names

        The keys attribute correspond to the keys of the indicator_dict
        """
        self.indicator_dict = None
        self.keys = []

        self.new_indicator_dict()

    def setup(self, simulation_model):
        """
        Setup method called during simulation setup.

        :param simulation_model:
        :return:
        """
        pass

    def new_indicator_dict(self):
        """
        Reset the indicator_dict, when computing the indicator
        for a new target
        :return: None, resets directly the indicator_dict attribute
        """
        pass

    def update(self, event, agent):
        """
        Update the kpi values according to the event content and the agent.

        :param event: processed event
        :param agent: subject of the event
        :return:
        """

        if isinstance(event, InputEvent):
            self.indicator_dict[self.KEY_ID] = agent.id


class MoveKPI(KPI):
    """
    This KPI evaluates the distance and spent time for each one of the simulation modes
    """

    #: **{mode}Distance**: distance travelled in <mode> [meters]
    SUFFIX_KEY_DISTANCE = "{mode}Distance"
    #: **{mode}Time**: time travelled in <mode> [seconds]
    SUFFIX_KEY_TIME = "{mode}Time"

    def __init__(self):

        self.modes = []

        # init of indicator dict
        super().__init__()

    def setup(self, simulation_model):

        self.modes = list(simulation_model.environment.topologies.keys())
        self.new_indicator_dict()

    def new_indicator_dict(self):
        """
        Initialize the time and distance values at 0
        for the considered modes
        :return:
        """
        base_dict = {}

        for mode in self.modes:
            key = self.SUFFIX_KEY_DISTANCE.format(mode=mode)
            base_dict[key] = 0
            self.keys += [key]

            key = self.SUFFIX_KEY_TIME.format(mode=mode)
            base_dict[key] = 0
            self.keys += [key]

        self.indicator_dict = base_dict

    def update(self, event, agent):
        """
        Add travelled distances and durations
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

        if isinstance(event, MoveEvent):
            self.indicator_dict[self.SUFFIX_KEY_DISTANCE.format(mode=event.mode)] += event.distance
            self.indicator_dict[self.SUFFIX_KEY_TIME.format(mode=event.mode)] += event.duration


class WaitKPI(KPI):
    """
    This KPI evaluates the time spent waiting
    """

    #: **waitTime**: total traced wait time [seconds]
    KEY_WAIT = "waitTime"

    def __init__(self):
        super().__init__()
        self.keys = [self.KEY_WAIT]

    def new_indicator_dict(self):

        self.indicator_dict = {self.KEY_WAIT: 0}

    def update(self, event, agent):
        """
        Add total wait duration of the request
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

        if isinstance(event, RequestEvent):
            self.indicator_dict[self.KEY_WAIT] += sum(event.request.waitSequence)

        if isinstance(event, WaitEvent):
            self.indicator_dict[self.KEY_WAIT] += event.waiting_time


class OdtWaitsKPI(KPI):
    """
    This KPI evaluates the lateness in ODT requests.
    """

    #: **odtPickupWait**: series of wait times at ODT pickups [seconds]
    KEY_PICKUP_WAIT = "odtPickupWait"
    #: **odtDetour**: series of ODT detour times [seconds]
    KEY_DETOUR = "odtDetour"
    #: **odtDirectTrip**: series of ODT direct trip times [seconds]
    KEY_DIRECT_TRIP = "odtDirectTrip"

    def __init__(self):

        super().__init__()
        self.keys = [self.KEY_PICKUP_WAIT, self.KEY_DETOUR, self.KEY_DIRECT_TRIP]

    def new_indicator_dict(self):

        self.indicator_dict = {
            self.KEY_PICKUP_WAIT: "",
            self.KEY_DETOUR: "",
            self.KEY_DIRECT_TRIP: "",
        }

    def update(self, event, agent):
        """
        Add wait durations of ODT requests to KPIs.

        :param event:
        :param agent:
        :return:
        """

        # TODO : find a better condition
        if isinstance(event, StopEvent) and event.serviceVehicle.type != PUBLIC_TRANSPORT_TYPE:
            dropoff_agents = [request.agent.id for request in event.dropoffs]
            pickup_agents = [request.agent.id for request in event.pickups]

            if agent.id in dropoff_agents:
                request = event.dropoffs[dropoff_agents.index(agent.id)]
                if len(request.waitSequence) > 1:
                    if self.indicator_dict[self.KEY_DETOUR] != "":
                        self.indicator_dict[self.KEY_DETOUR] += "-"
                        self.indicator_dict[self.KEY_DIRECT_TRIP] += "-"
                    self.indicator_dict[self.KEY_DETOUR] += str(request.waitSequence[1])
                self.indicator_dict[self.KEY_DIRECT_TRIP] += str(request.directTravelTime)

            elif agent.id in pickup_agents:
                request = event.pickups[pickup_agents.index(agent.id)]
                if len(request.waitSequence) > 0:
                    if self.indicator_dict[self.KEY_PICKUP_WAIT] != "":
                        self.indicator_dict[self.KEY_PICKUP_WAIT] += "-"
                    self.indicator_dict[self.KEY_PICKUP_WAIT] += str(request.waitSequence[0])


class GetVehicleKPI(KPI):
    """
    This KPI evaluates the number of vehicle uses
    """

    #: **nbGetVehicle**: number of uses of the vehicle
    KEY_GET_VEHICLE = "nbGetVehicle"

    def __init__(self):
        super().__init__()
        self.keys = [self.KEY_GET_VEHICLE]

    def new_indicator_dict(self):
        self.indicator_dict = {self.KEY_GET_VEHICLE: 0}

    def update(self, event, agent):
        """
        Add a new use for each GetVehicleEvent
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

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

    def __init__(self, indicator_selection):

        super().__init__()

        self.keys = indicator_selection

    def new_indicator_dict(self):

        base_dict = {
            self.KEY_FAILED_GET: 0,
            self.KEY_SUCCESS_GET: 0,
            self.KEY_FAILED_PUT: 0,
            self.KEY_SUCCESS_PUT: 0,
            self.KEY_FAILED_REQUEST: 0,
            self.KEY_SUCCESS_REQUEST: 0,
        }

        self.indicator_dict = base_dict

    def update(self, event, agent):
        """
        Add request events according to their success
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

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

    def __init__(self):
        super().__init__()
        self.keys = [
            self.KEY_FAILED_GET_STAFF,
            self.KEY_SUCCESS_GET_STAFF,
            self.KEY_FAILED_PUT_STAFF,
            self.KEY_SUCCESS_PUT_STAFF,
        ]

    def new_indicator_dict(self):

        self.indicator_dict = {
            self.KEY_FAILED_GET_STAFF: 0,
            self.KEY_SUCCESS_GET_STAFF: 0,
            self.KEY_FAILED_PUT_STAFF: 0,
            self.KEY_SUCCESS_PUT_STAFF: 0,
        }

    def update(self, event, agent):
        """
        Add operations to the total
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

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

    def __init__(self):

        #: **emptyTime**: time spent empty [seconds]
        self.KEY_EMPTY_TIME = "emptyTime"
        #: **emptyDistance**: distance travelled empty [meters]
        self.KEY_EMPTY_DISTANCE = "emptyDistance"
        #: **fullTime**: time spent full [seconds]
        self.KEY_FULL_TIME = "fullTime"
        #: **fullDistance**: distance travelled full [meters]
        self.KEY_FULL_DISTANCE = "fullDistance"
        #: **stockTime**: stock relative time (stock*time) [seconds]
        self.KEY_STOCK_TIME = "stockTime"
        #: **stockDistance**: stock relative distance (stock*distance) [meters]
        self.KEY_STOCK_DISTANCE = "stockDistance"
        #: **maxStock**: maximum stock
        self.KEY_MAX_STOCK = "maxStock"

        super().__init__()

        self.keys = [
            self.KEY_EMPTY_TIME,
            self.KEY_EMPTY_DISTANCE,
            self.KEY_FULL_TIME,
            self.KEY_FULL_DISTANCE,
            self.KEY_STOCK_TIME,
            self.KEY_STOCK_DISTANCE,
            self.KEY_MAX_STOCK,
        ]

        self.capacity = None
        self.currentStock = None
        self.previousTime = 0
        self.currentDistance = None

    def new_indicator_dict(self):
        """
        Initialize the time and distance counts to 0.
        """

        self.indicator_dict = {
            self.KEY_EMPTY_TIME: 0,
            self.KEY_EMPTY_DISTANCE: 0,
            self.KEY_FULL_TIME: 0,
            self.KEY_FULL_DISTANCE: 0,
            self.KEY_STOCK_TIME: 0,
            self.KEY_STOCK_DISTANCE: 0,
            self.KEY_MAX_STOCK: 0,
        }
        self.capacity = None
        self.currentStock = None
        self.previousTime = 0
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

    def add_to_stock(self, value, timestamp):
        """
        Update the full and empty time and distance counts, according to the previous
        stock value, then updates the stock and time.

        :param value: stock change (negative for stock loss)
        :param timestamp: timestamp of the stock change event
        """

        # compute time spent with last stock
        duration = timestamp - self.previousTime

        # add time to relevant time count
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
            self.indicator_dict[self.KEY_STOCK_DISTANCE] += self.currentDistance * self.currentStock

        # update stock and current time
        self.currentStock += value
        self.previousTime = timestamp

        if self.currentStock > self.indicator_dict[self.KEY_MAX_STOCK]:
            self.indicator_dict[self.KEY_MAX_STOCK] = self.currentStock

        # reset distance count
        if self.currentDistance is not None:
            self.currentDistance = 0

    def update(self, event, agent):
        """
        Update the stock and time counts from traced events

        :param agent:
        :param event:
        """

        super().update(event, agent)

        if isinstance(event, InputEvent):

            self.capacity = self.get_capacity(event.element)
            self.currentStock = self.get_initial_stock(event.element)
            self.indicator_dict[self.KEY_MAX_STOCK] = self.currentStock

        if isinstance(event, LeaveSimulationEvent):

            self.add_to_stock(0, event.timestamp)


class StationOccupationKPI(OccupationKPI):
    """
    This KPI evaluates the time spent in the empty and full states (of a station),
    and the stock relative time spent in the station
    """

    def __init__(self):
        super().__init__()

        self.keys = [self.KEY_EMPTY_TIME, self.KEY_FULL_TIME, self.KEY_STOCK_TIME]

    def get_capacity(self, element):

        return element.capacity

    def get_initial_stock(self, element):

        return element.initial_stock

    def update(self, event, agent):
        """
        Update the stock and time counts from request events

        :param agent:
        :param event:
        """

        super().update(event, agent)

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

    def __init__(self):
        super().__init__()
        self.currentDistance = 0

    def new_indicator_dict(self):
        super().new_indicator_dict()
        self.currentDistance = 0

    def get_capacity(self, element):

        return element.seats

    def get_initial_stock(self, element):

        # for now, initial stock is always 0 in our simulation
        return 0

    def update(self, event, agent):
        """
        Update the stock and time/distance counts from
        get/leave vehicle and move events

        :param agent:
        :param event:
        """

        super().update(event, agent)

        if isinstance(event, GetVehicleEvent):
            self.add_to_stock(event.agent.number, event.timestamp)

        elif isinstance(event, LeaveVehicleEvent):
            self.add_to_stock(-event.agent.number, event.timestamp)

        if isinstance(event, MoveEvent):
            self.currentDistance += event.distance


class ChargeKPI(KPI):
    """
    This KPI evaluates the trips's boards and un-boards
    """

    #: **routeId**: gtfs route id
    KEY_ROUTE_ID = "routeId"
    #: **tripId**: gtfs trip id
    KEY_TRIP_ID = "tripId"
    #: **tripDirection**: gtfs trip direction
    KEY_TRIP_DIRECTION = "tripDirection"
    #: **time**: simulation timestamp of board/un-board
    KEY_TIME = "time"
    #: **stopId**: stop id of board/un-board
    KEY_STOP_ID = "stopId"
    #: **boardType**: (+1) for boards, (-1) for un-boards
    KEY_BOARD_TYPE = "boardType"
    #: **value**: numeric value of the charge change
    KEY_VALUE = "value"

    def __init__(self, non_empty_only=True, public_transport=True):

        super().__init__()

        # boolean indicating if only non empty pickups and dropoffs should be traced
        self.non_empty_only = non_empty_only

        # boolean indicating if the simulated system is public transports (with gtfs tables)
        self.public_transport = public_transport

        self.trips = None
        self.routes = None

        self.keys = [
            self.KEY_TRIP_ID,
            self.KEY_TIME,
            self.KEY_STOP_ID,
            self.KEY_BOARD_TYPE,
            self.KEY_VALUE,
        ]

        if self.public_transport:
            self.keys = [self.KEY_ROUTE_ID, self.KEY_TRIP_DIRECTION] + self.keys

        self.new_indicator_dict()

    def setup(self, simulation_model):

        if self.public_transport:
            self.trips = simulation_model.gtfs.trips
            self.routes = simulation_model.gtfs.routes

    def new_indicator_dict(self):

        self.indicator_dict = dict()

        for key in [self.KEY_ID] + self.keys:
            self.indicator_dict[key] = []

    def update(self, event, agent):
        """
        Add stop information to the list

        :param agent:
        :param event:
        :return:
        """

        if isinstance(event, StopEvent):

            if event.dropoffs:
                self.update_stop_information(event, agent)
                self.indicator_dict[self.KEY_TIME].append(event.dropoff_time)
                self.indicator_dict[self.KEY_BOARD_TYPE].append(-1)
                self.indicator_dict[self.KEY_VALUE].append(len(event.dropoffs))

            if event.pickups:
                self.update_stop_information(event, agent)
                self.indicator_dict[self.KEY_TIME].append(event.pickup_time)
                self.indicator_dict[self.KEY_BOARD_TYPE].append(1)
                self.indicator_dict[self.KEY_VALUE].append(len(event.pickups))

            if not event.pickups and not event.dropoffs and not self.non_empty_only:
                self.update_stop_information(event, agent)
                self.indicator_dict[self.KEY_TIME].append(event.timestamp)
                self.indicator_dict[self.KEY_BOARD_TYPE].append(0)
                self.indicator_dict[self.KEY_VALUE].append(0)

    def update_stop_information(self, event, agent):
        """
        Update the indicator with the information common to dropoffs and pickups.

        :param event:
        :param agent:
        """

        self.indicator_dict[self.KEY_ID].append(agent.id)

        trip_id = event.trip

        self.indicator_dict[self.KEY_TRIP_ID].append(trip_id)

        self.indicator_dict[self.KEY_STOP_ID].append(get_stop_id_of_event(event))

        if self.public_transport:
            self.indicator_dict[self.KEY_ROUTE_ID].append(
                get_route_id_of_trip(self.trips, trip_id, event)
            )
            self.indicator_dict[self.KEY_TRIP_DIRECTION].append(
                get_direction_of_trip(self.trips, trip_id)
            )


class TransferKPI(KPI):
    """
    This KPI lists the transfers realised by a user,
    with additional information such as walk distance and duration,
    wait duration, from/to trip/stop
    """

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

    def __init__(self):
        super().__init__()

        self.trips = None
        self.routes = None

        self.keys = [
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

    def setup(self, simulation_model):

        if simulation_model.gtfs is not None:
            self.trips = simulation_model.gtfs.trips
            self.routes = simulation_model.gtfs.routes

    def new_indicator_dict(self):

        self.indicator_dict = {
            self.KEY_ID: [],
            self.KEY_WALK_DIST: [],
            self.KEY_WALK_DURATION: [],
            self.KEY_WAIT_TIME: [],
            self.KEY_FROM_ROUTE: [],
            self.KEY_FROM_TRIP: [],
            self.KEY_FROM_STOP: [],
            self.KEY_TO_ROUTE: [],
            self.KEY_TO_TRIP: [],
            self.KEY_TO_STOP: [],
        }

    def update(self, event, agent):

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

            if agent.id in dropoff_agents:
                self.from_trip = event.trip
                self.from_stop = stop_id

            elif agent.id in pickup_agents:
                self.to_trip = event.trip
                self.to_stop = stop_id

                self.write_variables(agent)
                self.reset_variables()

        elif isinstance(event, DestinationReachedEvent):

            self.write_variables(agent)
            self.reset_variables()

    def reset_variables(self):
        self.current_walk_distance = 0
        self.current_walk_duration = 0
        self.current_wait_time = 0
        self.from_trip = None
        self.from_stop = None
        self.to_trip = None
        self.to_stop = None

    def write_variables(self, agent):

        self.indicator_dict[self.KEY_ID].append(agent.id)
        self.indicator_dict[self.KEY_WALK_DIST].append(self.current_walk_distance)
        self.indicator_dict[self.KEY_WALK_DURATION].append(self.current_walk_duration)
        self.indicator_dict[self.KEY_WAIT_TIME].append(self.current_wait_time)
        self.indicator_dict[self.KEY_FROM_ROUTE].append(
            get_route_short_name_of_trip(self.trips, self.routes, self.from_trip)
        )
        self.indicator_dict[self.KEY_FROM_TRIP].append(self.from_trip)
        self.indicator_dict[self.KEY_FROM_STOP].append(self.from_stop)
        self.indicator_dict[self.KEY_TO_ROUTE].append(
            get_route_short_name_of_trip(self.trips, self.routes, self.to_trip)
        )
        self.indicator_dict[self.KEY_TO_TRIP].append(self.to_trip)
        self.indicator_dict[self.KEY_TO_STOP].append(self.to_stop)


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

    def __init__(self):
        super().__init__()

        self.keys = [self.KEY_DESTINATION_REACHED]

    def new_indicator_dict(self):

        self.indicator_dict = {self.KEY_DESTINATION_REACHED: "NA"}

    def update(self, event, agent):
        """
        Add total wait duration of the request
        :param agent:
        :param event:
        :return:
        """

        super().update(event, agent)

        if isinstance(event, DestinationReachedEvent):
            self.indicator_dict[self.KEY_DESTINATION_REACHED] = event.timestamp


class LeaveSimulationKPI(KPI):
    """
    This KPI evaluates the cause of the simulation leave.
    """

    #: **leaveSimulation**: code used when leaving the simulation (see model doc)
    KEY_LEAVE_SIMULATION = "leaveSimulation"

    def __init__(self):

        super().__init__()

        self.keys = [self.KEY_LEAVE_SIMULATION]

    def new_indicator_dict(self):

        self.indicator_dict = {self.KEY_LEAVE_SIMULATION: None}

    def update(self, event, agent):
        """
        Add the cause of the LeaveSimulationEvent.

        :param event:
        :param agent:
        """

        super().update(event, agent)

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
