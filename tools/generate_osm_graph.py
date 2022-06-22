"""
This python script imports OSM graphs from the given arguments.

OSM graphs are used in the simulation to represent the networks where agents will evolve.
They must be provided in the parameters file in the "topologies" field.

Imports are realised using the OSMnX library, with the functions graph_from_place, graph_from_point
and graph_from_polygon. The relevant information must be provided when running the command:

- Import from **place**: provide a query and optionally a result number. You can test the results of a query on `OpenStreetMap <https://www.openstreetmap.org>`_.

- Import from **point**: provide a center point and a distance. The distance is used to draw a bbox around the center point.

- Import from **polygon**: provide a polygon as a list of (lon, lat) coordinates, and a filename.

Examples of command lines:

.. code-block:: bash

    python3 -m tools.generate_osm_graph place --query 'Nantes, France' -n walk

.. code-block:: bash

    python3 -m tools.generate_osm_graph point --point -1.2 47.4 -d 3000 -n bike

.. code-block:: bash

    python3 -m tools.generate_osm_graph polygon -n drive -o triangle.graphml \
--polygon '[[-1.55, 47.20], [-1.55, 47.21], [-1.56, 47.20], [-1.55, 47.20]]'

Run the script with ``-h`` (or ``--help``) to see the execution options.

Graphs are saved directly in :data:`~starling_sim.utils.paths.osm_graphs_folder`.
"""

from starling_sim.utils.utils import import_osm_graph
import argparse
import json


def str_or_json_loads(string):
    """
    Try to convert the string into a list or a dict if it contains [ or {.

    :param string:

    :raises ValueError:

    :return: the list or dict from the string, or the original string
    """

    try:
        if "[" in string or "{" in string:
            return json.loads(string)
        else:
            return string
    except json.decoder.JSONDecodeError as e:
        raise ValueError(str(e))


if __name__ == "__main__":

    # command line parser

    parser = argparse.ArgumentParser(
        description="Script for the generation of OSM graph",
        epilog="Examples:\n\n"
        "python3 -m tools.generate_osm_graph place --query 'Nantes, France' -n walk\n"
        "python3 -m tools.generate_osm_graph point --point -1.2 47.4 -d 3000 -n bike\n"
        "python3 -m tools.generate_osm_graph polygon -n drive -o triangle.graphml "
        "--polygon '[[-1.55, 47.20], [-1.55, 47.21], [-1.56, 47.20], [-1.55, 47.20]]'\n\n"
        "For more details about the import functions, see the documentation "
        "of the OSMnX library and its graph import functions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "method",
        help="import method for the OSM graph. Corresponds to an import method of OSMnX."
        " If 'place', provide a query, and optionally a result number (which-result)."
        " If 'point', provide a point and distance."
        " If 'polygon', provide a polygon and an outfile name.",
        choices=["place", "point", "polygon"],
    )

    parser.add_argument(
        "-n", "--network", help="network type to be extracted", type=str, required=True
    )

    parser.add_argument(
        "--query",
        help="string, dict or list describing a place (must be geocodable)",
        type=str_or_json_loads,
        default=None,
    )

    parser.add_argument(
        "--which-result",
        help="integer (> 0) describing which geocoding result to use",
        dest="which_result",
        default=None,
    )

    parser.add_argument(
        "--point",
        help="GPS coordinates of the center point of the graph (lon, lat)",
        type=float,
        metavar=("lon", "lat"),
        nargs=2,
        default=None,
    )

    parser.add_argument(
        "--dist",
        help="distance (in meters) from the center point (dist_type='bbox')",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--polygon",
        help="list of (lon, lat) points describing a polygon." " Avoid whitespaces or use quotes",
        type=json.loads,
        default=None,
    )

    parser.add_argument(
        "-ns",
        "--no-simplify",
        help="avoid graph simplification",
        action="store_false",
        dest="simplify",
    )

    parser.add_argument(
        "-o",
        "--outfile",
        help="name of the output file. If a '.bz2' extension is detected, the graph is compressed.",
        type=str,
        default=None,
        nargs="?",
    )

    # parse arguments
    input_args = parser.parse_args()

    # generate and save osm graph
    import_osm_graph(
        input_args.method,
        input_args.network,
        input_args.simplify,
        query=input_args.query,
        which_result=input_args.which_result,
        point=input_args.point,
        dist=input_args.dist,
        polygon=input_args.polygon,
        outfile=input_args.outfile,
    )
