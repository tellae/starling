"""
Free-floating vehicle-sharing user
"""

from starling_sim.basemodel.agent.persons.person import Person
from starling_sim.basemodel.agent.requests import Request


class User(Person):
    """
    This class describes a free-floating vehicle-sharing user
    """

    def __init__(self, simulation_model, agent_id, origin, destination, **kwargs):
        super().__init__(simulation_model, agent_id, origin, destination, **kwargs)

        # all for now

    def loop_(self):
        """
        Main loop of a free-floating vehicle-sharing user
        """

        # loop on trying to get closest vehicle
        yield self.execute_process(self.request_loop_(self.maxTries))

        if self.vehicle is None:
            # if failed to get a vehicle, leave the system
            self.leave_simulation("FAIL_GET")

        # get closest point to destination on the adequate topology and move to it
        vehicle_mode = self.vehicle.mode
        self.tempDestination = self.closest_walkable_node_of(
            vehicle_mode, position=self.destination
        )
        yield self.execute_process(self.move_shortest_with_vehicle_())

        # leave vehicle
        self.leave_vehicle()

        # end trip
        yield self.execute_process(self.walk_to_destination_())

        return

    def try_new_request_(self):
        """
        Try to get the closest vehicle available.

        :return: Request object, completed according to request result
        """

        # create a new request
        vehicle_request = Request(self, self.sim.scheduler.now(), request_type=Request.GET_REQUEST)

        # get relevant vehicles
        vehicles = []

        for vehicle in self.sim.agentPopulation["vehicle"].values():
            # only check vehicles with occupants == []
            if not vehicle.occupants:
                vehicles.append(vehicle)

        # compute closest vehicle
        closest_vehicle, route = self.sim.environment.closest_object(
            self.position, vehicles, True, "walk", return_path=True, n=3
        )

        # if no vehicle available, fail
        if closest_vehicle is None:
            vehicle_request.success = False
            return vehicle_request

        # walk to vehicle position
        self.tempDestination = closest_vehicle.position
        yield self.execute_process(self.move_(route=route))

        # if vehicle is available, take it
        if closest_vehicle.position == self.position and not closest_vehicle.occupants:
            self.get_vehicle(closest_vehicle)
            vehicle_request.success = True
            vehicle_request.result = closest_vehicle
        else:
            vehicle_request.success = False

        return vehicle_request
