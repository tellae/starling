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
import gzip
import shutil
import copy
from shapely.geometry import Polygon, LineString
from numbers import Integral
from jsonschema import Draft7Validator, Draft4Validator, validators, ValidationError, RefResolver
from starling_sim.utils.paths import (
    schemas_folder,
    gtfs_feeds_folder,
    osm_graphs_folder,
    scenario_inputs_folder,
    PARAMETERS_FILENAME,
    INPUT_FOLDER_NAME,
)
from starling_sim.utils.simulation_logging import BLANK_LOGGER

pd.set_option("display.expand_frame_repr", False)


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

    LeavingSimulation exceptions are caught in the agent :meth:`~starling_sim.basemodel.agent.agent.Agent.simpy_loop_`
    method so a LeavingSimulationEvent can be traced and the agent main process can terminate.
    """


class SimulationError(LeavingSimulation):
    """
    Simulation error exception.

    This exception should be used when an unwanted
    event occurs in a simulation, like saying "We shouldn't be here".
    """


class PlanningChange(Exception):
    """
    Exception raised to interrupt a service vehicle loop
    when its planning has changed.
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


# compression utils


def gz_compression(filepath, delete_source=True):
    """
    Compress the given file using gzip.

    Delete the source file if asked.

    :param filepath: path pointing to the source file
    :param delete_source: boolean indicating if the source file should be deleted
    """

    # compress the file using gzip
    compressed_path = filepath + ".gz"
    with open(filepath, "rb") as f_in:
        with gzip.open(compressed_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # delete source file if asked
    if delete_source:
        os.remove(filepath)

    return compressed_path


def gz_decompression(filepath, delete_source=True):
    """
    Decompress the given file using gzip.

    Delete the source file if asked.

    :param filepath: path pointing to the source file
    :param delete_source: boolean indicating if the source file should be deleted

    :raises: ValueError if the filepath does not end with '.gz'
    """

    # test if the file ends with .gz
    if not filepath.endswith(".gz"):
        logging.log(
            30,
            "File to decompress does not end with '.gz'. Continuing without decompressing the file.",
        )

    # decompress the file unsing gzip
    with gzip.open(filepath, "rb") as f_in:
        with open(filepath[:-3], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # delete source file if asked
    if delete_source:
        os.remove(filepath)


# starling file information


def create_file_information(
    filepath,
    mimetype,
    compressed_mimetype=None,
    content=None,
    subject=None,
    keep_filepath=False,
):
    """
    Create a dict containing file information.

    :param filepath: file path
    :param mimetype: file mimetype
    :param compressed_mimetype: file mimetype after decompression
    :param content: content metadata
    :param subject: subject metadata
    :param keep_filepath: keep complete file path in 'filename'

    :return: { filename/filepath, mimetype, metadata }
    """

    if content is None:
        raise ValueError("'content' metadata was not provided for file {}".format(filepath))

    if compressed_mimetype is None:
        compressed_mimetype = mimetype

    metadata = {"compressed-mimetype": compressed_mimetype, "content": content}

    if subject is not None:
        metadata["subject"] = subject

    file_information = {
        "filename": filepath if keep_filepath else os.path.basename(filepath),
        "mimetype": mimetype,
        "metadata": metadata,
    }

    return file_information


# json schema validation

# use the type check from Draft4Validator, because Draft7 considers 1.0 as integer
CustomValidator = validators.extend(Draft7Validator, type_checker=Draft4Validator.TYPE_CHECKER)


def validate_against_schema(instance, schema, raise_exception=True):

    # load schema object
    schema = load_schema(schema, False)

    # get the absolute path and setup a resolver
    schema_abs_path = "file:///{0}/".format(os.path.abspath(schemas_folder()).replace("\\", "/"))
    resolver = RefResolver(schema_abs_path, schema)
    validator = CustomValidator(schema=schema, resolver=resolver)

    # validate against schema and catch eventual exception
    try:
        validator.validate(instance)
        return True
    except ValidationError as e:
        if raise_exception:
            raise e
        else:
            logging.log(
                30,
                "JSON Schema validation of :\n\n{}\n\nfailed with message:\n\n {} ".format(
                    instance, e
                ),
            )
            return False


def add_defaults_and_validate(instance, schema, raise_exception=True):

    # initialise an empty result dict
    res = copy.deepcopy(instance)

    # load schema object
    schema = load_schema(schema)

    # add default properties to the schema
    add_defaults(res, schema)

    # validate the final instance against the schema
    validate_against_schema(res, schema, raise_exception)

    return res


def add_defaults(instance, schema, current_prop=None):

    if schema["type"] == "object" and "default" not in schema:
        for prop in schema["properties"].keys():

            if current_prop is None:
                prop_instance = instance
            else:
                if current_prop in instance:
                    prop_instance = instance[current_prop]
                else:
                    prop_instance = dict()
                    instance[current_prop] = prop_instance

            add_defaults(prop_instance, schema["properties"][prop], prop)

    else:
        if current_prop not in instance and "default" in schema:
            instance[current_prop] = schema["default"]


def load_schema(schema, make_copy=True):
    if isinstance(schema, str):
        # load the schema if a path is provided
        final_schema = json_load(schemas_folder() + schema)
    elif isinstance(schema, dict):
        if make_copy:
            final_schema = copy.deepcopy(schema)
        else:
            final_schema = schema
    else:
        raise TypeError("The provided schema is neither a dict nor a path to a schema file")

    return final_schema


# converters


def get_sec(time_str):
    """Get Seconds from time."""

    # HH:MM:SS to seconds
    h, m, s = time_str.split(":")
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
    geometry = {"type": "Point", "coordinates": point_localisation}

    return new_feature(geometry, properties)


def new_line_string_feature(linestring, properties=None):

    # create  the feature geometry
    geometry = {"type": "LineString", "coordinates": linestring}

    return new_feature(geometry, properties)


def new_multi_polygon_feature(polygon_list, properties=None):
    """


    :param polygon_list: list of polygon coordinates.
    :param properties:
    :return:
    """

    # create  the feature geometry
    geometry = {"type": "MultiPolygon", "coordinates": polygon_list}

    return new_feature(geometry, properties)


def new_feature(geometry, properties=None):

    # set properties with empty dict by default
    if properties is None:
        properties = dict()

    # build a geojson feature
    feature = {"type": "Feature", "geometry": geometry, "properties": properties}

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
    feature_collection = {"type": "FeatureCollection", "features": features}

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
        localisations = pd.DataFrame(
            {"lat": localisations[0], "lon": localisations[1]}, columns=["lat", "lon"], index=[0]
        )

    # create a GeoDataFrame from df
    gdf = geopandas.GeoDataFrame(
        localisations, geometry=geopandas.points_from_xy(localisations.lon, localisations.lat)
    )

    # set epsg
    gdf.set_crs("epsg:4326")

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
    gdf.set_crs("epsg:4326")

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

    # set epsg
    geopandas_points.set_crs("epsg:4326")

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

        # convert properties to DataFrame
        properties = pd.DataFrame([properties])

        # append a new row
        stops_table = pd.concat([stops_table, properties], ignore_index=True)

    return stops_table


def stop_table_from_gtfs(
    gtfs_feed, routes=None, zone=None, fixed_stops=None, active_stops_only=False
):

    result_table = pd.DataFrame()

    gtfs_stops = gtfs_feed.get_stops().copy()

    if fixed_stops is not None:
        result_table = pd.concat(
            [result_table, gtfs_stops[gtfs_stops["stop_id"].isin(fixed_stops)]], sort=False
        )

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
        gtfs_stops = gtfs_stops[
            (gtfs_stops["location_type"] == 0) | (gtfs_stops["location_type"].isna())
        ]

    result_table = pd.concat([result_table, gtfs_stops], sort=False)
    result_table.drop_duplicates(inplace=True)

    return result_table


def import_osm_graph(
    method,
    network_type,
    simplify,
    query=None,
    which_result=None,
    point=None,
    dist=None,
    polygon=None,
    outfile=None,
):
    """
    Generate an OSM graph from given parameters and store it in a file.

    The osmnx function used to generate the OSM graph is specified by the method parameter.

    The correct parameters must be provided according to the import method.

    :param method: name of the osmnx import method. Among ['place', 'point', 'polygon'].
    :param network_type: OSM network_type of the graph
    :param simplify: boolean indicating if the graph should be simplified
    :param query: string, dict or list describing the place (must be geocodable)
    :param which_result: integer describing which geocoding result to use,
        or None to auto-select the first (Multi)Polygon
    :param point: [lon, lat] coordinates of the center point
    :param dist: distance of the bbox from the center point
    :param polygon: list of points describing a polygon
    :param outfile: optional name for the output file
    """

    # import the OSM graph according to the given method
    if method == "place":
        graph = osm_graph_from_place(query, which_result, network_type, simplify)
        default_outfile = "G{}_{}.graphml.bz2".format(network_type, query)

    elif method == "point":
        graph = osm_graph_from_point(point, dist, network_type, simplify)
        default_outfile = "G{}_{}-{}_{}.graphml.bz2".format(network_type, point[0], point[1], dist)

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
    save_osm_graph(graph, filename=outfile, folder=osm_graphs_folder())

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
        print(
            "The point and distance parameters must be specified when importing graph from point."
        )
        exit(1)

    # reverse the point coordinates (osmnx takes (lat, lon) coordinates)
    point = (point[1], point[0])

    return ox.graph_from_point(
        point, dist=distance, dist_type="bbox", network_type=network_type, simplify=simplify
    )


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


def osm_graph_from_place(query, which_result, network_type, simplify):
    """
    Import an OSM graph of the area described by the geocodable query.

    :param query: string, dict or list describing the place (must be geocodable)
    :param which_result: integer describing which geocoding result to use,
        or None to auto-select the first (Multi)Polygon
    :param network_type: osm network type
    :param simplify: boolean indicating if the graph should be simplified

    :return: a networkx graph
    """

    if query is None:
        print("The query parameter must be specified when importing graph from place.")
        exit(1)

    return ox.graph_from_place(
        query, network_type=network_type, simplify=simplify, which_result=which_result
    )


def save_osm_graph(graph, filename, folder):
    """
    Save the given graph in a .graphml file.

    Detect if the filename ends with '.bz2', and realise
    a bz2 compression accordingly.

    :param graph: saved graph
    :param filename: name of the save file
    :param folder: name of the save folder
    """

    # check bz2 extension
    if filename.endswith(".bz2"):
        to_bz2 = True
        filename = filename[:-4]
    else:
        to_bz2 = False

    # check filename
    if not filename.endswith(".graphml"):
        raise ValueError("OSM graph filename must end with .graphml or .graphml.bz2")

    # save the graph
    filepath = folder + filename
    ox.save_graphml(graph, filepath)

    # compress to bz2 if necessary
    if to_bz2:
        subprocess.run(["bzip2", "-z", "-f", filepath])
        print("Saved osm graph at " + filepath + ".bz2")
    else:
        print("Saved osm graph at " + filepath)


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


def import_gtfs_feed(gtfs_filename, transfer_restriction=None, folder=None):
    """
    Import a gtfs feed from the given file.

    Also check that stop times are ordered and transfers are symmetrical.

    :param gtfs_filename: name of a gtfs file
    :param transfer_restriction: duration restriction on the transfers
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
        transfer_table = transfer_table[
            transfer_table["from_stop_id"] != transfer_table["to_stop_id"]
        ]
        transfer_table["stop_A"] = transfer_table[["from_stop_id", "to_stop_id"]].apply(min, axis=1)
        transfer_table["stop_B"] = transfer_table[["from_stop_id", "to_stop_id"]].apply(max, axis=1)
        count = transfer_table.groupby(["stop_A", "stop_B"], as_index=False).agg(["count"])
        counts_not_equal_to_2 = count[count["min_transfer_time"]["count"] != 2]
        if not counts_not_equal_to_2.empty:
            logging.warning(
                "Transfer table of {} is not symmetrical (in term of arcs, not transfer times)".format(
                    gtfs_filename
                )
            )
        if not is_transitive(feed.transfers) and transfer_restriction is not None:
            feed.transfers = transitively_closed_transfers(feed.transfers, transfer_restriction)
    else:
        logging.warning("The given GTFS has no transfer table")

    return feed


def transitively_closed_transfers(transfers, restrict_transfer_time):
    """
    Restrict the transfer table under the given time limit and then make it transitive.

    The restriction on the transfer times help keeping the transfer table at a reasonable size
    after making it transitive.

    :param transfers: transfer table
    :param restrict_transfer_time: transfer duration limit

    :return: transitive closure of the restricted transfer table
    """

    # restrict original transfers so the final set of transfers isn't too large
    if restrict_transfer_time is not None:
        logging.info(
            "The GTFS transfer table is not transitively closed. "
            "Transfers are restricted to duration under {} seconds and then made transitive.".format(
                restrict_transfer_time
            )
        )
        transfers = transfers[transfers["min_transfer_time"] <= restrict_transfer_time]
        return make_transfers_transitively_closed(transfers)
    # else:
    #     new_transfers = None
    #     restrict_transfer_time = 60
    #     computations_too_big = False
    #     while not computations_too_big:
    #         restricted_transfers = transfers[transfers["min_transfer_time"] <= restrict_transfer_time]
    #         try:
    #             new_transfers = make_transfers_transitively_closed(restricted_transfers)
    #             restrict_transfer_time += 60
    #         except TimeoutError as e:
    #             computations_too_big = True
    #             if restrict_transfer_time == 60:
    #                 raise e
    #
    #     return new_transfers


def is_transitive(transfers):
    """
    Test if the given transfer table is transitive.

    :param transfers: transfer table

    :return: boolean indicating if the table is transitive
    """

    if transfers is None:
        return True

    nb_transfers = len(transfers)
    # create new transfers using transitive property
    new_transfers = pd.merge(transfers, transfers, left_on="to_stop_id", right_on="from_stop_id")
    new_transfers["min_transfer_time"] = (
        new_transfers["min_transfer_time_x"] + new_transfers["min_transfer_time_y"]
    )
    new_transfers["from_stop_id"] = new_transfers["from_stop_id_x"]
    new_transfers["to_stop_id"] = new_transfers["to_stop_id_y"]
    if "transfer_type" in transfers.columns:
        new_transfers["transfer_type"] = new_transfers[["transfer_type_x", "transfer_type_y"]].max(
            axis=1
        )
    new_transfers = new_transfers[transfers.columns]

    # add them to the former set of transfers
    transfers = pd.concat([transfers, new_transfers])

    # keep the best transfer for each couple of stops
    transfers.sort_values(by="min_transfer_time", inplace=True)
    transfers = transfers.groupby(by=["from_stop_id", "to_stop_id"], as_index=False).first()

    # break condition
    return len(transfers) == nb_transfers


def make_transfers_transitively_closed(transfers):
    """
    Make the given transfer table transitive by incrementally adding transition transfers.

    If transfers from A to B and from B to C exist, create a transfer from A to C.
    If several transfers from A to C exist, keep the one with shorter transfer duration.
    Repeat.

    :param transfers: transfer table

    :return: transitive closure of the given transfer table
    """

    # loop until no new transfer is found
    nb_transfers = len(transfers)
    while True:
        # create new transfers using transitive property
        new_transfers = pd.merge(
            transfers, transfers, left_on="to_stop_id", right_on="from_stop_id"
        )
        new_transfers["min_transfer_time"] = (
            new_transfers["min_transfer_time_x"] + new_transfers["min_transfer_time_y"]
        )
        new_transfers["from_stop_id"] = new_transfers["from_stop_id_x"]
        new_transfers["to_stop_id"] = new_transfers["to_stop_id_y"]
        if "transfer_type" in transfers.columns:
            new_transfers["transfer_type"] = new_transfers[
                ["transfer_type_x", "transfer_type_y"]
            ].max(axis=1)
        new_transfers = new_transfers[transfers.columns]

        # add them to the former set of transfers
        transfers = pd.concat([transfers, new_transfers])

        # keep the best transfer for each couple of stops
        transfers.sort_values(by="min_transfer_time", inplace=True)
        transfers = transfers.groupby(by=["from_stop_id", "to_stop_id"], as_index=False).first()

        # break condition
        if len(transfers) == nb_transfers:
            break

        nb_transfers = len(transfers)

    return transfers


def stops2geojson(stops_df):
    """
    Create a geojson FeatureCollection from the GTFS stops.

    :param stops_df: stops DataFrame of the GTFS

    :return: feature collection
    """

    features = []
    stops_df.apply(
        lambda x: features.append(
            new_point_feature(
                point_localisation=[x["stop_lon"], x["stop_lat"]],
                properties={
                    "stop_id": x["stop_id"],
                    "stop_name": x["stop_name"],
                },
            )
        ),
        axis=1,
    )

    return new_feature_collection(features)


def transfers2geojson(transfers_df, stops_df):
    """
    Create a geojson FeatureCollection from the GTFS transfers.

    :param transfers_df: transfers DataFrame of the GTFS
    :param stops_df: stops DataFrame of the GTFS

    :return: feature collection
    """

    # add the stop information to the from_stop and to_stop
    geo_transfers = pd.merge(transfers_df, stops_df, left_on=["from_stop_id"], right_on=["stop_id"])
    geo_transfers = pd.merge(geo_transfers, stops_df, left_on=["to_stop_id"], right_on=["stop_id"])
    geo_transfers = geo_transfers[
        [
            "from_stop_id",
            "to_stop_id",
            "min_transfer_time",
            "stop_lat_x",
            "stop_lon_x",
            "stop_lat_y",
            "stop_lon_y",
        ]
    ]

    # create the geometry attribute
    geo_transfers["geometry"] = geo_transfers.apply(
        lambda x: LineString(
            [(x["stop_lon_x"], x["stop_lat_x"]), (x["stop_lon_y"], x["stop_lat_y"])]
        ),
        axis=1,
    )
    geo_transfers = geopandas.GeoDataFrame(geo_transfers)
    geo_transfers = geo_transfers[["min_transfer_time", "geometry"]]

    geojson = geo_transfers.to_json(drop_id=True)

    return geojson


# folder creation


def create_if_not_exists(folder):
    """
    Test the existence of the folder and create it if not present.

    :param folder: path of the folder
    """

    if not os.path.exists(folder):
        os.mkdir(folder)
        return True
    else:
        return False


# console log


def display_horizontal_bar(lvl=20):
    """
    Display a horizontal bar in the terminal.

    Try to make it the size of the terminal width.

    :param lvl: log level
    """

    try:
        bar_size = os.get_terminal_size().columns
    except OSError:
        bar_size = 100

    BLANK_LOGGER.log(lvl, "\u2014" * bar_size)


# multiple scenarios


def create_sub_scenarios(simulation_scenario):

    logging.info("Creating sub scenarios of: " + simulation_scenario.name)

    nb_scenarios = simulation_scenario["multiple"]
    scenarios_folder = os.path.join(simulation_scenario.scenario_folder, "scenarios")
    create_if_not_exists(scenarios_folder)

    # set random seed
    np.random.seed(simulation_scenario["seed"])
    seeds = np.random.choice(range(100000), size=nb_scenarios, replace=False)
    sub_scenario_name_format = "{base_scenario}-{index}"

    scenario_paths = []
    for i in range(nb_scenarios):

        sub_scenario_name = sub_scenario_name_format.format(
            base_scenario=simulation_scenario.name, index=i
        )
        sub_scenario_folder = os.path.join(scenarios_folder, sub_scenario_name)
        sub_scenario_inputs_folder = scenario_inputs_folder(sub_scenario_folder)
        scenario_paths.append(sub_scenario_folder)

        if os.path.exists(sub_scenario_folder):
            logging.info("Scenario {} already created".format(sub_scenario_name))
            continue
        else:
            logging.info("Creating scenario " + sub_scenario_name)

        # create sub scenario folders
        create_if_not_exists(sub_scenario_folder)
        create_if_not_exists(sub_scenario_inputs_folder)

        # sub scenario inputs
        sub_parameters = simulation_scenario.copy_parameters()
        sub_parameters["scenario"] = sub_scenario_name
        sub_parameters["seed"] = int(seeds[i])
        del sub_parameters["multiple"]
        json_pretty_dump(
            sub_parameters, os.path.join(sub_scenario_inputs_folder, PARAMETERS_FILENAME)
        )

        # create symlinks to original inputs
        for input_file in os.listdir(simulation_scenario.inputs_folder):
            if input_file == PARAMETERS_FILENAME:
                continue
            input_filepath = os.path.join("..", "..", "..", INPUT_FOLDER_NAME, input_file)
            os.symlink(input_filepath, os.path.join(sub_scenario_inputs_folder, input_file))

    logging.info("End of sub scenarios creation\n")

    return scenario_paths
