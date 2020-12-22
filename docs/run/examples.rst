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

The scenarios and their environment are stored on the Google Drive
of Tellae. The ids of the files are stored in the module constants.py,
so make sure that your git is up-to-date if you want the latest examples.

Run main.py with the ``-e`` (or ``--examples``) option to download the example scenarios and
their environments. This also creates the data folder tree if it
does not exist.

.. code-block:: bash

    python3 main.py -e

You can also provide one or more model code to specify the models you
are interested in.

.. code-block:: bash

    python3 main.py -e SB_VS SB_VS_R

You will find the newly downloaded scenarios in the folders of their
respective models, in the data folder.

***
Run
***

Example scenarios can be run like any other scenario by running main.py
with the path to the parameters file. For instance:

.. code-block:: bash

    python3 main.py data/models/SB_VS/example_nantes/inputs/Params.json

You will then see the simulation logs display in the console, until the run finishes.
If you find the logs too verbose, you can set the logging level to a higher level
with the ``-l`` option (see simulation_logging.py for more information):

.. code-block:: bash

    python3 main.py -l 20 data/models/SB_VS/example_nantes/inputs/Params.json

*******
Outputs
*******

After the simulation has finished, you should find an output folder next to
the scenario inputs. This folder contains the output files of the simulation:

- Key Indicators of Performance (KPIs) tables
- Visualisation file

The KPIs tables are .csv files and can be used or visualised with
classic software and libraries.

The visualisation file is a .geojson. It can be uploaded to
`Kite <https://kite.tellae.fr/>`_ to visualise the simulation.