from abc import ABC
import json


class NetworkDisutility(ABC):
    """
    This class is used for computing disutility on the graph edges.

    Paths on the graph are evaluated by minimising disutility using
    a shortest path algorithm.
    """

    def __init__(self):

        self.default_parameters = {}

    def pre_process_edge(self, u, v, d):
        """
        Add attributes to the edges before compute disutility.

        :param u: edge origin
        :param v: edge destination
        :param d: edge data
        """
        pass

    def compute_edge_disutility(self, u, v, d, parameters):
        """
        Compute and set edge disutility using edge data and parameters.

        The attribute key to set is the hash of the parameters.

        :param u: edge origin
        :param v: edge destination
        :param d: edge data
        :param parameters: agent specific parameters
        """
        raise NotImplementedError()

    def get_parameters_hash(parameters):
        """
        Get the hash of the given disutility parameters.

        :param parameters:

        :return: hash of the parameters, associated to the computed disutility.
        """
        return "hash"
        # return hash(json.dumps(parameters, sort_keys=True))
    get_parameters_hash = staticmethod(get_parameters_hash)
