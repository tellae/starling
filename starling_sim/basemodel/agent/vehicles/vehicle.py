from starling_sim.basemodel.agent.moving_agent import MovingAgent
from starling_sim.basemodel.trace.events import (
    MoveEvent,
    RouteEvent,
    PositionChangeEvent,
    GetVehicleEvent,
    LeaveVehicleEvent,
)


class Vehicle(MovingAgent):
    """
    This class describes the basic features of a vehicle agent

    It should be extended to implement more specific features and behaviours
    """

    SCHEMA = {
        "properties": {
            "seats": {
                "type": "integer",
                "title": "Number of seats of the vehicle",
                "description": "Capacity of the vehicle",
                "minimum": 0,
            }
        },
        "required": ["seats"],
    }

    def __init__(self, simulation_model, agent_id, origin, seats, **kwargs):
        """
        A vehicle have a number of seats and a list of occupants.

        :param simulation_model:
        :param agent_id:
        :param origin:
        :param seats:
        :param kwargs:
        """

        MovingAgent.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.seats = seats
        self.occupants = []
        self.vehicle = None

    def __str__(self):

        return "[id={}, origin={}, seats={}]".format(self.id, self.origin, self.seats)

    def change_position(self, new_position, mode):
        """
        The vehicle changes the position of all of its occupants along with its own.

        :param new_position:
        :param mode:
        :return:
        """

        # change occupants positions
        for occupant in self.occupants:
            occupant.change_position(new_position, mode)

        # change own position
        super().change_position(new_position, mode)

    def trace_event(self, event):
        """
        The vehicle adds its move and route traces to its occupants.

        :param event:
        :return:
        """

        # add event to occupants traces
        if (
            isinstance(event, MoveEvent)
            or isinstance(event, RouteEvent)
            or isinstance(event, PositionChangeEvent)
        ):
            for occupant in self.occupants:
                occupant.trace_event(event)

        # add event to own trace
        super().trace_event(event)

    def load(self):
        """
        Compute the current load of the vehicle.

        :return: vehicle load
        """

        load = 0
        for occupant in self.occupants:
            if hasattr(occupant, "number"):
                load += occupant.number
            else:
                load += 1

        return load

    def add_passenger(self, passenger):

        if self.load() >= self.seats:
            self.log_message("Adding a new passenger while full", 30)

        passenger.vehicle = self
        self.occupants.append(passenger)

    def get_passenger(self, passenger):
        """
        Add the passenger to the list of occupants.

        :param passenger: agent
        """

        # add passenger
        self.add_passenger(passenger)

        # trace event
        passenger.trace_event(GetVehicleEvent(self.sim.scheduler.now(), passenger, self))

    def remove_passenger(self, passenger):

        # check if passenger is in vehicle
        if passenger not in self.occupants is None:
            self.log_message("Tried to leave passenger not in vehicle", 30)
            return

        # leave passenger
        self.occupants.remove(passenger)
        passenger.vehicle = None

    def leave_passenger(self, passenger):
        """
        Remove the passenger from the list of occupants.

        :param passenger: agent
        """

        # remove passenger from occupants
        self.remove_passenger(passenger)

        # trace event
        passenger.trace_event(LeaveVehicleEvent(self.sim.scheduler.now(), passenger, self))
