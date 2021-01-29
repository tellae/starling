from starling_sim.models.SB_VS.model import Model as SB_VS_model
from starling_sim.models.SB_VS_R.model import Model as SB_VS_R_model
from starling_sim.models.FF_VS.model import Model as FF_VS_model
from starling_sim.basemodel.parameters.simulation_parameters import parameters_from_file
from starling_sim.utils.paths import MODEL_IMPORT_PATH
from starling_sim.utils.simulation_logging import setup_logging, DEFAULT_LOGGER_LEVEL
from starling_sim.utils.data_tree import create_data_tree, import_example_scenario, import_example_environment
from starling_sim.version import __version__

import argparse
import os
import logging
import time
import importlib

models_dict = {
    "SB_VS": SB_VS_model,
    "SB_VS_R": SB_VS_R_model,
    "FF_VS": FF_VS_model
}

model_codes = list(models_dict.keys())


class ModelSimulator:
    """The simulator runs a simulation model"""

    def __init__(self, model):
        """
        Initialize the simulator and its elements

        :param model: SimulationModel object describing the simulation to run
        """

        self.simulationModel = model

    def setup_simulation(self):
        """
        Prepares the simulation model for running
        """

        self.simulationModel.setup()

    def run_simulation(self):
        """
        Call the run method of the simulation model
        """

        self.simulationModel.run()

    def generate_output(self):
        """
        Generates an output of the simulation at its current state
        """

        self.simulationModel.generate_output()

    def init_simulator_from_parameters(simulation_parameters, pkg):
        """
        Returns a simulator initialised according to the model code
        contained in the given parameters

        :param simulation_parameters: SimulationParameters containing "code"
        :param pkg: name of the source package

        :return: ModelSimulator object
        """

        code = simulation_parameters["code"]

        # if the code corresponds to a public model, fetch the Model class in models_dict
        if code in models_dict:
            model_class = models_dict[code]

        # otherwise, import the Model class using importlib
        else:

            model_path = MODEL_IMPORT_PATH.format(starling_pkg=pkg, model_code=code)

            # try to import the module corresponding to the model code
            try:
                module = importlib.import_module(model_path)
            except ModuleNotFoundError as e:
                logging.error("Cannot find the module model.py in package starling_sim.models.{}".format(code))
                raise e

            # try to get the Model class from the model module
            try:
                model_class = module.Model
            except AttributeError as e:
                logging.error("Cannot find the class Model in starling_sim.models.{}.model".format(code))
                raise e

        # create a new instance of the simulation model
        try:
            simulation_model = model_class(simulation_parameters)
        except TypeError as e:
            logging.error("Instantiation of {}  failed with message :\n {}"
                          .format(model_codes[code], e))
            raise e

        # initialise and return the ModelSimulator object
        simulator = ModelSimulator(simulation_model)
        return simulator

    init_simulator_from_parameters = staticmethod(init_simulator_from_parameters)


def run_main():

    # create a command line parser

    parser = argparse.ArgumentParser(description="Starling agent-based simulation framework")

    parser.add_argument("param_path",
                        help="path to parameter file.",
                        nargs="?")

    parser.add_argument("-l", "--level",
                        help="specify the logger level. See simulation_logging.py for more information.",
                        type=int,
                        default=DEFAULT_LOGGER_LEVEL)

    parser.add_argument("-D", "--data-tree",
                        help="generate the data tree according to the paths stored in paths.py and exit.",
                        action="store_true")

    parser.add_argument("-e", "--examples",
                        help="import example scenarios of the given model codes from the Google Drive of Tellae "
                             "and exit. If no model code is provided, import example scenarios for all public models."
                             "Generate the data tree folders if they don't exist.",
                        nargs="*",
                        metavar=("MODEL_CODE_1", "MODEL_CODE_2"),
                        default=None)

    parser.add_argument("-S", "--sphinx",
                        action="store_true",
                        help="generate the project documentation using Sphinx and exit.")

    parser.add_argument('-p', '--package',
                        help="indicate an alternative name for the base package of starling",
                        type=str,
                        action="store",
                        default="starling_sim")

    parser.add_argument("-v", "--version",
                        action="version",
                        version=__version__)

    # parse the command line

    input_args = parser.parse_args()

    # setup logging
    setup_logging(input_args.level)

    # documentation generation
    if input_args.sphinx:
        os.system("./docs/sphinx-doc.sh")
        exit(0)

    # data tree create
    if input_args.data_tree:
        create_data_tree()
        exit(0)

    # example scenarios
    if input_args.examples is not None:

        # make sure the data tree is setup
        create_data_tree()

        # import examples environment
        import_example_environment()

        if len(input_args.examples) == 0:
            # if no model code is provided, import examples for all public models
            for code in model_codes:
                import_example_scenario(code)
        else:
            for code in input_args.examples:
                if code not in model_codes:
                    raise ValueError("Unknown model code {} for example import. "
                                     "The list of public model codes is {}".format(code, model_codes))
                import_example_scenario(code)
        exit(0)

    # launch simulation
    logging.info("Launching Starling {}\n".format(__version__))
    launch_simulation(input_args.param_path, input_args.package)


def launch_simulation(parameters_path, pkg):
    """
    Realises the initialisation, setup, run and output of the simulation
    using the given parameters file. Displays logs of execution times

    :param parameters_path: path to parameters files
    :param pkg: name of the source package
    """

    if parameters_path is None:
        raise ValueError("No parameters file provided to simulation launcher.")

    # initialise simulation parameters from parameters file
    simulation_parameters = parameters_from_file(parameters_path)

    # init the simulator
    logging.info("Initializing simulator for the model code "
                 + simulation_parameters["code"] + ", scenario "
                 + simulation_parameters["scenario"] + "\n")
    simulator = ModelSimulator.init_simulator_from_parameters(simulation_parameters, pkg)

    # setup the simulator
    logging.info("Setting entries for: " + simulator.simulationModel.name)
    start = time.time()
    simulator.setup_simulation()
    duration = time.time() - start
    logging.info("End of setup. Elapsed time : "
                 + str(duration) + " seconds\n")
    simulator.simulationModel.runSummary["setup_time"] = duration

    # run the simulation
    logging.info("Starting the simulation\n")
    start = time.time()
    simulator.run_simulation()
    duration = time.time() - start
    logging.info("End of simulation run. Elapsed time : "
                 + str(duration) + " seconds\n")
    simulator.simulationModel.runSummary["execution_time"] = duration

    shortest_path_count = 0
    for topology in simulator.simulationModel.environment.topologies.values():
        shortest_path_count += topology.shortest_path_count
    logging.info("Number of shortest_path computed : {}".format(shortest_path_count))
    simulator.simulationModel.runSummary["shortest_paths"] = shortest_path_count

    # generate simulation output
    logging.info("Generating outputs of the simulation\n")
    simulator.generate_output()

    logging.shutdown()
