from starling_sim.basemodel.trace.trace import Traced
from starling_sim.basemodel.trace.events import InputEvent
from starling_sim.utils.utils import json_load, validate_against_schema
from starling_sim.utils.constants import STOP_POINT_POPULATION
from jsonschema import ValidationError
from json import JSONDecodeError

import traceback
import random


class DynamicInput(Traced):
    """
    This class manages the agent entering the simulation.

    It generates base agents at the beginning of the simulation, and
    dynamically adds agents in the environment during the simulation.
    """

    AGENT_FEATURE_SCHEMA = "AgentFeature.schema.json"

    def __init__(self, agent_type_dict):

        super().__init__("INPUT")

        #: correspondence dict between agent_type and class
        self.agent_type_class = agent_type_dict

        self.dynamic_feature_list = None

    def __str__(self):
        """
        Gives a string display to the dynamic input
        :return:
        """

        return "[dynamicInput: model={}, randomSeed={}]" \
            .format(self.sim.name, self.sim.randomSeed)

    def setup(self, simulation_model):
        """
        Set the simulation model attribute and generate the base agents.

        :param simulation_model: SimulationModel
        """

        # set the simulation model attribute
        self.sim = simulation_model

        # set the attribute of dynamic features

        self.dynamic_feature_list = self.feature_list_from_file(
            self.sim.parameters["dynamic_input_file"])

        # sort list according to origin times
        self.dynamic_feature_list = sorted(self.dynamic_feature_list, key=lambda x: x["properties"]["origin_time"])

        # get the list of static features (present at the start of the simulation)
        init_file = self.sim.parameters["init_input_file"]
        init_feature_list = self.feature_list_from_file(init_file)

        # TODO : pre-process init feature collection

        for feature in init_feature_list:

            # generate a new agent based on the feature properties
            self.new_agent_input(feature)

        # pre-process the dynamic feature collection
        self.pre_process_features(self.dynamic_feature_list, "walk")

    def play_dynamic_input_(self):
        """
        Add agents to the simulation over time.

        Agents are created based on the dynamic input file,
        where the generation time is specified as 'origin_time'.
        """

        for feature in self.dynamic_feature_list:

            # TODO : check the feature schema ? duplicate with FeatureCollection check

            # see if an offset should be applied to the input origin time
            if "early_dynamic_input" in self.sim.parameters and self.sim.parameters["early_dynamic_input"]:
                early_input_time_offset = self.sim.parameters["early_dynamic_input"]
            else:
                early_input_time_offset = 0

            # compute the effective generation time
            generation_time = int(feature["properties"]["origin_time"]) - early_input_time_offset

            # check that the generation time is positive
            if generation_time < 0:
                self.log_message("Feature {} cannot be generated at {}, "
                                 "generation at time 0 instead.".format(feature, generation_time), 30)
                generation_time = 0

            # wait for the next generation
            waiting_time = generation_time - self.sim.scheduler.now()
            yield self.sim.scheduler.timeout(waiting_time)

            # generate new agent
            self.new_agent_input(feature)

    def new_agent_input(self, feature):
        """
        Create and initialise a new agent, and add it to the simulation environment.

        :param feature:
        :return:
        """

        # validate the agent feature against the json schema
        if not validate_against_schema(feature, self.AGENT_FEATURE_SCHEMA, raise_exception=False):
            return

        # get the agent input dict
        input_dict = feature["properties"]

        # pre-process the agent input dict
        self.pre_process_input_dict(input_dict)

        # the agent is associated to the population of its type and other provided populations
        if "population" in input_dict:
            populations = input_dict["population"]
            if isinstance(populations, list):
                populations.append(input_dict["agent_type"])
            else:
                populations = [populations, input_dict["agent_type"]]

            # only keep distinct populations
            populations = set(populations)
            populations = list(populations)
        else:
            populations = input_dict["agent_type"]

        # get the agent type
        agent_type = input_dict["agent_type"]

        if agent_type in self.agent_type_class:

            # get the class to generate
            agent_class = self.agent_type_class[agent_type]

            # generate the new agent
            new_agent = agent_class.__new__(agent_class)

            # initialise the new agent
            try:
                new_agent.__init__(self.sim, **input_dict)
            except (TypeError, KeyError, ValidationError) as e:
                # if the initialisation fails, log and leave
                self.log_message("Instantiation of {}  failed with message :\n {}"
                                 .format(self.agent_type_class[agent_type], traceback.format_exc()), 30)
                exit(1)

            # add the agent to the simulation environment
            self.add_agent_to_simulation(new_agent, populations)

            return new_agent

        else:
            self.log_message("Unknown agent_type {}. Class dict is {}."
                             .format(agent_type, self.agent_type_class))
            return

    def add_agent_to_simulation(self, agent, populations):
        """
        Add the agent to the simulation environment.

        Add the agent to its population, then trace an input event
        and start its simpy loop.

        :param agent: Agent object
        :param populations: population(s) where the agent belongs
        """

        # add agent to relevant population
        self.sim.agentPopulation.new_agent_in(agent, populations)

        # trace and log input event
        self.trace_event(InputEvent(self.sim.scheduler.now(), agent))

        # add the agent loop to the event manager
        agent.main_process = self.sim.scheduler.new_process(agent.simpy_loop_())

    # get and manage input dicts from the input files

    def feature_list_from_file(self, filename):
        """
        Get the list of input features from the given filename.

        The file must be a geojson, following the FeatureCollection schema,
        and be stored in the input folder.

        :param filename: name of the input file, stored in the input folder
        :return: list of geojson Feature dicts
        """

        if filename is None:
            return []

        # complete the file path with the input folder path
        filepath = self.sim.parameters["input_folder"] + filename

        # read the dict contained in input file
        try:
            geojson_input = json_load(filepath)

            # TODO : validate against FeatureCollection

        except JSONDecodeError as e:
            # TODO : test this
            self.log_message("Error while decoding input file {} : {}\n "
                             "Are you sure the file is a JSON ?".format(filename, e), 30)
            return []

        except ValidationError as e:
            self.log_message("Error while validating the input data : {}\n Are you sure "
                             "the json follows the FeatureCollection schema ?".format(e), 30)
            return []

        # return the feature list
        return geojson_input["features"]

    def make_demand_static(self):

        if "make_static" in self.sim.parameters \
                and self.sim.parameters["make_static"] in ["all", "prebooked", "prebooked_only", "ghosts"]:

            # also add the agents of dynamic input that are prebooked
            dynamic_features = []

            make_static = self.sim.parameters["make_static"]

            for feature in self.dynamic_feature_list:
                properties = feature["properties"]

                if make_static == "all":
                    self.new_agent_input(feature)
                elif make_static == "prebooked" and properties["prebooked"]:
                    self.new_agent_input(feature)
                elif make_static == "prebooked_only":
                    if properties["prebooked"]:
                        self.new_agent_input(feature)
                elif make_static == "ghosts":
                    self.new_agent_input(feature)
                else:
                    dynamic_features.append(feature)

            # store the dynamic ones back
            self.dynamic_feature_list = dynamic_features

    # TODO : adapt to init_input_file and clean
    def pre_process_features(self, features, mode):
        """
        Pre-process the features of the list before
        introduction in the simulation.

        The features are specified using the Geosjon schema.

        :param features: list of input features
        :param mode: topology mode
        :return: list of pre-processed features, or nothing ??
        """

        if not features:
            return

        # first, build a list of longitudes and latitudes
        latitudes = []
        longitudes = []
        for feature in features:

            input_dict = feature["properties"]

            # TODO : clarify this set
            if "mode" not in input_dict:
                input_dict["mode"] = mode

            if "origin_stop_point" in input_dict:
                self.add_key_position_from_stop_point(input_dict, "origin")
            elif "origin_lat" in input_dict and "origin_lon" in input_dict:
                latitudes.append(input_dict["origin_lat"])
                longitudes.append(input_dict["origin_lon"])

            if "destination_stop_point" in input_dict:
                self.add_key_position_from_stop_point(input_dict, "destination")
            if "destination_lat" in input_dict and "destination_lon" in input_dict:
                latitudes.append(input_dict["destination_lat"])
                longitudes.append(input_dict["destination_lon"])

        # find nearest nodes
        if len(longitudes) != 0:
            nearest_nodes = self.sim.environment.localisations_nearest_nodes(longitudes, latitudes, mode)

        # add nodes to input dicts
        i = 0
        for feature in features:

            input_dict = feature["properties"]

            if "origin_stop_point" in input_dict:
                pass
            elif "origin_lat" in input_dict and "origin_lon" in input_dict:
                input_dict["origin"] = nearest_nodes[i]
                i += 1

            if "destination_stop_point" in input_dict:
                pass
            elif "destination_lat" in input_dict and "destination_lon" in input_dict:
                input_dict["destination"] = nearest_nodes[i]
                i += 1

    def pre_process_input_dict(self, input_dict):
        """
        Enhance the given input dict according to the agent type and the needs of the model.

        :param input_dict: input dict to be completed
        :return:
        """
        pass

    def add_key_position_with_mode(self, input_dict, key, modes=None):
        """
        Enhance the given input dict by adding an new position item.

        The position item is found in the environment corresponding to <modes>,
        using the '$key$_lat' and '$key$_lon'parameters.

        :param input_dict: input dict to be completed
        :param key: suffix of the current items and key of the new item
        :param modes: modes to which the position must belong, default mode is found in input dict
        """

        if modes is None:
            modes = input_dict["mode"]

        key_lat = key + "_lat"
        key_lon = key + "_lon"

        if key_lat in input_dict and key_lon in input_dict:

            localisation = (input_dict[key_lat], input_dict[key_lon])
            if type(modes) == list:
                input_dict[key] = self.sim.environment.nearest_node_in_modes(
                    localisation, modes)
            else:
                input_dict[key] = self.sim.environment.topologies[modes].\
                    nearest_position(localisation)

    def add_key_position_from_stop_point(self, input_dict, key):

        input_dict_key = key + "_stop_point"

        # if an operator is provided, use its stop points
        if "operator_id" in input_dict:
            stop_points_dict = self.sim.agentPopulation.get_agent(input_dict["operator_id"]).stopPoints
        # otherwise fetch them from the global stop points population
        else:
            stop_points_dict = self.sim.agentPopulation[STOP_POINT_POPULATION]

        if input_dict[input_dict_key] == "random":
            stop_point = random.choice(list(stop_points_dict.values()))
        else:
            stop_point = stop_points_dict[input_dict[input_dict_key]]

        input_dict[key] = stop_point.position

    def add_key_operator(self, input_dict, input_service=None, operator_id=None, operator_population=None):

        # get the operator id, look in the input dict if not provided
        if operator_id is None:
            operator_id = input_dict["operator_id"]

        # get the operator
        operator = self.sim.agentPopulation.get_agent(operator_id, operator_population)

        # set the "operator" key in input dict
        input_dict["operator"] = operator

        # set others keys according to input service
        if input_service is None:
            return
        elif input_service in ["fleet", "staff"]:

            # set the operator fleet mode if not already done
            # SUPPOSITION : all fleet and staff use the same mode
            if operator.mode is None:
                operator.mode = {input_service: input_dict["mode"]}
            elif input_service not in operator.mode or operator.mode[input_service] is None:
                operator.mode[input_service] = input_dict["mode"]
            else:

                # set input mode from operator if no mode provided
                if "mode" not in input_dict or input_dict["mode"] is None:
                    input_dict["mode"] = operator.mode[input_service]

                # if both are provided and are different, log an error and exit
                elif operator.mode[input_service] != input_dict["mode"]:
                    self.log_message("Input mode of '{}' agent {} ({}) differs from operator's mode ({})"
                                     .format(input_service, input_dict["agent_id"],
                                             input_dict["mode"], operator.mode[input_service]), 40)
                    exit(1)

            # set the input population
            if input_service == "fleet":
                input_dict["population"] = operator.fleet_name
            else:
                input_dict["population"] = operator.staff_dict_name
        else:
            self.log_message("Unknown input service type {}".format(input_service))
