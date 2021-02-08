from starling_sim.model_simulator import launch_simulation

from starling_sim.utils.constants import DEFAULT_PARAMS_NAME
from starling_sim.utils.paths import *

import os
import logging
import subprocess
import difflib
import time

EXPECTED_OUTPUTS_FOLDER = "./tests/expected_outputs/"

test_logger = logging.getLogger("test_logger")
test_logger.propagate = False
stream_handler = logging.StreamHandler()
test_logger.addHandler(stream_handler)
test_logger.setLevel(20)


def test_models(model_code_list, pkg):

    start = time.time()

    # get the list of models with a test folder
    testable_models = os.listdir(EXPECTED_OUTPUTS_FOLDER)

    if len(model_code_list) == 0:
        model_code_list = testable_models

    test_logger.info("Running tests for the models {}\n".format(model_code_list))

    # test the models
    for model_code in model_code_list:

        if model_code not in testable_models:
            test_logger.warning("Model code {} has no test scenarios".format(model_code))
        else:
            test_model(model_code, pkg)

    test_logger.info("\nTotal testing time: {}".format(time.time() - start))


def test_model(model_code, pkg):

    # get the test scenarios of the model
    model_expected_outputs = EXPECTED_OUTPUTS_FOLDER + model_code + "/"
    test_scenarios = os.listdir(model_expected_outputs)

    # test the scenarios
    for scenario in test_scenarios:
        try:
            run_time = test_scenario(model_code, pkg, scenario)
            message = "Success ({})".format(run_time)
        except ValueError as e:
            message = str(e)

        test_logger.info("{}, {} : {}".format(model_code, scenario, message))


def test_scenario(model_code, pkg, scenario):

    # get the scenario parameters file
    parameters_path = MODELS_FOLDER + model_code + "/" + scenario + "/" + INPUT_FOLDER_NAME + "/" + DEFAULT_PARAMS_NAME

    # test the existance of the scenario
    if not os.path.exists(parameters_path):
        raise ValueError("Scenario parameters not found")

    try:
        # run the scenario
        start = time.time()
        launch_simulation(parameters_path, pkg)
        run_time = time.time() - start
    except Exception as e:
        message = "Simulation crash ({})".format(str(e))
        raise ValueError(message)

    # compare the scenario outputs with reference files
    compare_scenario_outputs(model_code, scenario)

    return run_time


def compare_scenario_outputs(model_code, scenario):

    # get the test files
    test_scenario_output_folder = MODELS_FOLDER + model_code + "/" + scenario + "/" + OUTPUT_FOLDER_NAME + "/"
    test_scenario_output_files = os.listdir(test_scenario_output_folder)

    # extract bz2 archives
    for output_file in test_scenario_output_files:
        if output_file.endswith(".bz2"):
            subprocess.run(["bzip2", "-d", "-f", test_scenario_output_folder + output_file])
    test_scenario_output_files = os.listdir(test_scenario_output_folder)

    # get the reference files
    scenario_expected_outputs_folder = EXPECTED_OUTPUTS_FOLDER + model_code + "/" + scenario + "/"
    expected_output_files_list = os.listdir(scenario_expected_outputs_folder)

    # compare each reference file to its
    for expected_file in expected_output_files_list:

        # test file existence
        if expected_file not in test_scenario_output_files:
            raise ValueError("Missing output file ({})".format(expected_file))

        # open the files
        expected_file_path = scenario_expected_outputs_folder + expected_file
        with open(expected_file_path) as f1:
            f1_text = f1.read()
        test_file_path = test_scenario_output_folder + expected_file
        with open(test_file_path) as f2:
            f2_text = f2.read()

        # find diff (generator)
        diff = difflib.unified_diff(f1_text, f2_text, fromfile=expected_file_path, tofile=test_file_path,
                                    lineterm='')

        # if diff is not empty, raise an error
        for _ in diff:
            raise ValueError("Output differences")
