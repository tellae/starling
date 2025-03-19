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

    def evaluate_path_lengths(self, path: list) -> list:
        """
        Evaluate the intermediate arc lengths of the given path.

        :param path: list of adjacent graph nodes
        :return: list of arc length values
        """

        def evaluate_arc_length(previous_position, new_position, _):
            return self.get_edge_data(previous_position, new_position, self.LENGTH_ATTRIBUTE)

        return self.evaluate_on_path(path, evaluate_arc_length, 0)

    def evaluate_path_durations(self, path: list) -> list:
        """
        Evaluate the intermediate arc durations of the given path.

        :param path: list of adjacent graph nodes
        :return: list of arc duration values
        """

        def evaluate_arc_duration(previous_position, new_position, _):
            return self.get_edge_data(previous_position, new_position, self.TIME_ATTRIBUTE)

        return self.evaluate_on_path(path, evaluate_arc_duration, 0)

    def evaluate_path_durations_with_uniform_speed(self, path: list, speed: float, lengths: list):
        """
        Evaluate the intermediate arc durations of the given path with a uniform speed.

        Durations are evaluated by dividing length values by the given speed,
        considered uniform on the path.

        :param path: list of adjacent graph nodes
        :param speed: uniform speed on the path
        :param lengths: list of arc length values
        :return: list of arc duration values
        """

        def evaluate_arc_duration(_previous_pos, _new_pos, i):
            return float(lengths[i]) / speed

        return self.evaluate_on_path(path, evaluate_arc_duration, 0)

    def evaluate_on_path(path, func, first_value=0):
        """
        Evaluate numeric values along the given path.

        The func parameter is a function that evaluates a value given the arc
        origin and destination nodes and its position in the path:
        func(start, end, path_index) -> value

        The evaluation result is rounded, and a remainder is stored to be added
        to the next evaluated value.

        :param path: list of adjacent graph nodes
        :param func: function used to evaluate data on each path arc
        :param first_value: first value of the returned list
        :return: evaluated values
        """

        # start with first arc, node 0 to 1
        previous_position = path[0]

        # use provided initial value
        values = [first_value]

        # since the link values may not be integers, we use a remainder
        remainder = 0

        for i in range(1, len(path)):
            new_position = path[i]
            arc_value = func(previous_position, new_position, i) + remainder

            # update remainder
            remainder = arc_value - int(arc_value)

            # add value to data list
            values.append(int(arc_value))

            # update previous position
            previous_position = path[i]

        return values

    evaluate_on_path = staticmethod(evaluate_on_path)

    def evaluate_route_data(self, path, duration=None, durations_sum_to=None):
        """
        Evaluate a route_data object from the given path.

        :param path: list of adjacent graph nodes
        :param duration: total duration of the route
        :param durations_sum_to: value the total duration must sum to

        :return: { "route": path_nodes, "length": length_list, "time": time_list }
        """

        # build an object { "route": path_nodes, "length": length_list, "time": time_list }
        route_data = {"route": path, "length": self.evaluate_path_lengths(path)}

        if duration is not None:
            if duration == 0:
                speed = float("inf")
            else:
                total_length = sum(route_data["length"])
                speed = float(total_length) / duration
            durations = self.evaluate_path_durations_with_uniform_speed(
                path, speed, route_data["length"]
            )
        else:
            durations = self.evaluate_path_durations(path)
        route_data["time"] = durations

        # check that the duration fits (to avoid round-up error)
        if duration is None and durations_sum_to is not None:
            duration = durations_sum_to

        time_sum = sum(route_data["time"])

        if duration is not None and duration != time_sum:
            route_data["time"][-1] += int(duration - time_sum)

        return route_data

    def route_event_trace(self, route_event, time_limit=None):
        """

        :param route_event: RouteEvent instance
        :param time_limit: stop evaluating routes after this timestamp

        :return: tuple of lists, localisations and timestamps
        """

        route = route_event.data["route"]
        durations = route_event.data["time"]

        current_time = route_event.timestamp

        localisations = []
        timestamps = []

        for i in range(len(route)):
            # compute current time
            current_time += durations[i]

            # we stop at simulation time limit
            if time_limit is not None and current_time > time_limit:
                break

            # append the localisation and time data
            if isinstance(route[i], tuple):
                localisations.append(route[i])
            else:
                localisations.append(self.position_localisation(route[i]))

            timestamps.append(current_time)

        return localisations, timestamps

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

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, return_dist=False):
        """
        Return the graph nodes nearest to a list of points.

        This method should allow a faster computation than multiple nearest_position calls.

        :param x_coordinates: list of X coordinates of the localisations (lon in GPS)
        :param y_coordinates: list of Y coordinates of the localisations (lat in GPS)
        :param return_dist: optionally also return distance between points and nearest nodes
        :return: list of nearest nodes
        """
        raise NotImplementedError()
