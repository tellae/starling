"""
This package contains the different modules of Starling.
"""

from starling_sim.utils.simulation_logging import AGENT_LEVEL, ALGO_LEVEL
from loguru import logger

# add a log level for agents
logger.level(AGENT_LEVEL, no=15, color="<bold><cyan>")

# add a log level for algorithms
logger.level(ALGO_LEVEL, no=13, color="<bold><light-cyan>")

# disable loguru library wide (call configure_logger or use your own configuration to enable loguru)
logger.disable("starling_sim")
