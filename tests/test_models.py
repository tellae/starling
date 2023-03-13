"""
Test Starling models
"""

from starling_sim.utils.testing import run_model_test


def test_model_scenario(model, scenario):
    """
    Run a test scenario. See utils.testing.py for more information.
    """
    assert run_model_test(model, scenario)
