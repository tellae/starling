"""
Starling has a precise repository structure in order to separate the
base classes of the framework, the simulation models and the simulation data.

You will find here the structure of different parts of the project.

**Data folder generation**

The *data* folder tree is not included in the git repository, but it
can be generated using the ``-D`` (or ``--data-tree``) option of main.py

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
    │   └── utils               # programming utils
    |
    ├── tools                   # tools for the simulation runs
    ├── data                    # data folder
    ├── schemas                 # json schemas
    ├── tests                   # testing scripts (TODO)
    ├── docs                    # documentation files and scripts
    ├── docker                  # docker files
    ├── main.py
    ├── requirements.txt
    ├── .gitignore
    └── README.md

****************************
Structure of the data folder
****************************

.. code-block:: text

    data
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

***************************
Structure of models package
***************************

.. code-block:: text

    models
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

#: local prefix
path_prefix = "./"

#: data folder
DATA_FOLDER = path_prefix + "data/"

#: environment folder
ENVIRONMENT_FOLDER = DATA_FOLDER + "environment/"

#: default path to folder for loading and saving graphs with osmnx
OSM_GRAPHS_FOLDER = ENVIRONMENT_FOLDER + "osm_graphs/"

#: default path to folder containing graph speeds
GRAPH_SPEEDS_FOLDER = ENVIRONMENT_FOLDER + "graph_speeds/"

#: default path to folder containing gtfs feeds
GTFS_FEEDS_FOLDER = ENVIRONMENT_FOLDER + "gtfs_feeds/"

#: path to folder containing various json schemas for the simulator
SCHEMA_FOLDER = "schemas/"

#: models folder
MODELS_FOLDER = DATA_FOLDER + "models/"

#: inputs folder
INPUT_FOLDER_NAME = "inputs"

#: outputs folder
OUTPUT_FOLDER_NAME = "outputs"

#: import path for non public models
MODEL_IMPORT_PATH = "{starling_pkg}.models.{model_code}.model"
