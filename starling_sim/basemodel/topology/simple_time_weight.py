from starling_sim.basemodel.topology.network_weight import NetworkWeight


class SimpleTimeWeight(NetworkWeight):
    """
    Simply define the weight as equal to the time spent on the edge.

    This results in shortest (time) paths.
    """

    def compute_edge_weight(self, u, v, d, parameters):
        return d[self.topology.TIME_ATTRIBUTE]
