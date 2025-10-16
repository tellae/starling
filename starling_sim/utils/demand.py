"""
This module contains functions for generating and managing Starling demand.

In a Starling simulation, the population represents the "demand": agents that use the available
transport services in order to reach their destination.

This Python script generates a Starling population from a given Eqasim population.
The available options allow filtering and sampling the Eqasim population.
Among other utils, this module provides functions for generating a Starling population from
an `Eqasim <https://github.com/eqasim-org/ile-de-france>`_ (open source synthetic population generation pipeline) output.

The demand generation functions are accessible through the ``starling-sim`` command line. Run the following command for more information:

.. code-block:: bash

    starling-sim eqasim-demand -h

"""

import pandas as pd
import geopandas as gpd
import argparse
from os import path


#: expected columns on a Starling population GeoDataFrame
STARLING_MINIMUM_COLUMNS = ["agent_type", "icon", "agent_id", "mode", "origin_time", "geometry"]


def demand_from_eqasim(
    eqasim_population: gpd.GeoDataFrame,
    sample_rate: float = None,
    sample_seed=None,
    spatial_filter: gpd.GeoDataFrame = None,
) -> gpd.GeoDataFrame:
    """
    Generate a Starling population from an Eqasim population.

    :param eqasim_population: GeoDataFrame describing an Eqasim population
    :param sample_rate: fraction of the original population that is kept in the final population
    :param sample_seed: seed used for sampling
    :param spatial_filter: GeoDataFrame used as spatial filter

    :return: GeoDataFrame of a Starling population generated from the Eqasim population
    """

    if eqasim_population.empty:
        return gpd.GeoDataFrame(columns=STARLING_MINIMUM_COLUMNS, crs="epsg:4326")

    starling_population = eqasim_population.copy()

    # sample the population
    if sample_rate is not None:
        starling_population = starling_population.sample(frac=sample_rate, random_state=sample_seed)

    # apply spatial filter to the population
    if spatial_filter is not None:
        # get a column containing the points composing the LineString
        starling_population["OD"] = starling_population.geometry.extract_unique_points()

        # apply filter: only keep elements that have all their points within the spatial filter
        starling_population.set_geometry("OD")
        starling_population = starling_population.sjoin(
            spatial_filter, how="inner", predicate="within"
        )
        starling_population.set_geometry("geometry")
        starling_population.drop(columns=["OD"], inplace=True)

    if starling_population.empty:
        raise ValueError("Population is empty after applying filters")

    # eqasim population are in epsg:2154, convert to epsg:4326
    starling_population.to_crs("epsg:4326", inplace=True)

    # convert to int
    starling_population["origin_time"] = starling_population["departure_time"].astype(int)

    # add attributes specific to Starling demand
    add_starling_demand_attributes(starling_population)

    return starling_population


def default_agent_ids(population: pd.DataFrame) -> list:
    """
    Default function for generating agent ids on a population.

    :param population: population DataFrame on which agent ids are generated
    :return: list of agent ids
    """
    return ["u-" + str(i) for i in range(len(population))]


def add_starling_demand_attributes(
    population: pd.DataFrame, agent_id_generator: callable = default_agent_ids
) -> pd.DataFrame:
    """
    Add default Starling users attributes: agent type, icon, agent id and mode.

    Caution: this function modifies the original DataFrame.

    :param population: population DataFrame to enrich
    :param agent_id_generator: function that takes the population as parameter and returns an "agent_id" column

    :return: enriched population DataFrame
    """

    population["agent_type"] = "user"
    population["icon"] = "user"
    population["agent_id"] = agent_id_generator(population)
    population["mode"] = "walk"

    return population


# command line utils


def eqasim_demand_from_args(input_args):
    # evaluate export filepath
    if input_args.outfile is None:
        filepath = path.basename(input_args.eqasim_file).replace(".geoparquet", ".geojson")
    else:
        filepath = input_args.outfile
    if path.basename(filepath) == filepath:
        filepath = path.join(path.dirname(input_args.eqasim_file), filepath)
    assert filepath.endswith(".geojson"), "The generated file must have the '.geojson' extension"

    # read Eqasim population
    assert input_args.eqasim_file.endswith(
        ".geoparquet"
    ), "A file with the '.geoparquet' extension is expected as the first argument"
    population = gpd.read_parquet(input_args.eqasim_file)
    assert population.crs is not None

    # read spatial filter file
    if input_args.spatial_filter is not None:
        spatial_filter = gpd.read_file(input_args.spatial_filter, driver="GeoJSON")
        spatial_filter.to_crs(population.crs, inplace=True)
    else:
        spatial_filter = None

    # generate the Starling population from the resulting sample
    starling_population = demand_from_eqasim(
        population,
        sample_rate=input_args.sample,
        sample_seed=input_args.seed,
        spatial_filter=spatial_filter,
    )

    # write file
    print(f"Creating Starling demand file at: {filepath}")
    starling_population.to_file(filepath, drop_id=True, driver="GeoJSON")


def add_eqasim_demand_action(subparsers):
    """
    Add a subparser for the eqasim-demand action.

    :param subparsers: argparse subparsers
    """

    demand_parser = subparsers.add_parser(
        "eqasim-demand",
        description="Script for the generation of Starling demand from an Eqasim population",
        help="Generate a Starling population from Eqasim outputs",
        epilog="Examples:\n\n"
        "starling-sim eqasim-demand data/eqasim/example_population.geoparquet\n"
        "starling-sim eqasim-demand data/eqasim/example_population.geoparquet --sample 0.01 --seed 42\n"
        "starling-sim eqasim-demand data/eqasim/example_population.geoparquet --spatial-filter data/eqasim/example_zone.geojson\n"
        "starling-sim eqasim-demand data/eqasim/example_population.geoparquet -o ./starling_population.geojson\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    demand_parser.add_argument(
        "eqasim_file",
        help="Eqasim population geoparquet file",
    )

    demand_parser.add_argument(
        "--spatial-filter",
        help="file describing a geometry used as spatial filter",
        type=str,
        metavar="GEOJSON_FILE",
    )

    demand_parser.add_argument(
        "-s",
        "--sample",
        help="Population sampling rate, between 0 and 1",
        type=float,
        metavar="SAMPLE_RATE",
    )

    demand_parser.add_argument("--seed", help="random seed used for sampling", type=int)

    demand_parser.add_argument(
        "-o",
        "--outfile",
        help="name of the output file. Default is the input filename with '.geojson' extension. "
        "If only a filename is provided, generate the new file in the same folder than the Eqasim population file",
        type=str,
    )
