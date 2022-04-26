from starling_sim.basemodel.agent.vehicles.vehicle import Vehicle


class StationBasedVehicle(Vehicle):
    """
    This class describes a vehicle of a station-based vehicle sharing service.
    """

    SCHEMA = {
        "properties": {
            "station": {
                "title": "Origin station",
                "description": "Origin station of the vehicle",
                "type": "string",
            }
        },
        "required": ["station"],
        "remove_props": ["origin"],
    }

    def __init__(self, simulation_model, agent_id, seats, station, **kwargs):
        """
        Get information from the origin station and update its stock.

        :param simulation_model:
        :param agent_id:
        :param seats:
        :param kwargs:
        """

        # get the station agent
        station_agent = simulation_model.agentPopulation.get_agent(station)
        if station_agent is None:
            raise ValueError(
                "Could not match the station id '{}' with any simulation "
                "agent (initialising vehicle  {})".format(station, agent_id)
            )

        # update the station's store
        station_agent.store.items.append(self)
        station_agent.initial_stock += 1

        super().__init__(simulation_model, agent_id, station_agent.origin, seats, **kwargs)
