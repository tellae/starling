"""
This package contains the different modules of Starling.
"""
from starling_sim.utils.simulation_logging import AGENT_LEVEL, ALGO_LEVEL
from loguru import logger

# add a log level for agents
logger.level(AGENT_LEVEL, no=15, color="<blue>", icon="🐍")

# add a log level for algorithms
logger.level(ALGO_LEVEL, no=13, color="<cyan>", icon="🐍")

# disable loguru library wide (call configure_logger or use your own configuration to enable loguru)
logger.disable("starling_sim")