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

For now, the following simulation models are available.
Each model has a code corresponding to its package name and used
for project execution via command line:


- :ref:`SB_VS`: Car rental system in which users can pickup a vehicle at specific
  locations (stations) and leave it at any other station.

- :ref:`SB_VS_R`: Station-based rental system with repositioning operations.

- :ref:`FF_VS`: Bike rental system in which users can pickup/leave vehicles at any
  location of the network.

- :ref:`PT`: Conventional public transport system where public transport vehicles
  (buses, tramways, subways, etc) follow a theoretical timetable.

.. toctree::
    :maxdepth: 1
    :hidden:

    SB_VS
    SB_VS_R
    FF_VS
    PT

