import os
import networkx as nx
import numpy as np
import scipy.io as sio

from starling_sim.basemodel.topology.topology import Topology


class theoricNetwork(Topology):
    """
    """

    def __init__(self, transport_mode, geography_file, weight_class=None, store_paths=False):
        super().__init__(transport_mode, weight_class=weight_class, store_paths=store_paths)
        self.geography_file = os.path.join("data/environment/osm_graphs",geography_file)
        self.geography = sio.loadmat(self.geography_file)

    def init_graph(self):
        nb_stations = len(self.geography["C"])
        self.graph = nx.complete_graph(nb_stations, nx.MultiDiGraph())
        self.graph.add_edges_from([(i, i) for i in range(nb_stations)])
        time = "WalkingTime" if self.mode == "walk" else "RidingTime"
        for idx, w in np.ndenumerate(self.geography[time]):
            val = int(w*60*30)
            self.graph.edges[idx[0], idx[1], 0]["time"] = val
            self.graph.edges[idx[0], idx[1], 0]["length"] = val
            self.graph.edges[idx[1], idx[0], 0]["time"] = val
            self.graph.edges[idx[1], idx[0], 0]["length"] = val

    def add_time_and_length(self, u, v, d):
        pass

    def position_localisation(self, position):
        return [0,0]

    def nearest_position(self, localisation):
        return [0]

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, method=None):
        return [0]

    def dijkstra_shortest_path_and_length(self, origin, destination, parameters, return_weight=False):
        """
        Overriding from Topology
        :param origin: origin position
        :param destination: destination position
        :param parameters: parameters defining the utility
        :param return_weight: also return the total weight

        :return: path (list of positions), duration, length
        """

        if origin is None or destination is None:
            raise ValueError("Cannot evaluate path, origin or destination is None")

        # evaluate the weight parameters
        parameters = {}

        for default in self.weight.default_parameters:
            if default not in parameters:
                parameters[default] = self.weight.default_parameters[default]

        self.shortest_path_count += 1

        total_weight, path = self.get_edge_data(origin, destination, "time"), [origin, destination]
        duration, length = self.evaluate_path_duration_and_length(path)

        if return_weight:
            return path, duration, length, total_weight
        return path, duration, length

    def compute_dijkstra_path(self, origin, destination, weight):
        length, path = self.get_edge_data(origin, destination, "length"), [origin, destination]
        return path, length