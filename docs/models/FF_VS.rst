.. _FF_VS:

Free-floating vehicle-sharing [FF_VS]
*************************************

This model describes a rental transport system in which users can pick-up
and leave vehicles anywhere in the network environment. Indigo Wheel is an example of this system for bike vehicles.

Users
=====

Users travel from their origin to destination using the vehicle-sharing system, based on the behaviour described in the
following flowchart. All users have access to all available vehicle locations. Users access to information at origin
location and vehicle location. Information is therefore not available during a walk or a ride.
They can easily choose the nearest vehicle. However, the chosen vehicle might be taken during the walk to the
vehicle location by another user. The vehicle is therefore not available and the user have to locate a new vehicle.


.. figure:: /images/free_floating_user.svg
    :height: 500 px
    :width: 500 px
    :align: center

    Simulation flowchart of a user agent

(a) A vehicle is parked at the nearest network node to the destination.
    And this node must be accessible by the vehicle, i.e. a car can’t be parked on a pedestrian path.


Vehicles
========

Vehicles don’t have an autonomous behaviour: they are only used by the clients
for their rides and are idle in the environment otherwise. They allow agents to
use a different part of the network and travel a different speed.

Classes of the model
====================

Simulation model
^^^^^^^^^^^^^^^^

+ **Simulation model**: :class:`simulator.models.FF_VS.Model`

Agents
^^^^^^

+ **Agent population**: :class:`simulator.basemodel.population.dict_population`

+ **Users**: :class:`simulator.models.FF_VS.User`

+ **Vehicles**: :class:`simulator.basemodel.agent.vehicles.vehicle`

Environment
^^^^^^^^^^^

+ **Environment**: :class:`simulator.basemodel.environment.environment`

+ **Topology**: :class:`simulator.basemodel.topology.osm_network`

Input
^^^^^

+ **Parameters**: :class:`simulator.basemodel.parameters.simulation_parameters`

+ **Dynamic input**: :class:`simulator.models.FF_VS.Input`

Output
^^^^^^

+ **Output factory**: :class:`simulator.models.FF_VS.Output`

+ **Geojson output**: :class:`simulator.basemodel.output.geojson_output`

+ **KPIs**: :class:`simulator.basemodel.output.kpi.kpi`