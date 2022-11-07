.. _PT:

#####################
Public transport [PT]
#####################

This model describes a conventional public transport service described
by a GTFS (General Transit Feed Specification).

*****************
Model description
*****************

Operator
--------

The operator ensures a collective transport service which is described by a timetable.
It also manages the fleet of vehicles that realise this service.

Service vehicles
----------------

Each service vehicle is affected to a set of trips. Trips are described in the
timetables, and consist in a series of stops where users can be picked up or dropped off.
The behaviour of the service vehicles is summarised in the following flowchart.

.. figure:: /images/timetable_public_transport_vehicle.svg
    :height: 500 px
    :width: 500 px
    :align: center

    Simulation flowchart of a public transport service vehicle

Users
-----

This model does not include the simulation of users.

********************
Model implementation
********************

Simulation model
----------------

+ **Simulation model**: :class:`starling_sim.models.PT.model.Model`

+ **Agent population**: :class:`~starling_sim.basemodel.population.dict_population.DictPopulation`

+ **Environment**: :class:`~starling_sim.basemodel.environment.environment.Environment`

+ **Topology**: :class:`~starling_sim.basemodel.topology.osm_network.OSMNetwork`

+ **Dynamic input**: :class:`~starling_sim.basemodel.input.dynamic_input.DynamicInput`

+ **Output factory**: :class:`starling_sim.models.PT.output.Output`

Agent types and classes
-----------------------

This table provides the agent_type values to put in the input files for the agents
of the model and their respective classes.

.. list-table:: **PT agents**
   :widths: auto
   :align: center

   * - Agent
     - agent_type
     - class
   * - Public transports
     - <PUBLIC_TRANSPORT_TYPE>
     - :class:`~starling_sim.basemodel.agent.vehicles.public_transport_vehicle.PublicTransportVehicle`
   * - Operator
     - operator
     - :class:`~starling_sim.basemodel.agent.operators.public_transport_operator.PublicTransportOperator`
