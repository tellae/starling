from starling_sim.basemodel.simulation_model import SimulationModel
from starling_sim.basemodel.population.dict_population import DictPopulation
from starling_sim.basemodel.environment.environment import Environment
from starling_sim.models.SB_VS_R.input import Input
from starling_sim.models.SB_VS_R.output import Output
from starling_sim.basemodel.schedule.scheduler import Scheduler
from starling_sim.models.SB_VS_R.operator import Operator
from starling_sim.models.SB_VS_R.repositioning_staff import RepositioningStaff
from starling_sim.models.SB_VS.user import User
from starling_sim.basemodel.agent.vehicles.station_based_vehicle import StationBasedVehicle
from starling_sim.basemodel.agent.stations.vehicle_sharing_station import VehicleSharingStation


class Model(SimulationModel):
    """Simple model for the simulation of a one-way station-based vehicle sharing,
    with repositioning operations"""

    name = "Station-based vehicle-sharing with repositioning model"

    agent_type_class = {
        "user": User,
        "vehicle": StationBasedVehicle,
        "station": VehicleSharingStation,
        "staff": RepositioningStaff,
        "operator": Operator
    }

    leaving_codes = {
        "FAIL_GET": "Failed to get a vehicle"
    }

    modes = {
        "user": ["walk"],
        "vehicle": ["station"],
        "station": [None, "walk", "staff"],
        "staff": [None],
        "operator": {
            "staff": "staff",
            "fleet": "station"
        }
    }

    def __init__(self, parameters):
        """
        Initialisation of the classes used by the station-based with repositioning model

        :param parameters: SimulationParameters object
        """

        super().__init__(parameters)

        # elements of the model
        self.agentPopulation = DictPopulation(self.agent_type_class.keys())
        self.environment = Environment(self.parameters)

        # inputs and outputs
        self.dynamicInput = Input(self.agent_type_class)
        self.outputFactory = Output()

        # event manager
        self.scheduler = Scheduler()
