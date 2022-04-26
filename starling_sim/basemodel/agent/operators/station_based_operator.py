from starling_sim.basemodel.agent.operators.operator import Operator


class StationBasedOperator(Operator):
    """
    Class describing an operator of a station-based shared vehicle service
    """

    SCHEMA = {
        "properties": {
            "stations_dict": {
                "type": "string",
                "title": "Stations population",
                "description": "Population of the operator's station agents",
            },
            "staff_dict": {
                "x-display": "",
                "title": "Staff population",
                "description": "Population of the operator's staff agents",
                "type": "string",
            },
        },
        "required": ["stations_dict"],
    }

    def __init__(self, simulation_model, agent_id, fleet_dict, stations_dict, **kwargs):

        super().__init__(simulation_model, agent_id, fleet_dict, **kwargs)

        # set the station population (agents that store the fleet agents)
        self.stations_dict_name = stations_dict
        self.stations = self.sim.agentPopulation.new_population(stations_dict)

    def init_depot_points(self, depot_points_coord):

        if depot_points_coord is not None and len(depot_points_coord) > 1:
            self.log_message("Multiple depot points are not supported yet", 30)
            depot_points_coord = [depot_points_coord[0]]

        super().init_depot_points(depot_points_coord)
