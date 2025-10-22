"""
Command line interface for running Starling simulation and other utils scripts.

This CLI should be called via the command line exposed by the Starling package.

.. code-block:: bash

    starling-sim --help
"""

import argparse
import json
import os
from loguru import logger
from starling_sim.version import __version__
from starling_sim.utils.simulation_logging import configure_logger
from starling_sim.model_simulator import launch_simulation, ModelSimulator
from starling_sim.utils import paths
from starling_sim.utils.data_tree import create_data_tree, import_examples
from starling_sim.utils.osm_graphs import add_osm_graph_action
from starling_sim.utils.demand import add_eqasim_demand_action
from starling_sim.utils.zip_scenario import add_zip_unzip_actions

parser = argparse.ArgumentParser(
    description="Starling command line interface",
    epilog="Examples:\n\n"
    "starling-sim --version\n"
    "starling-sim run data/models/SB_VS/example_nantes --level 10\n"
    "starling-sim osm-graph -n bike place 'Nantes, France'\n"
    "starling-sim eqasim-demand data/eqasim/example_population.geoparquet\n"
    "starling-sim data --data-tree\n\n",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument("-v", "--version", action="version", version=__version__)

parser.add_argument(
    "-l",
    "--level",
    help="specify the logger level. See simulation_logging.py for more information",
    type=str,
    default="ALGO",
)

parser.add_argument("--data-folder", help="specify an alternative data folder", default=None)

# create a subparser for each possible action
subparsers = parser.add_subparsers(required=True, help="Action to perform", dest="action")


# parser for running Starling simulations
run_parser = subparsers.add_parser(
    "run",
    description="Run a simulation scenario using the associated Starling model",
    help="Run a simulation scenario",
)

run_parser.add_argument("scenario_path", help="path to scenario folder")

run_parser.add_argument(
    "-p",
    "--package",
    help="indicate an alternative name for the base package of starling",
    type=str,
    action="store",
    default="starling_sim",
)

# parser for managing simulation data
data_parser = subparsers.add_parser(
    "data",
    description="Generate folder tree or example data",
    help="Generate folder tree or example data",
)

data_parser.add_argument(
    "-D",
    "--data-tree",
    help="generate the data tree according to the paths stored in paths.py",
    action="store_true",
)


data_parser.add_argument(
    "-e",
    "--examples",
    help="import the example scenarios of the given model codes from the test folder",
    action="store_true",
)

# parser for generating package docs
# doc_parser = subparsers.add_parser(
#     "doc",
#     description="generate the project documentation using Sphinx and exit.",
#     help="?",
# )

# parser for generating json schemas
schema_parser = subparsers.add_parser(
    "schema",
    description="Generate json schemas for each agent type of the given model",
    help="Generate the input schemas for a Starling model",
)

schema_parser.add_argument(
    "model",
    help="generate json schemas for each agent type of the model",
    metavar="MODEL_CODE",
    type=str,
    action="store",
)

# TODO: remove duplicate
schema_parser.add_argument(
    "-p",
    "--package",
    help="indicate an alternative name for the base package of starling",
    type=str,
    action="store",
    default="starling_sim",
)

# parser for osm graph generation
add_osm_graph_action(subparsers)

# parser for generating demand from eqasim population
add_eqasim_demand_action(subparsers)

# parsers for zipping and unzipping scenarios
add_zip_unzip_actions(subparsers)


def run_cli():
    input_args = parser.parse_args()

    # setup logging
    configure_logger(input_args.level)

    # setup data folder
    if input_args.data_folder is not None:
        if input_args.data_folder.endswith("/"):
            paths._DATA_FOLDER = input_args.data_folder
        else:
            paths._DATA_FOLDER = input_args.data_folder + "/"

    # act depending on action
    if input_args.action == "run":
        # launch simulation
        logger.info("Launching Starling {}\n".format(__version__))
        launch_simulation(input_args.scenario_path, input_args.package)

    elif input_args.action == "schema":
        model_class = ModelSimulator.get_model_class(input_args.model, input_args.package)
        schemas = model_class.get_agent_type_schemas()
        print(json.dumps(schemas, indent=4))
    elif input_args.action == "data":
        if input_args.data_tree:
            # create empty data tree
            create_data_tree()

        if input_args.examples:
            # create the data tree if it does not exist
            create_data_tree()

            # import the example scenarios and environment
            import_examples()
    elif input_args.action == "doc":
        # documentation generation
        os.system("./docs/sphinx-doc.sh")
    elif input_args.action == "osm-graph":
        input_args.func(input_args)
    elif input_args.action == "zip":
        input_args.zip(input_args)
    elif input_args.action == "unzip":
        input_args.unzip(input_args)
    else:
        raise ValueError(f"Unknown action '{input_args.action}'")
