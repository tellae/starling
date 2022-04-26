"""
This module contains the MovingAgent class,
with useful methods to make an agent move in the environment
"""

from starling_sim.basemodel.agent.spatial_agent import SpatialAgent
from starling_sim.basemodel.trace.events import RouteEvent, PositionChangeEvent
from starling_sim.utils.utils import make_int
from starling_sim.utils.config import config


class MovingAgent(SpatialAgent):
    """
    This class describes an agent with the capacity of moving
    """

    def __init__(self, simulation_model, agent_id, origin, **kwargs):
        """
        Create a moving agent, setting its positional attributes and destination

        :param simulation_model:
        :param agent_id:
        :param origin:
        """

        SpatialAgent.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.tempDestination = None

    # move methods

    def move_(
        self,
        route=None,
        duration=None,
        check_dest=False,
        destination=None,
        parameters=None,
        verb=True,
    ):
        """
        Compute a route with the given parameters and follow it.

        :param route: list of consecutive nodes in the environment
        :param duration: total duration of the move
        :param check_dest: boolean indicating the destination changes should be checked while following the route
        :param destination: used for computing the route. If None, self.tempDest is used
        :param parameters: agent specific parameters used for path evaluation
        :param verb: boolean indicating if a message should be displayed when calling the function

        :return: yield one or several processes during the route execution
        """

        # get move's mode
        mode = self.mode

        # get move's destination
        if destination is None:
            destination = self.tempDestination

        # ignore moves to current position
        if destination == self.position and duration is None:
            return

        # get move's route data
        route_data = self.sim.environment.compute_route_data(
            route, duration, self.position, destination, parameters, mode
        )

        # execute route data
        yield self.execute_process(self.follow_route_data_(route_data, check_dest, mode, verb))

    def follow_route_data_(self, route_data, check_dest, mode, verb=True):
        """
        Travel along the given route

        :param route_data: route_data to be followed
        :param check_dest: boolean indicating if destination changes
         should be checked during the trip
        :param mode: mode used
        :param verb: boolean indicating if a log should be displayed when calling the function
        """

        route = route_data["route"]

        # check route

        # route departure should be self.position
        if route[0] != self.position:
            self.log_message(
                "Trying to execute a route that starts at {} while being at {}".format(
                    route[0], self.position
                ),
                40,
            )
            raise ValueError(route)
        # check route length
        if len(route) == 0:
            return

        # log agent movement
        if verb:
            self.log_message("Moving to {} with mode {}".format(route[-1], self.mode))

        # trace route move
        event = RouteEvent(self.sim.scheduler.now(), route_data, mode)
        self.trace_event(event)

        # TODO : manage if interrupted
        if check_dest:

            durations = route_data["time"]

            for i in range(1, len(route)):

                if route[-1] != self.tempDestination:
                    new_route_data = {
                        "route": route_data["route"][:i],
                        "time": route_data["time"][:i],
                        "length": route_data["length"][:i],
                    }
                    event.set_route_data(new_route_data)
                    break

                yield self.execute_process(self.move_to_(route[i], durations[i]), True)

        else:

            # execute travel and store the process
            total_time = sum(route_data["time"])
            yield self.execute_process(self.move_to_(route[-1], total_time), True)

    def change_position(self, new_position, mode):
        """
        Change the current position of the agent.

        :param new_position: new position of the agent
        :param mode: agent transport mode
        :return:
        """

        # self.trace_event(PositionChangeEvent(self.sim.scheduler.now(), new_position, mode))
        self.position = new_position

    def move_to_(self, destination, duration):
        """
        Perform the action of moving from the current position to a given destination

        :param destination: Destination in the simulation environment
        :param duration: Duration of the trip
        :return: yield a trip duration process
        """

        # wait the given duration
        yield self.execute_process(self.spend_time_(duration))

        # change agent position and trace the event
        self.change_position(destination, self.mode)

    def fly_(
        self,
        destination=None,
        duration=None,
        length=None,
        distance_factor=None,
        speed=None,
        mode=None,
        verb=True,
    ):
        """
        Realise a direct trip from current position to destination without using the network.

        The information provided (duration, length, speed) must allow to compute the
        trip duration and length. Length can be computed using euclidean distance.
        If duration and length are provided, speed is not used.

        :param destination: destination of the trip.
            Default is self.tempDestination.
        :param duration: duration of the trip.
            Default is computed using length and speed.
        :param length: length of the trip.
            Default is computed using duration and speed, or using euclidean distance.
        :param distance_factor: value multiplied to euclidean distance to get trip distance.
            Default is defined by the 'distance_factor' config value.
        :param speed: speed of the agent, used to compute duration and length
        :param mode: mode of traveling.
            Default is self.mode.
        :param verb: boolean indicating if a log should be displayed when calling the function

        :return: yield a trip duration process
        """

        # get or compute trip information
        origin = self.position

        if distance_factor is None:
            distance_factor = config["distance_factor"]

        if destination is None:
            destination = self.tempDestination

        if speed is None:
            if duration is None:
                self.log_message("Can't fly without knowing duration or speed", 40)
                raise ValueError(speed)
            else:
                if length is None:
                    length, _ = self.approximate_trip(origin, destination, distance_factor, None)

        else:
            if duration is None:
                if length is None:
                    length, duration = self.approximate_trip(
                        origin, destination, distance_factor, speed
                    )
                else:
                    duration = int(length / speed)
            else:
                if length is None:
                    length = int(duration * speed)

        if mode is None:
            mode = self.mode

        if None in [origin, destination, duration, length, mode]:
            self.log_message("Error in the fly method, missing information", 40)

        # check that duration and length are Python int
        duration = make_int(duration)
        length = make_int(length)

        # log agent movement
        if verb:
            self.log_message("Flying to {} with mode {}".format(destination, mode))

        # trace trip
        self.trace_event(
            PositionChangeEvent(
                self.sim.scheduler.now(), origin, destination, length, duration, mode
            )
        )

        # realise trip
        yield self.execute_process(self.move_to_(destination, duration))

    def approximate_trip(self, origin, destination, distance_factor, speed):
        """
        Approximate the length and time of a trip based on the euclidean distance and speed.

        The computation is based on a factor that is applied to the euclidean distance.

        :param origin: origin position
        :param destination: destination position
        :param distance_factor: value multiplied to euclidean distance to get trip distance.
        :param speed: speed of the travelling agent, in m/s.
            If None, travel time is not computed
        :return: tuple (travel_length, travel_time)
        """

        return self.sim.environment.approximate_path(
            origin, destination, distance_factor, speed, mode=self.mode
        )
