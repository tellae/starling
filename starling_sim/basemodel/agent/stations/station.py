from starling_sim.basemodel.agent.spatial_agent import SpatialAgent


class Station(SpatialAgent):
    """
    Station agent
    """

    SCHEMA = {}

    def __init__(self, simulation_model, agent_id, origin, operator=None, **kwargs):

        SpatialAgent.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.operator = operator

    def __str__(self):

        return "[id={}, position={}]" \
            .format(self.id, self.position)
