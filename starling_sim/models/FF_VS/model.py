from starling_sim.basemodel.simulation_model import SimulationModel
from starling_sim.basemodel.population.dict_population import DictPopulation
from starling_sim.basemodel.environment.environment import Environment
from starling_sim.models.FF_VS.input import Input
from starling_sim.models.FF_VS.output import Output
from starling_sim.basemodel.schedule.scheduler import Scheduler
from starling_sim.models.FF_VS.user import User
from starling_sim.basemodel.agent.vehicles.vehicle import Vehicle


class Model(SimulationModel):
    """
    Simple model for the simulation of a free-floating vehicle-sharing system
    """

    name = "Free-floating vehicle-sharing model"

    agent_type_class = {
        "user": User,
        "vehicle": Vehicle
    }

    leaving_codes = {
        "FAIL_GET": "Failed to get a vehicle"
    }

    modes = {
        "user": ["walk"],
        "vehicle": [None, "walk"]
    }

    def __init__(self, parameters):
        """
        Initialisation of the classes used by the free-floating model

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
