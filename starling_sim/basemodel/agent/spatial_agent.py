from starling_sim.basemodel.agent.agent import Agent


class SpatialAgent(Agent):
    """
    Class describing a spatial agent, with a position and origin in the simulation environment.
    """

    SCHEMA = {
        "properties": {
            "origin": {
                "type": ["number", "string"],
                "title": "Origin position",
                "description": "origin position id (inferred from geometry)",
            }
        },
        "required": ["origin"],
    }

    def __init__(self, simulation_model, agent_id, origin, **kwargs):

        Agent.__init__(self, simulation_model, agent_id, **kwargs)

        self.origin = origin

        self.position = origin

    def __str__(self):

        return "[id={}, origin={}]".format(self.id, self.origin)
