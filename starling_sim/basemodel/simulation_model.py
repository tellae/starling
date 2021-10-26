import random
import logging
import numpy
import copy
import json
from starling_sim.basemodel.trace.trace import trace_simulation_end
from starling_sim.utils.utils import import_gtfs_feed, validate_against_schema, json_load
from starling_sim.utils.paths import schemas_folder
from starling_sim.utils.constants import PT_PARAMETERS_SCHEMA, BASE_LEAVING_CODES
from starling_sim.utils.config import config
from starling_sim.basemodel.agent.agent import Agent


class SimulationModel:
    """
    Generic simulation model

    It must be extended to describe concrete systems,
    with their specific topologies and agents
    """

    #: Name of the simulation model
    name = "Unnamed model"

    #: Agent types of the model and their classes
    agent_type_class = None

    #: leaving codes of the model and their description
    leaving_codes = {}

    #: Agent types of the model and their modes
    modes = None

    def __init__(self, parameters):
        """
        Initialisation of the simulation model with instances of its different elements

        This constructor must be extended to instantiate the model elements
        using the correct classes

        :param parameters: SimulationParameters object
        """

        # simulation parameters
        self.parameters = parameters

        # run_summary
        self.runSummary = parameters.copy_dict()

        # add the base leaving codes
        self.add_base_leaving_codes()

        # random seed for the simulation setup and run
        self.randomSeed = parameters["seed"]

        # information to be completed for the specific models

        # elements  of the model
        self.agentPopulation = None
        self.environment = None

        # inputs and outputs
        self.dynamicInput = None
        self.outputFactory = None

        # event manager
        self.scheduler = None

        # complete, unfiltered gtfs timetable, if relevant
        self.gtfs = None
        
        # public transport parameters if relevant
        self.PT_parameters = None

        # TODO : data structure to store simulation information (e.g. demand)
        # self.data = None

    def setup(self):
        """
        Sets the entries of the simulation model and prepares it for the simulation run.
        It is here that the files and data are effectively read and imported in the model.

        This method can be extended to manage and setup other elements of the model
        """
        schema = {}
        for agent_type, agent_class in self.agent_type_class.items():
            schema[agent_type] = self.get_schema(agent_class)
        logging.info(str(json.dumps(schema, indent=4)))

        exit(0)

        # set the parameters and initialize the random seed
        self.setup_seeds()

        # start the simulation setup

        logging.info("Simulation environment setup")
        self.environment.setup(self)

        if "gtfs_timetables" in self.parameters:
            logging.info("GTFS tables setup")
            self.setup_gtfs()

        if "PT_parameters" in self.parameters:
            logging.info("PT parameters setup")
            self.setup_pt_parameters()

        logging.info("Dynamic input setup")
        self.dynamicInput.setup(self)

        logging.info("Output factory setup")
        self.outputFactory.setup(self)

    def get_schema(self, aclass):
        if aclass == Agent:
            return aclass.SCHEMA

        class_schema = aclass.SCHEMA
        parent_schema = copy.deepcopy(self.get_schema(aclass.__bases__[0]))
        if class_schema:
            if "remove_props" in class_schema:
                for prop in class_schema["remove_props"]:
                    del parent_schema["properties"][prop]
                    parent_schema["required"].remove(prop)
            if "required" in class_schema:
                for prop in class_schema["required"]:
                    parent_schema["required"].append(prop)

            if "advanced" in class_schema["properties"]:
                parent_schema["properties"]["advanced"]["properties"]\
                    .update(class_schema["properties"]["advanced"]["properties"])
                del class_schema["properties"]["advanced"]

            parent_schema["properties"].update(class_schema["properties"])

        advanced = parent_schema["properties"]["advanced"]
        del parent_schema["properties"]["advanced"]
        parent_schema["properties"]["advanced"] = advanced

        return parent_schema

    def run(self):
        """
        Runs the simulation model until the time limit is reached.

        This method can be extended to run other elements of the model
        """

        # if asked, add a process that logs the simulation time every hour
        if "time_log" in self.parameters and self.parameters["time_log"]:
            self.scheduler.new_process(self.periodic_hour_log())

        # create agents and add their loops
        self.scheduler.new_process(self.dynamicInput.play_dynamic_input_())

        # run the simulation
        self.scheduler.run(self.parameters["limit"])

        # trace the end of the simulation for all agents
        trace_simulation_end(self)

    def generate_output(self):
        """
        Generate an output of the current simulation
        """

        self.outputFactory.extract_simulation(self)

    def add_base_leaving_codes(self):
        """
        Add the base leaving codes to the ones specified for the model.

        This will overwrite any custom code named as a base code.
        """

        self.leaving_codes.update(BASE_LEAVING_CODES)

    def setup_seeds(self):
        """
        Set the seeds of the random functions
        """

        random.seed(self.randomSeed)
        numpy.random.seed(self.randomSeed)

    def periodic_hour_log(self):

        while True:

            logging.info("Current simulation time is {}".format(self.scheduler.now()))

            yield self.scheduler.timeout(3600)

    def setup_gtfs(self):
        """
        Setup a gtfs timetable for the simulation.
        """

        # import the gtfs timetable from the zip given in the parameters
        restrict_transfers = config["transfer_restriction"]
        self.gtfs = import_gtfs_feed(self.parameters["gtfs_timetables"], restrict_transfers)

    def setup_pt_parameters(self):
        """
        Setup the public transport parameters dict of the simulation.

        Import from the simulation parameters,
        complete with default values of the schema
        and validate against schema
        """

        pt_param_schema = json_load(schemas_folder() + PT_PARAMETERS_SCHEMA)

        # get PT parameters dict
        if "PT_parameters" in self.parameters:
            pt_params = self.parameters["PT_parameters"]
        else:
            pt_params = dict()

        validate_against_schema(pt_params, pt_param_schema)

        # complete PT parameters with default values
        for prop in pt_param_schema["properties"].keys():
            if prop not in pt_params:
                pt_params[prop] = pt_param_schema["properties"][prop]["default"]

        # set the PT parameters attribute
        self.PT_parameters = pt_params
