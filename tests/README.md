# Starling tests

## Running tests

Run tests from the root of the project using pytest. Use the `-v` option for verbose output.

```bash
pytest [-v]
```

## Model tests

The test_model_scenario function runs the test scenarios of all models.
Each test scenario corresponds to a test, displayed like this when using verbose:

```bash
tests/test_models.py::test_model_scenario[MODEL_CODE-test_scenario_name]
```

You can select a subset of models to test by using the `--models` option with a list of model codes. For instance:

```bash
pytest --models SB_VS PT -v
```

Test scenarios and their environment are located in `tests/simulation_test_data`.
To create a new test scenario, simply create a new scenario folder in the model
folder, and add the expected outputs in a `reference` folder next to the `inputs` and `outputs` folders.

## Coverage

Tests coverage can be obtained with the plugin pytest-cov.

```bash
pytest --cov=starling_sim --cov-report html
```
