import argparse
import logging
import os
import json

from starling_sim.model_simulator import launch_simulation, ModelSimulator
from starling_sim.utils.data_tree import create_data_tree, import_examples
from starling_sim.utils.simulation_logging import DEFAULT_LOGGER_LEVEL, setup_logging
from starling_sim.utils.test_models import launch_tests
from starling_sim.utils import paths
from starling_sim import __version__


def run_main():

    # create a command line parser

    parser = argparse.ArgumentParser(description="Starling agent-based simulation framework")

    parser.add_argument("scenario_path", help="path to scenario folder.", nargs="?")

    parser.add_argument(
        "-l",
        "--level",
        help="specify the logger level. See simulation_logging.py for more information.",
        type=int,
        default=None,
    )

    parser.add_argument(
        "-D",
        "--data-tree",
        help="generate the data tree according to the paths stored in paths.py and exit.",
        action="store_true",
    )

    parser.add_argument(
        "-e",
        "--examples",
        help="import the example scenarios of the given model codes from the test folder "
        "and exit. Generate the data tree folders if they don't exist.",
        action="store_true",
    )

    parser.add_argument(
        "-t",
        "--test",
        help="run tests on the given model codes based on the scenarios in tests/expected_outputs.",
        nargs="*",
        metavar=("MODEL_CODE_1", "MODEL_CODE_2"),
        default=None,
    )

    parser.add_argument(
        "-S",
        "--sphinx",
        action="store_true",
        help="generate the project documentation using Sphinx and exit.",
    )

    parser.add_argument(
        "-p",
        "--package",
        help="indicate an alternative name for the base package of starling",
        type=str,
        action="store",
        default="starling_sim",
    )

    parser.add_argument("--data-folder", help="Change the path to the data folder", default=None)

    parser.add_argument(
        "-J",
        "--json-schema",
        help="generate json schemas for each agent type of the model",
        metavar="MODEL_CODE",
        type=str,
        action="store",
    )

    parser.add_argument("-v", "--version", action="version", version=__version__)

    # parse the command line

    input_args = parser.parse_args()

    # setup logging
    if input_args.level is None:
        # default logger level is 40 when running tests
        if input_args.test is not None:
            input_args.level = 40
        else:
            input_args.level = DEFAULT_LOGGER_LEVEL
    setup_logging(input_args.level)

    if input_args.json_schema is not None:
        model_class = ModelSimulator.get_model_class(input_args.json_schema, input_args.package)
        schemas = model_class.get_agent_type_schemas()
        print(json.dumps(schemas, indent=4))
        exit(0)

    # documentation generation
    if input_args.sphinx:
        os.system("./docs/sphinx-doc.sh")
        exit(0)

    if input_args.data_folder is not None:
        if input_args.data_folder.endswith("/"):
            paths._DATA_FOLDER = input_args.data_folder
        else:
            paths._DATA_FOLDER = input_args.data_folder + "/"

    # data tree create
    if input_args.data_tree:
        create_data_tree()
        exit(0)

    # example scenarios
    if input_args.examples:

        # make sure the data tree is setup
        create_data_tree()

        # import the example scenarios and environment
        import_examples()
        exit(0)

    # test scenarios
    if input_args.test is not None:
        launch_tests(input_args.test, input_args.package)
        exit(0)

    # launch simulation
    logging.info("Launching Starling {}\n".format(__version__))
    launch_simulation(input_args.scenario_path, input_args.package)
