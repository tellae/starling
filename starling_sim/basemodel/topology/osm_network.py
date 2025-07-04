import logging
import osmnx as ox
import numpy as np
import pandas as pd

from starling_sim.basemodel.topology.topology import Topology
from starling_sim.utils.utils import json_load
from starling_sim.basemodel.topology.network_speeds import ConstantSpeed, SpeedByHighwayType, SpeedByEdge


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

        # subclass of NetworkEdgeSpeed used to evaluate edge speed
        self.network_speed = None

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
                self.graph = ox.load_graphml(self.network_file)

        if self.speed_file is None:
            logging.error("No speed file provided for topology initialisation")
            raise ValueError("Speed file provided is {}".format(self.network_file))
        else:
            logging.debug(
                "Importing graph speeds for mode '{}' from file {}".format(
                    self.mode, self.speed_file
                )
            )
            network_speed = None
            if isinstance(self.speed_file, int) or isinstance(self.speed_file, float):
                network_speed = ConstantSpeed(self.speed_file)
            elif isinstance(self.speed_file, str):
                if self.speed_file.endswith(".json"):
                    network_speed = SpeedByHighwayType(self.speed_file)
                elif self.speed_file.endswith(".csv"):
                    network_speed = SpeedByEdge(self.speed_file)

            if network_speed is None:
                raise ValueError(f"Unsupported parameter type/format for network speed: {self.speed_file}")

            self.network_speed = network_speed

    def add_time_and_length(self, u, v, d):
        """
        Set the edge time and length using the speeds dict and OSM length values.

        Speeds are set according to OSM 'highway' attribute.
        If the attribute's value doesn't correspond to any key, use the 'other' key.

        :param u:
        :param v:
        :param d:
        """

        # evaluate edge speed (in km/h)
        speed = self.network_speed(u, v, d)

        # store speed
        d["speed"] = speed

        # round the length value
        d[self.LENGTH_ATTRIBUTE] = round(d[self.LENGTH_ATTRIBUTE])

        # time is valued in seconds
        d[self.TIME_ATTRIBUTE] = round(3600 * ((d[self.LENGTH_ATTRIBUTE] / 1000) / speed))

    def position_localisation(self, position):
        return [self.graph.nodes[position]["y"], self.graph.nodes[position]["x"]]

    def nearest_position(self, localisation):
        return ox.distance.nearest_nodes(self.graph, float(localisation[1]), float(localisation[0]))

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, return_dist=False):
        # convert coordinate lists to np.array
        x_array = np.array(x_coordinates, dtype=np.float32)
        y_array = np.array(y_coordinates, dtype=np.float32)

        # we use osmnx nearest_nodes function
        return ox.distance.nearest_nodes(self.graph, x_array, y_array, return_dist=return_dist)
