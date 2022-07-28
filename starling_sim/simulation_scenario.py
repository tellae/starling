"""
This module manages the parameters of the simulation
"""

import logging
import os
import json
from copy import deepcopy

from starling_sim.utils.utils import json_load, validate_against_schema
from starling_sim.utils import paths


class SimulationScenario:
    """
    This class describes a simulation scenario folders and data.
    """

    BASE_PARAM_SCHEMA = "parameters.schema.json"

    def __init__(self, scenario_folder_path: str):

        # scenario folder path
        self.scenario_folder = None

        # scenario inputs folder path
        self.inputs_folder = None

        # scenario outputs folder path
        self.outputs_folder = None

        # simulation parameters (can be accessed using SimulationScenario["key"])
        self.parameters = None

        # scenario model code
        self.model = None

        # scenario name
        self.name = None

        # set the scenario folders
        self._set_scenario_folders(scenario_folder_path)

    def _set_scenario_folders(self, scenario_folder_path: str):
        """
        Set the folder attributes from the scenario folder path.

        Paths are built according to the structure enforced by the functions of starling_sim.utils.paths.

        :param scenario_folder_path: path to the scenario folder
        """

        # check scenario folder
        self.scenario_folder = os.path.join(scenario_folder_path, "")
        if not os.path.exists(self.scenario_folder):
            raise ValueError("The scenario folder does not exist : {}".format(self.scenario_folder))

        # check inputs folder
        self.inputs_folder = paths.scenario_inputs_folder(self.scenario_folder)
        if not os.path.exists(self.inputs_folder):
            raise ValueError("The inputs folder does not exist : {}".format(self.inputs_folder))

        # create outputs folder if it does not exist
        if "OUTPUT_FOLDER" in os.environ:
            output_folder = os.path.join(os.environ["OUTPUT_FOLDER"], "")
        else:
            output_folder = paths.scenario_outputs_folder(self.scenario_folder)
        self.outputs_folder = output_folder
        if not os.path.exists(self.outputs_folder):
            os.mkdir(self.outputs_folder)

    def get_scenario_parameters(self):
        """
        Get and validate the scenario simulation parameters.

        Also get the scenario model and name from the parameters.

        The parameter file path is enforced by the scenario_parameters_filepath function.
        """

        try:
            parameters_path = paths.scenario_parameters_filepath(self.scenario_folder)
            self.parameters = json_load(parameters_path)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError("Error while loading the scenario parameters : {}".format(str(e)))

        # parameters validation
        schema = json_load(paths.schemas_folder() + self.BASE_PARAM_SCHEMA)
        validate_against_schema(self.parameters, schema)

        # change date format from YYYY-MM-DD to YYYYMMDD
        if "date" in self.parameters:
            self.parameters["date"] = self.parameters["date"].replace("-", "")

        # get model and scenario
        self.model = self.parameters["code"]
        self.name = self.parameters["scenario"]

    def __getitem__(self, item):
        """
        Method called when using 'SimulationScenario[item]'

        :param item: Name of the parameter accessed
        :return: self.parameters[item]
        """

        if item not in self.parameters:
            logging.error(
                "Trying to access unknown parameter '"
                + str(item)
                + "'. Does it appears in the parameter entry ?"
            )
            raise KeyError("The parameter '" + str(item) + "' does not exist")

        return self.parameters[item]

    def __contains__(self, item):
        """
        Method called when using 'item in simulationParameters'

        :param item:
        :return: True if item is in self.parameters, False otherwise
        """

        return item in self.parameters

    def copy_parameters(self):
        """
        Return a deepcopy of the simulation parameters.

        :return: deepcopy of simulation parameters
        """

        return deepcopy(self.parameters)
