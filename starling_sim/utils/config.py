"""
This module contains a config dict with simulation related values.

Config values can be provided to the simulator using a json file name after the _CONFIG_FILE constant.

For a complete description of the config specification and its default values,
see the JSON schema (schemas/starling_config.schema.json):

.. literalinclude:: /../schemas/starling_config.schema.json
    :language: json
"""

from starling_sim.utils.utils import json_load, add_defaults_and_validate

import os

#: name of the config file
_CONFIG_FILE = "starling_config.json"

#: filename of the config schema
_CONFIG_SCHEMA = "starling_config.schema.json"


def _init_config():
    """
    Initialise config variables from a config file or from the default schema values.
    """

    # if a config file exists at the project root, use it to define config values
    if os.path.exists(_CONFIG_FILE):
        user_config = json_load(_CONFIG_FILE)
    else:
        user_config = {}

    # use the default values for the keys that are not provided
    return add_defaults_and_validate(user_config, _CONFIG_SCHEMA)


#: config dict used in Starling
config = _init_config()
