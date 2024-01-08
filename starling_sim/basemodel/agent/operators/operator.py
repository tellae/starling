from starling_sim.basemodel.agent.agent import Agent
from starling_sim.basemodel.agent.requests import TripRequest, UserStop, StopPoint
from starling_sim.utils.utils import (
    geopandas_polygon_from_points,
    points_in_zone,
    json_load,
    load_schema,
    stops_table_from_geojson,
    stop_table_from_gtfs,
)
from starling_sim.utils.paths import (
    gtfs_feeds_folder,
    scenario_agent_input_filepath,
)
from starling_sim.utils.constants import STOP_POINT_POPULATION, ADD_STOPS_COLUMNS

import pandas as pd
from typing import Union


class Operator(Agent):
    """
    Class describing an operator of a transport service.

    Operators manage a fleet of vehicle, and receive requests for the service
    they provide.

    The assignment of these requests is managed by a Dispatcher object.
    """

    OPERATION_PARAMETERS_SCHEMA = {
        "type": "object",
        "title": "Operation parameters",
        "required": [],
        "properties": {
            "routes": {
                "advanced": True,
                "type": "array",
                "items": {"type": "string"},
                "title": "GTFS routes to keep in the public transport simulation",
                "description": "List of route ids that should be present in the simulation. If null, keep all routes.",
            },
            "max_travel_time": {
                "type": ["string", "null"],
                "title": "Max travel time formula",
                "description": "Python expression used to evaluate the maximum travel time for each trip [seconds]. "
                "It can use the trip direct travel time value by using the "
                "following placeholder: {direct_travel_time}. The expression must evaluate to an "
                "object that can be cast or rounded using Python int().",
                "examples": ["{direct_travel_time} * 1.5", "{direct_travel_time} + 900", "1800"],
                "default": None,
            },
        },
    }

    SCHEMA = {
        "properties": {
            "mode": {
                "type": "object",
                "title": "Operator networks",
                "description": "Networks of the operator's agents",
                "properties": {
                    "fleet": {
                        "title": "Fleet network",
                        "description": "Default network of the operator's fleet",
                        "type": "string",
                    },
                    "staff": {
                        "title": "Staff network",
                        "description": "Default network of the operator's staff",
                        "type": "string",
                    },
                },
                "required": ["fleet"],
            },
            "fleet_dict": {
                "type": "string",
                "title": "Fleet population",
                "description": "Population of the operator's fleet agents",
            },
            "staff_dict": {
                "x-display": "hidden",
                "title": "Staff population",
                "description": "Population of the operator's staff agents",
                "type": "string",
            },
            "zone_polygon": {
                "x-display": "hidden",
                "title": "Service area file",
                "description": "Geojson input file describing the service area",
                "type": "string",
            },
            "depot_points": {
                "advanced": True,
                "title": "Depot points",
                "description": "List of depot points descriptors",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "name": {"type": "string"},
                    },
                    "required": ["id", "coordinates"],
                },
                "default": [],
            },
            "stop_points_from": {
                "title": "Stop points source",
                "description": "Indicates how stop points are generated. "
                "If not provided, the operator starts with an empty set of stop points.",
                "anyOf": [
                    {
                        "title": "GeoJSON input",
                        "description": "A GeoJSON file placed in the inputs folder, with Point features. "
                        "Optional properties 'stop_id' and 'stop_name'.",
                        "type": "string",
                        "pattern": "(.)*(.geojson)",
                    },
                    {
                        "const": "gtfs",
                        "title": "GTFS",
                        "description": "Use the stop points of the global gtfs.",
                    },
                    {
                        "title": "Other",
                        "description": "Another option. The 'init_stops' method must be overriden to manage this case.",
                    },
                ],
            },
            "extend_graph_with_stops": {
                "advanced": True,
                "title": "Extend graph with stops",
                "description": "Extend the graph with service stop points",
                "type": "boolean",
                "default": False,
            },
            "operation_parameters": OPERATION_PARAMETERS_SCHEMA,
        },
        "required": ["fleet_dict"],
        "remove_props": ["icon"],
    }

    DISPATCHERS = {}

    @classmethod
    def get_schema(cls):
        schema = cls.compute_schema()

        if len(cls.DISPATCHERS) > 0:
            enum = []

            operation_parameters_schema = schema["properties"]["operation_parameters"]

            for key in cls.DISPATCHERS.keys():
                if "title" in cls.DISPATCHERS[key]:
                    title = cls.DISPATCHERS[key]["title"]
                else:
                    title = key

                dispatchers_ops = dict()
                required_dispatchers_ops = []

                if "online" in cls.DISPATCHERS[key]:
                    online_schema = cls.DISPATCHERS[key]["online"].SCHEMA
                    if isinstance(online_schema, str):
                        online_schema = load_schema(online_schema)
                    dispatchers_ops = {**online_schema["properties"]}
                    if "required" in online_schema:
                        for prop in online_schema["required"]:
                            if prop not in required_dispatchers_ops:
                                required_dispatchers_ops.append(prop)

                if "punctual" in cls.DISPATCHERS[key]:
                    punctual_schema = cls.DISPATCHERS[key]["punctual"].SCHEMA
                    if isinstance(punctual_schema, str):
                        punctual_schema = load_schema(punctual_schema)
                    dispatchers_ops = {**punctual_schema["properties"]}
                    if "required" in punctual_schema:
                        for prop in punctual_schema["required"]:
                            if prop not in required_dispatchers_ops:
                                required_dispatchers_ops.append(prop)

                dispatcher_schema = {
                    "title": title,
                    "properties": {
                        "dispatcher": {"type": "string", "const": key, "title": "Dispatch method"},
                        **dispatchers_ops,
                    },
                    "required": required_dispatchers_ops,
                }

                enum.append(dispatcher_schema)

            operation_parameters_schema["oneOf"] = enum

        return schema

    @classmethod
    def compute_schema(cls):
        schema = super().compute_schema()

        parent_class = cls.__bases__[0]
        operation_parameters_schema = cls.OPERATION_PARAMETERS_SCHEMA
        if (
            issubclass(parent_class, Operator)
            and operation_parameters_schema != parent_class.OPERATION_PARAMETERS_SCHEMA
        ):
            if isinstance(operation_parameters_schema, str):
                operation_parameters_schema = load_schema(operation_parameters_schema)
            cls.update_class_schema(
                schema["properties"]["operation_parameters"], operation_parameters_schema, cls
            )

        return schema

    def __init__(
        self,
        simulation_model,
        agent_id,
        fleet_dict,
        mode=None,
        staff_dict=None,
        depot_points=None,
        stop_points_from=None,
        extend_graph_with_stops=False,
        zone_polygon=None,
        operation_parameters=None,
        **kwargs,
    ):
        """
        Initialise the service operator with the relevant properties.

        The operator class present many different attributes. All are not
        necessarily used when describing a transport system operator.

        :param simulation_model: SimulationModel object
        :param agent_id: operator's id
        :param fleet_dict: name of the population that contains the operator's fleet
        :param staff_dict: name of the population that contains the operator's staff
        :param depot_points: list of dicts describing operator depot points
        :param stop_points_from: stop points source
        :param extend_graph_with_stops: boolean indicating if the graph should be extended with the stop points
        :param zone_polygon: list of GPS points delimiting the service zone
        :param operation_parameters: additional parameters used for service operation
        :param kwargs:
        """

        Agent.__init__(self, simulation_model, agent_id, mode=mode, **kwargs)

        # data structures containing the service information

        # parent operator id
        self.parentOperatorId = None

        # parameters determining the service operation
        self.operationParameters = None
        self.init_operation_parameters(operation_parameters)

        # graph extension boolean
        self.extend_graph_with_stops = extend_graph_with_stops

        # set the fleet population (agents that provide the main transport service)
        self.fleet_name = fleet_dict
        self.fleet = self.sim.agentPopulation.new_population(fleet_dict)

        # set the staff population (agents that manage the fleet and operations)
        self.staff_dict_name = staff_dict
        self.staff = self.sim.agentPopulation.new_population(staff_dict)

        # data structure containing the main service structure, if there is one
        self.service_info = None
        self.init_service_info()

        # DataFrame containing the shapes of the service lines with columns
        # stop_id_A	stop_name_A	stop_id_B stop_name_B lon lat sequence distance distance_proportion
        self.line_shapes = None
        self.init_line_shapes()

        # GeoDataFrame representing the service zone of the operator
        self.serviceZone = None
        self.init_zone(zone_polygon)

        # a dict of the service stop points {id: StopPoint}
        self.stopPoints = dict()
        self.init_stops(stop_points_from)

        # set the dict containing the depot points of the service
        self.depotPoints = dict()
        self.init_depot_points(depot_points)

        # trip count, used when generating trips
        self.tripCount = 0

        # a dict of service trips {trip_id: [agent, planning]}
        self.trips = dict()
        self.init_trips()

        # requests management

        # request count
        self.requestCount = 0
        # request dict
        self.requests = dict()
        # fulfilled requests
        self.fulfilled = dict()
        # left out requests
        self.leftOutRequests = []
        # minimum horizon for booking a trip
        self.bookingDeadline = 0

        # request dispatcher called punctually
        self.punctual_dispatcher = None

        # dispatcher called to handle requests online
        self.online_dispatcher = None

        self.init_dispatchers()

    # properties

    @property
    def servicePoints(self):
        """
        Return a dict mapping both stop points and depot points.
        """
        return {**self.stopPoints, **self.depotPoints}

    # attributes initialisation methods

    def init_operation_parameters(self, operation_parameters):
        """
        Initialise the operation parameters of the operator.

        If the class attribute OPERATION_PARAMETERS_SCHEMA is provided, it is
        used to validate the given parameters and set default values if needed.

        :param operation_parameters: dict of operational parameters
        """
        if operation_parameters is None:
            operation_parameters = dict()
        self.operationParameters = operation_parameters

    def init_service_info(self):
        """
        Import and initialise the data structures containing
        service information and line shapes.
        """

    def init_line_shapes(self):
        """
        Set the service lines shapes file according to the dedicated parameter.
        """

        if "line_shapes_file" in self.operationParameters:
            line_shapes_path = gtfs_feeds_folder() + self.operationParameters["line_shapes_file"]
            self.line_shapes = pd.read_csv(line_shapes_path, sep=";")
            self.line_shapes = self.line_shapes.astype({"stop_id_A": str, "stop_id_B": str})

    def init_zone(self, zone_polygon):
        """
        Set the operator service zone according to the given polygon.

        The service zone is described by a GeoDataFrame containing a
        shapely Polygon.

        :param zone_polygon: list of points describing a polygon
        """

        if isinstance(zone_polygon, str):
            filepath = scenario_agent_input_filepath(
                self.sim.scenario.scenario_folder, zone_polygon
            )
            geojson = json_load(filepath)
            service_zone = geopandas_polygon_from_points(
                geojson["features"][0]["geometry"]["coordinates"][0]
            )
        elif zone_polygon is None:
            service_zone = None
        else:
            raise TypeError(
                "The zone_polygon parameter must be either an input filename or a list of coordinates"
            )

        self.serviceZone = service_zone

    def init_depot_points(self, depot_points):
        """
        Initialise the depotPoints attribute using the given depots information.

        Depot points are StopPoint instances but are stored in a separate attribute named depotPoints.

        :param depot_points: { id, coordinates, name } information dict
        """

        if depot_points is None:
            return

        for depot_data in depot_points:
            depot_id = depot_data["id"]
            name = depot_data["depot_name"] if "depot_name" in depot_data else None
            coordinates = depot_data["coordinates"]

            # infer depot position according to service modes
            if self.mode is None:
                depot_modes = list(self.sim.environment.topologies.values())
            else:
                depot_modes = list(self.mode.values())
            position = self.sim.environment.nearest_node_in_modes(
                [coordinates[1], coordinates[0]], depot_modes
            )

            # create depot as a StopPoint object and add it to depotPoints
            self.new_stop_point(position, depot_id, name, allow_existing=False, is_depot=True)

    def init_stops(self, stop_points_from):
        """
        Initialise the stopPoints attribute using the provided method.
        """

        # get a table of stop points using the provided method
        if stop_points_from is None:
            return
        elif stop_points_from.endswith(".geojson"):
            stops_table = self._stops_table_from_geojson(stop_points_from)
        elif stop_points_from == "gtfs":
            stops_table = self._stops_table_from_gtfs()
        else:
            raise ValueError(
                f"Unsupported value for parameter 'stop_points_from' : {stop_points_from}"
            )

        # create stop points from table and assign them to the operator
        # TODO : prefix ? error, stopPoints will be named differently
        if not stops_table.empty:
            self.add_stops(stops_table, id_prefix="")

    def _stops_table_from_geojson(self, filename):
        """
        Create a stops table from the provided GeoJSON input filename.

        :param filename: input filename (*.geojson)

        :return: stops table
        """
        stops_filepath = scenario_agent_input_filepath(
            self.sim.scenario.scenario_folder,
            filename,
        )
        stops_table = stops_table_from_geojson(stops_filepath)
        return stops_table

    def _stops_table_from_gtfs(self):
        """
        Create a stops table from the operator's GTFS (service_info).

        :return: stops table
        """
        stops_table = stop_table_from_gtfs(self.service_info)
        return stops_table

    def add_stops(self, stops_table, id_prefix=""):
        """
        Add the sequence of stops to the stopPoints dict.

        The stops table is a gtfs-like DataFrame, with the columns
        "stop_id" and "stop_name". The method also uses the
        'stop_correspondence_file", which links service stops
        to topology positions.

        :param stops_table: gtfs-like DataFrame
        :param id_prefix: prefix to add to stop ids
        """

        if not set(ADD_STOPS_COLUMNS).issubset(set(stops_table.columns)):
            raise ValueError(
                "Missing columns when adding stop points. Required columns are {} and {} are provided.".format(
                    ADD_STOPS_COLUMNS, stops_table.columns
                )
            )

        # TODO : this choice of modes is arbitrary, do better
        correspondence_modes = ["walk", self.mode["fleet"]]

        # find the nearest nodes of the stops and extend the graph if asked
        self.sim.environment.add_stops_correspondence(
            stops_table, correspondence_modes, self.extend_graph_with_stops
        )

        # browse stops and add StopPoint objects to stopPoints
        for index, row in stops_table.iterrows():
            # get the stop point id, name and position from the table
            stop_point_id = id_prefix + row["stop_id"]
            stop_point_name = row["stop_name"]
            stop_position = row["nearest_node"]

            self.new_stop_point(stop_position, stop_point_id, stop_point_name)

    def new_stop_point(
        self,
        stop_point_position,
        stop_point_id,
        stop_point_name=None,
        allow_existing=True,
        is_depot=False,
    ):
        """
        Create or get existing StopPoint and add it to the operator stop points.

        :param stop_point_id: new stop id
        :param stop_point_position: new stop position
        :param stop_point_name: new stop name
        :param allow_existing: allow existence of a stop point with same id
        :param is_depot: indicates if new stop point is a depot

        :return: corresponding StopPoint object
        """
        stop_point_population = self.sim.agentPopulation.new_population(STOP_POINT_POPULATION)
        # if the stop point already exists, get it from the stop point population
        if stop_point_id in stop_point_population:
            if allow_existing:
                stop_point = stop_point_population[stop_point_id]
                # no comparison between the two positions. The stops initialisation must be well ordered
            else:
                raise ValueError("Stop point with id {} already exists !".format(stop_point_id))

        # otherwise, create a new StopPoint object and add it to the population
        else:
            if stop_point_name is None:
                stop_point = StopPoint(stop_point_position, stop_point_id)
            else:
                stop_point = StopPoint(stop_point_position, stop_point_id, stop_point_name)
            self.sim.agentPopulation.new_agent_in(stop_point, STOP_POINT_POPULATION)

        # add the stop point to the relevant operator dict
        if is_depot:
            self.depotPoints[stop_point.id] = stop_point
        else:
            self.stopPoints[stop_point.id] = stop_point

        return stop_point

    def init_trips(self):
        """
        Initialise the trips attribute using simulation data.
        """

    def add_trip(self, agent, planning, trip_id=None):
        """
        Add a new trip to the trips dict.

        Associate the trip_id to the agent that realises the trip
        and the planning that describes the trip.

        The default trip id built as <self.id>_T<self.tripCount>.

        :param agent: agent realising the trip, or None if the agent is not known yet
        :param planning: planning of the trip
        :param trip_id: id of the trip, or None

        :return: id of the trip
        """

        # set a default trip id if not provided
        if trip_id is None:
            trip_id = self.id + "_T" + str(self.tripCount)

        # set the trip's agent and planning
        self.trips[trip_id] = [agent, planning]

        # increment trip count
        self.tripCount += 1

        # return trip id
        return trip_id

    def position_in_zone(self, position):
        """
        Test if the given position belongs to the service zone.

        The method returns <self> (the operator) if the position
        is in the service zone, and None otherwise.

        :param position: topology node

        :return: either self (operator), if in zone, or None otherwise
        """

        # if no service zone, all is in service zone
        if self.serviceZone is None:
            return self

        # get position GPS localisation from global environment
        position_localisation = self.sim.environment.get_localisation(position)

        # test if localisation is in service zone
        in_zone = points_in_zone(position_localisation, self.serviceZone)

        # return self if in zone
        if in_zone:
            return self
        else:
            return None

    def init_dispatchers(self):
        """
        Initialise the punctual_dispatcher and online_dispatcher attributes.
        """

        if "dispatcher" not in self.operationParameters:
            return
        else:
            dispatcher = self.operationParameters["dispatcher"]

        if dispatcher not in self.DISPATCHERS:
            raise ValueError(
                "Unsupported operation parameter 'dispatcher' value '{}' (see schema)".format(
                    dispatcher
                )
            )

        dispatcher_classes = self.DISPATCHERS[dispatcher]

        parameters = self.dispatcher_parameters()

        try:
            if "online" in dispatcher_classes:
                self.online_dispatcher = dispatcher_classes["online"].__new__(
                    dispatcher_classes["online"]
                )
                self.online_dispatcher.__init__(**parameters)

            if "punctual" in dispatcher_classes:
                self.punctual_dispatcher = dispatcher_classes["punctual"].__new__(
                    dispatcher_classes["punctual"]
                )
                self.punctual_dispatcher.__init__(**parameters)

        except (TypeError, KeyError) as e:
            raise ValueError(
                "Instantiation of operator dispatcher failed with message :\n {}".format(str(e)), 30
            )

    def dispatcher_parameters(self):
        return {"simulation_model": self.sim, "operator": self, "verb": True}

    # new requests management

    def new_request(self, agent, number):
        """
        Create a new request object to the operator, and return it to the requesting agent.

        In the basic Operator's method, the request object is a TripRequest,
        the event is a simple SimPy event, and the request id looks like "R$self.request_count$"

        :param agent: requesting agent
        :param number: number of seats requested
        :return: Request object
        """

        # generate a new request id
        request_id = "R" + str(self.requestCount)

        # initialise a new Request object
        request = TripRequest(agent, self.sim.scheduler.now(), self, number, request_id)
        request.set_request_event()

        # add it to the request list and increment the request count
        self.requestCount += 1
        self.requests[request_id] = request

        # return the request
        return request

    def create_trip_request(
        self,
        agent,
        number,
        pickup_position,
        dropoff_position,
        pickup_request_time,
        dropoff_request_time=None,
        pickup_max_time=None,
        dropoff_max_time=None,
        pickup_stop_point=None,
        dropoff_stop_point=None,
        direct_travel_time=None,
        max_travel_time=None,
        trip_id=None,
    ):
        """
        Create a TripRequest object containing the given trip constraints.

        :param agent:
        :param number:
        :param pickup_position:
        :param dropoff_position:
        :param pickup_request_time:
        :param dropoff_request_time:
        :param pickup_max_time:
        :param dropoff_max_time:
        :param pickup_stop_point:
        :param dropoff_stop_point:
        :param direct_travel_time:
        :param max_travel_time:
        :param trip_id:
        :return:
        """

        # create the TripRequest object
        trip_request = self.new_request(agent, number)

        # create the pickup UserStop
        pickup = UserStop(
            TripRequest.GET_REQUEST,
            pickup_position,
            trip_request.id,
            requested_time=pickup_request_time,
            max_time=pickup_max_time,
            stop_point_id=pickup_stop_point,
        )

        # create the dropoff UserStop
        dropoff = UserStop(
            TripRequest.PUT_REQUEST,
            dropoff_position,
            trip_request.id,
            requested_time=dropoff_request_time,
            max_time=dropoff_max_time,
            max_travel_time=max_travel_time,
            stop_point_id=dropoff_stop_point,
        )

        # set the request user stops
        trip_request.set_stops(pickup, dropoff)

        # set direct travel time
        trip_request.directTravelTime = direct_travel_time

        # set trip id
        if trip_id is not None:
            trip_request.set_trip(trip_id)

        # set a timeout event for pickup
        if pickup_max_time is not None:
            duration_before_max_pickup_time = int(pickup_max_time - self.sim.scheduler.now())
            timeout_event = self.sim.scheduler.new_event_object() | self.sim.scheduler.timeout(
                duration_before_max_pickup_time
            )
            trip_request.pickupEvent = timeout_event

        return trip_request

    def assign_request(self, request):
        """
        Assign the given request to an agent of the fleet

        Call the dispatch algorithm in order to assign a vehicle
        to the given request, and signal the schedule change to
        the chosen vehicle.

        :param request:
        """

        if self.online_dispatcher is None:
            self.leftOutRequests.append(request)
        else:
            self.online_dispatcher.online_dispatch(request)

    def cancel_request(self, request):
        """
        Remove the pending queues of the given assigned request.

        For instance, remove the UserStop objects from the stop points lists.

        Called when a request is canceled by the requesting user or the operator.

        :param request: cancelled request
        """

        print("hello")

    def build_trip_request(
        self,
        number,
        agent=None,
        origin_position=None,
        origin_stop=None,
        origin_time=None,
        destination_position=None,
        destination_stop=None,
        destination_time=None,
        **kwargs,
    ):
        """
        Build a request for a trip with the operator service from the given information.

        Depending on the operator, all parameters may not be necessary, and others mays be added .

        :param agent: agent making the trip request
        :param number: number of seats requested
        :param origin_position: trip origin position in environment
        :param origin_stop: trip origin stop id
        :param origin_time: trip origin time
        :param destination_position: trip destination position in environment
        :param destination_stop: trip destination stop id
        :param destination_time: trip destination time
        :param kwargs: other eventual parameters

        :return: TripRequest completed with trip information set
        """

    # idle service vehicles management

    def idle_behaviour_(self, agent):
        """
        Perform an idle behaviour.

        This method is called when an agent of the
        operator's fleet is idle. The agent then executes
        the behaviour until it is interrupted. The default
        behaviour is to wait indefinitely.

        :param agent: Agent object
        :return: yield a process describing an idle behaviour
        """

        yield agent.execute_process(agent.spend_time_())

    # creation of new service vehicles
    def new_service_vehicle(self, feature):
        """
        Create and initialise a new service vehicle using the model's dynamic input

        :param feature: dictionary containing the service vehicle information
        :return: newly generated ServiceVehicle
        """

        if (
            "operator_id" not in feature["properties"]
            or feature["properties"]["operator_id"] != self.id
        ):
            self.log_message(
                "Error in the 'operator' field for the generation of "
                "a service vehicle : {}".format(feature),
                30,
            )
            return

        new_service_vehicle = self.sim.dynamicInput.new_agent_input(feature)

        return new_service_vehicle

    # utils

    def evaluate_time_window(self, base_time: int, time_window: int):
        """
        Evaluate a time window from the reference and the time window width.

        If the time window width is negative, the reference time is the upper bound,
        and the lower bound is evaluated.

        :param base_time: base for the evaluation of the time window
        :param time_window: time window width

        :return: (time window_end, time_window_end) tuple
        """

        if time_window == 0:
            self.log_message("Time window cannot be equal to 0", 40)
            raise ValueError("Time window cannot be equal to 0")
        elif time_window > 0:
            start = base_time
            end = base_time + time_window
        else:
            start = base_time + time_window
            end = base_time

        return start, end

    def compute_max_travel_time(self, direct_travel_time: int) -> Union[int, None]:
        """
        Evaluate the max travel time formula to get a maximum travel time value [seconds].

        The formula is a Python expression, evaluated using the builtin eval function.
        It can use the direct travel time value by using the following placeholder: {direct_travel_time}
        It must return something that can be cast or rounded using int().

        Examples (without the brackets):
            - "{direct_travel_time} * 1.5"
            - "{direct_travel_time} + 900"
            - "1800"

        :param direct_travel_time: value of the direct travel time (int)

        :return: value of the maximum travel time (int) or None if no constraint is applied
        :raises: ValueError if the evaluation of the formula fails
        """

        # get formula from operation parameters
        max_travel_time_formula = self.operationParameters["max_travel_time"]
        if max_travel_time_formula is None:
            return None

        # format formula with direct travel time
        formula = max_travel_time_formula.format(direct_travel_time=direct_travel_time)

        try:
            # evaluate formula with eval() builtin
            max_travel_time = eval(formula)

            # cast to integer if not None
            if max_travel_time is not None:
                max_travel_time = int(max_travel_time)
        except Exception:
            msg = "Failed to evaluate the following formula for max travel time: {}".format(
                max_travel_time_formula
            )
            self.log_message(msg, 40)
            raise ValueError(msg)

        return max_travel_time
