.. _FF_VS:

#####################################
Free-floating vehicle-sharing [FF_VS]
#####################################

This model describes a rental transport system in which users can pick-up
and leave vehicles anywhere in the network environment. Indigo Wheel is an example of this system for bike vehicles.

*****************
Model description
*****************

Users
-----

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
--------

Vehicles don’t have an autonomous behaviour: they are only used by the clients
for their rides and are idle in the environment otherwise. They allow agents to
use a different part of the network and travel a different speed.

********************
Model implementation
********************

Simulation model
----------------

+ **Simulation model**: :class:`starling_sim.models.FF_VS.model.Model`

+ **Agent population**: :class:`~starling_sim.basemodel.population.dict_population.DictPopulation`

+ **Environment**: :class:`~starling_sim.basemodel.environment.environment.Environment`

+ **Topology**: :class:`~starling_sim.basemodel.topology.osm_network.OSMNetwork`

+ **Parameters**: :class:`~starling_sim.basemodel.parameters.simulation_parameters.SimulationParameters`

+ **Dynamic input**: :class:`starling_sim.models.FF_VS.input.Input`

+ **Output factory**: :class:`starling_sim.models.FF_VS.output.Output`

Agent types and classes
-----------------------

This table provides the agent_type values to put in the input files for the agents
of the model and their respective classes.

.. list-table:: **FF_VS agents**
   :widths: auto
   :align: center

   * - Agent
     - agent_type
     - class
   * - Users
     - user
     - :class:`starling_sim.models.SB_VS.user.User`
   * - Vehicles
     - vehicle
     - :class:`~starling_sim.basemodel.agent.vehicles.vehicle.Vehicle`
