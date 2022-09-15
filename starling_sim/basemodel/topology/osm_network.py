import logging
import osmnx as ox
import numpy as np

from starling_sim.basemodel.topology.topology import Topology
from starling_sim.utils.paths import graph_speeds_folder
from starling_sim.utils.utils import json_load, osm_graph_from_file


class OSMNetwork(Topology):
    """
    Open Street Map network topology
    """

    def __init__(
        self,
        transport_mode,
        weight_class=None,
        store_paths=False,
        network_file=None,
        speed_file=None,
        graph=None,
    ):
        """
        Create the topology structure, without initializing the network

        :param transport_mode: type of the given network
        :param weight_class: class used for defining weight
        :param store_paths: boolean indicating if shortest paths should be stored
        :param network_file: graphml file for network import
        :param speed_file: json file containing the link speeds
        :param graph: graph object for direct initialisation
        """
        super().__init__(transport_mode, weight_class=weight_class, store_paths=store_paths)

        self.network_file = network_file
        self.speed_file = speed_file

        self.graph = graph
        self.speeds = None

    def init_graph(self):
        if self.graph is None:

            if self.network_file is None:
                logging.error("No network file provided for topology initialisation")
                raise ValueError("Network file provided is {}".format(self.network_file))
            else:
                logging.debug(
                    "Importing OSM graph for mode '{}' from file {}".format(
                        self.mode, self.network_file
                    )
                )
                self.graph = osm_graph_from_file(self.network_file)

        if self.speed_file is None:
            logging.error("No speed file provided for topology initialisation")
            raise ValueError("Speed file provided is {}".format(self.network_file))
        else:
            logging.debug(
                "Importing graph speeds for mode '{}' from file {}".format(
                    self.mode, self.speed_file
                )
            )
            self.speeds = json_load(graph_speeds_folder() + self.speed_file)

    def add_time_and_length(self, u, v, d):
        """
        Set the edge time and length using the speeds dict and OSM length values.

        Speeds are set according to OSM 'highway' attribute.
        If the attribute's value doesn't correspond to any key, use the 'other' key.

        :param u:
        :param v:
        :param d:
        """

        if isinstance(d["highway"], list):
            d["highway"] = d["highway"][0]

        # differentiate speeds among the link types
        if d["highway"] in self.speeds:
            speed = self.speeds[d["highway"]]["speed"]
        else:
            speed = self.speeds["other"]["speed"]

        d["speed"] = speed

        # round the length values
        d[self.LENGTH_ATTRIBUTE] = round(d[self.LENGTH_ATTRIBUTE])

        # time is valued in seconds
        d[self.TIME_ATTRIBUTE] = round(3600 * ((d[self.LENGTH_ATTRIBUTE] / 1000) / speed))

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
