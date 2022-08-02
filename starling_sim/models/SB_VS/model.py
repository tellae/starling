from starling_sim.basemodel.simulation_model import SimulationModel
from starling_sim.models.SB_VS.input import Input
from starling_sim.models.SB_VS.output import Output
from starling_sim.models.SB_VS.user import User
from starling_sim.basemodel.agent.vehicles.station_based_vehicle import StationBasedVehicle
from starling_sim.basemodel.agent.stations.vehicle_sharing_station import VehicleSharingStation


class Model(SimulationModel):
    """
    Simple model for the simulation of a one-way, station-based, vehicle-sharing system
    """

    name = "Station-based vehicle-sharing model"

    agent_type_class = {
        "user": User,
        "vehicle": StationBasedVehicle,
        "station": VehicleSharingStation,
    }

    leaving_codes = {"FAIL_GET": "Failed to get a vehicle"}

    modes = {"user": ["walk"], "vehicle": ["station"], "station": [None, "walk"]}

    input_class = Input
    output_class = Output
