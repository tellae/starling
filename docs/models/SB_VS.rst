.. _SB_VS:

Station-based vehicle-sharing
*****************************

This model describes a rental transport system in which users can pick-up a vehicle at specific locations (called stations),
and realise a one-way trip: the vehicle can be dropped at any station of the system. Former parisian Autolib is an example of this system.


Stations
========

Stations can store a limited number of vehicles (parking places). No more vehicle can be parked if a station is full.
In order to get or leave a vehicle, users must request the station. If their request cannot be satisfied,
for instance if they want to leave their vehicle but the station is full, they can wait in the station's queue.
If a change in the station's stock allow the request to be satisfied, it is immediately realised and
the user leaves the queue.

Users
=====

Users travel from their origin to destination using the vehicle-sharing system, based on the behaviour described in the
following flowchart. They may, or not, be informed of current stock of vehicles and available parking places on each
station (e.g. with a mobile application). They also have a patience attribute that defines the time they spend
waiting at stations before deciding a new action.

.. figure:: /images/station_based_user.svg
    :height: 600 px
    :width: 600 px
    :align: center

    Simulation flowchart of a user agent

(a) The choice of a station depends on the information available to the users.
    If they have a service application, they can ignore the irrelevant stations and go
    to the closest one fitting their needs. If they don't have it, they simply go to the
    closest station.

(b) When they are in a station's queue, users wait until their patience is exhausted.
    Then, they decide if they leave the queue or if they keep waiting.


Vehicles
========

Vehicles don't have an autonomous behaviour: they are only used by the clients for their rides and are idle in the
stations otherwise. They allow agents to use a different part of the network and travel a different speed.

Classes of the model
====================

Simulation model
^^^^^^^^^^^^^^^^

+ **Simulation model**: :class:`simulator.models.SB_VS.Model`

Agents
^^^^^^

+ **Agent population**: :class:`simulator.basemodel.population.dict_population`

+ **Stations**: :class:`simulator.basemodel.agent.stations.vehicle_sharing_station`

+ **Users**: :class:`simulator.models.SB_VS.User`

+ **Vehicles**: :class:`simulator.basemodel.agent.vehicles.vehicle`

Environment
^^^^^^^^^^^

+ **Environment**: :class:`simulator.basemodel.environment.environment`

+ **Topology**: :class:`simulator.basemodel.topology.osm_network`

Input
^^^^^

+ **Parameters**: :class:`simulator.basemodel.parameters.simulation_parameters`

+ **Dynamic input**: :class:`simulator.models.SB_VS.Input`

Output
^^^^^^

+ **Output factory**: :class:`simulator.models.SB_VS.Output`

+ **Geojson output**: :class:`simulator.basemodel.output.geojson_output`

+ **KPIs**: :class:`simulator.basemodel.output.kpi.kpi`
