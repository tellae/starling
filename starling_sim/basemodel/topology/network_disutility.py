from abc import ABC


class NetworkDisutility(ABC):

    def __init__(self):

        self.default_parameters = {}

    def pre_process_edge(self, u, v, d):

        pass

    def compute_edge_disutility(self, u, v, d, parameters):
        raise NotImplementedError()
