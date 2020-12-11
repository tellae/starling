API Reference
*************

This section provides more details on the framework's classes. It can be useful for understanding the existing models and developing new ones.

The architecture of the framework can be represented as follows :

.. code-block:: text

    RD-EM-MOVE
    ├── simulator
    │   └── basemodel : generic structure for agent-based transport models
    │       ├── agent
    │       ├── environment
    │       ├── input
    │       ├── output
    │       ├── parameters
    │       ├── population
    │       ├── schedule
    │       ├── topology
    │       ├── trace
    │       └── simulation_model.py
    │   └── models : concrete simulation models extending the basemodel
    │       ├── FF_VS
    │       └── ...
    ├── data
    │   ├── environment
    │       ├── graphSpeeds
    │       ├── gtfs_feeds
    │       └── osmGraphs
    │   └── models
    │       ├── FF_VS
    │       └── ...
    ├── utils
    │   ├── schemas
    │   └── utils.py
    ├── docs
    ├── main.py
    ├── paths.py
    ├── constants.py
    ├── run_tests.sh
    ├── .gitignore
    └── README.md




.. toctree::
   :maxdepth: 4

   src/starling_sim
   

