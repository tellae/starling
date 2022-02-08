import os
import networkx as ntx
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
        self.graph = ntx.complete_graph(nb_stations, ntx.MultiDiGraph())
        self.graph.add_edges_from([(i,i) for i in range(nb_stations)])
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

    def nearest_position(self, loc):
        return [0]

    def localisations_nearest_nodes(self, x, y, method="Null"):
        return [0]
