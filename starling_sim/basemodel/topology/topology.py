from starling_sim.basemodel.topology.simple_time_weight import SimpleTimeWeight
from starling_sim.basemodel.topology.bike_weight_osm import BikeWeightOSM

import networkx as nx
from abc import ABC

# this shouldn't be here, doesn't allow adding new weights
NETWORK_WEIGHT_CLASSES = {"simple_time_weight": SimpleTimeWeight, "bike_weight_osm": BikeWeightOSM}


class Topology(ABC):
    """
    This abstract class describes a network of the simulation.

    Networks are stored as NetworkX graphs.
    """

    TIME_ATTRIBUTE = "time"
    LENGTH_ATTRIBUTE = "length"

    def __init__(self, transport_mode, weight_class=None, store_paths=False):
        """
        The constructor should not instantiate the topology data structure,
        which is done in the setup method
        """

        # transport mode described by this topology
        self.mode = transport_mode

        # networkx graph representation of the network
        self.graph = None

        # weight class
        self.weight = None
        self.init_weight(weight_class)
        self.parameters_hash = {
            self.weight.get_parameters_hash(
                self.weight.default_parameters
            ): self.weight.default_parameters
        }

        # paths storage
        self.store_paths = store_paths
        self.paths = {}
        self.shortest_path_count = 0

    # graph initialisation and setup

    def init_weight(self, weight_class):
        """
        Initialise the weight class.

        :param weight_class: weight class key
        """

        if weight_class is not None:
            if weight_class not in NETWORK_WEIGHT_CLASSES:
                raise ValueError("Unknown weight class key '{}'".format(weight_class))
        else:
            weight_class = "simple_time_weight"

        self.weight = NETWORK_WEIGHT_CLASSES[weight_class].__new__(
            NETWORK_WEIGHT_CLASSES[weight_class]
        )
        self.weight.__init__(self)

    def setup(self):
        """
        Prepare the topology for the simulation run.

        Initialise the network graph, set relevant attributes
        and compute weight values for path evaluation.
        """

        self.init_graph()

        for u, v, d in self.graph.edges(data=True):

            self.weight.pre_process_edge(u, v, d)

            self.add_time_and_length(u, v, d)

            self.compute_weights(u, v, d)

    def init_graph(self):
        """
        Initialise the network graph from any data source.
        """
        raise NotImplementedError()

    def add_time_and_length(self, u, v, d):
        """
        Set the TIME_ATTRIBUTE and LENGTH_ATTRIBUTE attributes on the graph edge.

        :param u: edge origin
        :param v: edge destination
        :param d: edge data
        """
        raise NotImplementedError()

    def compute_weights(self, u, v, d):
        """
        For each edge, set a value for each weight hash.

        :param u:
        :param v:
        :param d:
        """

        for param_hash in self.parameters_hash:
            parameters = self.parameters_hash[param_hash]
            d[param_hash] = self.weight.compute_edge_weight(u, v, d, parameters)

    # path evaluation

    def shortest_path_length(self, origin, destination, parameters):
        _, duration, _ = self.dijkstra_shortest_path_and_length(origin, destination, parameters)
        return duration

    def dijkstra_shortest_path_and_length(
        self, origin, destination, parameters, return_weight=False
    ):
        """
        Find the path from origin to destination with minimum the total weight.

        Get the hash corresponding to the parameters and call Dijkstra's algorithm
        on the corresponding weight values.

        Raises an exception if origin or destination is None,
        instead of computing all shortest path (which is what NetworkX would do)

        :param origin: origin position
        :param destination: destination position
        :param parameters: parameters defining the utility
        :param return_weight: also return the total weight

        :return: path (list of positions), duration, length
        """

        if origin is None or destination is None:
            raise ValueError("Cannot evaluate path, origin or destination is None")

        # evaluate the weight parameters
        if parameters is None:
            parameters = {}
        else:
            raise ValueError("Weight parameters are not accepted yet, please set them to None")
        for default in self.weight.default_parameters:
            if default not in parameters:
                parameters[default] = self.weight.default_parameters[default]
        param_hash = self.weight.get_parameters_hash(parameters)

        od = (origin, destination)

        if self.store_paths and od in self.paths[param_hash]:
            path, duration, length, total_weight = self.paths[param_hash][od]
        else:
            self.shortest_path_count += 1

            total_weight, path = nx.single_source_dijkstra(
                self.graph, origin, target=destination, weight=param_hash
            )

            duration, length = self.evaluate_path_duration_and_length(path)

            if self.store_paths:
                self.paths[param_hash][od] = path, duration, length, total_weight

        if return_weight:
            return path, duration, length, total_weight
        else:
            return path, duration, length

    def compute_dijkstra_path(self, origin, destination, weight):
        length, path = nx.single_source_dijkstra(
            self.graph, origin, target=destination, weight=weight
        )
        return path, length

    def evaluate_path_duration_and_length(self, path):

        total_duration = 0
        total_length = 0

        if len(path) < 1:
            raise ValueError("Cannot evaluate duration/length of path shorter than 2")

        current_position = path[0]

        for next_position in path[1:]:
            total_duration += self.get_edge_data(
                current_position, next_position, self.TIME_ATTRIBUTE
            )
            total_length += self.get_edge_data(
                current_position, next_position, self.LENGTH_ATTRIBUTE
            )
            current_position = next_position

        return total_duration, total_length

    # get graph information

    def get_positions(self):
        """
        Return the list of all topology positions

        :return: list of positions
        """

        return self.graph.nodes

    def get_edge_data(self, node1, node2, data):
        """
        Return the corresponding edge information

        :param node1: node of the topology
        :param node2: node of the topology
        :param data: requested attribute
        :return: data information of the edge
        """

        d = self.graph.get_edge_data(node1, node2)

        # TODO : check why min

        return min(attr.get(data) for attr in d.values())

    def position_localisation(self, position):
        """
        Return the localisation [lat, lon] of the position

        :param position: position in the topology

        :return: list [lat, lon]
        """
        raise NotImplementedError()

    def nearest_position(self, localisation):
        """
        Return the nearest position to given localisation (lat, lon)

        :param localisation: (lat, lon) tuple
        :return: position
        """
        raise NotImplementedError()

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, method=None):
        """
        Return the graph nodes nearest to a list of points.

        This method should allow a faster computation than multiple nearest_position calls.

        :param x_coordinates: list of X coordinates of the localisations (lon in GPS)
        :param y_coordinates: list of Y coordinates of the localisations (lat in GPS)
        :param method: name of the method used for the computation
        :return: list of nearest nodes
        """
        raise NotImplementedError()
