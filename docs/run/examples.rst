.. _examples:

########
Examples
########

Once you have setup Starling on your device, it can be a good
thing to run some example scenarios in order to test your installation
and understand how simulations work. You should then be able to create
your own scenarios with specific parameters and data.

Example scenarios are available only for the models provided with Starling.

******
Import
******


The example scenarios are the same than those used for testing, so the import consists in copying the
test scenarios in the :data:`~starling_sim.utils.paths.data_folder`.
This also creates the data folder tree if it does not exist.

The operation overwrites all the existing files, so if you have modified example scenarios,
be sure to rename them.

Run `starling-sim data` with the ``-e`` (or ``--examples``) option to import the example scenarios.

.. code-block:: bash

    starling-sim data --examples

You will find the scenarios in the folders of their
respective models, in :data:`~starling_sim.utils.paths.data_folder`.

***
Run
***

Example scenarios can be run like any other scenario by running `starling-sim run`
with the path to the scenario folder. For instance:

.. code-block:: bash

    starling-sim run data/models/SB_VS/example_nantes/

You will then see the simulation logs display in the console, until the run finishes.
If you find the logs too verbose, you can set the logging level to a higher level
with the ``-l`` option (see simulation_logging.py for more information):

.. code-block:: bash

    starling-sim -l INFO run data/models/SB_VS/example_nantes/

*******
Outputs
*******

After the simulation has finished, you should find an output folder next to
the scenario inputs. This folder contains the output files of the simulation:

- Key Indicators of Performance (KPIs) tables
- Visualisation file
- Traces file

The KPIs tables are .csv files and can be used or visualised with
classic software and libraries.

The visualisation file is a .geojson. It can be uploaded to
`Kite <https://kite.tellae.fr/>`_ to visualise the simulation.