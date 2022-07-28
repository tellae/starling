# Starling

**Starling** is an agent-based simulation framework for urban mobility.

It provides generic classes to build transport models such as station-based sharing system,
public transport or shared taxis.

**Citation info**: Leblond, V, Desbureaux, L, Bielecki, V., 2020. "[A new agent-based software for designing and optimizing emerging mobility services : application to city of Rennes](https://aetransport.org/past-etc-papers/conference-papers-2020?abstractId=6706&state=b)." *Proceedings of the European Transport Conference*, 11 September 2020, Milan

![](./docs/images/starling-viz.gif)

## License

[CeCILL-B](LICENSE.txt)

Feel free to use and contribute to **Starling** project as long as you comply with the licence terms.

## Quickstart

This section will show you how to run the example simulation scenarios.

For a more detailed setup guide, see the section
[Running simulations](https://starling.readthedocs.io/en/latest/run/running_simulations.html)
of the documentation.

### Installation

Starling must be cloned locally in order to be run.

```bash
git clone https://github.com/tellae/starling.git
```

Then, you can either install the dependencies directly on your linux or
use a Docker container to run a simulation.

We recommend the Linux installation for development and the Docker installation for running simulations.

#### On-device (Ubuntu)

This procedure is described for a Linux Ubuntu 18.04 or 20.04 with Python 3.6 or higher already installed.

First, install the necessary Linux packages with

```bash
sudo apt-get install -yy -q libcurl4-gnutls-dev \
    libssl-dev libproj-dev libgdal-dev gdal-bin python3-gdal \
    libgdal-dev libudunits2-dev pkg-config libnlopt-dev libxml2-dev \
    libcairo2-dev libudunits2-dev \
    libgdal-dev libgeos-dev libproj-dev python3-pip python3-dev \
    build-essential libspatialindex-dev python3-rtree
```

Then, install the Python libraries using pip3

```bash
# upgrade pip
python3 -m pip install --upgrade pip
# install the project requirements
pip3 install -r requirements.txt
```

#### Docker (Linux and Windows)

Run the following command
to create a Docker image named starling
containing python and all requirements.
This image doesn’t contain Starling source code but it
contains all python dependencies for running Starling.

```bash
docker build . --tag="starling"
```

You can run Docker in interactive mode (which will place you inside the container,
as in a terminal) with the following command:

**Linux**

```bash
docker run -it -v "$(pwd):/starling_dir/" --name container_name starling
```

**Windows**

```bash
docker run -it -v "%cd%:/starling_dir/" --name container_name starling
```

Docker can also be run in detached mode, which lets the simulations
run on their own (see the [documentation](https://starling.readthedocs.io/en/latest/run/install.html#detached-mode)).

### Download examples

You can now build the data structure and download example scenarios by
running the following command in your environment

```bash
python3 main.py -e
```

### Usage

Once the data is prepared, a scenario can be run from the project
root by running main.py with the path to the scenario folder.

Run one of the example scenarios, for instance:

```bash
python3 main.py data/models/SB_VS/example_nantes/
```

You will see the progression of the simulation with the logs that
appear in the console.

### Outputs

You can find the outputs of the scenario in the output folder.
In this case, its data/models/SB_VS/example_nantes/outputs/.

KPI files (.csv.gz) can be visualised with any spreadsheet software.

The visualisation file (.geojson) can be uploaded to the web application
[Kite](https://kite.tellae.fr/) to visualise the simulation run.

## Documentation

The project documentation is generated using Sphinx and hosted by *Read the Docs* here:

<https://starling.readthedocs.io/en/latest/>

The documentation is still incomplete, but contributions and suggestions are very welcome.

## Contributing

Feedback and contributions on Starling, the code, the documentation or
even the github management are very welcome.

We haven't established a contributing procedure yet, but we will do our
best to guide you if you want to contribute to this project.

## Support

You can email us at starling@tellae.fr for any support demand.

## Project status

[*Tellae*](https://tellae.fr/) is actively contributing to Starling as part of its research and development activities.

Tellae uses Starling in commercial contracts to study mobility projects. This is why
some of the models and algorithms developed around Starling are not shared in this repository.
