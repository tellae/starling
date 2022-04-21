from starling_sim.basemodel.agent.operators.station_based_operator import StationBasedOperator
from starling_sim.basemodel.algorithms.pal_zhang_dispatcher import PalZhangGreedyDispatcher


class Operator(StationBasedOperator):
    """
    This class describes the operator of the SB_VS_R model.
    """

    DISPATCHERS = {"PZ": {"punctual": PalZhangGreedyDispatcher}}

    def __init__(self, simulation_model, agent_id, fleet_dict, stations_dict, **kwargs):

        super().__init__(simulation_model, agent_id, fleet_dict, stations_dict, **kwargs)

    def loop_(self):

        # if no dispatcher is provided, do not execute repositioning
        if self.punctual_dispatcher is None:
            return

        # otherwise, follow the dispatching loop of the punctual dispatcher
        yield self.execute_process(self.punctual_dispatcher.dispatching_loop_())
