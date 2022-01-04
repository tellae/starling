from starling_sim.basemodel.topology.simple_time_disutility import SimpleTimeDisutility

import networkx as nx
from abc import ABC


class Topology(ABC):
    """
    This abstract class describes a network of the simulation.

    Networks are stored as NetworkX graphs.
    """

    def __init__(self, transport_mode, store_paths=False):
        """
        The constructor should not instantiate the topology data structure,
        which is done in the setup method
        """

        # transport mode described by this topology
        self.mode = transport_mode

        # networkx graph representation of the network
        self.graph = None

        # disutility class
        self.disutility = SimpleTimeDisutility()
        self.parameters_hash = {
            "hash": {}
        }

        # paths storage
        self.store_paths = store_paths
        self.paths = {}
        self.shortest_path_count = 0

    # graph initialisation and setup

    def setup(self):
        """
        Prepare the topology for the simulation run.

        Initialise the network graph, set relevant attributes
        and compute disutility values for path evaluation.
        """

        self.init_graph()

        for u, v, d in self.graph.edges(data=True):

            self.disutility.pre_process_edge(u, v, d)

            self.add_time_and_length(u, v, d)

            self.compute_disutilities(u, v, d)

    def init_graph(self):
        pass

    def add_time_and_length(self, u, v, d):
        pass

    def compute_disutilities(self, u, v, d):
        """
        For each edge, set a value for each disutility hash.

        :param u:
        :param v:
        :param d:
        """

        for param_hash in self.parameters_hash:
            parameters = self.parameters_hash[param_hash]
            d[param_hash] = self.disutility.compute_edge_disutility(u, v, d, parameters)

    # TODO : remove
    def update(self):
        """
        Update the topology state

        :return:
        """

    # path evaluation

    def shortest_path_length(self, origin, destination, parameters):
        _, duration, _ = self.dijkstra_shortest_path_and_length(origin, destination, parameters)
        return duration

    def dijkstra_shortest_path_and_length(self, origin, destination, parameters, return_disutility=False):
        """
        Find the path from origin to destination with minimum the total disutility.

        Get the hash corresponding to the parameters and call Dijkstra's algorithm
        on the corresponding utility values.

        Raises an exception if origin or destination is None,
        instead of computing all shortest path (which is what NetworkX would do)

        :param origin: origin position
        :param destination: destination position
        :param parameters: parameters defining the utility
        :param return_disutility: also return the total disutility

        :return: path (list of positions), duration, length
        """

        if origin is None or destination is None:
            raise ValueError("Cannot evaluate path, origin or destination is None")

        param_hash = self.get_parameters_hash(parameters)

        od = (origin, destination)

        if self.store_paths and od in self.paths[param_hash]:
            path, duration, length, disutility = self.paths[param_hash][od]
        else:
            self.shortest_path_count += 1

            disutility, path = nx.single_source_dijkstra(self.graph, origin, target=destination,
                                                         weight=param_hash)

            duration, length = self.evaluate_path_duration_and_length(path)

            if self.store_paths:
                self.paths[param_hash][od] = path, duration, length, disutility

        if return_disutility:
            return path, duration, length, disutility
        else:
            return path, duration, length

    def compute_dijkstra_path(self, origin, destination, weight):
        length, path = nx.single_source_dijkstra(self.graph, origin, target=destination, weight=weight)
        return path, length

    def evaluate_path_duration_and_length(self, path):

        total_duration = 0
        total_length = 0

        if len(path) < 1:
            raise ValueError("Cannot evaluate duration/length of path shorter than 2")

        current_position = path[0]

        for next_position in path[1:]:
            total_duration += self.get_edge_data(current_position, next_position, "time")
            total_length += self.get_edge_data(current_position, next_position, "length")
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

    def get_parameters_hash(_):
        # TODO
        return "hash"
    get_parameters_hash = staticmethod(get_parameters_hash)
