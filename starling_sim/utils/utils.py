"""
This module contains utils for the Starling framework.
"""

import os
import logging
import json
import geopandas
import pandas as pd
import numpy as np
import gtfs_kit as gt
import osmnx as ox
from shapely.geometry import Point, Polygon
from numbers import Integral
from jsonschema import validate, ValidationError, RefResolver
from starling_sim.utils.paths import SCHEMA_FOLDER, GTFS_FEEDS_FOLDER, \
    OSM_GRAPHS_FOLDER

pd.set_option('display.expand_frame_repr', False)


# Starling exceptions

class StarlingException(Exception):
    """
    Base class for all Starling exceptions.
    """


class LeavingSimulation(StarlingException):
    """
    Exception raised by agents for leaving the simulation.

    Agents should raise this exception by calling their leave_simulation() method
    to leave their loop and terminate their SimPy process.

    LeavingSimulation exceptions are caught in the agent simpy_loop_ method so a
    LeavingSimulationEvent can be traced and the agent main process can terminate.
    """


class SimulationError(LeavingSimulation):
    """
    Simulation error exception.

    This exception should be used when an unwanted
    event occurs in a simulation, like saying "We shouldn't be here".
    """


# json utils

def json_dump(data, filepath):
    """
    Create a json file and dump the given object

    :param data:
    :param filepath:
    :return:
    """

    with open(filepath, "w") as outfile:
        json.dump(data, outfile)


def json_pretty_dump(data, filepath):
    """
    Creates a json file and dumps the given object
    in a pretty print way

    :param data: object to be dumped into the json file
    :param filepath: path to the json file
    """

    with open(filepath, "w") as outfile:
        outfile.write(json.dumps(data, indent=4))


# TODO : check that the file contains a json, or at least catch exception
def json_load(filepath):
    """
    Loads the content of the given json file

    :param filepath: path to the json file
    :return: object loaded from json file
    """

    with open(filepath, "r") as param_file:
        return json.load(param_file)


# json schema validation

def validate_against_schema(instance, schema, raise_exception=True):

    # load the schema if a path is provided
    if isinstance(schema, str):
        schema = json_load(SCHEMA_FOLDER + schema)

    # get the absolute path and setup a resolver
    schema_abs_path = 'file:///{0}/'.format(os.path.abspath(SCHEMA_FOLDER).replace("\\", "/"))
    resolver = RefResolver(schema_abs_path, schema)

    # validate against schema and catch eventual exception
    try:
        validate(instance=instance, schema=schema, resolver=resolver)
        return True
    except ValidationError as e:
        if raise_exception:
            logging.log(40, "JSON Schema validation error")
            raise e
        else:
            logging.log(30, "JSON Schema validation of :\n\n{}\n\nfailed with message:\n\n {} ".format(instance, e))
            return False


# converters

def get_sec(time_str):
    """Get Seconds from time."""

    # HH:MM:SS to seconds
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def make_int(a):
    """
    Convert the given integer to the Python int type.

    Check that the given number is an Integral, and raise a
    ValueError if it is not the case.

    :param a: integer to check

    :return: integer with Python int type
    """

    if isinstance(a, float):
        if not a.is_integer():
            raise ValueError("Object {} is not Integral".format(a))
    elif not isinstance(a, Integral):
        raise ValueError("Object {} is not Integral, cannot convert to int".format(a))

    return int(a)


# geojson utils


def new_point_feature(point_localisation=None, properties=None):
    """

    :param point_localisation:
    :param properties:
    :return:
    """

    # set point localisation to [0, 0] by default
    if point_localisation is None:
        point_localisation = [0, 0]

    # create  the feature geometry
    geometry = {
        "type": "Point",
        "coordinates": point_localisation
    }

    return new_feature(geometry, properties)


def new_line_string_feature(linestring, properties=None):

    # create  the feature geometry
    geometry = {
        "type": "LineString",
        "coordinates": linestring
    }

    return new_feature(geometry, properties)


def new_multi_polygon_feature(polygon_list, properties=None):
    """


    :param polygon_list: list of polygon coordinates.
    :param properties:
    :return:
    """

    # create  the feature geometry
    geometry = {
        "type": "MultiPolygon",
        "coordinates": polygon_list
    }

    return new_feature(geometry, properties)


def new_feature(geometry, properties=None):

    # set properties with empty dict by default
    if properties is None:
        properties = dict()

    # build a geojson feature
    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties
    }

    return feature


def new_feature_collection(features=None):
    """

    :param features:
    :return:
    """

    # set features to empty list by default
    if features is None:
        features = []

    # build a geojson feature collection
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    return feature_collection


# shapes functions

def shapely_polygon_from_points(points, reverse=False):
    """
    Create and return a Shapely Polygon object.

    The polygon is initialised using the given list of tuples
    representing coordinates. If reverse is True, the coordinates
    values are inverted. This can be used to set GPS coordinates in
    order, for instance.

    :param points: list of lists containing point coordinates
    :param reverse: boolean indicating if coordinates should be reversed.
        Default is False.

    :return: Shapely Polygon object
    """

    # if asked, transform (lat, lon) points into (lon, lat) ones
    if reverse:
        points = [point[::-1] for point in points]

    # create a shapely Polygon from point list
    polygon = Polygon(points)

    return polygon


def geopandas_points_from_localisations(localisations):
    """
    Create and return a GeoDataFrame containing shapely Point objects.

    localisations can either be a tuple or list describing a single
    (lat, lon) point, or a Dataframe containing a 'lat' and a 'lon' column.

    The localisations must be specified using "epsg:4326"

    :param localisations: either a single point (lat, lon) coordinates,
        or a Dataframe containing a 'lat' and a 'lon' column, "epsg:4326"

    :return: GeoDataFrame containing shapely Point objects with crs="epsg:4326"
    """

    if isinstance(localisations, tuple) or isinstance(localisations, list):
        # create a DataFrame containing the point coordinates
        localisations = pd.DataFrame({"lat": localisations[0], "lon": localisations[1]},
                                     columns=["lat", "lon"], index=[0])

    # create a GeoDataFrame from df
    gdf = geopandas.GeoDataFrame(
        localisations, geometry=geopandas.points_from_xy(localisations.lon, localisations.lat))

    # set epsg
    gdf.crs = {"init": "epsg:4326"}

    return gdf


def geopandas_polygon_from_points(points):
    """
    Create and return a GeoDataFrame containing a single polygon.

    The GeoDataFrame contains a Shapely Polygon object created using
    the given points, and stored in the first line of the 'geometry' column.

    The point coordinates are reversed to have a zone specified with
    (lon, lat) points, with "epsg:4326"

    :param points: list of coordinates, must be (lat, lon) points.

    :return: GeoDataFrame containing a shapely Polygon with crs="epsg:4326"
    """

    # create a shapely Polygon from point list
    polygon = shapely_polygon_from_points(points, reverse=True)

    # create a GeoDataFrame containing the polygon
    gdf = geopandas.GeoDataFrame([polygon], columns=["geometry"])

    # set epsg, not in GeoDataFrame init
    gdf.crs = {"init": "epsg:4326"}

    return gdf


def bbox_centered_on_point(point_localisation, distance):
    """
    Recreate a osmnx bbox using a central point and distance.

    The resulting bbox is a square with edges of size 2*dist,
    centered on the given point.

    :param point_localisation: (lat, lon), central point of the bbox
    :param distance: "radius" of the square bbox

    :return: GeoDataFrame containing a shapely Polygon with crs="epsg:4326"
    """

    # create a GeoDataFrame point
    bbox = geopandas_points_from_localisations(point_localisation)

    # convert GeoDataFrame to cartesian
    bbox = bbox.to_crs({"init": "epsg:2154"})

    # compute coordinates of the bbox corners
    center_point = bbox.loc[0, "geometry"]

    corner_point = Point(center_point.x - float(distance), center_point.y + float(distance))
    bbox = bbox.append({"geometry": corner_point}, ignore_index=True)

    corner_point = Point(center_point.x + float(distance), center_point.y + float(distance))
    bbox = bbox.append({"geometry": corner_point}, ignore_index=True)

    corner_point = Point(center_point.x + float(distance), center_point.y - float(distance))
    bbox = bbox.append({"geometry": corner_point}, ignore_index=True)

    corner_point = Point(center_point.x - float(distance), center_point.y - float(distance))
    bbox = bbox.append({"geometry": corner_point}, ignore_index=True)

    # remove central point
    bbox = bbox.drop(index=0)

    # convert GeoDataFrame back to GPS coordinates
    bbox = bbox.to_crs({"init": "epsg:4326"})

    # get points coordinates to create a geopandas polygon
    points = [(corner.y, corner.x) for corner in bbox["geometry"].values]
    bbox_zone = geopandas_polygon_from_points(points)

    return bbox_zone


def points_in_zone(localisations, zone):
    """
    Evaluate if the given points are contained in the zone.

    localisations can either be a tuple or list describing a single
    (lat, lon) point, or a DataFrame containing a 'lat' and a 'lon' column.

    The function either returns a boolean if a single point is provided,
    or adds a "in_zone" column to the DataFrame containing booleans.

    :param localisations: either a single point (lat, lon) coordinates,
        or a DataFrame containing a 'lat' and a 'lon' column, "epsg:4326"
    :param zone: GeoDataFrame containing a shapely Polygon with crs="epsg:4326"

    :return: either a boolean, or the localisations DataFrame with an
        additional "in_zone" column containing booleans.
    """

    # create a GeoDataFrame point
    geopandas_points = geopandas_points_from_localisations(localisations)

    # convert point to zone projection
    geopandas_points = geopandas_points.to_crs(zone.crs)

    # evaluate if within zone
    res = geopandas.sjoin(geopandas_points, zone, how="left", op="within")

    # set new column 'in_zone'
    res["in_zone"] = res["index_right"].replace(to_replace={np.nan: False, 0: True})

    # remove evaluation columns
    res.drop(labels=["geometry", "index_right"], axis=1, inplace=True)

    # if a single point was provided, return a the boolean
    if isinstance(localisations, tuple) or isinstance(localisations, list):
        res = res.loc[res.index[0], "in_zone"]

    return res


def stops_table_from_geojson(geojson_path):
    """
    Create a stops table from the provided geojson file.

    :param geojson_path:

    :return: a DataFrame containing the stops information
    """

    # get the feature collection from the geojson
    stops_feature_collection = json_load(geojson_path)

    # initialise the table
    stops_table = pd.DataFrame()

    for i in range(len(stops_feature_collection["features"])):

        feature = stops_feature_collection["features"][i]
        properties = feature["properties"]

        # get coordinates from the geometry
        properties["stop_lon"] = feature["geometry"]["coordinates"][0]
        properties["stop_lat"] = feature["geometry"]["coordinates"][1]

        # create a stop id if not provided
        if "stop_id" not in properties:
            properties["stop_id"] = i

        # create a stop name if not provided
        if "stop_name" not in properties:
            properties["stop_name"] = "Stop point {id}".format(id=properties["stop_id"])

        # append a new row
        stops_table = stops_table.append(properties, ignore_index=True)

    return stops_table


# osmnx utils

def import_osm_graph(point, dist, mode="walk", simplify=True, outfile=None):
    """
    Generate an osm graph from parameters and store it in a file.

    The generation method uses osmnx graph_from_point method with
    dist_type="bbox".

    :param point: [lon, lat] coordinates of the center point
    :param dist: distance of the bbox from the center point
    :param mode: network_type of the graph
    :param simplify: boolean indicating if the graph should be simplified
    :param outfile: optional name for the output file
    """

    # reverse lon and lat since osmnx takes [lat, lon]
    point = [point[1], point[0]]

    # check mode
    if mode not in ["walk", "bike", "drive", "drive_service", "all", "all_private"]:
        raise ValueError("Unknown network type {}".format(mode))

    # import graph

    graph = osm_graph_from_point(point, dist, mode, simplify)

    # determine filename
    if outfile is None:
        filename = "G{}_{}_{}_{}.graphml".format(mode, point[1], point[0], dist)
        if simplify:
            filename = "S" + filename
    else:
        filename = outfile

    # save the graph at .graphml format
    save_osm_graph(graph, filename=filename, folder=OSM_GRAPHS_FOLDER)


# TODO : store generation information somewhere else
def osm_graph_from_point(point, distance, mode, simplify=True):
    """
    Import an osm graph of an area around the location point.

    The graph is reduced to its largest connected component, since
    we want connected graphs in order to find path between all nodes.

    For now, we store the generation information in the name attribute.

    :param point: (lat, lon) point
    :param distance: distance around point
    :param mode: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    graph_name = "{};{};{};{}".format(mode, point[0], point[1], distance)

    graph = ox.graph_from_point(point, distance=distance, distance_type="bbox",
                                network_type=mode, simplify=simplify, name=graph_name)

    # we want a strongly connected graph
    graph = ox.geo_utils.get_largest_component(graph, strongly=True)

    return graph


def osm_graph_from_polygon(polygon_points, mode, simplify=True):
    """
    Import an osm graph of the area with the polygon.

    :param polygon_points: list of (lat, lon) points delimiting the network zone
    :param mode: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    polygon_points_strings = polygon_points.apply(str)
    graph_name = polygon_points_strings.join(";")

    shapely_polygon = shapely_polygon_from_points(polygon_points)

    graph = ox.graph_from_polygon(shapely_polygon, network_type=mode, simplify=simplify,
                                  name=graph_name)

    # we want a strongly connected graph
    graph = ox.geo_utils.get_largest_component(graph, strongly=True)

    return graph


def save_osm_graph(graph, filename, folder):
    """
    Save the given graph in a graphml file

    If the files already exists, does nothing (? to be verified)

    :param graph: saved graph
    :param filename: name of the save file
    :param folder: name of the save folder
    """

    # check filename
    if not filename.endswith(".graphml"):
        raise ValueError("OSM graph filename must end with .graphml")

    # print saving message
    print("Saving osm graph at " + folder + filename)

    # save the graph
    ox.save_graphml(graph, filename=filename, folder=folder)


def osm_graph_from_file(filename):
    """
    Import an osm graph from a .graphml file.

    The file is expected to be in OSM_GRAPHS_FOLDER.

    :param filename: path to the graphml file

    :return: a networkx graph, or None if import fails
    """

    graph = ox.load_graphml(filename=filename, folder=OSM_GRAPHS_FOLDER)
    return graph


# gtfs utils

def import_gtfs_feed(gtfs_filename, folder=None):
    """
    Import a gtfs feed from the given file.

    Also check that stop times are ordered and transfers are symmetrical.

    :param gtfs_filename: name of a gtfs file
    :param folder: folder where the gtfs is stored.
        Default is the GTFS_FEEDS_FOLDER.
    :return: gtfs-kit Feed object
    """

    # read the gtfs feed using gtfs-kit
    if folder is None:
        folder = GTFS_FEEDS_FOLDER
    path = folder + gtfs_filename
    feed = gt.read_feed(path, dist_units="km")

    # additional operations and validations

    # order stop_times by trip_id and stop_sequence
    stop_times = feed.stop_times
    if stop_times is not None:
        stop_times = stop_times.sort_values(by=["trip_id", "stop_sequence"])
        feed.stop_times = stop_times
        feed.stop_times = feed.stop_times

    # check that foot-path transfers are symmetrical
    if feed.transfers is not None:
        transfer_table = feed.transfers.copy()
        transfer_table = transfer_table[transfer_table["from_stop_id"] != transfer_table["to_stop_id"]]
        transfer_table["stop_A"] = transfer_table[["from_stop_id", "to_stop_id"]].apply(min, axis=1)
        transfer_table["stop_B"] = transfer_table[["from_stop_id", "to_stop_id"]].apply(max, axis=1)
        count = transfer_table.groupby(["stop_A", "stop_B"], as_index=False).agg(["count"])
        counts_not_equal_to_2 = count[count["min_transfer_time"]["count"] != 2]
        if not counts_not_equal_to_2.empty:
            logging.warning("Transfer table of {} is not symmetrical (in term of arcs, not transfer times)"
                            .format(gtfs_filename))

    return feed


# folder creation

def create_if_not_exists(folder):
    """
    Test the existence of the folder and create it if not present.

    :param folder: path of the folder
    """

    if not os.path.exists(folder):
        os.mkdir(folder)
