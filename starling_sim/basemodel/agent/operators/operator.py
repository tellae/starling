from starling_sim.basemodel.agent.agent import Agent
from starling_sim.basemodel.agent.requests import TripRequest, StopPoint
from starling_sim.basemodel.agent.stations.station import Station
from starling_sim.utils.utils import geopandas_polygon_from_points, points_in_zone, json_load, validate_against_schema
from starling_sim.utils.paths import gtfs_feeds_folder, schemas_folder
from starling_sim.utils.constants import STOP_POINT_POPULATION, ADD_STOPS_COLUMNS
from collections import OrderedDict

import pandas as pd


class Operator(Agent):
    """
    Class describing an operator of a transport service.

    Operators manage a fleet of vehicle, and receive requests for the service
    they provide.

    The assignment of these requests is managed by a Dispatcher object.
    """

    OPERATION_PARAMETERS_SCHEMA = {}

    SCHEMA = {
        "properties": {
            "fleet_dict": {
                "type": "string",
                "title": "Fleet population",
                "description": "Population of the operator's fleet agents"
            },
            "staff_dict": {
                "advanced": True,
                "title": "Staff population",
                "description": "Population of the operator's staff agents",
                "type": "string"
            },
            "depot_points": {
                "advanced": True,
                "title": "Depot points",
                "description": "List of depot points coordinates",
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    },
                    "minItems": 2,
                    "maxItems": 2
                }
            },
            "zone_polygon": {
                "advanced": True,
                "title": "Service area file",
                "description": "Geojson input file describing the service area",
                "type": "string"
            },
            "network_file": {
                "advanced": True,
                "title": "Service network file",
                "description": "OSM graph file for the service area",
                "type": "string"
            },
            "operation_parameters": OPERATION_PARAMETERS_SCHEMA,
            "parent_operator_id": {
                "advanced": True,
                "title": "Parent operator ID",
                "description": "Identifier of the parent operator",
                "type": "string"
            },
            "extend_graph_with_stops": {
                "advanced": True,
                "title": "Extend graph with stops",
                "description": "Indicate if the transport network should be extended with stop points",
                "type": "boolean"
            }

        },
        "required": ["fleet_dict"]
    }

    def __init__(self, simulation_model, agent_id, fleet_dict, staff_dict=None, depot_points=None,
                 zone_polygon=None, network_file=None, operation_parameters=None, parent_operator_id=None,
                 extend_graph_with_stops=False, **kwargs):
        """
        Initialise the service operator with the relevant properties.

        The operator class present many different attributes. All are not
        necessarily used when when describing a transport system operator.

        :param simulation_model: SimulationModel object
        :param agent_id: operator's id
        :param fleet_dict: name of the population that contains the operator's fleet
        :param staff_dict: name of the population that contains the operator's staff
        :param depot_points: list of coordinates of the operator depot points
        :param zone_polygon: list of GPS points delimiting the service zone
        :param network_file: file describing a topology specific to the service
        :param operation_parameters: additional parameters used for service operation
        :param parent_operator_id: id of the parent operator, if there is one
        :param extend_graph_with_stops: boolean indicating if the graph should be extended with the stop points
        :param kwargs:
        """

        Agent.__init__(self, simulation_model, agent_id, **kwargs)

        # data structures containing the service information

        # parent operator id
        self.parentOperatorId = parent_operator_id

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

        # set the dict containing the depot points of the service
        self.depotPoints = dict()
        self.init_depot_points(depot_points)

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

        # a Topology object specific to this operator (smaller graph)
        self.serviceTopology = None
        self.init_topology(network_file)

        # a dict of the service stop points {id: StopPoint}
        self.stopPoints = dict()
        self.init_stops()

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

    # attributes initialisation methods

    def init_operation_parameters(self, operation_parameters):
        """
        Initialise the operation parameters of the operator.

        If the class attribute OPERATION_PARAMETERS_SCHEMA is provided, it is
        used to validate the given parameters and set default values if needed.

        :param operation_parameters: dict of operational parameters
        """

        self.operationParameters = operation_parameters

        if self.operationParameters is None:
            self.operationParameters = dict()

        if self.OPERATION_PARAMETERS_SCHEMA is not None:

            # validate given dict against schema
            operation_param_schema = json_load(schemas_folder() + self.OPERATION_PARAMETERS_SCHEMA)
            validate_against_schema(self.operationParameters, self.OPERATION_PARAMETERS_SCHEMA)

            # complete the parameters with the schema default values
            for param in operation_param_schema["properties"].keys():
                if param not in self.operationParameters:
                    self.operationParameters[param] = operation_param_schema["properties"][param]["default"]

    def init_service_info(self):
        """
        Import and initialise the data structures containing
        service information and line shapes.
        """

    def init_line_shapes(self):
        """
        Set the service lines shapes file according to the dedicated parameter.
        """

        if "line_shapes_file" in self.sim.parameters:
            line_shapes_path = gtfs_feeds_folder() + self.sim.parameters["line_shapes_file"]
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
            filepath = self.sim.parameters["input_folder"] + zone_polygon
            geojson = json_load(filepath)
            service_zone = geopandas_polygon_from_points(geojson["features"][0]["geometry"]["coordinates"][0])
        elif isinstance(zone_polygon, list):
            service_zone = geopandas_polygon_from_points(zone_polygon)
        elif zone_polygon is None:
            service_zone = None
        else:
            raise TypeError("The zone_polygon parameter must be either an input filename or a list of coordinates")

        self.serviceZone = service_zone

    def init_topology(self, network_file):
        """
        Set a topology for the operator if a file is provided.

        The topology will be used by the operator to compute paths
        and distances in its service zone. Its smaller size should
        reduce computation times.

        If network_file is None, use the fleet (or staff ?) topology.

        :param network_file: init file for the topology, or None
        """

    def init_depot_points(self, depot_points_coord):
        """
        Initialise the depotPoints attribute using the given coordinates.

        :param depot_points_coord:
        :return:
        """

        if depot_points_coord is not None and isinstance(depot_points_coord, list):

            for i, coord in enumerate(depot_points_coord):
                depot_id = "depot-" + str(i)
                if self.mode is None:
                    depot_modes = list(self.sim.environment.topologies.values())
                else:
                    depot_modes = list(self.mode.values())
                position = self.sim.environment.nearest_node_in_modes(coord, depot_modes)
                depot = Station(self.sim, depot_id, position)
                self.depotPoints[depot_id] = depot

    def init_stops(self):
        """
        Initialise the stopPoints attribute with using simulation data.
        """

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
            raise ValueError("Missing columns when adding stop points. Required columns are {} and {} are provided."
                             .format(ADD_STOPS_COLUMNS, stops_table.columns))

        # TODO : this choice of modes is arbitrary, do better
        correspondence_modes = ["walk", self.mode["fleet"]]

        # find the nearest nodes of the stops and extend the graph if asked
        self.sim.environment.add_stops_correspondence(stops_table, correspondence_modes, self.extend_graph_with_stops)

        # browse stops and add StopPoint objects to stopPoints
        for index, row in stops_table.iterrows():

            # get the stop point id, name and position from the table
            stop_point_id = id_prefix + row["stop_id"]
            stop_point_name = row["stop_name"]
            stop_position = row["nearest_node"]

            stop_point_population = self.sim.agentPopulation.new_population(STOP_POINT_POPULATION)

            # if the stop point already exists, get it from the stop point population
            if stop_point_id in stop_point_population:
                stop_point = stop_point_population[stop_point_id]

                # no comparison between the two positions. The stops initialisation must be well ordered

            # otherwise, create a new StopPoint object and add it to the population
            else:
                stop_point = StopPoint(stop_position, stop_point_id, stop_point_name)
                self.sim.agentPopulation.new_agent_in(stop_point, STOP_POINT_POPULATION)

            # add the stop point to the operator stop points dict
            self.stopPoints[stop_point.id] = stop_point

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
            return None

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

    # new requests management

    def new_request(self, agent):
        """
        Create a new request object to the operator, and return it to the requesting agent.

        In the basic Operator's method, the request object is a TripRequest,
        the event is a simple SimPy event, and the request id looks like "R$self.request_count$"

        :param agent: requesting agent
        :return: Request object
        """

        # generate a new request id
        request_id = "R" + str(self.requestCount)

        # initialise a new Request object
        request = TripRequest(agent, self.sim.scheduler.now(), self, request_id)
        request.set_request_event()

        # add it to the request list and increment the request count
        self.requestCount += 1
        self.requests[request_id] = request

        # return the request
        return request

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

    def build_trip_request(self, agent=None, origin_position=None, origin_stop=None, origin_time=None,
                           destination_position=None, destination_stop=None, destination_time=None, **kwargs):
        """
        Build a request for a trip with the operator service from the given information.

        Depending on the operator, all parameters may not be necessary, and others mays be added .

        :param agent: agent making the trip request
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

        if "operator" not in feature["properties"] or feature["properties"]["operator"] != self:
            self.log_message("Error in the 'operator' field for the generation of "
                             "a service vehicle : {}".format(feature), 30)
            return

        new_service_vehicle = self.sim.dynamicInput.new_agent_input(feature)

        return new_service_vehicle

    # evaluation of a set of user journeys using operator service

    def user_journeys(self, origin, destination, parameters,
                      objective_time, objective_type="start_after"):
        """
        Compute a list of journeys using the operator's transport system.

        Journeys from origin to destination are computed according to the
        operator service, using routers or other itinerary tools.

        The parameters are also used to adjust the journeys characteristics.

        The objective type is either "start_after" or "arrive_before", which correspond
        to the way the journeys will be computed. The objective time specifies the value
        of this start or arrival time.

        A journey is represented as a DataFrame (see journeys.py).

        :param origin: origin position
        :param destination: destination position
        :param parameters: dict of parameters.
        :param objective_time: value of the start or arrival time
        :param objective_type: way of computing journeys, either "start_after" or "arrive_before"
            Default is "start_after".
        :return: a list of journeys represented by DataFrames
        """

    def create_journeys(self, departures_table, arrival_stops, parameters):
        """
        Compute a list of journeys for the given departures timetable and arrival stops.

        :param departures_table:
        :param arrival_stops:
        :param parameters:

        :return: a list of journeys
        """

    def confirm_journey_(self, journey, agent, parameters):
        """
        Confirm the journey choice of the agent and assign its requests if necessary.

        The request assignment may not be immediate, so the confirmation can take some time.

        :param journey:
        :param agent:
        :param parameters:

        :return: boolean indicating if the chosen journey can be executed
        """

        yield self.execute_process(self.spend_time_(0))

        return True

    # utils

    def compute_travel_time_with_detour(direct_travel_time, max_detour):
        """
        Compute the travel time of a trip with a given detour.

        The deviated travel time can be used to compute a maximum acceptable
        travel time, or an estimated travel time.

        If the detour is a float, it is used as a multiplicand with the direct travel time.
        If it is an integer, it is used as a constant (in seconds) added to the direct travel time.

        :param direct_travel_time: direct travel time in seconds
        :param max_detour: maximum detour, either as a multiplicand or as a constant, or None

        :return: deviated travel time (can be a float or an int), or None if max detour is None
        """

        if isinstance(max_detour, float):
            max_travel_time = direct_travel_time * max_detour
        elif isinstance(max_detour, int):
            max_travel_time = direct_travel_time + max_detour
        elif max_detour is None:
            max_travel_time = None
        else:
            raise ValueError("Unsupported type for max detour parameter : {}".format(type(max_detour)))

        return max_travel_time

    compute_travel_time_with_detour = staticmethod(compute_travel_time_with_detour)
