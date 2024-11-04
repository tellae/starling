"""
This module contains utils for generating and managing Starling demand.
"""
from os import popen

import pandas as pd
import geopandas as gpd

def demand_from_eqasim(eqasim_population: gpd.GeoDataFrame, sample_rate: float = None, sample_seed = None, spatial_filter: gpd.GeoDataFrame=None, spatial_predicate: str = None) -> gpd.GeoDataFrame:
    """
    Generate a Starling population from an Eqasim population.

    :param eqasim_population: GeoDataFrame describing an Eqasim population
    :param sample_rate: fraction of the original population that is kept in the final population
    :param sample_seed: seed used for sampling
    :param spatial_filter: GeoDataFrame used as spatial filter
    :param spatial_predicate: predicate used for spatial filtering

    :return: GeoDataFrame of a Starling population generated from the Eqasim population
    """

    starling_population = eqasim_population.copy()

    # sample the population
    if input_args.sample is not None:
        starling_population = starling_population.sample(frac=sample_rate, random_state=sample_seed)

    # apply spatial filter to the population
    if spatial_filter is not None:
        starling_population = starling_population.sjoin(spatial_filter, how="inner", predicate=spatial_predicate)

    # eqasim population are in epsg:2154, convert to epsg:4326
    starling_population.to_crs("epsg:4326", inplace=True)

    # convert to int
    starling_population["origin_time"] = starling_population["origin_time"].astype(int)

    # add attributes specific to Starling demand
    add_starling_demand_attributes(starling_population)

    return starling_population


def default_agent_ids(population: pd.DataFrame) -> list:
    """
    Default fonction for generating agent ids on a population.

    :param population: population DataFrame on which agent ids are generated
    :return: list of agent ids
    """
    return ["u-" + str(i) for i in range(len(population))]



def add_starling_demand_attributes(population: pd.DataFrame, agent_id_generator: callable = default_agent_ids) -> pd.DataFrame:
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

