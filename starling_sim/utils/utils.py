"""
This module contains utils for the Starling framework.
"""

import os
import subprocess
import logging
import json
import geopandas
import pandas as pd
import numpy as np
import gtfs_kit as gt
import osmnx as ox
from shapely.geometry import Polygon
from numbers import Integral
from jsonschema import validate, ValidationError, RefResolver
from starling_sim.utils.paths import schemas_folder, gtfs_feeds_folder, osm_graphs_folder

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
        schema = json_load(schemas_folder() + schema)

    # get the absolute path and setup a resolver
    schema_abs_path = 'file:///{0}/'.format(os.path.abspath(schemas_folder()).replace("\\", "/"))
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

    :param points: list of coordinates, must be (lon, lat) points.

    :return: GeoDataFrame containing a shapely Polygon with crs="epsg:4326"
    """

    # create a shapely Polygon from point list
    polygon = shapely_polygon_from_points(points)

    # create a GeoDataFrame containing the polygon
    gdf = geopandas.GeoDataFrame([polygon], columns=["geometry"])

    # set epsg, not in GeoDataFrame init
    gdf.crs = {"init": "epsg:4326"}

    return gdf


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
            properties["stop_id"] = str(i)

        # create a stop name if not provided
        if "stop_name" not in properties:
            properties["stop_name"] = "Stop point {id}".format(id=properties["stop_id"])

        # append a new row
        stops_table = stops_table.append(properties, ignore_index=True)

    return stops_table


def stop_table_from_gtfs(gtfs_feed, routes=None, zone=None, fixed_stops=None, active_stops_only=False):

    result_table = pd.DataFrame()

    gtfs_stops = gtfs_feed.get_stops().copy()

    if fixed_stops is not None:
        result_table = pd.concat([result_table, gtfs_stops[gtfs_stops["stop_id"].isin(fixed_stops)]], sort=False)

    if active_stops_only:
        stop_times = gtfs_feed.get_stop_times()
        stop_ids = stop_times.drop_duplicates("stop_id")
        gtfs_stops = pd.merge(gtfs_stops, stop_ids)[gtfs_stops.columns]

    if routes is not None:
        gtfs_stops = gtfs_feed.get_stops(route_ids=routes)

    if zone is not None:
        gtfs_stops.rename(columns={"stop_lat": "lat", "stop_lon": "lon"}, inplace=True)
        gtfs_stops = points_in_zone(gtfs_stops, zone)
        gtfs_stops.rename(columns={"lat": "stop_lat", "lon": "stop_lon"}, inplace=True)

        gtfs_stops = gtfs_stops[gtfs_stops["in_zone"]]

        # remove stops areas
        gtfs_stops = gtfs_stops[(gtfs_stops["location_type"] == 0) | (gtfs_stops["location_type"].isna())]

    result_table = pd.concat([result_table, gtfs_stops], sort=False)
    result_table.drop_duplicates(inplace=True)

    return result_table


def import_osm_graph(method, network_type, simplify, query=None, point=None, dist=None, polygon=None,
                     outfile=None, bz2_compression=True):
    """
    Generate an OSM graph from given parameters and store it in a file.

    The osmnx function used to generate the OSM graph is specified by the method parameter.

    The correct parameters must be provided according to the import method.

    :param method: name of the osmnx import method. Among ['place', 'point', 'polygon'].
    :param network_type: OSM network_type of the graph
    :param simplify: boolean indicating if the graph should be simplified
    :param query: string, dict or list describing the place (must be geocodable)
    :param point: [lon, lat] coordinates of the center point
    :param dist: distance of the bbox from the center point
    :param polygon: list of points describing a polygon
    :param outfile: optional name for the output file
    :param bz2_compression: boolean indicating if the file should be compressed in bz2
    """

    # import the OSM graph according to the given method
    if method == "place":
        graph = osm_graph_from_place(query, network_type, simplify)
        default_outfile = "G{}_{}.graphml".format(network_type, query)

    elif method == "point":
        graph = osm_graph_from_point(point, dist, network_type, simplify)
        default_outfile = "G{}_{}-{}_{}.graphml".format(network_type, point[0], point[1], dist)

    elif method == "polygon":
        default_outfile = None
        if outfile is None:
            print("Outfile name must be provided when importing from polygon.")
            return
        graph = osm_graph_from_polygon(polygon, network_type, simplify)

    else:
        print("Unknown import method {}. Choices are ['point', 'place', 'polygon'].")
        return

    # keep the largest strongly connected component of the graph
    graph = ox.utils_graph.get_largest_component(graph, strongly=True)

    # get the output filename
    if outfile is None:

        # add 'S' to simplified graphs
        if simplify:
            default_outfile = "S" + default_outfile

        outfile = default_outfile

    # save the graph at .graphml format
    save_osm_graph(graph, filename=outfile, folder=osm_graphs_folder(), bz2_compression=bz2_compression)

    # return the graph
    return graph


def osm_graph_from_point(point, distance, network_type, simplify):
    """
    Import an OSM graph of an area around the location point.

    The import is done with the distance_type parameter set to 'bbox'.

    :param point: (lon, lat) point
    :param distance: distance around point
    :param network_type: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    if point is None or distance is None:
        print("The point and distance parameters must be specified when importing graph from point.")
        exit(1)

    # reverse the point coordinates (osmnx takes (lat, lon) coordinates)
    point = (point[1], point[0])

    return ox.graph_from_point(point, dist=distance, dist_type="bbox",
                               network_type=network_type, simplify=simplify)


def osm_graph_from_polygon(polygon_points, network_type, simplify):
    """
    Import an OSM graph of the area within the polygon.

    :param polygon_points: list of (lon, lat) points delimiting the network zone
    :param network_type: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    if polygon_points is None:
        print("The polygon parameter must be specified when importing graph from polygon.")
        exit(1)

    # create a shapely polygon with (lat, lon) coordinates from the list of points
    shapely_polygon = shapely_polygon_from_points(polygon_points)

    return ox.graph_from_polygon(shapely_polygon, network_type=network_type, simplify=simplify)


def osm_graph_from_place(query, network_type, simplify):
    """
    Import an OSM graph of the area described by the geocodable query.

    :param query: string, dict or list describing the place (must be geocodable)
    :param network_type: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    if query is None:
        print("The query parameter must be specified when importing graph from place.")
        exit(1)

    return ox.graph_from_place(query, network_type=network_type, simplify=simplify)


def save_osm_graph(graph, filename, folder, bz2_compression):
    """
    Save the given graph in a .graphml file.

    The parameter bz2_compression indicates if the .graphml file
    should be compressed using bzip2.

    :param graph: saved graph
    :param filename: name of the save file
    :param folder: name of the save folder
    :param bz2_compression: boolean indicating if the file should be compressed in bz2
    """

    # check filename
    if not filename.endswith(".graphml"):
        raise ValueError("OSM graph filename must end with .graphml")

    # save the graph
    filepath = folder + filename
    ox.save_graphml(graph, filepath)

    # compress to bz2 if asked
    if bz2_compression:
        subprocess.run(["bzip2", "-z", "-f", folder + filename])
        print("Saved osm graph at " + folder + filename + ".bz2")
    else:
        print("Saved osm graph at " + folder + filename)


def osm_graph_from_file(filename, folder=None):
    """
    Import an osm graph from a .graphml file.

    :param filename: path to the .graphml file
    :param folder: folder containing the .graphml file.
        Default is the osm graphs folder.

    :return: a networkx graph, or None if import fails
    """

    if folder is None:
        folder = osm_graphs_folder()

    filepath = folder + filename

    return ox.load_graphml(filepath)


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
        folder = gtfs_feeds_folder()
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
