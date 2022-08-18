import random
import logging
import numpy
import time

from starling_sim.basemodel.population.dict_population import DictPopulation
from starling_sim.basemodel.environment.environment import Environment
from starling_sim.basemodel.input.dynamic_input import DynamicInput
from starling_sim.basemodel.output.output_factory import OutputFactory
from starling_sim.basemodel.schedule.scheduler import Scheduler
from starling_sim.basemodel.trace.trace import trace_simulation_end
from starling_sim.utils.utils import import_gtfs_feed, display_horizontal_bar
from starling_sim.utils.constants import BASE_LEAVING_CODES
from starling_sim.utils.config import config


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

    #: Model environment class
    environment_class = Environment

    #: Model population class
    population_class = DictPopulation

    #: Model dynamic input class
    input_class = DynamicInput

    #: Model output factory class
    output_class = OutputFactory

    def __init__(self, scenario):
        """
        Initialisation of the simulation model with instances of its different elements

        :param scenario: SimulationScenario object
        """

        # simulation parameters
        self.scenario = scenario

        # random seed for the simulation setup and run
        self.randomSeed = scenario["seed"]

        # information to be completed for the specific models

        # elements  of the model
        self.environment = None
        self.agentPopulation = None
        self.dynamicInput = None
        self.outputFactory = None

        # event manager
        self.scheduler = None

        # complete, unfiltered gtfs timetable, if relevant
        self.gtfs = None

        self._base_init(scenario)

    def _base_init(self, scenario):
        self._init_model(scenario)
        self._init_scenario_run(scenario)

    def _init_model(self, scenario):
        """
        Initialise the simulation model with element that do not depend on the scenario.

        This method is called once, during the model initialisation.

        :param scenario: SimulationScenario object
        """

        # add the base leaving codes
        self.add_base_leaving_codes()

        # create the simulation environment
        self._init_environment(scenario)

    def _init_scenario_run(self, scenario):
        """
        Initialise the scenario-related elements of the model.

        This method should be called before running a new simulation scenario.

        :param scenario: SimulationScenario object
        """
        # base scenario information
        self.scenario = scenario
        self.randomSeed = scenario["seed"]

        # event manager
        self._init_scheduler()

        # model elements
        self._init_agent_population()
        self._init_dynamic_input()

        # maybe we could move the output factory to the model elements ?
        self._init_output_factory()

    def _init_environment(self, scenario):
        """
        Initialise the simulation environment using the environment_class attribute.

        :param scenario: SimulationScenario object
        """
        self.environment = self.environment_class.__new__(self.environment_class)
        self.environment.__init__(scenario)

    def _init_agent_population(self):
        """
        Initialise the simulation agent population using the population_class attribute.
        """
        self.agentPopulation = self.population_class.__new__(self.population_class)
        self.agentPopulation.__init__(self.agent_type_class.keys())

    def _init_dynamic_input(self):
        """
        Initialise the simulation dynamic input using the input_class attribute.
        """
        self.dynamicInput = self.input_class.__new__(self.input_class)
        self.dynamicInput.__init__(self.agent_type_class)

    def _init_output_factory(self):
        """
        Initialise the simulation output factory using the output_class attribute.
        """
        self.outputFactory = self.output_class.__new__(self.output_class)
        self.outputFactory.__init__()

    def _init_scheduler(self):
        """
        Initialise the simulation scheduler.
        """
        self.scheduler = Scheduler()

    def setup(self):
        """
        Sets the entries of the simulation model and prepares it for the simulation run.
        It is here that the files and data are effectively read and imported in the model.

        This method can be extended to manage and setup other elements of the model
        """
        self._setup_model()
        self._setup_scenario_run()

    def _setup_model(self):
        """
        Set up the simulation model elements that do not depend on the scenario.

        This method is called once, during the model setup.
        """
        start = time.time()

        logging.info("Setting up model")
        # setup model elements
        self._setup_environment()
        self.setup_gtfs()

        duration = round(time.time() - start, 1)
        logging.info("End of model setup. Elapsed time : {} seconds\n".format(duration))
        self.scenario.set_stat("model_setup_time", duration)

    def _setup_scenario_run(self):
        """
        Set up the scenario-related elements of the model.

        This method should be called before running a new simulation scenario.
        """

        display_horizontal_bar()
        logging.info("Setting up run of scenario: {}".format(self.scenario.name))
        start = time.time()
        # set the parameters and initialize the random seed
        self.setup_seeds()

        # setup scenario elements
        self._setup_dynamic_input()
        self._setup_output_factory()

        duration = round(time.time() - start, 1)
        logging.info("End of scenario setup. Elapsed time : {} seconds\n".format(duration))
        self.scenario.set_stat("scenario_setup_time", duration)

    def _setup_environment(self):
        """
        Set up the simulation environment.
        """
        logging.debug("Simulation environment setup")
        self.environment.setup(self)

    def _setup_dynamic_input(self):
        """
        Set up the simulation dynamic input.
        """
        logging.debug("Dynamic input setup")
        self.dynamicInput.setup(self)

    def _setup_output_factory(self):
        """
        Set up the simulation output factory.
        """
        logging.debug("Output factory setup")
        self.outputFactory.setup(self)

    def run(self):
        """
        Runs the simulation model until the time limit is reached.

        This method can be extended to run other elements of the model
        """

        logging.info("Starting simulation run")

        start = time.time()

        # if asked, add a process that logs the simulation time every hour
        if "time_log" in self.scenario and self.scenario["time_log"]:
            self.scheduler.new_process(self.periodic_hour_log())

        # create agents and add their loops
        self.scheduler.new_process(self.dynamicInput.play_dynamic_input_())

        # run the simulation
        self.scheduler.run(self.scenario["limit"])

        # trace the end of the simulation for all agents
        trace_simulation_end(self)

        duration = round(time.time() - start, 1)

        logging.info("End of simulation run. Elapsed time : {} seconds\n".format(duration))
        self.scenario.set_stat("execution_time", duration)

        shortest_path_count = 0
        for topology in self.environment.topologies.values():
            shortest_path_count += topology.shortest_path_count
        self.scenario.set_stat("shortest_paths", shortest_path_count)

    def generate_output(self):
        """
        Generate an output of the current simulation
        """

        logging.info("Generating outputs")
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
        Set up a gtfs timetable for the simulation.
        """

        if "gtfs_timetables" in self.scenario:
            logging.debug("GTFS tables setup")
            # import the gtfs timetable from the zip given in the parameters
            restrict_transfers = config["transfer_restriction"]
            self.gtfs = import_gtfs_feed(self.scenario["gtfs_timetables"], restrict_transfers)

    @classmethod
    def get_agent_type_schemas(cls):

        agent_type_class = cls.agent_type_class
        schemas = dict()
        for agent_type in agent_type_class.keys():
            schemas[agent_type] = agent_type_class[agent_type].get_schema()

        return schemas
