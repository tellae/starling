.. _models_introduction:

Simulation models
*****************

The framework was implemented along with several simple
transportation models.
The generic elements developed
for these models were added to the framework's
structure and could be re-used later on. This
incremental method was especially relevant for
the construction of a coherent and robust architecture
for the framework.

For now, the following simulation models have been
developed within the scope of this project (in
chronological order). Each model has a code used
in his class namespace and for project execution
via command line:


- :ref:`SB_VS`: Car rental system in which users can pickup a vehicle at specific
  locations (stations) and leave it at any other station.


- :ref:`FF_VS`: Bike rental system in which users can pickup/leave vehicles at any
  location of the network.


.. toctree::
    :maxdepth: 1
    :hidden:

    SB_VS
    FF_VS

