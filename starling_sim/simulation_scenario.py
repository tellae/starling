"""
This module manages the parameters of the simulation
"""

import datetime
from loguru import logger
import os
import json
from copy import deepcopy

from starling_sim.utils.utils import json_load, add_defaults_and_validate
from starling_sim.utils import paths
from starling_sim.utils.config import config
from starling_sim.version import __version__


class SimulationScenario:
    """
    This class describes a simulation scenario folders and data.
    """

    BASE_PARAM_SCHEMA = "parameters.schema.json"

    def __init__(self, scenario_folder_path: str):
        # scenario model code
        self.model = None

        # scenario name
        self.name = None

        # simulation parameters (can be accessed using SimulationScenario["key"])
        self.parameters = None

        # run summary
        self.runSummary = None

        # scenario folder path
        self.scenario_folder = None

        # scenario inputs folder path
        self.inputs_folder = None

        # scenario outputs folder path
        self.outputs_folder = None

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
        if not (os.path.exists(self.scenario_folder) and os.path.isdir(self.scenario_folder)):
            raise ValueError(
                "The scenario folder does not exist or is not a folder : {}".format(
                    self.scenario_folder
                )
            )

        # check inputs folder
        self.inputs_folder = paths.scenario_inputs_folder(self.scenario_folder)
        if not (os.path.exists(self.inputs_folder) and os.path.isdir(self.inputs_folder)):
            raise ValueError(
                "The inputs folder does not exist or is not a folder : {}".format(
                    self.inputs_folder
                )
            )

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

        # check scenario folder against scenario name
        # in fact this is not necessary, scenario name is not used for pathing anymore
        if os.path.basename(os.path.dirname(self.scenario_folder)) != self.parameters["scenario"]:
            raise ValueError("The scenario folder must be named after the scenario name")

        # parameters validation
        schema = json_load(paths.schemas_folder() + self.BASE_PARAM_SCHEMA)
        self.parameters = add_defaults_and_validate(self.parameters, schema)

        # change date format from YYYY-MM-DD to YYYYMMDD
        if "date" in self.parameters:
            self.parameters["date"] = self.parameters["date"].replace("-", "")

        # get model and scenario
        self.model = self.parameters["code"]
        self.name = self.parameters["scenario"]

        self.init_run_summary()

    def __getitem__(self, item):
        """
        Method called when using 'SimulationScenario[item]'

        :param item: Name of the parameter accessed
        :return: self.parameters[item]
        """

        if item not in self.parameters:
            logger.error(
                f"Trying to access unknown parameter '{str(item)}'. Does it appears in the parameter entry ?"
            )
            raise KeyError(f"The parameter '{str(item)}' does not exist")

        return self.parameters[item]

    def __contains__(self, item):
        """
        Method called when using 'item in simulationParameters'

        :param item:
        :return: True if item is in self.parameters, False otherwise
        """

        return item in self.parameters

    def get_input_filepath(self, filename):
        """
        Get the full path to the given input file.

        :param filename: filename of the input, located in the inputs folder
        :return: path to the input file
        """
        filepath = os.path.join(self.inputs_folder, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File was not found in the inputs folder: {filepath}")
        return filepath

    def get_dynamic_input_filepath(self):
        """
        Get the full path to the dynamic input file.

        :return: path to the dynamic input file or None if the parameter is missing
        """
        dynamic_input_file = self["dynamic_input_file"]
        if dynamic_input_file is None:
            return None
        return paths.scenario_agent_input_filepath(self.scenario_folder, dynamic_input_file)

    def get_init_input_filepaths(self):
        """
        Get the full paths to the init input files.

        :return: list of file paths or None if the parameter is absent
        """
        init_input_file = self["init_input_file"]
        if init_input_file is None:
            return None
        if isinstance(init_input_file, str):
            init_input_file = [init_input_file]

        return [paths.scenario_agent_input_filepath(self.scenario_folder, filename) for filename in init_input_file]

    def get_topology_info(self, mode):
        """
        Get the topology info as a dict, with filenames converted to filepaths.

        This doesn't really work, cannot know which info is a filename.

        :param mode:
        :return:
        """
        topologies = self["topologies"]
        if mode not in topologies:
            raise KeyError(f"The topology '{mode}' was not found in the parameters")

        topology_parameter = topologies[mode]
        if topology_parameter is None:
            return None
        else:
            if isinstance(topology_parameter, dict):
                network_info = topology_parameter["graph"]
                speeds_info = topology_parameter["speeds"]
                weight_class = topology_parameter.get("weight", None)
                network_class = topology_parameter.get("network_class", "OSMNetwork")

            elif isinstance(topology_parameter, list):  # array specification is deprecated
                network_info = topology_parameter[0]
                speeds_info = topology_parameter[1]
                if len(topology_parameter) == 3:
                    weight_class = topology_parameter[2]
                else:
                    weight_class = None
                network_class = "OSMNetwork"

            else:
                raise ValueError(f"Unsupported type for '{mode}' topology info: {type(topology_parameter)}")

            if network_class != "OSMNetwork":
                raise ValueError(f"Unknown network class {network_class}")

            return {
                "graph": os.path.join(paths.osm_graphs_folder(), network_info),
                "speeds": os.path.join(paths.graph_speeds_folder(), speeds_info) if isinstance(speeds_info, str) else speeds_info,
                "weight": weight_class,
                "network_class": network_class
            }

    def get_gtfs_timetable_filepath(self):
        """
        Get the full path to the GTFS file.

        :return: path to GTFS file or None if the parameter is absent
        """
        gtfs_timetable = self.parameters.get("gtfs_timetables", None)
        if gtfs_timetable is None:
            return None
        return os.path.join(paths.gtfs_feeds_folder(), gtfs_timetable)

    def init_run_summary(self):
        """
        Initialise the run summary.
        """

        summary = dict()

        # get run date
        summary["date"] = str(datetime.datetime.today())

        # get starling version
        summary["starling_version"] = __version__

        # copy scenario parameters
        summary["parameters"] = self.copy_parameters()

        # copy config
        summary["config"] = config.copy()

        # scenario output files
        summary["output_files"] = dict()

        # run statistics
        summary["stats"] = dict()

        self.runSummary = summary

    def copy_parameters(self):
        """
        Return a deepcopy of the simulation parameters.

        :return: deepcopy of simulation parameters
        """

        return deepcopy(self.parameters)

    def set_stat(self, key, value):
        """
        Set a value for the given stat key.

        :param key: stat key
        :param value: stat value
        """
        stats = self.runSummary["stats"]

        if key in stats:
            logger.warning(f"Overwriting '{key}' scenario statistic")

        stats[key] = value
