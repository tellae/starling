.. _SB_VS_R:

##########################################################
Station-based vehicle-sharing with repositioning [SB_VS_R]
##########################################################

This model describes a station-based rental system (see :ref:`SB_VS`)
with repositioning operations, in order to maintain balance between the stations.
Most of the existing station-based systems use repositioning operations.

*****************
Model description
*****************

Stations
--------

Stations can store a limited number of vehicles (parking places). No more vehicle can be parked if a station is full.
In order to get or leave a vehicle, users must request the station. If their request cannot be satisfied,
for instance if they want to leave their vehicle but the station is full, they can wait in the station's queue.
If a change in the station's stock allow the request to be satisfied, it is immediately realised and
the user leaves the queue.

Users
-----

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
--------

Vehicles don't have an autonomous behaviour: they are only used by the clients for their rides and are idle in the
stations otherwise. They allow agents to use a different part of the network and travel a different speed.

Operator
--------

The operator contains the set of stations, vehicles and repositioning staff.

Repositioning staff
-------------------

Repositioning staff are vehicles that can store and move several vehicles from
one station to another. They are used to balance the stations' stocks and
avoid failed user requests.

The balancing strategy is defined by the operator dispatch attributes.

********************
Model implementation
********************

Simulation model
----------------

+ **Simulation model**: :class:`starling_sim.models.SB_VS_R.model.Model`

+ **Agent population**: :class:`~starling_sim.basemodel.population.dict_population.DictPopulation`

+ **Environment**: :class:`~starling_sim.basemodel.environment.environment.Environment`

+ **Topology**: :class:`~starling_sim.basemodel.topology.osm_network.OSMNetwork`

+ **Parameters**: :class:`~starling_sim.basemodel.parameters.simulation_parameters.SimulationParameters`

+ **Dynamic input**: :class:`starling_sim.models.SB_VS_R.input.Input`

+ **Output factory**: :class:`starling_sim.models.SB_VS_R.output.Output`

Agent types and classes
-----------------------

This table provides the agent_type values to put in the input files for the agents
of the model and their respective classes.

.. list-table:: **SB_VS_R agents**
   :widths: auto
   :header-rows: 1
   :align: center

   * - Agent
     - agent_type
     - class
   * - Stations
     - station
     - :class:`~starling_sim.basemodel.agent.stations.vehicle_sharing_station.VehicleSharingStation`
   * - Users
     - user
     - :class:`starling_sim.models.SB_VS.user.User`
   * - Vehicles
     - vehicle
     - :class:`~starling_sim.basemodel.agent.vehicles.vehicle.Vehicle`
   * - Operator
     - operator
     - :class:`starling_sim.models.SB_VS.operator.Operator`
   * - Repositioning staff
     - staff
     - :class:`starling_sim.models.SB_VS_R.repositioning_staff.RepositioningStaff`
