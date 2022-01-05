from starling_sim.basemodel.topology.network_disutility import NetworkDisutility


class SimpleTimeDisutility(NetworkDisutility):
    """
    Simply define the disutility as equal to the time spent on the edge.

    This results in shortest (time) paths.
    """

    def compute_edge_disutility(self, u, v, d, parameters):
        return d[self.topology.TIME_ATTRIBUTE]
