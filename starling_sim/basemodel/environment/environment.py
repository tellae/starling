import logging
import sys
import numpy as np
import osmnx as ox
from starling_sim.utils.utils import points_in_zone
from starling_sim.basemodel.topology.osm_network import OSMNetwork
from geopy import distance


class Environment:
    """
    Describes an environment in which the simulation will take place
    """

    def __init__(self, parameters, network="osm"):
        """
        Initialization of the environment, without import of data structures.

        It should be extended for the needs of the chosen environment
        """

        self.sim = None
        self.topologies = {}

        # get the topologies dict
        topologies_dict = parameters["topologies"]

        for mode, info in topologies_dict.items():

            network_file = info[0]
            speeds_file = info[1]

            # create a topology object according to the given network type
            if network == "osm":
                topology = OSMNetwork(mode, network_file, speeds_file)

            else:
                logging.error("Unknown network type {}".format(network))
                continue

            self.topologies[mode] = topology

    def setup(self, simulation_model):
        """
        Setup the environment for the simulation run.

        Set the simulation model attribute and
        prepare the environment for the simulation

        :param simulation_model: simulation model
        """

        self.sim = simulation_model
        for topology in self.topologies.values():
            topology.setup()

    def periodic_update_(self, period):
        """
        Periodically update the simulation environment using the topology update method

        :param period: Update period, put 0 for no updates
        :return:
        """

        if period == 0:
            return

        # Log periodic_update
        logging.debug("Start periodical environment update, period=" + period)

        while period:

            # Wait for period to elapse
            yield self.sim.scheduler.timeout(period)

            # Log new update
            logging.debug("Environment update")

            # Update
            for topology in self.topologies.values():
                topology.update()

    # TODO : Move to subclass ? Not very pretty
    # environment utils

    def compute_route_data(self, route, duration, origin, destination, dimension, mode):
        """
        Compute a route data from the given parameters

        :param route: list of consecutive nodes in the environment.
            If None, a shortest path from <origin> to <destination> is computed
        :param duration: total duration of the route execution.
            If None, use the "time" links of the environment
        :param origin: origin used for the shortest path computation
        :param destination: destination used for the shortest path computation
        :param dimension: dimension minimised in the shortest path computation
        :param mode: mode of the move
        :return: route_data={"route": position_list, "length": length_list, "time": time_list}
        """

        # if route is None, compute the path from <origin> to <destination>
        # which minimises <dimension>
        if route is None:
            # compute shortest path
            route = self.topologies[mode].shortest_path(origin, destination, dimension)

        # store route in a dict
        route_data = {"route": route}

        # add length data
        self.add_route_data(route_data, mode, "length")

        # add time data
        if duration is not None:

            if duration == 0:
                speed = float("inf")
            else:
                total_length = sum(route_data["length"])
                speed = float(total_length) / duration

            self.add_route_data(route_data, mode, "time", speed=speed)
        else:
            self.add_route_data(route_data, mode, "time")

        # check that the duration fits (to avoid round-up error)
        if duration is None:
            duration = int(self.sim.environment.topologies[mode].shortest_path_length(origin, destination, "time"))
        time_sum = sum(route_data["time"])

        if duration != time_sum:
            route_data["time"][-1] += duration - time_sum

        return route_data

    def add_route_data(self, route_data, mode, data, speed=None):
        """
        Complete the given route_data with the relevant list

        :param route_data: route_data to be completed
        :param mode: mode of the move
        :param data: type of data to add, either "length" or "time"
        :param speed: speed of the move, used for "time" data.
            If None, use the links' speeds
        """

        route = route_data["route"]

        # complete a data list corresponding to the links between the route positions
        previous_position = route[0]
        data_list = [0]
        # since the link values may not be integers, we use a remainder
        remainder = 0

        for i in range(1, len(route)):

            if data == "time" and speed is not None:

                # use the speed for computing "time" data, if provided
                move_data = float(route_data["length"][i])/speed + remainder

            else:

                # use the environment links data
                move_data = self.topologies[mode].get_edge_data(
                    previous_position, route[i], data) + remainder

            # update remainder
            remainder = move_data - int(move_data)

            # add value to data list
            data_list.append(int(move_data))

            # update previous position
            previous_position = route[i]

        # update the route_data dict
        route_data[data] = data_list

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
            if row["sequence"] == len(shape_table)+1:
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
                time = duration*row["distance_proportion"] + time_remainder
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
            return self.topologies[mode].position_localisation(node)
        else:
            agent_localisation = None
            for topology in self.topologies.values():
                agent_localisation = None
                try:
                    return topology.position_localisation(node)

                except KeyError:

                    pass

            return agent_localisation

    def compute_network_distance(self, source, target, mode, dimension="time", return_path=False):

        # if no mode is given, return None
        if mode is None:
            logging.warning("No mode provided for network distance computation")
            return None
        else:
            if return_path:
                return self.topologies[mode].dijkstra_shortest_path_and_length(source, target, dimension)
            else:
                return self.topologies[mode].shortest_path_length(source, target, dimension)

    def compute_euclidean_distance(self, position1, position2, mode=None):

        # get position localisations
        loc1 = self.get_localisation(position1, mode)
        loc2 = self.get_localisation(position2, mode)

        # geopy would return a distance even if one localisation is None, caution
        if loc1 is None or loc2 is None:
            logging.warning("One of the given localisations is None, "
                            "computed euclidean distance will be false")

        dist = 1000*distance.great_circle(loc1, loc2).kilometers

        return dist

    def distance_dict_between(self, position, obj_list, distance_type, n=None, maximum_distance=None,
                              position_lambda=None, mode=None, is_origin=True, dimension="time", return_path=False):

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

                    distance_res = self.compute_network_distance(position, self.get_position(obj, position_lambda),
                                                                 mode, dimension, return_path)
                else:
                    distance_res = self.compute_network_distance(self.get_position(obj, position_lambda),
                                                                 position, mode, dimension, return_path)

            elif distance_type == "euclidean":
                distance_res = self.compute_euclidean_distance(position,
                                                               self.get_position(obj, position_lambda), mode)

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

    def euclidean_n_closest(self, position, obj_list, n, maximum_distance=None, position_lambda=None):

        distance_dict = self.distance_dict_between(position, obj_list, "euclidean", n=n,
                                                   maximum_distance=maximum_distance,
                                                   position_lambda=position_lambda)

        sorted_list = sorted(distance_dict.keys(), key=lambda x: distance_dict[x])

        return sorted_list

    def closest_object(self, position, obj_list, is_origin, mode, dimension="time",
                       position_lambda=None, return_path=False, n=None):
        """
        Find the object of the list that is closest to the given position.

        We compute network distances between the objects of the list and the given
        position. If the n param is provided, we pre-process the list, and only
        keep the n euclidean closest objects.

        :param position:
        :param obj_list:
        :param is_origin: boolean indicating if the
        :param mode:
        :param dimension:
        :param position_lambda:
        :param return_path:
        :param n:
        :return:
        """

        if not obj_list or n == 0:
            return None

        # look only at the n (euclidean) closest objects
        if n is not None:

            obj_list = self.euclidean_n_closest(position=position, obj_list=obj_list,
                                                n=n, position_lambda=position_lambda)

        # do the network distance computation and keep the closest object
        distance_dict = self.distance_dict_between(position, obj_list, "network",
                                                   position_lambda=position_lambda, mode=mode, is_origin=is_origin,
                                                   dimension=dimension, return_path=return_path)
        if return_path:
            closest_object = min(list(distance_dict.keys()),
                                 key=lambda x: distance_dict[x][1])
            return closest_object, distance_dict[closest_object][0]
        else:
            closest_object = min(list(distance_dict.keys()),
                                 key=lambda x: distance_dict[x])
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
            node_localisation = self.topologies[modes[0]].position_localisation(node)

            # compute euclidean distance
            dist = distance.great_circle(localisation, node_localisation)

            # if distance is improved, keep the node
            if dist < best_dist:
                best_dist = dist
                best_node = node

        return best_node

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, modes):
        """
        Call the topology localisations_nearest_nodes method.

        :param x_coordinates: list of X coordinates of the localisations
        :param y_coordinates: list of Y coordinates of the localisations
        :param modes: topology modes
        :return: list of nearest nodes
        """
        print("called for modes {}".format(modes))
        if isinstance(modes, list):
            base_graph = self.topologies[modes[0]].graph
            target_graph = base_graph.copy()

            for mode in modes[1:]:

                intersect_graph = self.topologies[mode].graph

                target_graph.remove_nodes_from(n for n in base_graph if n not in intersect_graph)

        else:
            target_graph = self.topologies[modes].graph

        target_topology = OSMNetwork(modes, graph=target_graph)

        return target_topology.localisations_nearest_nodes(x_coordinates, y_coordinates)

    def get_common_nodes_of(self, modes):
        """
        Find the nodes that are common to the given topologies

        :param modes: transport modes, each corresponding to a topology
        :return: set object, containing the intersection of the topology nodes
        """

        # initialize the set of common nodes with the first topology nodes
        intersection_set = set(self.topologies[modes[0]].graph.nodes)

        # realize the intersection with other topologies
        for mode in modes[1:]:
            intersection_set = intersection_set & set(self.topologies[mode].graph.nodes)

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

    def is_in_modes_bbox(self, point, modes):
        """
        Check if the given point belongs to the bbox of ALL given modes.

        :param point: (lat, lon)
        :param modes: list of modes, must correspond to topologies keys
        :return: boolean
        """

        is_in = True

        for mode in modes:

            topology = self.topologies[mode]
            is_in = is_in and topology.is_in_zone(point)

        return is_in

    def add_node(self, node_id, properties, modes):
        """
        Add a node id and its properties to the given modes.

        :param node_id: id of the new node
        :param properties: properties of the node
        :param modes: list topologies to add the node to
        """

        for mode in modes:

            topology = self.topologies[mode]

            if node_id in topology.graph.nodes:
                # logging.warning("Adding node already in graph {}".format(node_id))
                # TODO : test if properties are same
                continue

            topology.graph.add_node(node_id, **properties)

    def build_gtfs_correspondence(self, feed, modes):
        """
        Build a correspondence dict between the gtfs stops and the environment positions.

        For each stop, the nearest position common to the given modes is found.
        The second info added is if the stop localisation belongs to the modes bbox.
        If it is in the bbox, the second info is None, since the stop position can be described using
        the mode nodes. Otherwise, we add the stop localisation. It is then possible to know which stops
        belong to the bbox or not, and then extend the graph with these stops if wanted.

        :param feed: gtfs_kit Feed object
        :param modes: list of modes

        :return: {stop_id: [position, (lat, lon) or None]
        """

        # initialise a dict that maps stop points to topology nodes
        correspondences = dict()

        # get the gtfs stop points
        stops = feed.get_stops()

        # compute a network as the intersection of all given modes
        graph_0 = self.topologies[modes[0]].graph
        intersection_graph = graph_0.copy()

        for mode in modes[1:]:
            mode_graph = self.topologies[mode].graph
            intersection_graph.remove_nodes_from(n for n in graph_0 if n not in mode_graph)

        intersection_topology = OSMNetwork("intersection", graph=intersection_graph)

        # compute the nearest node in the intersection network for all stop points
        latitudes = stops["stop_lat"].values
        longitudes = stops["stop_lon"].values

        nearest_nodes = intersection_topology.localisations_nearest_nodes(longitudes, latitudes)

        # check if stops are in topologies zones
        stops.rename(columns={"stop_lat": "lat", "stop_lon": "lon"}, inplace=True)
        for mode in modes:
            stops = points_in_zone(stops, self.topologies[mode].zone)
            stops.rename(columns={"in_zone": mode}, inplace=True)
        stops.rename(columns={"lat": "stop_lat", "lon": "stop_lon"}, inplace=True)

        # consider stops that are not in ALL zones as out
        stops["in_zones"] = stops[modes].all(axis=1)

        # build the correspondence dict from the previous computations
        i = 0
        for index, row in stops.iterrows():

            # get the stop point id
            stop_id = row["stop_id"]

            # get the stop point position
            position = int(nearest_nodes[i])

            # see if the stop point is in the topologies zones
            if not row["in_zones"]:
                extension = (row["stop_lat"], row["stop_lon"])
            else:
                extension = None

            # set the stop point information
            correspondences[stop_id] = [position, extension]

            i += 1

        return correspondences

    def extend_graph_with_gtfs(self, stops, correspondence_dict, modes):
        """
        Extend the modes' graphs with the stops of the given feed
        that don't belong to the bbox.

        The method uses the correspondence file to know if stops belong to the modes' bbox.

        :param stops: gtfs_kit Feed object
        :param correspondence_dict: dict mapping stop points with topology nodes
        :param modes: topologies to extend with given stops
        """

        # browse the stops and add their positions to the environment
        for index, row in stops.iterrows():

            info = correspondence_dict[row["stop_id"]]

            if info[1] is not None:
                self.add_node(row["stop_id"],
                              {"y": row["stop_lat"], "x": row["stop_lon"],
                               "osmid": row["stop_id"]}, modes)
