.. _installation:

############
Installation
############

First, you must clone Starling locally from `the github project <https://github.com/tellae/starling>`_.

.. code-block::

    git clone https://github.com/tellae/starling.git

Then, you can either install dependencies directly on your Linux or
use a Docker container.

We recommend the Linux installation for development and the Docker installation for running simulations.

Linux (Ubuntu)
==============

This procedure is described for Ubuntu 18.04 or 20.04 with Python 3.6 or higher already installed.

First, install the necessary Linux packages with

.. code-block:: bash

    sudo apt-get install -yy -q libcurl4-gnutls-dev \
        libssl-dev libproj-dev libgdal-dev gdal-bin python3-gdal \
        libgdal-dev libudunits2-dev pkg-config libnlopt-dev libxml2-dev \
        libcairo2-dev libudunits2-dev \
        libgdal-dev libgeos-dev libproj-dev python3-pip python3-dev \
        build-essential libspatialindex-dev python3-rtree

and then the Python dependencies using pip3

.. code-block:: bash

    # upgrade pip
    python3 -m pip install --upgrade pip
    # install the project requirements
    pip3 install -r requirements.txt

Docker (Ubuntu)
===============

Docker installation
-------------------

For installing Docker on Ubuntu, you should refer to the
`official documentation <https://docs.docker.com/engine/install/ubuntu/>`_.

Image creation
--------------

Run the following command to create a Docker image named starling
containing Python and all the project requirements. This image doesn't
contain Starling source code but it contains all python dependencies
for running Starling.

.. code-block:: bash

    docker build . --tag="starling"

You should then be able to use this image to create Docker containers
running the framework. Use the -v option to mount the Starling repository
in the container.

The Dockerfile create a new Linux user named 'starling_user'. If you need to use sudo,
the password is also 'starling_user'.

Detached mode
+++++++++++++

You can execute Docker in detached mode, which allows you to let one
or more simulations run on their own.

.. code-block:: bash

    docker run -d -v "$(pwd)":/starling_dir/ --name container_name starling\
        bash -c "my_command -option"

Interactive mode
++++++++++++++++

You can also run Docker in interactive mode, which will place you inside the
container and allow you to execute shell commands as in a terminal.

.. code-block:: bash

    docker run -it -v "$(pwd)":/starling_dir/ --name container_name starling
