import argparse
import logging
import os

from starling_sim.model_simulator import model_codes, launch_simulation
from starling_sim.utils.data_tree import create_data_tree, import_example_environment, import_example_scenario
from starling_sim.utils.simulation_logging import DEFAULT_LOGGER_LEVEL, setup_logging
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
                        default=DEFAULT_LOGGER_LEVEL)

    parser.add_argument("-D", "--data-tree",
                        help="generate the data tree according to the paths stored in paths.py and exit.",
                        action="store_true")

    parser.add_argument("-e", "--examples",
                        help="import example scenarios of the given model codes from the Google Drive of Tellae "
                             "and exit. If no model code is provided, import example scenarios for all public models."
                             "Generate the data tree folders if they don't exist.",
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
    if input_args.examples is not None:

        # make sure the data tree is setup
        create_data_tree()

        # import examples environment
        import_example_environment()

        if len(input_args.examples) == 0:
            # if no model code is provided, import examples for all public models
            for code in model_codes:
                import_example_scenario(code)
        else:
            for code in input_args.examples:
                if code not in model_codes:
                    raise ValueError("Unknown model code {} for example import. "
                                     "The list of public model codes is {}".format(code, model_codes))
                import_example_scenario(code)
        exit(0)

    # launch simulation
    logging.info("Launching Starling {}\n".format(__version__))
    launch_simulation(input_args.param_path, input_args.package)
