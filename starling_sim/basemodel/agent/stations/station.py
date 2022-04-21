from starling_sim.basemodel.agent.spatial_agent import SpatialAgent


class Station(SpatialAgent):
    """
    Station agent
    """

    SCHEMA = {
        "properties": {
            "operator_id": {
                "title": "Operator ID",
                "description": "ID of the operator managing this agent",
                "type": "string",
            }
        }
    }

    def __init__(self, simulation_model, agent_id, origin, operator_id=None, **kwargs):

        SpatialAgent.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.operator = None
        if operator_id is not None:
            self.operator = self.sim.agentPopulation.get_agent(operator_id)

    def __str__(self):

        return "[id={}, position={}]".format(self.id, self.position)
