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

    BASE_PARAM_SCHEMA = "parameters.schema.json"

    def __init__(self, scenario_folder_path):

        self.scenario_folder = None
        self.inputs_folder = None
        self.outputs_folder = None

        self.parameters = None

        self.model = None
        self.name = None

        self._get_scenario_folders(scenario_folder_path)
        self._get_scenario_parameters()

    def _get_scenario_folders(self, scenario_folder_path):
        # check scenario folder
        self.scenario_folder = scenario_folder_path
        if not self.scenario_folder.endswith("/"):
            self.scenario_folder = self.scenario_folder + "/"
        if not os.path.exists(self.scenario_folder):
            raise ValueError("The scenario folder does not exist : {}".format(self.scenario_folder))

        # check inputs folder
        self.inputs_folder = self.scenario_folder + paths.INPUT_FOLDER_NAME + "/"
        if not os.path.exists(self.inputs_folder):
            raise ValueError("The inputs folder does not exist : {}".format(self.inputs_folder))

        # create outputs folder if it does not exist
        self.outputs_folder = self.scenario_folder + paths.OUTPUT_FOLDER_NAME + "/"
        if not os.path.exists(self.outputs_folder):
            os.mkdir(self.outputs_folder)

    def _get_scenario_parameters(self):

        try:
            parameters_path = self.inputs_folder + paths.PARAMETERS_FILENAME
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
        Method called when using 'simulationParameters[item]'
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

    def __setitem__(self, key, value):
        """
        Method called when using 'simulationParameters[key] = value'
        :param key: Name of the parameter
        :param value: Value associated to the parameter
        :return:
        """

        if key in self.parameters:
            logging.warning("Replacing already existing parameter '" + str(key) + "'")

        self.parameters[key] = value

    def __contains__(self, item):
        """
        Method called when using 'item in simulationParameters'

        :param item:
        :return: True if item is in self.parameters, False otherwise
        """

        return item in self.parameters

    def copy_dict(self):
        """
        Return a deepcopy of the simulation parameters.

        :return: deepcopy of simulation parameters
        """

        return deepcopy(self.parameters)


class SimulationParameters:
    """
    This class stores the simulation parameters in a dict structure

    It must be extended to build the dict from different sources

    The parameters should be set and accessed using the builtin methods of a dict
    """

    BASE_PARAM_SCHEMA = "parameters.schema.json"

    def __init__(self, parameters, param_schema_path=None):
        """
        This constructor must be extended to initialize the dict from specific arguments
        """

        # get JSON schema
        if param_schema_path is None:
            param_schema_path = paths.schemas_folder() + self.BASE_PARAM_SCHEMA

        self.schema = json_load(param_schema_path)

        # parameters validation
        validate_against_schema(parameters, self.schema)

        # change date format from YYYY-MM-DD to YYYYMMDD
        if "date" in parameters:
            parameters["date"] = parameters["date"].replace("-", "")

        self._parametersDict = parameters

    def __getitem__(self, item):
        """
        Method called when using 'simulationParameters[item]'
        :param item: Name of the parameter accessed
        :return: self._parametersDict[item]
        """

        if item not in self._parametersDict:
            logging.error(
                "Trying to access unknown parameter '"
                + str(item)
                + "'. Does it appears in the parameter entry ?"
            )
            raise KeyError("The parameter '" + str(item) + "' does not exist")

        return self._parametersDict[item]

    def __setitem__(self, key, value):
        """
        Method called when using 'simulationParameters[key] = value'
        :param key: Name of the parameter
        :param value: Value associated to the parameter
        :return:
        """

        if key in self._parametersDict:
            logging.warning("Replacing already existing parameter '" + str(key) + "'")

        self._parametersDict[key] = value

    def __contains__(self, item):
        """
        Method called when using 'item in simulationParameters'

        :param item:
        :return: True if item is in _parametersDict, False otherwise
        """

        return item in self._parametersDict

    def keys(self):
        """
        Returns the keys of the _parametersDict attribute

        :return: keys of the _parametersDict attribute
        """

        return self._parametersDict.keys()

    def set_dict(self, params_dict):
        """
        Sets the _parametersDict attribute with the given dict

        :param params_dict:
        :return:
        """

        self._parametersDict = params_dict

    def copy_dict(self):
        """
        Return a deepcopy of the simulation parameters.

        :return: deepcopy of simulation parameters
        """

        return deepcopy(self._parametersDict)


class ParametersFromDict(SimulationParameters):
    """
    Get simulation parameters from an existing dict
    """

    def __init__(self, params_dict):
        """
        Just set the _parametersDict
        :param params_dict:
        """

        super().__init__(params_dict)


class ParametersFromFile(SimulationParameters):
    """
    Get simulation parameters from a json file
    """

    def __init__(self, filepath):
        """
        Initialisation of the param dict by reading params in a json file
        :param filepath:
        """

        # check that the parameters file has the correct name
        if os.path.basename(filepath) != paths.PARAMETERS_FILENAME:
            raise ValueError("The parameters file must be named " + paths.PARAMETERS_FILENAME)

        # read json
        json_param = json_load(filepath)

        # create empty dict
        super().__init__(json_param)


# parameters management


def parameters_from_file(param_path):
    """
    Generates a simulation parameters from the parameters file.

    :param param_path: path to parameters file

    :return: SimulationParameters object
    """

    # create simulation parameters
    parameters = ParametersFromFile(param_path)

    add_paths_to_parameters(parameters)

    return parameters


def add_paths_to_parameters(parameters):
    """
    Adds the input and output paths to the given parameters
    using the 'code' and 'scenario' items
    :param parameters:
    :return:
    """

    model_code = parameters["code"]
    scenario = parameters["scenario"]

    # input folder
    parameters["input_folder"] = paths.scenario_input_folder(model_code, scenario)

    # output folder (will be generated by output)
    parameters["output_folder"] = paths.scenario_output_folder(model_code, scenario)
