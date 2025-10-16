.. _installation:

############
Installation
############

Installing Starling as a package from PiPy
==========================================

The *starling-sim* package is available on PiPy and can be installed using pip:

.. code-block::

    pip install starling-sim

You can check that the package was correctly installed by running the ``starling-sim`` command:

.. code-block::

    starling-sim --version


Cloning the repository
======================

You can also clone Starling locally from `the github project <https://github.com/tellae/starling>`_.
This is especially useful if you want to get example scenarios or make modifications to the source code.

.. code-block:: bash

    git clone https://github.com/tellae/starling.git


Install in editable mode
++++++++++++++++++++++++

If you want to run Starling as if it was installed as a package, you can install
it from your disk using pip's `editable` option:

.. code-block:: bash

    # from the project's root
    pip install -e .

This will:

- Install the Starling dependencies
- Provide you with the ``starling-sim`` command
- Make your changes in the code directly effective without having to reload the package (see `setuptools' Development Mode <https://setuptools.pypa.io/en/latest/userguide/development_mode.html>`_).

Install the dependencies manually
+++++++++++++++++++++++++++++++++

You can also install the dependencies manually:

.. code-block:: bash

    # from the project's root
    pip install -r requirements.txt

This will not add the ``starling-sim`` command to your environment.
Instead, you can execute the package folder with Python for the same result:

.. code-block:: bash

    # from the project's root
    python3 -m starling_sim --help


Run using docker (deprecated)
+++++++++++++++++++++++++++++

You can also run Starling in a Docker environment using the Dockerfile at the root
of the repository.

Run the following command to create a Docker image named `starling`
containing Python and all the project requirements. This image doesn't
contain Starling source code but it contains all python dependencies
for running Starling.

.. code-block:: bash

    docker build . --tag="starling"

.. note::

    The Dockerfile creates a new Linux user named 'starling_user'.
    If you need to use sudo in the container, the password is also 'starling_user'.

You should then be able to use this image to create Docker containers
running the framework. Use the -v option to mount the Starling repository
in the container. On Windows, replace *$(pwd)* by *%cd%* to get the absolute
path to the current folder.


Detached mode
-------------

You can execute Docker in detached mode, which allows you to let one
or more simulations run on their own.

**Linux**

.. code-block:: bash

    docker run -d -v "$(pwd):/starling_dir/" --name container_name starling\
        bash -c "my_command -option"

**Windows**

.. code-block:: bash

    docker run -d -v "%cd%:/starling_dir/" --name container_name starling\
        bash -c "my_command -option"

Interactive mode
----------------

You can also run Docker in interactive mode, which will place you inside the
container and allow you to execute shell commands as in a terminal.

**Linux**

.. code-block:: bash

    docker run -it -v "$(pwd):/starling_dir/" --name container_name starling

**Windows**

.. code-block:: bash

    docker run -it -v "%cd%:/starling_dir/" --name container_name starling


What's next
===========

The next pre-requisite to run a simulation is to understand the repository structure.
To do so, jump to the :ref:`next section <repository-structure>`.
