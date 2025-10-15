"""
Simulation logs offer an insight of the flow of events during the simulation run.
They are displayed in chronological order and contain various information such as simulation setup,
output generation or agent activity.

Simulation logs are managed using the
`loguru <https://loguru.readthedocs.io/en/stable/index.html>`_ library.

*************************
Simulation logging levels
*************************

In addition to the base levels of `loguru`, we introduce two new ones:

- An agent level that displays the agents' activities
- An algorithm level that displays the algorithms' steps

This results in the following available levels:

.. list-table:: **STARLING LOGGING LEVELS**
   :widths: auto
   :header-rows: 1
   :align: center

   * - Level
     - Numeric value
   * - CRITICAL
     - 50
   * - ERROR
     - 40
   * - WARNING
     - 30
   * - SUCCESS
     - 25
   * - INFO
     - 20
   * - AGENT
     - 15
   * - ALGO
     - 13
   * - DEBUG
     - 10
   * - TRACE
     - 5

You can use these custom levels like this:

.. code-block:: python

    from loguru import logger
    from starling_sim.utils.simulation_logging import ALGO_LEVEL

    logger.log(ALGO_LEVEL, "my_message")


The default logging level is 13.
To run a simulation with a different logging level, you can use the ``-l`` (or ``--level``) option of the command line interface.
For instance:

.. code-block:: bash

    starling-sim -l INFO run data/models/SB_VS/example_nantes/
"""

from loguru import logger
import sys

AGENT_LEVEL = "AGENT"
ALGO_LEVEL = "ALGO"


def configure_logger(level=ALGO_LEVEL):
    # enable starling logs
    logger.enable("starling_sim")

    # remove default sink
    logger.remove()

    # add a simple sink
    logger.add(sys.stderr, format="<level>{level: <8} :: {message}</level>", level=level)

def add_agent_file_sink(filepath):
    # add a file sink for agent logs
    logger.add(filepath, format="[{timestamp}], {id} : {message}", filter="starling_sim.basemodel.agent.agent", level=AGENT_LEVEL)
