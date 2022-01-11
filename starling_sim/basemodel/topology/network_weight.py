from abc import ABC
import json


class NetworkWeight(ABC):
    """
    This class is used for computing weight on the graph edges.

    Paths on the graph are evaluated by minimising weight using
    a shortest path algorithm.
    """

    DEFAULT_PARAMETERS = {}

    def __init__(self, topology):

        self.topology = topology
        self.default_parameters = self.DEFAULT_PARAMETERS

    def pre_process_edge(self, u, v, d):
        """
        Add attributes to the edges before compute weight.

        :param u: edge origin
        :param v: edge destination
        :param d: edge data
        """
        pass

    def compute_edge_weight(self, u, v, d, parameters):
        """
        Compute and set edge weight using edge data and parameters.

        The attribute key to set is the hash of the parameters.

        :param u: edge origin
        :param v: edge destination
        :param d: edge data
        :param parameters: agent specific parameters
        """
        raise NotImplementedError()

    def get_parameters_hash(parameters):
        """
        Get the hash of the given weight parameters.

        :param parameters:

        :return: hash of the parameters, associated to the computed weight.
        """
        return str(hash(json.dumps(parameters, sort_keys=True)))

    get_parameters_hash = staticmethod(get_parameters_hash)
