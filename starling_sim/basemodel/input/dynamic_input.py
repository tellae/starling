from starling_sim.basemodel.trace.trace import Traced
from starling_sim.basemodel.trace.events import InputEvent
from starling_sim.basemodel.agent.operators.operator import Operator
from starling_sim.utils.utils import json_load, validate_against_schema, add_defaults_and_validate
from starling_sim.utils.constants import STOP_POINT_POPULATION
from starling_sim.utils.paths import scenario_agent_input_filepath
from jsonschema import ValidationError
from json import JSONDecodeError

import traceback
import random
import os
from copy import deepcopy


class DynamicInput(Traced):
    """
    This class manages the agent entering the simulation.

    It generates base agents at the beginning of the simulation, and
    dynamically adds agents in the environment during the simulation.
    """

    def __init__(self, agent_type_dict):

        super().__init__("INPUT")

        #: correspondence dict between agent_type and class
        self.agent_type_class = agent_type_dict

        self.agent_type_schemas = None

        self.dynamic_feature_list = None

    def __str__(self):
        """
        Gives a string display to the dynamic input
        :return:
        """

        return "[dynamicInput: model={}, randomSeed={}]".format(self.sim.name, self.sim.randomSeed)

    def setup(self, simulation_model):
        """
        Set the simulation model attribute and generate the base agents.

        :param simulation_model: SimulationModel
        """

        # set the simulation model attribute
        self.sim = simulation_model

        self.agent_type_schemas = self.sim.get_agent_type_schemas()

        # set the attribute of dynamic features

        self.dynamic_feature_list = self.feature_list_from_file(
            self.sim.scenario["dynamic_input_file"]
        )

        # sort list according to origin times
        self.dynamic_feature_list = sorted(
            self.dynamic_feature_list, key=lambda x: x["properties"]["origin_time"]
        )

        # get the list of static features (present at the start of the simulation)
        init_files = self.sim.scenario["init_input_file"]

        # if there are several files, concatenate their feature lists
        if isinstance(init_files, list):
            init_feature_list = []
            for filename in init_files:
                init_feature_list += self.feature_list_from_file(filename)
        else:
            init_feature_list = self.feature_list_from_file(init_files)

        # resolve the modes of the agent types
        self.resolve_type_modes_from_inputs(init_feature_list + self.dynamic_feature_list)

        init_without_operators = []

        # create the operators agents
        for feature in init_feature_list:

            agent_type = feature["properties"]["agent_type"]
            agent_class = self.agent_type_class[agent_type]

            if issubclass(agent_class, Operator):
                self.new_agent_input(feature)
            else:
                init_without_operators.append(feature)

        # pre process the positions of the rest of the init input
        self.pre_process_position_coordinates(init_without_operators)

        # create the rest of the init input
        for feature in init_without_operators:

            # generate a new agent based on the feature properties
            self.new_agent_input(feature)

        # pre process the positions of the dynamic input
        self.pre_process_position_coordinates(self.dynamic_feature_list)

    def feature_schema_validation(self, feature):

        # validate against Feature schema
        validate_against_schema(feature, "geojson/Feature.json")

        # test if the feature has an 'agent_type' property
        if "agent_type" not in feature["properties"]:
            raise KeyError(
                "Error in {} : input features must contain an 'agent_type' property".format(feature)
            )

        # validate and set defaults using the schema corresponding to the agent type
        agent_schema = self.agent_type_schemas[feature["properties"]["agent_type"]]
        props = feature["properties"]
        final_props = add_defaults_and_validate(props, agent_schema)
        feature["properties"] = final_props

        return feature

    def play_dynamic_input_(self):
        """
        Add agents to the simulation over time.

        Agents are created based on the dynamic input file,
        where the generation time is specified as 'origin_time'.
        """

        for feature in self.dynamic_feature_list:

            # TODO : check the feature schema ? duplicate with FeatureCollection check

            # see if an offset should be applied to the input origin time
            if (
                "early_dynamic_input" in self.sim.scenario
                and self.sim.scenario["early_dynamic_input"]
            ):
                early_input_time_offset = self.sim.scenario["early_dynamic_input"]
            else:
                early_input_time_offset = 0

            # compute the effective generation time
            generation_time = int(feature["properties"]["origin_time"]) - early_input_time_offset

            # check that the generation time is positive
            if generation_time < 0:
                self.log_message(
                    "Feature {} cannot be generated at {}, "
                    "generation at time 0 instead.".format(feature, generation_time),
                    30,
                )
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

        # get the agent input dict
        input_dict = feature["properties"]

        if "operator_id" in input_dict:
            # link with operator
            self.add_key_operator(input_dict)

        # pre-process the agent input dict
        self.pre_process_input_dict(input_dict)

        # validate the feature and add default values
        try:
            feature = self.feature_schema_validation(feature)
        except Exception as e:
            self.log_message(
                "Agent input was not completed due to the following error : {}".format(str(e)), 30
            )
            return

        input_dict = feature["properties"]

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
            except (TypeError, KeyError, ValidationError):
                # if the initialisation fails, log and leave
                self.log_message(
                    "Instantiation of {}  failed with message :\n {}".format(
                        self.agent_type_class[agent_type], traceback.format_exc()
                    ),
                    30,
                )
                exit(1)

            # add the agent to the simulation environment
            self.add_agent_to_simulation(new_agent, populations)

            return new_agent

        else:
            self.log_message(
                "Unknown agent_type {}. Model agent types are {}.".format(
                    agent_type, list(self.agent_type_class.keys())
                ),
                30,
            )
            return

    def add_agent_to_simulation(self, agent, populations):
        """
        Add the agent to the simulation environment.

        Add the agent to its population, then trace an input event
        and start its simpy loop.

        :param agent: Agent object
        :param populations: population(s) where the agent belongs
        """

        # cancel add to simulation if agent already exists
        try:
            # add agent to relevant population
            self.sim.agentPopulation.new_agent_in(agent, populations)

            # trace and log input event
            self.trace_event(InputEvent(self.sim.scheduler.now(), agent))

            # add the agent loop to the event manager
            agent.main_process = self.sim.scheduler.new_process(agent.simpy_loop_())
        except KeyError:
            pass

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

        # get the path to the input file
        filepath = scenario_agent_input_filepath(self.sim.scenario.scenario_folder, filename)

        # read the dict contained in input file
        try:
            geojson_input = json_load(filepath)

            # TODO : validate against FeatureCollection

        except JSONDecodeError as e:
            self.log_message(
                "Error while decoding input file {} : {}\n "
                "Are you sure the file is a JSON ?".format(filename, e),
                40,
            )
            raise e

        except ValidationError as e:
            self.log_message(
                "Error while validating the input data : {}\n Are you sure "
                "the json follows the FeatureCollection schema ?".format(e),
                40,
            )
            raise e

        # return the feature list
        return geojson_input["features"]

    def make_demand_static(self):

        if "make_static" in self.sim.scenario and self.sim.scenario["make_static"] in [
            "all",
            "prebooked",
            "prebooked_only",
            "ghosts",
        ]:

            # also add the agents of dynamic input that are prebooked
            dynamic_features = []

            make_static = self.sim.scenario["make_static"]

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

    def pre_process_position_coordinates(self, features):
        """
        Add a position to the features with coordinates inputs.

        Group the features by modes and call localisations_nearest_nodes environment method,
        then update the features with the resulting positions.

        :param features: features to pre process
        """

        # create a global dict that associates modes to a list of features and their information
        pre_process_dict = dict()

        # get the model modes dict
        model_modes = self.sim.modes

        # base structure of the content associated to modes
        base_nearest_nodes_dict = {
            "inputs": [],
            "keys": [],
            "lon": [],
            "lat": [],
            "nearest_nodes": None,
        }

        # browse the features
        for feature in features:
            input_dict = feature["properties"]

            # prepare structures for storing feature information
            inputs = []
            keys = []
            lon = []
            lat = []

            # look for coordinates inputs

            origin_coordinates = self.get_position_coordinates_from_feature(feature, "origin")
            if origin_coordinates is not None:

                # deprecated properties 'origin_lon' and 'origin_lat'
                if (
                    origin_coordinates == [0, 0]
                    and "origin_lon" in input_dict
                    and "origin_lat" in input_dict
                ):
                    self.log_message(
                        "Use of 'origin_lon' and 'origin_lat' is deprecated, "
                        "using the feature geometry is preferred",
                        30,
                    )
                    origin_coordinates = [input_dict["origin_lon"], input_dict["origin_lat"]]

                if origin_coordinates != [0, 0]:
                    inputs.append(input_dict)
                    keys.append("origin")
                    lon.append(origin_coordinates[0])
                    lat.append(origin_coordinates[1])

            destination_coordinates = self.get_position_coordinates_from_feature(
                feature, "destination"
            )
            if destination_coordinates is not None:

                # deprecated properties 'destination_lon' and 'destination_lat'
                if (
                    destination_coordinates == [0, 0]
                    and "destination_lon" in input_dict
                    and "destination_lat" in input_dict
                ):
                    self.log_message(
                        "Use of 'destination_lon' and 'destination_lat' is deprecated, "
                        "using the feature geometry is preferred",
                        30,
                    )
                    destination_coordinates = [
                        input_dict["destination_lon"],
                        input_dict["destination_lat"],
                    ]

                if destination_coordinates != [0, 0]:
                    inputs.append(input_dict)
                    keys.append("destination")
                    lon.append(destination_coordinates[0])
                    lat.append(destination_coordinates[1])

            # if there are coordinates inputs, add them to the modes dict
            if len(inputs) != 0:

                # get the modes of the input
                modes = model_modes[input_dict["agent_type"]]

                # if the dict does not exist, create it
                if modes not in pre_process_dict:
                    pre_process_dict[modes] = deepcopy(base_nearest_nodes_dict)

                # append the information to the dict
                nearest_nodes_dict = pre_process_dict[modes]
                nearest_nodes_dict["inputs"] += inputs
                nearest_nodes_dict["keys"] += keys
                nearest_nodes_dict["lon"] += lon
                nearest_nodes_dict["lat"] += lat

        # for each mode group, compute the localisations
        for modes in pre_process_dict.keys():

            # call localisations_nearest_nodes on the dict information
            nearest_nodes_dict = pre_process_dict[modes]
            nearest_nodes = self.sim.environment.localisations_nearest_nodes(
                nearest_nodes_dict["lon"], nearest_nodes_dict["lat"], list(modes)
            )
            nearest_nodes_dict["nearest_nodes"] = nearest_nodes

            # affect the positions back to the input dicts
            for i in range(len(nearest_nodes_dict["inputs"])):
                input_dict = nearest_nodes_dict["inputs"][i]
                input_dict[nearest_nodes_dict["keys"][i]] = nearest_nodes_dict["nearest_nodes"][i]

    def get_position_coordinates_from_feature(self, feature, position_key):

        geometry_type = feature["geometry"]["type"]
        geometry_coordinates = feature["geometry"]["coordinates"]

        res_coordinates = None

        if position_key == "origin":

            if geometry_type == "Point":
                res_coordinates = geometry_coordinates
            elif geometry_type == "LineString":
                res_coordinates = geometry_coordinates[0]

        elif position_key == "destination":
            if geometry_type == "LineString":
                res_coordinates = geometry_coordinates[-1]

        else:
            self.log_message("Unsupported position key '{}'".format(position_key))

        return res_coordinates

    def resolve_type_modes_from_inputs(self, features):
        """
        Resolve the model modes from the inputs.

        Browse the inputs and resolve the missing values of the modes dict.
        Raise an error if there are conflicting values for a same mode.

        :param features: list of input features
        :raises ValueError: if there are problem during the mode resolve
        """

        # get the modes dict of the model
        model_modes = self.sim.modes
        if model_modes is None:
            raise ValueError("Model modes are not specified")

        # do a first pass without replacing the type references
        # only resolve None values and check for conflicts
        for feature in features:

            # get the input dict and its associated mode values
            input_dict = feature["properties"]
            type_modes = model_modes[input_dict["agent_type"]]

            # get an eventual input value
            if "mode" in input_dict:
                input_value = input_dict["mode"]
            else:
                input_value = None

            mode = None

            if isinstance(type_modes, list):
                for i in range(len(type_modes)):
                    mode = self.resolve_mode(type_modes, i, input_value, False)

            if isinstance(type_modes, dict):
                for key in type_modes.keys():

                    # get the relevant input value
                    if input_value is not None:
                        val = input_value[key]
                    else:
                        val = None

                    mode = self.resolve_mode(type_modes, key, val, False)

            # affect the resulting mode if no mode was specified
            if input_value is None and mode is not None:
                input_dict["mode"] = mode

        # do a second pass to resolve the type references
        for agent_type in model_modes.keys():

            modes = model_modes[agent_type]

            if isinstance(modes, list):
                for i in range(len(modes)):
                    self.resolve_mode(modes, i, None, True)

                # transform the lists into sorted tuples without duplicates
                model_modes[agent_type] = tuple(sorted(set(modes)))

            if isinstance(modes, dict):
                for key in modes.keys():
                    self.resolve_mode(modes, key, None, True)

    def resolve_mode(self, obj, key, input_value, replace_types):
        """
        Resolve the object mode value with recursive calls.

        Resolution is done depending on the nature of the mode value:

        - if the mode value is a topology, return it
        - if the mode value is an agent type, resolve the agent type first mode value
        - if the mode value is None, return the input value

        Input values are only used for the first mode value of lists or the mode values of dicts.

        Check the final result against the input value if provided.

        :param obj: object containing the mode values
        :param key: key of the resolved mode value
        :param input_value: input value or None
        :param replace_types: boolean indicating if agent type value should be
            replaced with the resolved mode.

        :return: resolved mode or None if not resolved
        """

        # only consider input value for first list values or dict values
        if isinstance(key, str) or key == 0:
            input_value = input_value
        else:
            input_value = None

        # get the list of topologies and the global dict of modes
        topologies = list(self.sim.environment.topologies.keys())
        agent_type_modes = self.sim.modes

        # get the keyword to replace
        keyword = obj[key]

        mode = None

        # if the mode value is a topology, return it
        if keyword in topologies:
            mode = keyword

        # if the mode value is an agent type, resolve the agent type first mode value
        elif keyword in agent_type_modes:

            # resolve the agent type mode first mode value
            mode = self.resolve_mode(agent_type_modes[keyword], 0, input_value, replace_types)

            # replace the agent type value with mode if asked
            if replace_types:
                obj[key] = mode

        # if the mode value is None, return the input value
        elif keyword is None:
            obj[key] = input_value
            mode = input_value

        # check the resulting mode with input value if mode value or dict object
        if input_value is not None and mode != input_value:
            raise ValueError(
                "Conflict between type mode '{}' and input value '{}'".format(mode, input_value)
            )

        return mode

    def pre_process_input_dict(self, input_dict):
        """
        Enhance the given input dict according to the agent type and the needs of the model.

        :param input_dict: input dict to be completed
        :return:
        """
        pass

    def add_key_position_from_stop_point(self, input_dict, key):

        input_dict_key = key + "_stop_point"

        # if an operator is provided, use its stop points
        if "operator_id" in input_dict:
            stop_points_dict = self.sim.agentPopulation.get_agent(
                input_dict["operator_id"]
            ).stopPoints
        # otherwise fetch them from the global stop points population
        else:
            stop_points_dict = self.sim.agentPopulation[STOP_POINT_POPULATION]

        if input_dict[input_dict_key] == "random":
            stop_point = random.choice(list(stop_points_dict.values()))
        else:
            stop_point = stop_points_dict[input_dict[input_dict_key]]

        input_dict[key] = stop_point.position

    def add_key_operator(self, input_dict):

        # get the operator id, look in the input dict if not provided
        operator_id = input_dict["operator_id"]

        # get the operator
        operator = self.sim.agentPopulation.get_agent(operator_id)

        populations = [input_dict["agent_type"]]
        if "population" in input_dict:
            populations.append(input_dict["population"])

        if operator.fleet_name in populations:
            input_service = "fleet"
        elif operator.staff_dict_name in populations:
            input_service = "staff"
        else:
            return

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
                    self.log_message(
                        "Input mode of '{}' agent {} ({}) differs from operator's mode ({})".format(
                            input_service,
                            input_dict["agent_id"],
                            input_dict["mode"],
                            operator.mode[input_service],
                        ),
                        40,
                    )
                    raise ValueError("Conflict between operator's mode and its fleet/staff's mode")

            # set the input population
            if input_service == "fleet":
                input_dict["population"] = operator.fleet_name
            else:
                input_dict["population"] = operator.staff_dict_name
        else:
            self.log_message("Unknown input service type {}".format(input_service))
