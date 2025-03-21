.. _inout:

##################
Inputs and outputs
##################

Simulations are run using input data and generate output data. These files are stored in
:data:`~starling_sim.utils.paths.data_folder` (see :ref:`repository-structure`).

************
JSON schemas
************

We use use `JSON Schema <https://json-schema.org/>`_ to describe the format of some of the files
and validate the inputs before running simulations.

Some of these schemas are displayed in this page, but you can also find them in
:data:`~starling_sim.utils.paths.schemas_folder`.

**********
Input data
**********

Inputs consist in environment data, that can be common to several simulation runs,
and in scenario inputs, that describe a specific simulation scenario.

Environment data
----------------

Environment data is stored in sub-folders of :data:`~starling_sim.utils.paths.environment_folder`.
Such data can be common to several scenarios, for instance OSM graphs.

OSM graphs
++++++++++

OSM graphs files are stored in :data:`~starling_sim.utils.paths.osm_graphs_folder`.

They are .graphml files that contain OSM graphs imported using :mod:`tools.generate_osm_graph`.
These files represent the networks used by the agents to evolve in the simulation and are used to
setup the :class:`~starling_sim.basemodel.topology.osm_network` using the *osmnx* library.

Graph speeds
++++++++++++

Graph speeds files are stored in :data:`~starling_sim.utils.paths.graph_speeds_folder`.

They are .json files that associate speeds to graph arcs based on their "highway" attribute.
If this attribute does not match the fields of the graph speeds, the default value is fetched in the "other" field.

GTFS feeds
++++++++++

GTFS feeds are stored in :data:`~starling_sim.utils.paths.gtfs_feeds_folder`.

They are .zip files that describe a public transport timetable.
See `Google's GTFS Static overview <https://developers.google.com/transit/gtfs>`_ for more information.
These files can be read using the *gtfs-kit* library.

Simulation scenario data
------------------------

For each scenario, the specific input data must be stored in the :data:`~starling_sim.utils.paths.scenario_input_folder`.

For the dynamic and initialisation input files, they can also be stored in the
:data:`~starling_sim.utils.paths.common_inputs_folder`, in order to share the files between several scenarios.
The framework looks in the common inputs folder if it does not find the files in the scenario inputs folder.

Parameters file
+++++++++++++++

The parameters file must be named as :data:`~starling_sim.utils.paths.PARAMETERS_FILENAME` and placed in the
scenario inputs folder. It is a .json file that contains values for several
simulation parameters and files.

Among other things, it contains the simulation model code and the scenario name, which must be consistent with
where the parameters file is stored. It also contains the paths or filename of the other input files of the scenario.

For a complete description of the format of the parameters file, see its JSON schema:

.. literalinclude:: ../../starling_sim/schemas/parameters.schema.json
    :language: json

Dynamic input file
++++++++++++++++++

The dynamic input file is a .geojson file that contains a representation of the dynamic agents of the simulation.
Here, dynamic means that agents are introduced in the course of the simulation, according to their ``origin_time`` key.

Agent inputs are described using `Geojson <https://geojson.org/>`_ Feature objects
with specific properties. JSON schemas for the agents of a model can be generated using the ``-J``
(or ``--json-schema``) option of main.py

.. code-block:: bash

    python3 main.py -J SB_VS

The agent features are fetched by :class:`~starling_sim.basemodel.input.dynamic_input.DynamicInput` (or any class
that inherits from it) in order to initialise simulation agents.

Initialisation input file
+++++++++++++++++++++++++

The initialisation input file is a .geojson file that contains a representation of the initial agents of the simulation.

This file is similar to the dynamic input file, but here the agents are initialised before the start of the simulation.
It can describe, for instance, stations and their vehicles, or a transport operator.

The initialisation file is subject to the same JSON schema than the dynamic input file, initial agents
are described with the same specification.

You can also provide a list of geojson files instead of one. In this case, the feature lists of the files are
concatenated and processed as in the case of one file.

***********
Output data
***********

For each scenario, the output data should be stored in the output folder
(see :data:`~starling_sim.utils.paths.OUTPUT_FOLDER_NAME)`.

The main outputs of the simulation are the visualisation file and the KPI tables.
The specification of what they exactly contain is made by the model developer in the class
extending :class:`~starling_sim.basemodel.output.output_factory.OutputFactory`.

Run summary
-----------

The run summary file is a .json file generated at the end of a successful simulation.
It contains information about the run (date, Starling version, commit), the simulation
parameters, and the outputs of the run.

Visualisation file
------------------

The visualisation file is a .geojson file (possibly compressed) generated by a subclass of
:class:`~starling_sim.basemodel.output.geojson_output.GeojsonOutput`.

It contains the traces of the simulation agents represented as `Geojson <https://geojson.org/>`_ Feature objects,
with additional simulation information. Static objects are represented with a Point or MultiPolygon geometry, and
moving agents with LineString geometry.

For the file visualisation, see the :ref:`visualisation` section.

KPI tables
----------

The KPI (Key Indicator of Performance) tables are .csv files (possibly compressed), each one generated by an instance of the
:class:`~starling_sim.basemodel.output.kpi_output.KpiOutput` class.

Each file corresponds to an agent population and contains specific metrics. For instance,
it can contain the total distance walked by the transport users, or the number of uses of a vehicle.

The tables can be extracted and used as any .csv file with relevant software and libraries.

KPI fields
++++++++++

You can find here the correspondence between the most of the KPI fields and their contents.

.. currentmodule:: starling_sim.basemodel.output.kpis

.. autosummary::
    KPI.KEY_ID
    MoveKPI.SUFFIX_KEY_DISTANCE
    MoveKPI.SUFFIX_KEY_TIME
    WaitKPI.KEY_WAIT
    GetVehicleKPI.KEY_GET_VEHICLE
    SuccessKPI.KEY_FAILED_GET
    SuccessKPI.KEY_SUCCESS_GET
    SuccessKPI.KEY_FAILED_PUT
    SuccessKPI.KEY_SUCCESS_PUT
    SuccessKPI.KEY_FAILED_REQUEST
    SuccessKPI.KEY_SUCCESS_REQUEST
    StaffOperationKPI.KEY_FAILED_GET_STAFF
    StaffOperationKPI.KEY_SUCCESS_GET_STAFF
    StaffOperationKPI.KEY_FAILED_PUT_STAFF
    StaffOperationKPI.KEY_SUCCESS_PUT_STAFF
    OccupationKPI.KEY_EMPTY_TIME
    OccupationKPI.KEY_EMPTY_DISTANCE
    OccupationKPI.KEY_FULL_TIME
    OccupationKPI.KEY_FULL_DISTANCE
    OccupationKPI.KEY_STOCK_TIME
    OccupationKPI.KEY_STOCK_DISTANCE
    OccupationKPI.KEY_MAX_STOCK
    ServiceKPI.KEY_SERVICE_DURATION
    DestinationReachedKPI.KEY_DESTINATION_REACHED
    LeaveSimulationKPI.KEY_LEAVE_SIMULATION

Events file
-----------

The events file is a XML file (possibly compressed) generated by the class
:class:`~starling_sim.basemodel.output.simulation_events.SimulationEvents`. The events file replaces the former trace file.

It contains events of the simulation grouped by agent. Here is the detail of the XML elements:

- The root element is <document> and contains the `event_file_version` attribute, the version number of the event file format
- Then comes the <agents> element
- This element contains an <agent> element for each agent of the simulation, with the `id` and `agentType` attributes
- Each <agent> element contains the simulation events related to this agent, as XML elements (in chronological order).

An event element's tag corresponds to the event class name. Class attributes are stored as element attributes.
Some event classes store their attributes using subelements.

Traces file (deprecated)
------------------------

The traces file is a .txt file which contains the sequence of events of the simulation agents.
The use of this file is now deprecated, use the events file instead.

Events are grouped by agent, not in chronological order.

The string representation of an event contains the event tracing time, its class name and its
main attributes.

Events
------

The different kind of events are implemented in the :mod:`starling_sim.basemodel.trace.events` module.

.. automodule:: starling_sim.basemodel.trace.events

.. autosummary::
    :nosignatures:

    InputEvent
    RouteEvent
    PositionChangeEvent
    WaitEvent
    IdleEvent
    RequestEvent
    StopEvent
    PickupEvent
    DropoffEvent
    StaffOperationEvent
    GetVehicleEvent
    LeaveVehicleEvent
    LeaveSystemEvent
    DestinationReachedEvent
    LeaveSimulationEvent







