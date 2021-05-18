import logging
import osmnx as ox
import networkx as nx
import numpy as np

from starling_sim.basemodel.topology.topology import Topology
from starling_sim.utils.paths import graph_speeds_folder
from starling_sim.utils.utils import json_load, osm_graph_from_file


class OSMNetwork(Topology):
    """
    Open Street Map network topology

    Stores the network as a networkx graph
    """

    IMPORT_ERROR = "Cannot import OSM network : "

    def __init__(self, transport_mode, network_file=None, speed_file=None, graph=None, store_paths=None):
        """
        Create the topology structure, without initializing the network

        :param transport_mode: type of the given network
        :param network_file: graphml file for network import
        :param speed_file: json file containing the link speeds
        :param graph: graph object for direct initialisation
        :param store_paths: boolean indicating if shortest paths should be stored
        """
        super().__init__()

        self.mode = transport_mode
        self.network_file = network_file
        self.speed_file = speed_file

        self.graph = graph
        self.speeds = None

        # paths storing
        if store_paths is None:
            self.store_paths = False
        else:
            self.store_paths = store_paths
        self.paths = {"time": {}, "length": {}}

        # TODO : replace with a decorator ?
        self.shortest_path_count = 0

    def setup(self):
        """
        Prepare the class for the simulation

        Import the OSM graph, set the speeds
        """

        if self.graph is None:

            if self.network_file is None:
                logging.error("No network file provided for topology initialisation")
                raise ValueError("Network file provided is {}".format(self.network_file))

            else:
                logging.debug("Importing OSM graph for mode '{}' from file {}".format(self.mode, self.network_file))
                self.graph = osm_graph_from_file(self.network_file)

        if self.speed_file is None:
            logging.error("No speed file provided for topology initialisation")
            raise ValueError("Speed file provided is {}".format(self.network_file))
        else:
            logging.debug("Importing graph speeds for mode '{}' from file {}".format(self.mode, self.speed_file))
            speeds = json_load(graph_speeds_folder() + self.speed_file)
            self.update_speeds(speeds)

    def update(self):
        """
        Update of the osm network during the simulation
        """

        # for now we don't update the network
        pass

    def get_positions(self):
        """
        Return the list of all topology positions

        :return: list of all graph nodes
        """

        return self.graph.nodes

    # group of static methods for the network management using osmnx and networkx

    def update_speeds(self, speeds):
        """
        Set the speed values according to the given dictionary, and then the time values

        :param speeds: speed dict {<link_type>: {speed: <speed_value>, ...}
        """

        for u, v, d in self.graph.edges(data=True):

            if isinstance(d["highway"], list):
                d["highway"] = d["highway"][0]

            # differentiate speeds among the link types
            if d["highway"] in speeds:
                speed = speeds[d["highway"]]["speed"]
            else:
                speed = speeds["other"]["speed"]

            d["speed"] = speed

            # round the length values
            d["length"] = round(d["length"])

            # time is valued in seconds
            d["time"] = round(3600 * ((d['length']/1000) / speed))

        self.speeds = speeds

    def shortest_path(self, origin, destination, dimension):
        """
        Compute the shortest path between origin and destination

        Raises an exception if origin or destination is None,
        instead of computing all shortest path (this is what nx would do)

        :param origin: origin node
        :param destination: destination node
        :param dimension: type of 'length' to consider (distance, time..)
        :return: shortest path : list of nodes, origin and destination included
        """

        if origin is None or destination is None:
            logging.error("Origin or destination provided for shortest path is None")
            raise ValueError((origin, destination))

        path, _ = self.dijkstra_shortest_path_and_length(origin, destination, dimension)

        return path

    def shortest_path_length(self, origin, destination, dimension):
        """
        Compute the length of the shortest path between origin and destination

        :param origin:
        :param destination:
        :param dimension:
        :return: length of the shortest path
        """

        if origin is None or destination is None:
            logging.error("Origin or destination provided for shortest path is None")
            raise ValueError((origin, destination))

        _, length = self.dijkstra_shortest_path_and_length(origin, destination, dimension)

        return length

    def dijkstra_shortest_path_and_length(self, origin, destination, dimension):
        """
        Compute a shortest path and its length using Dijkstra's algorithm

        :param origin: source node
        :param destination: target node
        :param dimension: weight used for computing the path length
        :return: tuple (path, path_length)
        """

        od = (origin, destination)

        if self.store_paths and od in self.paths[dimension]:
            return self.paths[dimension][od][0], self.paths[dimension][od][1]
        else:

            self.shortest_path_count += 1

            length, path = nx.single_source_dijkstra(self.graph, origin,
                                                     target=destination, weight=dimension)

            if self.store_paths:
                self.paths[dimension][od] = path, length

            return path, length

    def position_localisation(self, position):

        return [self.graph.nodes[position]["y"], self.graph.nodes[position]["x"]]

    def nearest_position(self, localisation):

        position = ox.get_nearest_node(self.graph, (float(localisation[0]), float(localisation[1])))
        return position

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, method="balltree"):

        # convert coordinate lists to np.array
        x_array = np.array(x_coordinates, dtype=np.float32)
        y_array = np.array(y_coordinates, dtype=np.float32)

        # we use osmnx get_nearest_nodes function, with method='balltree' [uses scikit_learn]
        return ox.get_nearest_nodes(self.graph, x_array, y_array, method=method)

    # TODO : add a check ?
    def get_edge_data(self, node1, node2, data):

        d = self.graph.get_edge_data(node1, node2)

        return min(attr.get(data) for attr in d.values())
