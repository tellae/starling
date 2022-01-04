from starling_sim.basemodel.topology.network_disutility import NetworkDisutility


class SimpleTimeDisutility(NetworkDisutility):

    def compute_edge_disutility(self, u, v, d, parameters):

        return d["time"]
