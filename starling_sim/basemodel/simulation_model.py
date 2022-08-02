import random
import logging
import numpy
import datetime

from starling_sim.basemodel.population.dict_population import DictPopulation
from starling_sim.basemodel.environment.environment import Environment
from starling_sim.basemodel.input.dynamic_input import DynamicInput
from starling_sim.basemodel.output.output_factory import OutputFactory
from starling_sim.basemodel.schedule.scheduler import Scheduler
from starling_sim.basemodel.trace.trace import trace_simulation_end
from starling_sim.utils.utils import import_gtfs_feed, get_git_revision_hash
from starling_sim.utils.constants import BASE_LEAVING_CODES
from starling_sim.utils.config import config
from starling_sim.version import __version__


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

        # run_summary
        self.runSummary = self.init_run_summary()

        # add the base leaving codes
        self.add_base_leaving_codes()

        # random seed for the simulation setup and run
        self.randomSeed = scenario["seed"]

        # information to be completed for the specific models

        # elements  of the model
        self.agentPopulation = self.population_class.__new__(self.population_class)
        self.agentPopulation.__init__(self.agent_type_class.keys())
        self.environment = self.environment_class.__new__(self.environment_class)
        self.environment.__init__(scenario)

        # inputs and outputs
        self.dynamicInput = self.input_class.__new__(self.input_class)
        self.dynamicInput.__init__(self.agent_type_class)
        self.outputFactory = self.output_class.__new__(self.output_class)
        self.outputFactory.__init__()

        # event manager
        self.scheduler = Scheduler()

        # complete, unfiltered gtfs timetable, if relevant
        self.gtfs = None

    def setup(self):
        """
        Sets the entries of the simulation model and prepares it for the simulation run.
        It is here that the files and data are effectively read and imported in the model.

        This method can be extended to manage and setup other elements of the model
        """

        # set the parameters and initialize the random seed
        self.setup_seeds()

        # start the simulation setup

        logging.info("Simulation environment setup")
        self.environment.setup(self)

        if "gtfs_timetables" in self.scenario:
            logging.info("GTFS tables setup")
            self.setup_gtfs()

        logging.info("Dynamic input setup")
        self.dynamicInput.setup(self)

        logging.info("Output factory setup")
        self.outputFactory.setup(self)

    def run(self):
        """
        Runs the simulation model until the time limit is reached.

        This method can be extended to run other elements of the model
        """

        # if asked, add a process that logs the simulation time every hour
        if "time_log" in self.scenario and self.scenario["time_log"]:
            self.scheduler.new_process(self.periodic_hour_log())

        # create agents and add their loops
        self.scheduler.new_process(self.dynamicInput.play_dynamic_input_())

        # run the simulation
        self.scheduler.run(self.scenario["limit"])

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
        self.gtfs = import_gtfs_feed(self.scenario["gtfs_timetables"], restrict_transfers)

    def init_run_summary(self):
        """
        Initialise the run summary.
        """

        summary = dict()

        # get run date
        summary["date"] = str(datetime.datetime.today())

        # get starling version
        summary["starling_version"] = __version__

        # get current commit
        summary["commit"] = get_git_revision_hash()

        # copy scenario parameters
        summary["parameters"] = self.scenario.copy_parameters()

        # copy config
        summary["config"] = config.copy()

        # scenario output files
        summary["output_files"] = dict()

        # run statistics
        summary["stats"] = dict()

        return summary

    @classmethod
    def get_agent_type_schemas(cls):

        agent_type_class = cls.agent_type_class
        schemas = dict()
        for agent_type in agent_type_class.keys():
            schemas[agent_type] = agent_type_class[agent_type].get_schema()

        return schemas
