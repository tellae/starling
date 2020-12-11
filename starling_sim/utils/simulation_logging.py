"""
This module implements the log system in the simulation.

Simulation logs are managed with the
`logging <https://docs.python.org/3.6/library/logging>`_ library.

In addition to the basic levels of logging, we introduce two new ones:

- An agent level that displays the agents' activities
- An algorithm level that displays the algorithms' steps

We also create specific loggers for the Traced and Algorithm classes with
different logging formats, in order to display additional information.

In order to display logs, instances of these classes should call their
internal method log_message so the relevant information is fetched
directly from their attributes and a default level is applied.

These additional loggers may also be used by any module developed around
Starling to display simulation logs, for instance algorithms that don't
inherit from the Algorithm class.
"""

import logging


#: logging format of the base logger
BASE_LOGGER_FORMAT = '%(levelname)s :: %(message)s'

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


#: Traced objects logger
TRACED_LOGGER = new_traced_logger()

#: algorithms logger
ALGO_LOGGER = new_algo_logger()
