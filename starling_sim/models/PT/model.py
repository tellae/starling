from starling_sim.basemodel.simulation_model import SimulationModel
from starling_sim.models.PT.output import Output
from starling_sim.basemodel.agent.vehicles.public_transport_vehicle import (
    PublicTransportVehicle,
)
from starling_sim.basemodel.agent.operators.public_transport_operator import (
    PublicTransportOperator,
)
from starling_sim.utils.constants import PUBLIC_TRANSPORT_TYPE


class Model(SimulationModel):
    """
    Model for the simulation of a Time Table Public Transport system
    """

    name = "Timetable public transport model"

    agent_type_class = {
        PUBLIC_TRANSPORT_TYPE: PublicTransportVehicle,
        "operator": PublicTransportOperator,
    }

    leaving_codes = {
        "NO_JOURNEY_FOUND": "No journey found that corresponds to request",
        "FAILED_JOURNEY": "Couldn't finish journey",
    }

    modes = {"operator": {"fleet": None}}

    output_class = Output
