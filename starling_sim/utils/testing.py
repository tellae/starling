from starling_sim.model_simulator import launch_simulation
from starling_sim.utils.utils import gz_decompression
from starling_sim.simulation_scenario import SimulationScenario
from starling_sim.utils import paths

import os
import shutil
import subprocess
import filecmp

#: folder containing test scenarios
SIMULATION_TEST_DATA_FOLDER = "tests/simulation_test_data/"

#: name of the reference folder (next to inputs and outputs)
REFERENCE_OUTPUTS_FOLDER_NAME = "reference"


def get_test_scenarios(models=None):
    """
    Enumerate test scenarios for the given models.

    If models is not provided, enumerate scenarios
    for all models available.

    /!\ It is expected that the data folder variable
    paths._DATA_FOLDER has already been modified to
    designate the test data folder.

    :param models: list of model codes

    :return: list of (model_code, scenario) models
    """

    # get list of tested models
    if models is not None and len(models) > 0:
        tested_models = models
    else:
        # get the list of models with a test folder
        tested_models = os.listdir(paths.models_folder())

    # get list of test scenarios
    # store a list of (model, scenario) tuples
    test_scenarios = []
    for model_code in tested_models:
        scenarios = os.listdir(paths.model_folder(model_code))
        for scenario in scenarios:
            test_scenarios.append((model_code, scenario))

    return test_scenarios


def run_model_test(model, scenario, pkg="starling_sim"):
    """
    Run the given test scenario and compare outputs.

    Outputs are compared to reference files stored in the scenario folder.

    :param model: model code
    :param scenario: scenario folder name
    :param pkg: starling package (see --help or run.py)

    :return: boolean indicating if test was successful
    :raises: ValueError if a problem occurs
    """

    # get scenario paths
    model_folder_path = paths.model_folder(model)
    scenario_path = os.path.join(model_folder_path, scenario, "")
    simulation_scenario = SimulationScenario(scenario_path)

    # remove existing outputs
    output_folder = simulation_scenario.outputs_folder
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    try:
        # run the scenario
        launch_simulation(scenario_path, pkg)
    except Exception as e:
        message = "Simulation crash ({})".format(str(e))
        raise ValueError(message)

    # compare the scenario outputs with reference files
    compare_scenario_outputs(simulation_scenario)

    return True


def compare_scenario_outputs(simulation_scenario):
    """
    Compare test scenario outputs with files of the reference folder.

    :param simulation_scenario: SimulationScenario object
    :raises: ValueError if files don't match
    """

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
