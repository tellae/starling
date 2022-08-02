from starling_sim.basemodel.simulation_model import SimulationModel
from starling_sim.models.FF_VS.output import Output
from starling_sim.models.FF_VS.user import User
from starling_sim.basemodel.agent.vehicles.vehicle import Vehicle


class Model(SimulationModel):
    """
    Simple model for the simulation of a free-floating vehicle-sharing system
    """

    name = "Free-floating vehicle-sharing model"

    agent_type_class = {"user": User, "vehicle": Vehicle}

    leaving_codes = {"FAIL_GET": "Failed to get a vehicle"}

    modes = {"user": ["walk"], "vehicle": [None, "walk"]}

    output_class = Output
