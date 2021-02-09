"""
This python script imports OSM graphs from the given arguments.

OSM graphs are used in the simulation to represent the networks where agents will evolve.
They must be provided in the parameters file in the "topologies" field.

The imports are realised using the import_osm_graph function from starling_sim.utils.utils.
Graphs are saved directly in :data:`~starling_sim.utils.paths.osm_graphs_folder`.

Run the script with ``-h`` (or ``--help``) to see the execution options.
The user must at least provide coordinates of the center point and a distance from this point.

Example of command line:

.. code-block:: bash

    python3 -m tools.generate_osm_graph -p -1.2 47.4 -d 3000

"""

from starling_sim.utils.utils import import_osm_graph
import argparse


if __name__ == "__main__":

    # command line parser

    parser = argparse.ArgumentParser(description="Script for the generation of OSM graph (bbox)")

    parser.add_argument("-p", "--point",
                        help="GPS coordinates of the center point of the graph (lon, lat)",
                        type=float,
                        metavar=("lon", "lat"),
                        nargs=2,
                        required=True)

    parser.add_argument("-d", "--distance",
                        help="distance (in meters) from the center point (dist_type='bbox')",
                        type=int,
                        metavar="dist",
                        required=True)

    parser.add_argument("-m", "--mode",
                        help="network type to be extracted. Default is 'walk'",
                        type=str,
                        default="walk",
                        nargs="?")

    parser.add_argument("-ns", "--no-simplify",
                        help="avoid simplifying the graph",
                        action="store_false",
                        dest="simplify")

    parser.add_argument("-o", "--outfile",
                        help="name of the output file. Default is '[S]Gmode_lon_lat_distance.graphml'",
                        type=str,
                        default=None,
                        nargs="?")

    # parse arguments
    input_args = parser.parse_args()

    # generate and save osm graph
    import_osm_graph(point=input_args.point, dist=input_args.distance, mode=input_args.mode,
                     simplify=input_args.simplify, outfile=input_args.outfile)
