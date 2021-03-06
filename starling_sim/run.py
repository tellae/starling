import argparse
import logging
import os

from starling_sim.model_simulator import model_codes, launch_simulation
from starling_sim.utils.data_tree import create_data_tree, import_examples
from starling_sim.utils.simulation_logging import DEFAULT_LOGGER_LEVEL, setup_logging
from starling_sim.utils.test_models import launch_tests
from starling_sim.version import __version__


def run_main():

    # create a command line parser

    parser = argparse.ArgumentParser(description="Starling agent-based simulation framework")

    parser.add_argument("param_path",
                        help="path to parameter file.",
                        nargs="?")

    parser.add_argument("-l", "--level",
                        help="specify the logger level. See simulation_logging.py for more information.",
                        type=int,
                        default=None)

    parser.add_argument("-D", "--data-tree",
                        help="generate the data tree according to the paths stored in paths.py and exit.",
                        action="store_true")

    parser.add_argument("-e", "--examples",
                        help="import the example scenarios of the given model codes from the test folder "
                             "and exit. Generate the data tree folders if they don't exist.",
                        action="store_true")

    parser.add_argument("-t", "--test",
                        help="run tests on the given model codes based on the scenarios in tests/expected_outputs.",
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
    if input_args.level is None:
        # default logger level is 40 when running tests
        if input_args.test is not None:
            input_args.level = 40
        else:
            input_args.level = DEFAULT_LOGGER_LEVEL
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
    launch_simulation(input_args.param_path, input_args.package)
