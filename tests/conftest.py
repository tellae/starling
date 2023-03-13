from starling_sim.utils.testing import get_test_scenarios, SIMULATION_TEST_DATA_FOLDER
from starling_sim.utils import paths


## Model testing setup

# set data folder for all test execution
paths._DATA_FOLDER = SIMULATION_TEST_DATA_FOLDER


# add a 'models' option to pytest command line
# allows specifying model codes to test
def pytest_addoption(parser):
    parser.addoption(
        "--models",
        nargs="*",
        metavar=("MODEL_CODE_1", "MODEL_CODE_2"),
        default=None,
        help="list of model codes to run tests on",
    )


# parameterize test_model_scenario test function
def pytest_generate_tests(metafunc):
    if metafunc.function.__name__ == "test_model_scenario":
        # list test scenarios present in the provided models' folders
        scenarios = get_test_scenarios(metafunc.config.getoption("models"))

        metafunc.parametrize("model, scenario", scenarios)
