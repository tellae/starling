import logging
import osmnx as ox
import networkx as nx
import numpy as np

from starling_sim.basemodel.topology.topology import Topology


class EmptyNetwork(Topology):
    """
    An initially empty topology
    """

    def __init__(self, transport_mode, weight_class=None, store_paths=False):
        """
        Create the topology structure, without initializing the network

        :param transport_mode: type of the given network
        :param weight_class: class used for defining weight
        :param store_paths: boolean indicating if shortest paths should be stored
        """
        super().__init__(transport_mode, weight_class=weight_class, store_paths=store_paths)

        self.graph = None
        self.speeds = None

    def init_graph(self):
        # initialise an empty graph object
        logging.debug("Generating an empty graph for mode '{}'".format(self.mode))
        self.graph = nx.MultiDiGraph()

    def add_time_and_length(self, u, v, d):
        pass

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
