from starling_sim.models.SB_VS.model import Model as SB_VS_model
from starling_sim.models.SB_VS_R.model import Model as SB_VS_R_model
from starling_sim.models.FF_VS.model import Model as FF_VS_model
from starling_sim.basemodel.parameters.simulation_parameters import parameters_from_file
from starling_sim.utils.paths import model_import_path

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

        # get the Model class
        model_class = ModelSimulator.get_model_class(simulation_parameters["code"], pkg)

        # create a new instance of the simulation model
        try:
            simulation_model = model_class(simulation_parameters)
        except TypeError as e:
            logging.error("Instantiation of {} failed with message :\n {}"
                          .format(model_class.__name__, e))
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
                raise ModuleNotFoundError("Cannot find the module '{}'.\n"
                                          "    Maybe there is an error in the model code ? "
                                          "Or maybe you forgot to use the -p option of main.py ?".format(model_path))

            # try to get the Model class from the model module
            try:
                model_class = module.Model
            except AttributeError as e:
                logging.error("Cannot find the class Model in {}.models.{}.model".format(pkg, model_code))
                raise e

        return model_class

    get_model_class = staticmethod(get_model_class)


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
    logging.info("End of setup. Elapsed time : {:.2f} seconds\n".format(duration))
    simulator.simulationModel.runSummary["setup_time"] = duration

    # run the simulation
    logging.info("Starting the simulation\n")
    start = time.time()
    simulator.run_simulation()
    duration = time.time() - start
    logging.info("End of simulation run. Elapsed time : {:.2f} seconds\n".format(duration))
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
