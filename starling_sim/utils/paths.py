"""
Starling has a precise repository structure in order to separate the
base classes of the framework, the simulation models and the simulation data.

You will find here the structure of different parts of the project.

**Data folder generation**

The :data:`~starling_sim.utils.paths.data_folder` and sub-folders are not included in the git repository,
but they can be generated using the ``-D`` (or ``--data-tree``) option of main.py

.. code-block:: bash

    python3 main.py -D

It is also generated when :ref:`importing the example scenarios<examples>`.

**********************************
Global structure of the repository
**********************************

.. code-block:: text

    starling-repo
    ├── starling_sim            # simulation modules
    |   |
    │   ├── basemodel           # base classes of the framework
    │   ├── models              # concrete models extending the basemodel
    |   ├── schemas             # json schemas
    │   └── utils               # programming utils
    |
    ├── tools                   # tools for the simulation runs
    ├── data                    # data folder
    ├── tests                   # testing
    ├── docs                    # documentation files and scripts
    ├── main.py
    ├── requirements.txt
    ├── .gitignore
    ├── CHANGELOG.md
    └── README.md

****************************
Structure of the data folder
****************************

.. code-block:: text

    data
    ├── common_inputs           # inputs shared between scenarios
    |
    ├── environment             # environment data
    │   |
    │   ├── graph_speeds        # .json files containing the graph speeds
    │   ├── gtfs_feeds          # .zip files containing the gtfs feeds
    │   └── osm_graphs          # .graphml files containing the OSM graphs
    |
    └── models                  # simulation scenarios
        |
        ├── SB_VS               # SB_VS scenarios
        |   |
        |   ├── scenario_1      # scenario_1 data
        |   |   |
        │   |   ├── inputs      # scenario_1 inputs
        │   |   └── outputs     # scenario_1 outputs
        |   |
        |   └── scenario_2      # scenario_2 data
        └── ...

The path to the data repository can be changed using the --data-folder option of main.py

.. code-block:: bash

    python3 main.py path/to/scenario/ --data-folder path/to/data_folder/

However, the structure of the data repository must remain the same. This is ensured by the functions
declared in starling_sim.utils.paths.py, that build the paths to the different folders by concatenating
the folder names in the correct order.

***************************
Structure of models package
***************************

.. code-block:: text

    starling_sim
    └── models
        ├── SB_VS             # public SB_VS model
        ├── ...               # other public models
        │
        └── MY_MODEL          # your own model
            |
            ├── model.py      # model module containing class Model(SimulationModel)
            ├── my_agent.py   # other simulation modules for your model
            └── ...

The models package is where concrete models extending the base model are placed.
It contains public models and the ones you developed.

The packages must be named with the model code, and contain a model.py module.
This module must contain a Model class extending SimulationModel of the base model.
See :ref:`create-models` for more information about the requirements for your models.
"""

import starling_sim
import os

#: path to the data folder
_DATA_FOLDER = "./data/"

#: name of the common inputs folder
COMMON_INPUTS_FOLDER = "common_inputs"

#: name of the environment folder
ENVIRONMENT_FOLDER_NAME = "environment"

#: name of the osm graphs folder
OSM_GRAPHS_FOLDER_NAME = "osm_graphs"

#: name of the graph speeds folder
GRAPH_SPEEDS_FOLDER_NAME = "graph_speeds"

#: name of the gtfs feeds folder
GTFS_FEEDS_FOLDER_NAME = "gtfs_feeds"

#: name of the schemas folder
SCHEMAS_FOLDER_NAME = "schemas"

#: name of the models folder
MODELS_FOLDER_NAME = "models"

#: name of the input folder
INPUT_FOLDER_NAME = "inputs"

#: name of the output folder
OUTPUT_FOLDER_NAME = "outputs"

#: unique parameters filename
PARAMETERS_FILENAME = "Params.json"

#: format of the model import string
_MODEL_IMPORT_FORMAT = "{starling_pkg}.models.{model_code}.model"


def data_folder():
    """
    Path to the data folder.
    """
    return _DATA_FOLDER


def common_inputs_folder():
    """
    Path to the common inputs folder
    """
    return os.path.join(data_folder(), COMMON_INPUTS_FOLDER, "")


def environment_folder():
    """
    Path to the environment folder.
    """
    return os.path.join(data_folder(), ENVIRONMENT_FOLDER_NAME, "")


def osm_graphs_folder():
    """
    Path to the osm graphs folder.
    """
    return os.path.join(environment_folder(), OSM_GRAPHS_FOLDER_NAME, "")


def graph_speeds_folder():
    """
    Path to the graph speeds folder.
    """
    return os.path.join(environment_folder(), GRAPH_SPEEDS_FOLDER_NAME, "")


def gtfs_feeds_folder():
    """
    Path to the gtfs feeds folder.
    """
    return os.path.join(environment_folder(), GTFS_FEEDS_FOLDER_NAME, "")


def models_folder():
    """
    Path to the models folder.
    """
    return os.path.join(data_folder(), MODELS_FOLDER_NAME, "")


def model_folder(model_code):
    """
    Path to the folder of the given model code.

    :param model_code: code of the model
    """
    return os.path.join(models_folder(), model_code, "")


def scenario_inputs_folder(scenario_folder):
    """
    Path to the input folder of the given scenario.

    :param scenario_folder: scenario folder path
    """
    return os.path.join(scenario_folder, INPUT_FOLDER_NAME, "")


def scenario_parameters_filepath(scenario_folder):
    """
    Path to the parameters file of the given scenario.

    :param scenario_folder: scenario folder path
    """
    return os.path.join(scenario_inputs_folder(scenario_folder), PARAMETERS_FILENAME)


def scenario_agent_input_filepath(scenario_folder, filename):
    """
    Get the path to the scenario input file (dynamic or initialisation file).

    First, look in the scenario input folder. If the file is not found,
    look in the common inputs folder. If the file is not there,
    raise a FileNotFoundError.

    :param scenario_folder: scenario folder path
    :param filename: name of the input file
    """

    # complete the file path with the input folder path
    filepath = os.path.join(scenario_inputs_folder(scenario_folder), filename)

    # if the file does not exist, look in the common inputs folder
    if not os.path.exists(filepath):
        filepath = os.path.join(common_inputs_folder(), filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                "Input file {} not found in scenario inputs folder "
                "or common inputs folder".format(filename)
            )

    return filepath


def scenario_outputs_folder(scenario_folder):
    """
    Path to the output folder in the given scenario folder.

    :param scenario_folder: scenario folder path
    """

    return os.path.join(scenario_folder, OUTPUT_FOLDER_NAME, "")


def starling_folder():
    """
    Path to the Starling folder.
    """
    return os.path.join(starling_sim.__path__[0], "..", "")


def schemas_folder():
    """
    Path to the schemas folder.
    """
    return os.path.join(os.path.dirname(__file__), "..", SCHEMAS_FOLDER_NAME, "")


def model_import_path(starling_pkg, model_code):
    """
    Import sequence for the given model.

    :param starling_pkg: name of the root starling package
    :param model_code: code of the model
    """
    return _MODEL_IMPORT_FORMAT.format(starling_pkg=starling_pkg, model_code=model_code)


# #: local prefix
# path_prefix = "./"
#
# #: data folder
# DATA_FOLDER = path_prefix + "data/"
#
# #: environment folder
# ENVIRONMENT_FOLDER = DATA_FOLDER + "environment/"
#
# #: default path to folder for loading and saving graphs with osmnx
# OSM_GRAPHS_FOLDER = ENVIRONMENT_FOLDER + "osm_graphs/"
#
# #: default path to folder containing graph speeds
# GRAPH_SPEEDS_FOLDER = ENVIRONMENT_FOLDER + "graph_speeds/"
#
# #: default path to folder containing gtfs feeds
# GTFS_FEEDS_FOLDER = ENVIRONMENT_FOLDER + "gtfs_feeds/"
#
# #: name of the folder containing the json schemas for the simulator
# SCHEMA_FOLDER_NAME = "schemas/"
#
# #: path to folder containing various json schemas
# SCHEMA_FOLDER = starling_sim.__path__[0] + "/../" + SCHEMA_FOLDER_NAME
#
# #: models folder
# MODELS_FOLDER = DATA_FOLDER + "models/"
#
# #: inputs folder
# INPUT_FOLDER_NAME = "inputs"
#
# #: outputs folder
# OUTPUT_FOLDER_NAME = "outputs"
#
# #: import path for non public models
# MODEL_IMPORT_PATH = "{starling_pkg}.models.{model_code}.model"

# _DATA_FOLDER = "./data/"
# _ENVIRONMENT_FOLDER_NAME = "environment"
# _OSM_GRAPHS_FOLDER_NAME = "osm_graphs"
# _GRAPH_SPEEDS_FOLDER_NAME = "graph_speeds"
# _GTFS_FEEDS_FOLDER_NAME = "gtfs_feeds"
# _SCHEMAS_FOLDER_NAME = "schemas"
# _MODELS_FOLDER_NAME = "models"
# _INPUT_FOLDER_NAME = "inputs"
# _OUTPUT_FOLDER_NAME = "outputs"
#
#
# class StarlingPath:
#
#     def __init__(self):
#
#         self._data_folder = None
#
#         self._ENVIRONMENT_FOLDER_NAME = None
#         self._OSM_GRAPHS_FOLDER_NAME = None
#         self._GRAPH_SPEEDS_FOLDER = None
#         self._GTFS_FEEDS_FOLDER = None
#         self._SCHEMA_FOLDER_NAME = None
#         self._MODELS_FOLDER_NAME = None
#         self._INPUT_FOLDER_NAME = None
#         self._OUTPUT_FOLDER_NAME = None
#
#         self._sep = None
#
#         self.set_attributes()
#
#     def set_attributes(self, data_folder=_DATA_FOLDER,
#                        environment_folder_name=_ENVIRONMENT_FOLDER_NAME,
#                        osm_graphs_folder_name=_OSM_GRAPHS_FOLDER_NAME,
#                        graph_speeds_folder_name=_GRAPH_SPEEDS_FOLDER_NAME,
#                        gtfs_feeds_folder_name=_GTFS_FEEDS_FOLDER_NAME,
#                        schemas_folder_name=_SCHEMAS_FOLDER_NAME,
#                        models_folder_name=_MODELS_FOLDER_NAME,
#                        input_folder_name=_INPUT_FOLDER_NAME,
#                        output_folder_name=_OUTPUT_FOLDER_NAME,
#                        folder_separator="/"):
#
#         self._data_folder = data_folder
#
#         self._ENVIRONMENT_FOLDER_NAME = environment_folder_name
#         self._OSM_GRAPHS_FOLDER_NAME = osm_graphs_folder_name
#         self._GRAPH_SPEEDS_FOLDER = graph_speeds_folder_name
#         self._GTFS_FEEDS_FOLDER = gtfs_feeds_folder_name
#         self._SCHEMA_FOLDER_NAME = schemas_folder_name
#         self._MODELS_FOLDER_NAME = models_folder_name
#         self._INPUT_FOLDER_NAME = input_folder_name
#         self._OUTPUT_FOLDER_NAME = output_folder_name
#
#         self._sep = folder_separator
#
#     @property
#     def starling_sim_folder(self):
#         return starling_sim.__path__[0] + self._sep
#
#     @property
#     def schemas_folder(self):
#         return self.starling_sim_folder + self._SCHEMA_FOLDER_NAME + self._sep
#
#     @property
#     def data_folder(self):
#         return self._data_folder
#
#     @property
#     def environment_folder(self):
#         return self.data_folder + self._ENVIRONMENT_FOLDER_NAME + self._sep
#
#     @property
#     def osm_graphs_folder(self):
#         return self.environment_folder + self._OSM_GRAPHS_FOLDER_NAME + self._sep
#
#     @property
#     def graph_speeds_folder(self):
#         return self.environment_folder + self._GRAPH_SPEEDS_FOLDER + self._sep
#
#     @property
#     def gtfs_feeds_folder(self):
#         return self.environment_folder + self._GTFS_FEEDS_FOLDER + self._sep
#
#     @property
#     def models_folder(self):
#         return self.data_folder + self._MODELS_FOLDER_NAME + self._sep
#
#     def model_folder(self, model):
#         return self.models_folder + model + self._sep
#
#     def scenario_folder(self, model, scenario):
#         return self.model_folder(model) + scenario + self._sep
#
#     def scenario_input_folder(self, model, scenario):
#         return self.scenario_folder(model, scenario) + self._INPUT_FOLDER_NAME + self._sep
#
#     def scenario_output_folder(self, model, scenario):
#         return self.scenario_folder(model, scenario) + self._OUTPUT_FOLDER_NAME + self._sep
#
#
# starling_paths = StarlingPath()
#
# print(starling_paths.data_folder)
# print(starling_paths.starling_sim_folder)
# print(starling_paths.environment_folder)
# print(starling_paths.scenario_input_folder("SB_VS", "oui"))
# starling_paths.set_attributes(data_folder="tests/test_data/")
# print(starling_paths.data_folder)
# print(starling_paths.starling_sim_folder)
# print(starling_paths.environment_folder)
# print(starling_paths.scenario_input_folder("SB_VS", "oui"))
# exit(0)
