from starling_sim.model_simulator import launch_simulation
from starling_sim.model_simulator import model_codes
from starling_sim.utils.simulation_logging import TEST_LOGGER
from starling_sim.utils.utils import gz_decompression
from starling_sim.utils import paths
from starling_sim.simulation_scenario import SimulationScenario

import os
import subprocess
import time
import shutil
import filecmp
import multiprocessing as mp


REFERENCE_OUTPUTS_FOLDER_NAME = "reference"
TEST_DATA_FOLDER = "tests/test_data/"
DEMAND_INPUT_FILE = "users_nantes.geojson"

PARALLEL_TESTS = 6


def launch_tests(model_code_list, pkg):

    start = time.time()

    if pkg != "starling_sim":

        public_models = []
        local_models = []

        # set the data repository to the starling test repository
        paths._DATA_FOLDER = paths.starling_folder() + TEST_DATA_FOLDER

        # get the public models of the list
        if len(model_code_list) == 0:
            test_models(public_models, "starling_sim")
        else:
            for model_code in model_code_list:
                if model_code in model_codes:
                    public_models.append(model_code)
                else:
                    local_models.append(model_code)

            if len(public_models) != 0:
                # run the tests for the public models
                test_models(public_models, "starling_sim")

        # now proceed to test to local models
        if len(model_code_list) == 0 or len(local_models) != 0:

            # set the data repository to the local test repository
            paths._DATA_FOLDER = TEST_DATA_FOLDER

            # copy the environment and demand input file
            starling_test_data_env = (
                paths.starling_folder() + TEST_DATA_FOLDER + paths.ENVIRONMENT_FOLDER_NAME + "/"
            )
            starling_test_data_demand = (
                paths.starling_folder()
                + TEST_DATA_FOLDER
                + paths.COMMON_INPUTS_FOLDER
                + "/"
                + DEMAND_INPUT_FILE
            )
            shutil.copytree(starling_test_data_env, paths.environment_folder())
            shutil.copy(
                starling_test_data_demand,
                TEST_DATA_FOLDER + paths.COMMON_INPUTS_FOLDER + "/" + DEMAND_INPUT_FILE,
            )

            # run the tests for the local models
            test_models(local_models, pkg)

            # remove the temporary test files
            shutil.rmtree(paths.environment_folder())
            os.remove(TEST_DATA_FOLDER + paths.COMMON_INPUTS_FOLDER + "/" + DEMAND_INPUT_FILE)

    else:
        # set the data repository to the local test repository
        paths._DATA_FOLDER = TEST_DATA_FOLDER

        # simply call test_models
        test_models(model_code_list, pkg)

    TEST_LOGGER.info("\nTotal testing time: {} seconds".format(int(time.time() - start)))


def test_models(model_code_list, pkg):

    # get the list of models with a test folder
    testable_models = os.listdir(paths.models_folder())

    if len(model_code_list) == 0:
        model_code_list = testable_models

    test_codes = []

    # test the models
    for model_code in model_code_list:

        if model_code not in testable_models:
            TEST_LOGGER.warning("Model code {} has no test scenario".format(model_code))
        else:
            test_codes.append(model_code)

    TEST_LOGGER.info("\nRunning tests for the models {}\n".format(model_code_list))

    # create a pool of processes
    p_p = mp.Pool(processes=PARALLEL_TESTS, maxtasksperchild=1)

    # create the tuple of parameters for each test
    params = [(code, pkg) for code in test_codes]

    # run the tests in parallel
    p_p.starmap(test_model, params)


def test_model(model_code, pkg):

    model_folder_path = paths.model_folder(model_code)

    # get the test scenarios of the model
    test_scenarios = os.listdir(model_folder_path)

    # test the scenarios
    for scenario in test_scenarios:
        try:
            scenario_folder_path = os.path.join(model_folder_path, scenario, "")
            simulation_scenario = SimulationScenario(scenario_folder_path)
            run_time = test_scenario(pkg, simulation_scenario)
            message = "Success ({} seconds)".format(run_time)
        except ValueError as e:
            message = str(e)

        TEST_LOGGER.info("{}, {} : {}".format(model_code, scenario, message))


def test_scenario(pkg, simulation_scenario):

    # get the scenario parameters file
    # parameters_path = paths.scenario_parameters_filepath(model_code, scenario)
    scenario_path = simulation_scenario.scenario_folder

    # test the existance of the scenario
    if not os.path.exists(scenario_path):
        raise ValueError("Scenario folder not found")

    # remove existing outputs
    output_folder = simulation_scenario.outputs_folder
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    try:
        # run the scenario
        start = time.time()
        launch_simulation(scenario_path, pkg)
        run_time = int(time.time() - start)
    except Exception as e:
        message = "Simulation crash ({})".format(str(e))
        raise ValueError(message)

    # compare the scenario outputs with reference files
    compare_scenario_outputs(simulation_scenario)

    return run_time


def compare_scenario_outputs(simulation_scenario):

    # get the test files
    test_scenario_output_folder = simulation_scenario.outputs_folder
    test_scenario_output_files = os.listdir(test_scenario_output_folder)

    # extract bz2 and gz archives
    for output_file in test_scenario_output_files:
        if output_file.endswith(".bz2"):
            subprocess.run(["bzip2", "-d", "-f", test_scenario_output_folder + output_file])
        if output_file.endswith(".gz"):
            gz_decompression(test_scenario_output_folder + output_file)

    # get the reference files
    scenario_expected_outputs_folder = os.path.join(
        simulation_scenario.scenario_folder, REFERENCE_OUTPUTS_FOLDER_NAME, ""
    )
    expected_output_files_list = os.listdir(scenario_expected_outputs_folder)

    # compare the files
    match, mismatch, errors = filecmp.cmpfiles(
        test_scenario_output_folder, scenario_expected_outputs_folder, expected_output_files_list
    )

    # raise errors if mismatch or error

    if len(mismatch) != 0:
        raise ValueError("Mismatches in the output files {}".format(mismatch))

    if len(errors) != 0:
        raise ValueError("Errors in the comparison of files {}".format(errors))
