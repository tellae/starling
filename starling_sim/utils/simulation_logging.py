"""
Simulation logs offer an insight of the flow of events during the simulation run.
They are displayed in chronological order and contain various information such as simulation setup,
output generation or agent activity.

Simulation logs are managed with the Python
`logging <https://docs.python.org/3.6/library/logging>`_ library.

*************************
Simulation logging levels
*************************

In addition to the base levels of *logging*, we introduce two new ones:

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
   * - INFO
     - 20
   * - AGENT
     - 15
   * - ALGO
     - 13
   * - DEBUG
     - 10

The default logging level is 13.

To run a simulation with a different logging level, you can use the ``-l`` (or ``--level``) option of main.py.
For instance:

.. code-block:: bash

    python3 main.py data/models/SB_VS/example_nantes/ -l 20

******************
Simulation loggers
******************

We also create specific loggers for the :class:`~starling_sim.basemodel.trace.trace.Traced` and
:class:`~starling_sim.basemodel.algorithms.algorithm.Algorithm` classes with
different logging formats, in order to display additional information (such as the simulation time). For instance:

.. code-block:: text

    AGENT :: [50904], S1 : Picked up u-11

In order to display logs, instances of these classes call their
internal method log_message so the relevant information is fetched
directly from their attributes and a default level is applied.

These additional loggers may also be used by any module developed around
Starling to display simulation logs.
"""

import logging


#: logging format of the base logger
BASE_LOGGER_FORMAT = "%(levelname)s :: %(message)s"

#: default logging level of the simulations
DEFAULT_LOGGER_LEVEL = 13

#: additional logging level AGENT for agent activity logs
AGENT_LEVEL, AGENT_LEVEL_NAME = 15, "AGENT"

#: additional logging level for algorithms logs
ALGO_LEVEL, ALGO_LEVEL_NAME = 13, "ALGO"


def setup_logging(logger_level):
    """
    Setup the logging configuration for the run.

    :param logger_level: integer describing the logger level
    """

    # add levels specific to the project

    # new logging level for traced agents
    logging.addLevelName(AGENT_LEVEL, AGENT_LEVEL_NAME)

    # new logging level for algorithms
    logging.addLevelName(ALGO_LEVEL, ALGO_LEVEL_NAME)

    # set the base logger level
    logging.basicConfig(format=BASE_LOGGER_FORMAT, level=logger_level)


#: logging format of TRACED_LOGGER
TRACED_LOGGER_FORMAT = "%(levelname)s :: [%(timestamp)s], %(id)s : %(message)s"


def new_traced_logger():
    """
    Create and return a logger for the traced agents.

    :return: Logger object from the logging library
    """

    traced_logger = logging.getLogger("traced_logger")
    traced_logger.propagate = False
    formatter = logging.Formatter(TRACED_LOGGER_FORMAT)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    traced_logger.addHandler(stream_handler)

    return traced_logger


#: logging format of ALGO_LOGGER
ALGO_LOGGER_FORMAT = "%(levelname)s :: %(alg_name)s : %(message)s"


def new_algo_logger():
    """
    Create and return a logger for the simulation algorithms.

    :return: Logger object from the logging library
    """

    algo_logger = logging.getLogger("algo_logger")
    algo_logger.propagate = False
    formatter = logging.Formatter(ALGO_LOGGER_FORMAT)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    algo_logger.addHandler(stream_handler)

    return algo_logger


def new_test_logger():
    """
    Create and return a logger for the testing.

    :return: Logger object from the logging library
    """

    test_logger = logging.getLogger("test_logger")
    test_logger.propagate = False
    stream_handler = logging.StreamHandler()
    test_logger.addHandler(stream_handler)
    test_logger.setLevel(20)

    return test_logger


#: logging format of BLANK_LOGGER
BLANK_LOGGER_FORMAT = "%(message)s"


def new_blank_logger():
    """
    Create and return a logger without prefix.

    :return: Logger object from the logging library
    """

    blank_logger = logging.getLogger("blank_logger")
    blank_logger.propagate = False
    formatter = logging.Formatter(BLANK_LOGGER_FORMAT)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    blank_logger.addHandler(stream_handler)

    return blank_logger


#: Traced objects logger
TRACED_LOGGER = new_traced_logger()

#: algorithms logger
ALGO_LOGGER = new_algo_logger()

#: testing logger
TEST_LOGGER = new_test_logger()

#: blank logger
BLANK_LOGGER = new_blank_logger()
