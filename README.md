# Starling

Starling is an agent-based simulation framework for urban mobility.

It provides generic classes to build transport models such as station-based sharing system,
public transport or shared taxis.

## Installation

Starling project must be cloned locally in order to be run.
Then, you can either install the dependencies directly on your linux or
use a Docker container to run a simulation.

We recommend the Linux installation for development and the Docker installation for running simulations.

### Linux (Ubuntu)

This procedure is described for a Linux Ubuntu 18.04 with Python 3.6 or 3.7 already installed. Running Starling with Python 3.8 will lead to execution errors.

First, install the necessary Linux packages with

```bash
sudo apt-get install -yy -q libcurl4-gnutls-dev \
    libssl-dev libproj-dev libgdal-dev gdal-bin python-gdal python3-gdal \
    libgdal-dev libudunits2-dev pkg-config libnlopt-dev libxml2-dev \
    libcairo2-dev gdal-bin python-gdal python3-gdal libudunits2-dev \
    libgdal-dev libgeos-dev libproj-dev python3-pip python3-dev \
    build-essential libspatialindex-dev python3-rtree
```

Then install the Python libraries using pip3

```bash
pip3 install -r requirements.txt
```

You can now build the data structure and download example scenarios.

```bash
# build data structure
python3 main.py -D
# download all example scenarios
python3 main.py -e
```

You can then run an example scenario.

```bash
python3 main.py data/models/SB_VS/example_nantes/inputs/Params.json
```

### Docker

Run the following command
to create a Docker image named starling
containing python and all requirements.

```bash
docker build . --tag="starling"
```

You can now build the data structure and download example scenarios.

```bash
docker run -d -v "$(pwd)":/starling/ --name init starling\
    bash -c "python3 main.py -D;python3 main.py -e"
```

You can then run an example scenario.

```bash
docker run -d -v "$(pwd)":/starling/ --name example_nantes starling\
    bash -c "python3 main.py 'data/models/SB_VS/example_nantes/inputs/Params.json'"
```

## Usage

Simulation scenarios are launched from a file that contains
global parameters of the simulation.

Simulation data must be placed in data/models/<model_code>/<scenario_name>/inputs
(see [data repository](#data-folder)).

Once data are prepared, a scenario can be run from the project
root by running main.py with the path to the scenario parameters.

### Usage with linux

In a terminal, use Python3 to execute main.py followed by the parameter file

```bash
python3 main.py $path_to_param_file
```

For more information about the options of main.py, run it the option -h or --help.

### Usage with Docker

With starling Docker image, a scenario can be executed with the following command

```bash
docker run -d -v "$(pwd)":/starling/ --name $scenario_name starling\
    bash -c "python3 main.py $path_to_param_file"
```

## Data repository and examples

### Data folder

The *data* folder and its sub-folders are not included in the git repository.

They can be generated using the -D option of main.py.

```bash
python3 main.py -D
```

The following tree view is expected in the data folder. If you choose to use a different structure,
you must modify the paths contained in simulator/utils/paths.py.

```text
data
├── environment             # environment data
│   |
│   ├── graph_speeds        # .json files containing the graph speeds
│   ├── gtfs_feeds          # .zip files containing the gtfs feeds
│   └── osm_graphs          # .graphml files containing the OSM graphs
|
└── models                  # simulation scenarios
    |
    ├── SB_VS               # SB_VS scenarios
    |   |
    |   ├── scenario_1      # scenario_1 data
    |   |   |
    │   |   ├── inputs      # scenario_1 inputs
    │   |   └── outputs     # scenario_1 outputs
    |   |
    |   └── scenario_2      # scenario_2 data
    └── ...
```

## Examples scenarios

Data for example scenarios can be downloaded from Tellae Google Drive after
building the data structure. To do so, use the -e option of main.py with
the codes of the models to import and download the example environment and scenario.

```bash
python3 main.py -e SB_VS
```

With Docker.

```bash
docker run -d -v "$(pwd)":/starling/ --name init starling \
    bash -c "python3 main.py -e SB_VS"
```

If no model code is provided, example scenarios for all available models are
downloaded.

## Visualisation

Simulations can be visualised using the web application [Kite](https://kite.tellae.fr/)
which is a web application developped by Tellae and opened to everyone.

To do so, upload the .geojson file from the simulation outputs.
It traces the agents actions and movements.

## Documentation

The documentation of the project and its code can be generated locally with the following command

```bash
python3 main.py -S
```

With Docker.

```bash
docker run -d -v "$(pwd)":/starling/ --name doc starling \
    bash -c "python3 main.py -S"
```

Then the index file can be opened in your navigator. For instance

```bash
firefox ./docs/_build/html/index.html
```

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
