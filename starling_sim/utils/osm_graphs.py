"""
This module contains functions for generating OSM graphs using various methods.

OSM graphs are used in the simulation to represent the networks where agents will evolve.
They must be provided in the parameters file in the "topologies" field.

The available import methods are:

- **place**: uses a query and optionally a result number. You can test the results of a query on `OpenStreetMap <https://www.openstreetmap.org>`_.
- **point**: uses a center point and a distance. The distance is used to draw a bbox around the center point.
- **polygon**: uses a polygon as a list of (lon, lat) coordinates.

Import functions are based on the OSMnX library, especially its functions graph_from_place, graph_from_point
and graph_from_polygon.

Graphs are saved directly in :data:`~starling_sim.utils.paths.osm_graphs_folder`.

The generation functions are accessible through the `starling-sim` command line. Run the following command for more information:

.. code-block:: bash

    starling-sim osm-graph -h

"""


import osmnx as ox
import subprocess
import json
import argparse
from starling_sim.utils.paths import osm_graphs_folder
from starling_sim.utils.utils import shapely_polygon_from_points, str_or_json_loads


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


# command line utils

def generate_osm_graph_from_args(args):
    """
    Execute import_osm_graph with parser args.

    :param args: argparse input args
    """
    import_osm_graph(
        args.method,
        args.network,
        args.simplify,
        query=args.query,
        which_result=args.which_result,
        point=args.point,
        dist=args.dist,
        polygon=args.polygon,
        outfile=args.outfile,
    )

def add_osm_graph_action(subparsers):
    """
    Add a subparser for the osm-graph action.

    :param subparsers: argparse subparsers
    """

    osm_graph_parser = subparsers.add_parser(
        "osm-graph",
        description="Generate a NetworkX graph from OpenStreetMap",
        help="Generate a NetworkX graph from OpenStreetMap",
        epilog="Examples:\n\n"
               "starling-sim osm-graph -n walk place 'Nantes, France'\n"
               "starling-sim osm-graph -n bike point --point -1.2 47.4 -dist 3000\n"
               "starling-sim osm-graph -n drive -o triangle.graphml polygon "
               "'[[-1.55, 47.20], [-1.55, 47.21], [-1.56, 47.20], [-1.55, 47.20]]'\n\n"
               "For more details about the import functions, see the documentation "
               "of the OSMnX library and its graph import functions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


    osm_graph_parser.add_argument(
        "-n", "--network", help="network type to be extracted", type=str, required=True
    )

    osm_graph_parser.add_argument(
        "-ns",
        "--no-simplify",
        help="avoid graph simplification",
        action="store_false",
        dest="simplify",
    )

    osm_graph_parser.add_argument(
        "-o",
        "--outfile",
        help="name of the output file. If a '.bz2' extension is detected, the graph is compressed.",
        type=str,
        default=None,
        nargs="?",
    )

    osm_subparsers = osm_graph_parser.add_subparsers(
        required=True, help="Import method, corresponds to an import method of OSMnX", dest="method"
    )

    # import the graph from an OSM query
    query_parser = osm_subparsers.add_parser(
        "place",
        description="Import the graph from a string query describing a place or area. Uses osmnx.graph_from_place",
        help="Import the graph from a string query describing a place or area",
    )

    query_parser.add_argument(
        "query",
        help="string, dict or list describing a place (must be geocodable). You can test the results of a query at https://www.openstreetmap.org",
        type=str_or_json_loads
    )

    query_parser.add_argument(
        "--which-result",
        help="integer (> 0) describing which geocoding result to use",
        dest="which_result"
    )

    # import the graph from a point and distance
    point_parser = osm_subparsers.add_parser(
        "point",
        description="Import the graph from a bbox around a point. Uses osmnx.graph_from_point",
        help="Import the graph from a bbox around a point",
    )

    point_parser.add_argument(
        "-p",
        "--point",
        help="GPS coordinates of the center point of the graph (lon, lat)",
        required=True,
        type=float,
        metavar=("lon", "lat"),
        nargs=2
    )

    point_parser.add_argument(
        "-d",
        "--dist",
        help="distance (in meters) from the center point (dist_type='bbox')",
        required=True,
        type=int
    )

    # import the graph from a polygon
    polygon_parser = osm_subparsers.add_parser(
        "polygon",
        description="Import the graph from a polygon. Uses osmnx.graph_from_polygon",
        help="Import the graph from a polygon",
    )

    polygon_parser.add_argument(
        "polygon",
        help="list of (lon, lat) points describing a polygon (without holes)." " Avoid whitespaces or use quotes",
        type=json.loads,
    )

    # store exec function in parser
    osm_graph_parser.set_defaults(func=generate_osm_graph_from_args)
