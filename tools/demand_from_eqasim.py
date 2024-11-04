"""
This python script imports generate a Starling population from a given Eqasim population.

The population represents the "demand" in a Starling simulation: they use the available
transport services in order to reach their destination.

Eqasim allows generating realistic synthetic populations from opendata sources.
See https://github.com/eqasim-org/ile-de-france for more information.

The available options allow filtering and sampling the given Eqasim population.

Run the script with ``-h`` (or ``--help``) to see the execution options.

.. code-block:: bash

    python3 -m --help

"""

import argparse
import numpy as np
import geopandas as gpd
from os import path

from starling_sim.utils.demand import demand_from_eqasim


parser = argparse.ArgumentParser(
    description="Script for the generation of Starling demand from an Eqasim population",
    epilog="Examples:\n\n"
           "python3 -m tools.demand_from_eqasim data/eqasim/example_population.geoparquet\n"
           "python3 -m tools.demand_from_eqasim data/eqasim/example_population.geoparquet --sample 0.01 --seed 42\n"
           "python3 -m tools.demand_from_eqasim data/eqasim/example_population.geoparquet --within data/eqasim/example_zone.geojson\n"
           "python3 -m tools.demand_from_eqasim data/eqasim/example_population.geoparquet -o ./starling_population.geojson\n",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument(
    "eqasim_file",
    help="Eqasim population geoparquet file",
)


parser.add_argument(
    "--within",
    help="file describing a geometry used as spatial filter",
    type=str,
    metavar="GEOJSON_FILE"
)

parser.add_argument(
    "--predicate",
    help="binary predicate used for spatial spatial filtering. "
         "See https://geopandas.org/en/stable/docs/user_guide/mergingdata.html#binary-predicate-joins for more information",
    choices=["intersects", "within"],
    default="intersects"
)


parser.add_argument(
    "-s",
    "--sample",
    help="Population sampling rate, between 0 and 1",
    type=float,
    metavar="SAMPLE_RATE"
)

parser.add_argument(
    "--seed", help="random seed used for sampling", type=int
)

parser.add_argument(
    "-o",
    "--outfile",
    help="name of the output file. Default is the input filename with '.geojson' extension. "
         "If only a filename is provided, generate the new file in the same folder than the Eqasim population file",
    type=str,
)

if __name__ == "__main__":
    # parse arguments
    input_args = parser.parse_args()

    # evaluate export filepath
    if input_args.outfile is None:
        filepath = path.basename(input_args.eqasim_file).replace(".geoparquet", ".geojson")
    else:
        filepath = input_args.outfile
    if path.basename(filepath) == filepath:
        filepath = path.join(path.dirname(input_args.eqasim_file), filepath)
    assert filepath.endswith(".geojson"), "The generated file must have the '.geojson' extension"

    # read Eqasim population
    assert input_args.eqasim_file.endswith(".geoparquet"), "A file with the '.geoparquet' extension is expected as the first argument"
    population = gpd.read_parquet(input_args.eqasim_file)
    assert population.crs is not None

    # sample the population
    if input_args.sample is not None:
        population = population.sample(frac=input_args.sample, random_state=input_args.seed)

    # apply spatial filter to the population
    if input_args.within is not None:
        filter_gdf = gpd.read_file(input_args.within, driver="GeoJSON")
        filter_gdf.to_crs(population.crs, inplace=True)
        population = population.sjoin(filter_gdf, how="inner", predicate=input_args.predicate)

    # generate the Starling population from the resulting sample
    starling_population = demand_from_eqasim(population)

    # write file
    print(f"Creating Starling demand file at: {filepath}")
    starling_population.to_file(filepath, drop_id=True, driver="GeoJSON")
