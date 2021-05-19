from starling_sim.basemodel.agent.moving_agent import MovingAgent
from starling_sim.basemodel.trace.events import RequestEvent, GetVehicleEvent, LeaveVehicleEvent, \
    DestinationReachedEvent
from starling_sim.basemodel.agent.requests import UserStop
from starling_sim.utils.utils import validate_against_schema
from starling_sim.utils.constants import DEFAULT_DISTANCE_FACTOR, DEFAULT_WALKING_SPEED, SUCCESS_LEAVE

import sys


class Person(MovingAgent):
    """
    This class describes the basic features of a human agent

    It should be extended to implement more specific features and behaviours
    """

    #: Dict of the profile's properties, with their specifications as a JSON schema
    PROPERTIES = {
        "walking_speed": {"description": "speed (in m/s) of the agents when they walk, "
                                         "if not specified by the topology",
                          "type": "number", "minimum": 0.01, "default": DEFAULT_WALKING_SPEED},
        "distance_factor": {"description": "distance factor used when computing "
                                           "approximate trips for Person agents",
                            "type": "number", "minimum": 0.01, "default": DEFAULT_DISTANCE_FACTOR}
    }

    def __init__(self, simulation_model, agent_id, origin, destination, origin_time, max_tries=None, **kwargs):
        """
        Initialize the new Person object, as a moving agent with specific user data.

        :param simulation_model:
        :param agent_id:
        :param origin: Origin position of the agent
        :param destination: Destination position of the agent
        :param origin_time: time at which the person should enter the simulation
        :param max_tries: maximum number of failed system tries before leaving the system.
            Default is None (infinite tries).
        :param kwargs:
        """

        super().__init__(simulation_model, agent_id, origin, **kwargs)

        # destination position of the agent, its spatial objective
        self.destination = destination

        # time at which the person should enter the simulation
        self.originTime = origin_time

        # number of failed system tries before leaving. If None, try indefinitely.
        self.maxTries = max_tries

        # profile of the agent, additional information that may be used by the models
        # these should be accessed using the profile dict
        self.profile = None
        self.init_profile(**kwargs)

        # persons start with no vehicle
        self.vehicle = None
        # time to wait when a request fails
        self.failTimeout = None

    def __str__(self):

        return "[id={}, origin={}, destination={}, vehicle={}]" \
            .format(self.id, self.origin, self.destination, self.vehicle)

    def init_profile(self, **kwargs):

        # build a profile dict
        profile = dict()

        for prop in self.PROPERTIES.keys():

            # look for the property in the agent input_dict (one value specified for each person)
            if prop in kwargs:
                profile[prop] = kwargs[prop]

            # look for the property in the simulation parameters (same value specified for all persons)
            elif prop in self.sim.parameters:
                profile[prop] = self.sim.parameters[prop]

            # look for the property in the default properties (no value specified, use default if possible)
            elif "default" in self.PROPERTIES[prop]:
                profile[prop] = self.PROPERTIES[prop]["default"]

            # signal missing property
            else:
                raise KeyError("Missing property '{}' for profile initialisation".format(prop))

        # validate the profile against the schema
        schema = {"type": "object", "properties": self.PROPERTIES}
        validate_against_schema(profile, schema)

        # set the profile attribute
        self.profile = profile

    def trace_event(self, event):
        """
        Add the event to the person's trace and to other relevant agents.

        In the case of a movement using a vehicle, the vehicle itself traces
        the movements of the agent.

        :param event: Event object to be added to the person's trace
        """

        # add event to agent trace
        super().trace_event(event)

        # add event to agent's vehicle trace
        try:
            if self.vehicle is not None:

                # relevant events for vehicle (move and position already called)
                if isinstance(event, GetVehicleEvent) or \
                        isinstance(event, LeaveVehicleEvent):
                    self.vehicle.trace_event(event)

        except AttributeError:
            # in case of generation event, agent don't have vehicle attribute already
            pass

        # add request events to requested agents
        if isinstance(event, RequestEvent):

            if event.request.structure is not None:
                event.request.structure.trace_event(event)

    # simulation interactions

    def move_shortest_with_vehicle_(self, destination=None, dimension="time"):
        """
        Call self.vehicle's move method.

        :param destination: agent destination, default is self.tempDestination
        :param dimension: minimised path length metric, default is time
        :return: yield the moving process of the agent's vehicle
        """

        # use the person's tempDest
        if destination is None:
            destination = self.tempDestination

        if self.vehicle is None:
            self.log_message("Tried to travel with vehicle but has None", 30)
            return
        else:
            yield self.execute_process(
                self.vehicle.move_(destination=destination, dimension=dimension))

    def walk_to_destination_(self):
        """
        Walk from current position to the destination position.

        :return:
        """
        # update tempDest
        self.tempDestination = self.destination

        # move to destination
        yield self.execute_process(self.move_())

        # trace destination reached event
        self.trace_event(DestinationReachedEvent(self.sim.scheduler.now()))

        # leave simulation with successful leave code
        self.leave_simulation(SUCCESS_LEAVE)

    def get_vehicle(self, vehicle):
        """
        Get the given vehicle.

        Set the agent's vehicle attribute, and add the agent to the
        vehicle occupants. This method should only be called after
        making sure the vehicle is available

        :param vehicle: Vehicle object
        """

        # get vehicle
        self.vehicle = vehicle
        vehicle.occupants.append(self)

        # trace event
        self.trace_event(GetVehicleEvent(
            self.sim.scheduler.now(), self, vehicle))

    def leave_vehicle(self):
        """
        Leave the currently owned vehicle.

        Set the agent's vehicle attribute, and add the agent to the
        vehicle occupants. This method should only be called after
        making sure the owner is allowed to leave the vehicle.
        """

        # check if agent has a vehicle
        if self.vehicle is None:
            self.log_message("Tried to leave vehicle without owning one", 30)
            return None

        # trace event
        self.trace_event(LeaveVehicleEvent(
            self.sim.scheduler.now(), self, self.vehicle))

        # leave vehicle
        self.vehicle.occupants.remove(self)
        self.vehicle = None

    def closest_walkable_node_of(self, mode, position=None, n=1,
                                 dimension="time", return_path=False):
        """
        Compute the closest node of the given mode that can be reached by walking.

        The node is computed by looking at the common nodes of the two modes. The default
        behaviour is then to look at the euclidean closest one (with n=1), but the shortest
        path can also be used. It can be returned with the result node.

        :param mode: mode that should be reached by walking
        :param position: departure position.
            Default is self.position.
        :param n: simplify the computation to the n euclidean closest nodes.
            Default is 1, we look at the euclidean closest node .
        :param dimension: dimension minimised for the shortest path.
            Default is "time".
        :param return_path: boolean indicating if the path should be returned.
            Default is False.
        :return: closest_node, or (closest_node, path) if return_path
        """

        # default position is self.position
        if position is None:
            position = self.position

        # get common nodes of the given modes
        intersection_set = self.sim.environment.get_common_nodes_of(["walk", mode])

        result = self.sim.environment.\
            closest_object(position, intersection_set, True, "walk",
                           dimension=dimension, position_lambda=lambda x: x,
                           return_path=return_path, n=n)

        return result

    # request methods
    # TODO : put these in a client class ?

    def try_new_request_(self):
        """
        Realise a new request according to the agent state.

        This method must be implemented according to the user's
        request mode

        :return: Request object, completed according to request result
        """

        pass

    def request_loop_(self, max_tentatives=None):
        """
        Loop over the requests and return the last one.

        This method allows the user to loop over a series of requests. The user
        either stop after succeeding in a request, or after reaching the
        maximum number of tentatives (which defaults to infinite). The creation
        and execution of new requests are realised by calling the try_new_request
        method, which must be implemented for the needs of the model.

        :param max_tentatives: number of failed requests until giving up
        :return: last Request object, completed according to request result
        """

        new_request = None
        success = False
        request_tentatives = 0

        if max_tentatives is None:
            max_tentatives = sys.maxsize

        while not success and request_tentatives < max_tentatives:

            # create a new request and try it
            new_request = yield self.execute_process(self.try_new_request_())

            # trace request event
            request_event = RequestEvent(self.sim.scheduler.now(), new_request)
            self.trace_event(request_event)

            # update request tentative and success
            request_tentatives += 1
            success = new_request.success

            # wait a bit
            if self.failTimeout is not None and not new_request.success:
                yield self.execute_process(self.spend_time_(self.failTimeout))

        return new_request

    def wait_for_request_(self, request, patience=None):
        """
        Wait for the given request, respecting a patience threshold.

        :param request: Request object
        :param patience: patience threshold, None corresponds to infinite patience
        :return: yield the request event, with a timeout event if patience is provided,
         and returns the request result
        """

        if patience is not None:
            result = yield request.event_ | self.sim.scheduler.timeout(patience)
        else:
            result = yield request.event_

        self.sim.scheduler.env.exit(result)

    def wait_trip_request_(self, request):

        # wait for the pickup
        yield request.pickupEvent_

        if self.vehicle is None:
            request.cancel()
            return False

        # wait for the dropoff
        yield request.dropoffEvent_

        if self.vehicle is not None:
            self.simulation_error("Has vehicle after dropoff")

        return True

    # TODO : request process unification

    def station_get_request(self, local_station):
        """
        Request (GET) the station at current position.

        :param local_station: Station object at current position
        :return: StationRequest object
        """

        # check position
        if self.position != local_station.position:
            self.log_message("Tried to request distant station", 40)

        # request vehicle
        request = local_station.get_from_store(self)

        self.log_message("Made a request : {}".format(request))

        return request

    def station_put_request(self, local_station):
        """
        Request (PUT) the station at current position.

        :param local_station: Station object at current position
        :return: StationRequest object
        """

        # check position
        if self.position != local_station.position:
            self.log_message("Tried to request distant station", 40)

        # request vehicle
        request = local_station.return_to_store(self, self.vehicle)

        self.log_message("Made a request : {}".format(request))

        return request
