from starling_sim.models.SB_VS.model import Model as SB_VS_model
from starling_sim.models.SB_VS_R.model import Model as SB_VS_R_model
from starling_sim.models.FF_VS.model import Model as FF_VS_model
from starling_sim.simulation_scenario import SimulationScenario
from starling_sim.utils.paths import model_import_path
from starling_sim.utils.utils import create_sub_scenarios

import logging
import time
import importlib

models_dict = {"SB_VS": SB_VS_model, "SB_VS_R": SB_VS_R_model, "FF_VS": FF_VS_model}

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

    def init_simulator_from_parameters(simulation_scenario, pkg):
        """
        Returns a simulator initialised according to the model code
        contained in the given parameters

        :param simulation_scenario: SimulationParameters containing "code"
        :param pkg: name of the source package

        :return: ModelSimulator object
        """

        # get the Model class
        model_class = ModelSimulator.get_model_class(simulation_scenario["code"], pkg)

        logging.info(
            "Initialising simulation model: {} ({})\n".format(
                model_class.name, simulation_scenario.model
            )
        )

        # create a new instance of the simulation model
        try:
            simulation_model = model_class(simulation_scenario)
        except TypeError as e:
            logging.error(
                "Instantiation of {} failed with message :\n {}".format(model_class.__name__, e)
            )
            raise e

        # initialise and return the ModelSimulator object
        simulator = ModelSimulator(simulation_model)
        return simulator

    init_simulator_from_parameters = staticmethod(init_simulator_from_parameters)

    def get_model_class(model_code, pkg):
        """
        Get the Model class of the simulation model.

        :param model_code: model code
        :param pkg: name of the source package

        :return: SimulationModel subclass
        """

        # if the code corresponds to a public model, fetch the Model class in models_dict
        if model_code in models_dict:
            model_class = models_dict[model_code]

        # otherwise, import the Model class using importlib
        else:
            model_path = model_import_path(starling_pkg=pkg, model_code=model_code)

            # try to import the module corresponding to the model code
            try:
                module = importlib.import_module(model_path)
            except ModuleNotFoundError:
                raise ModuleNotFoundError(
                    "Cannot find the module '{}'.\n"
                    "    Maybe there is an error in the model code ? "
                    "Or maybe you forgot to use the -p option of main.py ?".format(model_path)
                )

            # try to get the Model class from the model module
            try:
                model_class = module.Model
            except AttributeError as e:
                logging.error(
                    "Cannot find the class Model in {}.models.{}.model".format(pkg, model_code)
                )
                raise e

        return model_class

    get_model_class = staticmethod(get_model_class)


def launch_simulation(scenario_path, pkg):
    """
    Realises the initialisation, setup, run and output of the simulation
    using the given parameters file. Displays log of execution times

    :param scenario_path: path to scenario folder
    :param pkg: name of the source package
    """

    if scenario_path is None:
        raise ValueError("No scenario folder provided to simulation launcher.")

    # initialise simulation scenario from folder path
    simulation_scenario = SimulationScenario(scenario_path)
    # read simulation parameters
    simulation_scenario.get_scenario_parameters()

    # init the simulator
    simulator = ModelSimulator.init_simulator_from_parameters(simulation_scenario, pkg)

    # setup the simulator
    simulator.setup_simulation()

    # run the simulation
    simulator.run_simulation()

    # generate simulation output
    simulator.generate_output()

    logging.info("End of Starling execution\n")

    logging.shutdown()
