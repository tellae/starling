class Topology:
    """
    This class describes an type of environment for the simulation

    It should be extended for concrete use in the simulation
    """

    def __init__(self):
        """
        The constructor should not instantiate the topology data structure,
        which is done in the setup method
        """

        # transport mode described by this topology
        self.mode = None

    def setup(self):
        """
        Prepare the topology for the simulation run

        :return:
        """

    # TODO : doubles with udpate_speeds ?
    def update(self):
        """
        Update the topology state

        :return:
        """

    def get_positions(self):
        """
        Return the list of all topology positions

        :return: list of positions
        """

    # TODO : structure of speeds, and doc
    def update_speeds(self, speeds):
        """

        :param speeds:
        :return:
        """

    # TODO : unify all shortest path computations under the same method ?
    def shortest_path(self, origin, destination, dimension):
        """
        Compute the shortest path between origin and destination

        :param origin: origin position
        :param destination: destination position
        :param dimension: type of length to consider (distance, time, etc)
        :return: shortest path : list of positions, origin and destination included
        """

    # TODO : other shortest path methods ?

    def position_localisation(self, position):
        """
        Return the localisation (lat, lon) of the position

        :param position: position in the topology
        :return: tuple (lat, lon)
        """

    def nearest_position(self, localisation):
        """
        Return the nearest position to given localisation (lat, lon)

        :param localisation: (lat, lon) tuple
        :return: position
        """

    def localisations_nearest_nodes(self, x_coordinates, y_coordinates, method=None):
        """
        Return the graph nodes nearest to a list of points.

        This method should allow a faster computation than multiple nearest_position calls.

        :param x_coordinates: list of X coordinates of the localisations (lon in GPS)
        :param y_coordinates: list of Y coordinates of the localisations (lat in GPS)
        :param method: name of the method used for the computation
        :return: list of nearest nodes
        """

    def get_edge_data(self, node1, node2, data):
        """
        Return the corresponding edge information

        :param node1: node of the topology
        :param node2: node of the topology
        :param data: requested attribute
        :return: data information of the edge
        """



