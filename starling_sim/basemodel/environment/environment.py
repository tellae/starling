import logging
import sys
import hashlib
from starling_sim.basemodel.topology.osm_network import OSMNetwork
from starling_sim.basemodel.topology.empty_network import EmptyNetwork
from starling_sim.utils.config import config
from starling_sim.utils.paths import graph_speeds_folder, osm_graphs_folder
from geopy import distance


class Environment:
    """
    Describes an environment in which the simulation will take place
    """

    def __init__(self, scenario):
        """
        Initialization of the environment, without import of data structures.

        It should be extended for the needs of the chosen environment
        """

        self.sim = None

        # get the 'store_paths' parameter
        if "store_paths" in scenario:
            self._store_paths = scenario["store_paths"]
        else:
            self._store_paths = False

        self._topologies = dict()

        # fill the topologies dict
        topologies_info = scenario["topologies"]

        for mode, info in topologies_info.items():
            self._add_topology(mode, info)

    def __getitem__(self, item):
        return self._topologies[item]

    @property
    def modes(self) -> list:
        """
        List of modes of the environment
        """
        return list(self._topologies.keys())

    def setup(self, simulation_model):
        """
        Setup the environment for the simulation run.

        Set the simulation model attribute and
        prepare the environment for the simulation

        :param simulation_model: simulation model
        """

        self.sim = simulation_model
        for topology in self._topologies.values():
            topology.setup()

    def _add_topology(self, mode, info):
        """
        Add a new topology to the environment.

        This method adds an instance of a Topology subclass to the self._topologies dict.

        :param mode: name of the mode
        :param info: topology initialisation info
        """

        # see if paths of this topology should be stored
        if isinstance(self._store_paths, dict):
            if mode not in self._store_paths:
                raise ValueError("Missing topology in parameter 'store_paths'")
            else:
                store = self._store_paths[mode]
        else:
            store = self._store_paths

        weight_class = None

        if info is None:
            topology = EmptyNetwork(mode, store_paths=store)
        else:
            # fetch init info from parameters
            if isinstance(info, dict):
                network_info = info["graph"]
                speeds_info = info["speeds"]
                weight_class = info.get("weight", None)
                network_class = info.get("network_class", "OSMNetwork")
            elif isinstance(info, list):  # array specification is deprecated
                network_info = info[0]
                speeds_info = info[1]
                if len(info) == 3:
                    weight_class = info[2]
                network_class = "OSMNetwork"
            else:
                raise ValueError(f"Unsupported type for '{mode}' topology info: {type(info)}")

            # create the Topology instance
            topology = self._create_topology_instance(mode, network_class, network_info, speeds_info, weight_class, store)

        # add the topology to the topologies dict
        self._topologies[mode] = topology

    def _create_topology_instance(mode, network_class, network_info, speeds_info, weight_class, store_paths):
        """
        Create a new topology instance from the given information.

        Create and return an instance of a Topology subclass describing a mode network.

        :param mode: name of the mode
        :param network_class: Topology subclass used
        :param network_info: data used for graph setup
        :param speeds_info: data used for speeds setup
        :param weight_class: weight class used to define edge weights
        :param store_paths: whether to store paths or not

        :return: instance of a Topology subclass
        """
        if network_class == "OSMNetwork":
            topology = OSMNetwork(
                mode,
                network_file=osm_graphs_folder() + network_info,
                speed_file=graph_speeds_folder() + speeds_info if isinstance(speeds_info, str) else speeds_info,
                store_paths=store_paths,
                weight_class=weight_class,
            )
        else:
            raise ValueError("Unknown network type {}".format(network_class))

        return topology
    _create_topology_instance = staticmethod(_create_topology_instance)

    # def periodic_update_(self, period):
    #     """
    #     Periodically update the simulation environment using the topology update method
    #
    #     :param period: Update period, put 0 for no updates
    #     :return:
    #     """
    #
    #     if period == 0:
    #         return
    #
    #     # Log periodic_update
    #     logging.debug("Start periodical environment update, period=" + period)
    #
    #     while period:
    #
    #         # Wait for period to elapse
    #         yield self.sim.scheduler.timeout(period)
    #
    #         # Log new update
    #         logging.debug("Environment update")
    #
    #         # Update
    #         for topology in self.topologies.values():
    #             topology.update()

    # environment utils

    def compute_route_data(self, route, duration, origin, destination, parameters, mode):
        """
        Compute a route data from the given parameters

        :param route: list of consecutive nodes in the environment.
            If None, a shortest path from <origin> to <destination> is computed
        :param duration: total duration of the route execution.
            If None, use the "time" links of the environment
        :param origin: origin used for the shortest path computation
        :param destination: destination used for the shortest path computation
        :param parameters: agent specific parameters used for path evaluation
        :param mode: mode of the move
        :return: route_data={"route": position_list, "length": length_list, "time": time_list}
        """

        topology = self._topologies[mode]

        time = None
        if route is None:
            route, time, length = topology.dijkstra_shortest_path_and_length(
                origin, destination, parameters
            )

        return topology.evaluate_route_data(route, duration=duration, durations_sum_to=time)

    def compute_shaped_route(self, operator, shape_table, from_stop, to_stop, duration):
        # create a route_data structure
        route = [operator.stopPoints[from_stop].position]
        lengths = [0]
        length_remainder = 0
        times = [0]
        time_remainder = 0

        # complete it with the shape data
        for index, row in shape_table.iterrows():
            # append localisation to route
            if row["sequence"] == len(shape_table) + 1:
                route.append(operator.stopPoints[to_stop].position)
            else:
                route.append((row["lat"], row["lon"]))

            # append distance to lengths
            length = row["distance"] + length_remainder
            length_remainder = length - int(length)
            lengths.append(int(length))

            # append duration to times
            if row["sequence"] == len(shape_table) + 1:
                time = duration - sum(times)
            else:
                time = duration * row["distance_proportion"] + time_remainder
                time_remainder = time - int(time)
            times.append(int(time))

        # set route information
        route_data = {"route": route, "length": lengths, "time": times}

        return route_data

    def get_position(obj, position_lambda=None):
        # define lambda as obj.position if none is provided
        if position_lambda is None:

            def position_lambda(node):
                return node.position

        return position_lambda(obj)

    get_position = staticmethod(get_position)

    def get_localisation(self, node, mode=None):
        if mode is not None:
            return self[mode].position_localisation(node)
        else:
            agent_localisation = None
            for topology in self._topologies.values():
                agent_localisation = None
                try:
                    return topology.position_localisation(node)

                except KeyError:
                    pass

            return agent_localisation

    def compute_network_distance(self, source, target, mode, parameters=None, return_path=False):
        # if no mode is given, return None
        if mode is None:
            logging.warning("No mode provided for network distance computation")
            return None
        else:
            path, duration, _ = self[mode].dijkstra_shortest_path_and_length(
                source, target, parameters
            )
            if return_path:
                return path, duration
            else:
                return duration

    def compute_euclidean_distance(self, position1, position2, mode=None):
        # get position localisations
        loc1 = self.get_localisation(position1, mode)
        loc2 = self.get_localisation(position2, mode)

        # geopy would return a distance even if one localisation is None, caution
        if loc1 is None or loc2 is None:
            logging.warning(
                "One of the given localisations is None, "
                "computed euclidean distance will be false"
            )

        dist = 1000 * distance.great_circle(loc1, loc2).kilometers

        return dist

    def distance_dict_between(
        self,
        position,
        obj_list,
        distance_type,
        n=None,
        maximum_distance=None,
        position_lambda=None,
        mode=None,
        is_origin=True,
        parameters=None,
        return_path=False,
    ):
        # distance dictionary
        distance_dict = dict()

        # n can't be lesser than the list length
        if n is not None:
            n = min(n, len(obj_list))
            if n == 0:
                return distance_dict

        # compute all distances and fill the dict
        for obj in obj_list:
            if distance_type == "network":
                if is_origin:
                    distance_res = self.compute_network_distance(
                        position,
                        self.get_position(obj, position_lambda),
                        mode,
                        parameters,
                        return_path,
                    )
                else:
                    distance_res = self.compute_network_distance(
                        self.get_position(obj, position_lambda),
                        position,
                        mode,
                        parameters,
                        return_path,
                    )

            elif distance_type == "euclidean":
                distance_res = self.compute_euclidean_distance(
                    position, self.get_position(obj, position_lambda), mode
                )

            else:
                logging.warning("Unknown distance type : " + str(distance_type))
                continue

            is_too_far = False
            if maximum_distance is not None:
                if distance_type == "network" and return_path:
                    is_too_far = distance_res > maximum_distance[1]
                else:
                    is_too_far = distance_res > maximum_distance

            if not is_too_far:
                distance_dict[obj] = distance_res

        # if n is provided, only keep the n closest objects
        if n is not None:
            # sort the objects according to the length
            if distance_type == "network" and return_path:
                dict_list = sorted(list(distance_dict.keys()), key=lambda x: distance_dict[x][1])
            else:
                dict_list = sorted(list(distance_dict.keys()), key=lambda x: distance_dict[x])

            # select the objects to be removed
            dict_list = dict_list[n:]
            for obj in dict_list:
                distance_dict.pop(obj)

        # return the distance dictionary
        return distance_dict

    def euclidean_n_closest(
        self, position, obj_list, n, maximum_distance=None, position_lambda=None
    ):
        distance_dict = self.distance_dict_between(
            position,
            obj_list,
            "euclidean",
            n=n,
            maximum_distance=maximum_distance,
            position_lambda=position_lambda,
        )

        sorted_list = sorted(distance_dict.keys(), key=lambda x: distance_dict[x])

        return sorted_list

    def closest_object(
        self,
        position,
        obj_list,
        is_origin,
        mode,
        parameters=None,
        position_lambda=None,
        return_path=False,
        n=None,
    ):
        """
        Find the object of the list that is closest to the given position.

        We compute network distances between the objects of the list and the given
        position. If the n param is provided, we pre-process the list, and only
        keep the n euclidean closest objects.

        :param position:
        :param obj_list:
        :param is_origin: boolean indicating if the
        :param mode:
        :param parameters:
        :param position_lambda:
        :param return_path:
        :param n:
        :return:
        """

        if not obj_list or n == 0:
            return None

        # look only at the n (euclidean) closest objects
        if n is not None:
            obj_list = self.euclidean_n_closest(
                position=position, obj_list=obj_list, n=n, position_lambda=position_lambda
            )

        # do the network distance computation and keep the closest object
        distance_dict = self.distance_dict_between(
            position,
            obj_list,
            "network",
            position_lambda=position_lambda,
            mode=mode,
            is_origin=is_origin,
            parameters=parameters,
            return_path=return_path,
        )
        if return_path:
            closest_object = min(list(distance_dict.keys()), key=lambda x: distance_dict[x][1])
            return closest_object, distance_dict[closest_object][0]
        else:
            closest_object = min(list(distance_dict.keys()), key=lambda x: distance_dict[x])
            return closest_object

    def nearest_node_in_modes(self, localisation, modes):
        """
        Find the node common to given topologies that is closest (euclidean distance) to the localisation

        :param localisation: (lat, lng) localisation
        :param modes: transport modes, each corresponding to a topology
        :return: closest node that belongs to all topologies
        """

        # get intersection of the topologies nodes
        intersection_set = self.get_common_nodes_of(modes)

        # compute minimum euclidean distance between localisation and nodes
        best_dist = sys.maxsize
        best_node = None

        for node in intersection_set:
            # get the node's localisation
            node_localisation = self[modes[0]].position_localisation(node)

            # compute euclidean distance
            dist = distance.great_circle(localisation, node_localisation)

            # if distance is improved, keep the node
            if dist < best_dist:
                best_dist = dist
                best_node = node

        return best_node

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, modes, return_dist=False):
        """
        Call the topology localisations_nearest_nodes method.

        If a list of modes is provided, consider only nodes that are present
        in all provided topologies.

        If a node as no neighbour, assign None

        :param x_coordinates: list of X coordinates of the localisations
        :param y_coordinates: list of Y coordinates of the localisations
        :param modes: topology modes
        :param return_dist: optionally also return distance between points and nearest nodes

        :return: list of nearest nodes or (nearest_nodes, distances)
        """

        if isinstance(modes, list):
            base_graph = self[modes[0]].graph
            target_graph = base_graph.copy()

            for mode in modes[1:]:
                intersect_graph = self[mode].graph

                target_graph.remove_nodes_from(n for n in base_graph if n not in intersect_graph)

        else:
            target_graph = self[modes].graph

        # if there is no candidate nodes, the nearest node is None
        if len(target_graph.nodes) == 0:
            if isinstance(x_coordinates, list):
                nearest_nodes = [None] * len(x_coordinates)
            else:
                nearest_nodes = None
            if return_dist:
                return nearest_nodes, None
            else:
                return nearest_nodes

        target_topology = OSMNetwork(modes, graph=target_graph)

        return target_topology.localisations_nearest_nodes(
            x_coordinates, y_coordinates, return_dist=return_dist
        )

    def get_common_nodes_of(self, modes):
        """
        Find the nodes that are common to the given topologies

        :param modes: transport modes, each corresponding to a topology
        :return: set object, containing the intersection of the topology nodes
        """

        # initialize the set of common nodes with the first topology nodes
        intersection_set = set(self[modes[0]].graph.nodes)

        # realize the intersection with other topologies
        for mode in modes[1:]:
            intersection_set = intersection_set & set(self[mode].graph.nodes)

        return intersection_set

    def get_object_at(self, position, obj_list, position_lambda=None):
        """
        Return the first agent of the list that is at the given position.

        :param position:
        :param obj_list:
        :param position_lambda:
        :return:
        """

        for obj in obj_list:
            if self.get_position(obj, position_lambda) == position:
                return obj

        return None

    def approximate_path(self, origin, destination, distance_factor, speed, mode=None):
        """
        Approximate the length and time of a trip based on the euclidean distance and speed.

        The computation is based on a factor that is applied to the euclidean distance.

        :param origin: origin position
        :param destination: destination position
        :param distance_factor: value multiplied to euclidean distance to get trip distance.
        :param speed: speed of the travelling agent, in m/s.
            If None, travel time is not computed
        :param mode: position's topology.
            Default is None, then look at all environment's topologies.
        :return: tuple (travel_length, travel_time)
        """

        # compute euclidean distance between origin and destination
        euclidean_distance = self.compute_euclidean_distance(origin, destination, mode)

        # apply distance factor
        travel_length = euclidean_distance * distance_factor
        travel_length = int(travel_length)

        # apply speed (in m/s) to get travel time
        if speed is None:
            travel_time = None
        else:
            travel_time = travel_length / speed
            travel_time = int(travel_time)

        return travel_length, travel_time

    def add_node(self, node_id, properties, modes):
        """
        Add a node id and its properties to the given modes.

        :param node_id: id of the new node
        :param properties: properties of the node
        :param modes: list topologies to add the node to
        """

        for mode in modes:
            topology = self[mode]

            if node_id in topology.graph.nodes:
                # logging.warning("Adding node already in graph {}".format(node_id))
                # TODO : test if properties are same
                continue

            logging.debug("Adding node {} to topology {}".format(node_id, mode))

            topology.graph.add_node(node_id, **properties)

    def add_stops_correspondence(
        self, stops_table, modes, extend_graph, max_distance=config["max_stop_distance"]
    ):
        """
        Add a 'nearest_node' column to the given table containing the stop's nearest environment position.

        If extend_graph is True and the nearest node is further than max_distance from the stop,
        add a new node to the graph.

        :param stops_table: DataFrame with columns ["stop_id", "stop_lat", "stop_lon"]
        :param modes: list of modes
        :param extend_graph: boolean indicating if the graph should be extended when
            nearest nodes are too far
        :param max_distance: maximum node distance before extending graph
        """

        # get the stops coordinate lists
        latitudes = stops_table["stop_lat"].values
        longitudes = stops_table["stop_lon"].values

        # compute each stop nearest node
        (
            stops_table["nearest_node"],
            stops_table["node_distance"],
        ) = self.localisations_nearest_nodes(longitudes, latitudes, modes, return_dist=True)

        # extend graph with stops when needed
        # problem : with don't consider newly added nodes as possible neighbours
        if extend_graph:
            for index, row in stops_table.iterrows():
                # if the node has no close neighbour, add a new node at stop location
                if row["nearest_node"] is None or row["node_distance"] > max_distance:
                    # define node id TODO : ensure that the node doesn't already exist in topologies ?
                    m = hashlib.md5()
                    m.update(row["stop_id"].encode("utf-8"))
                    node_id = int(str(int(m.hexdigest(), 16))[0:10])

                    self.add_node(
                        node_id,
                        {"y": row["stop_lat"], "x": row["stop_lon"], "osmid": row["stop_id"]},
                        modes,
                    )

                    # update the stop's nearest node
                    stops_table.loc[index, "nearest_node"] = node_id
