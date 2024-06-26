#####
Usage
#####

****************
Data preparation
****************

Simulation scenarios are launched from a parameter file that contains
global parameters of the simulation.

Simulation data must be placed in data/models/<model_code>/<scenario_name>/inputs
(see :ref:`repository-structure`).
<model_code> and <scenario_name> must correspond to the respective fields
'code' and 'scenario' of the simulation parameters.

**************
Simulation run
**************

Once you have setup your execution environment (either on your device or with Docker, see :ref:`installation`)
and your simulation data (see :ref:`inout`), you can run your scenario.

Simulations are run by executing the script main.py from the project root
with the path to your scenario folder. For instance:

.. code-block:: bash

    python3 main.py data/models/SB_VS/my_scenario/

For more information about the options of main.py use the ``-h`` (or ``--help``) option:

.. code-block:: bash

    python3 main.py -h

***************
Run with Docker
***************

With Docker, this can be done in detached mode with

.. code-block:: bash

    docker run -d -v "$(pwd)":/starling_dir/ --name container_name starling\
        bash -c "python3 main.py data/models/SB_VS/my_scenario/"

or in interactive mode with

.. code-block:: bash

    docker run -it -v "$(pwd)":/starling_dir/ --name container_name starling

and then run the command line from inside the container.