from starling_sim.basemodel.algorithms.algorithm import Algorithm
from starling_sim.basemodel.agent.requests import Operation
from starling_sim.utils.utils import json_load
from starling_sim.basemodel.trace.events import StaffOperationEvent
import random


class PalZhangGCH(Algorithm):

    NAME = "PalZhangGCH"

    SCHEMA = {
        "type": "object",
        "properties": {
            "start_times": {
                "title": "Relocation start times",
                "description": "Times at which relocations will be performed",
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "default": [25000],
            },
            "durations": {
                "title": "Relocation durations",
                "description": "Durations of each relocation operation",
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "default": [12000],
            },
            "neighbor": {
                "title": "Neighbor evaluation method",
                "description": "Method for evaluating the station where the next relocation will take place",
                "type": "string",
                "oneOf": [
                    {"const": "util", "title": "Station with max utility (operations/time)"},
                    {"const": "nearest", "title": "Nearest station"},
                    {"const": "random", "title": "Random station"},
                ],
                "default": "util",
            },
            "threshold": {
                "type": "object",
                "properties": {
                    "min": {
                        "title": "Lower stock threshold",
                        "description": "Avoided lower stock threshold, if possible. "
                        "If integer, distance from empty station. "
                        "If between 0 and 1, the distance is computed as a fraction of "
                        "the station capacity",
                        "type": "number",
                        "default": 0.1,
                    },
                    "max": {
                        "title": "Upper stock threshold",
                        "description": "Avoided upper stock threshold, if possible. "
                        "If integer, distance from the station capacity. "
                        "If between 0 and 1, the distance is computed as a fraction of "
                        "the station capacity",
                        "type": "number",
                        "default": 0.1,
                    },
                },
            },
            "priority_threshold": {
                "title": "Priority threshold",
                "description": "Prioritised threshold when both cannot be respected",
                "type": "string",
                "oneOf": [
                    {"const": "max", "title": "Maximum"},
                    {"const": "min", "title": "Minimum"},
                ],
                "default": "max",
            },
        },
    }

    def __init__(self, simulation_model, operator, verb=False):

        super().__init__(simulation_model=simulation_model, operator=operator, verb=verb)

        # PalZhangGCH parameters

        # start times of the repositioning operations
        self.start_times = self.operator.operationParameters["start_times"]

        # duration of the operations
        self.durations = self.operator.operationParameters["durations"]

        # mode of neighbor selection
        self.neighbor = self.operator.operationParameters["neighbor"]

        self.threshold = self.operator.operationParameters["threshold"]

        self.priority_threshold = self.operator.operationParameters["priority_threshold"]

        # PalZhangGCH variables

        # demand at each station
        self.demand_dict = None

        # current simulation time
        self.current_time = None

        # time limit for the repositioning operations
        self.time_limit = None

        # current station node
        self.current_node = None

        # dict of relative number of operations needed at each station
        self.operations_needed = None

        # planning built by the algorithm
        self.planning = None

        # service vehicle (only one for this dispatch)
        self.vehicle = None

        # capacity of the repositioning vehicle
        self.vehicle_capacity = None

        # mode of the repositioning vehicle
        self.vehicle_mode = None

        # mode of the repositioning vehicle
        self.vehicle_dwell_time = None

        # depot of the repositioning vehicles
        self.depot = None

    def setup_new_run(self):

        if self.demand_dict is None:
            self.demand_dict = self.init_demand_dict()

        # consider only a single depot for now
        self.depot = list(self.operator.depotPoints.values())[0]

        self.planning = []
        self.append_depot_to_planning()

        self.current_node = self.depot.id
        self.current_time = self.sim.scheduler.now()

        if self.durations is not None:
            i = self.start_times.index(self.current_time)
            duration = self.durations[i]

            self.time_limit = self.current_time + duration

        self.operations_needed = self.compute_operations_needed()

        self.vehicle = list(self.operator.staff.values())[0]
        self.vehicle_capacity = self.vehicle.seats
        self.vehicle_mode = self.vehicle.mode
        self.vehicle_dwell_time = self.vehicle.dwellTime

    def run(self):

        # log algorithm start
        self.log_message("Start of the PalZhangGCH")

        max_operations = self.maximum_operations()

        while any(max_operations.values()):

            next_node, travel_time = self.select_next_neighbor(self.current_node, max_operations)

            if next_node in self.operator.stations:
                next_node_position = self.operator.stations[next_node].position
            else:
                next_node_position = self.operator.depotPoints[0].position
            end_time = self.current_time + travel_time + self.vehicle_dwell_time

            if self.breaking_condition(end_time):
                # TODO : what to do with current load ?
                self.log_message("End of planning due to limited operation duration")
                failed_get = 0
                failed_put = 0
                for op_needed in self.operations_needed.values():
                    if op_needed < 0:
                        failed_get -= op_needed
                    elif op_needed > 0:
                        failed_put += op_needed

                get_event = StaffOperationEvent(
                    self.sim.scheduler.now(), self.vehicle, 0, failed_get
                )
                put_event = StaffOperationEvent(
                    self.sim.scheduler.now(), self.vehicle, 0, failed_put
                )
                self.vehicle.trace_event(get_event)
                self.vehicle.trace_event(put_event)
                break

            operation = Operation(
                Operation.REPOSITIONING,
                next_node_position,
                max_operations[next_node],
                station_id=next_node,
            )

            operation.arrivalTime = int(self.current_time + travel_time)
            operation.departureTime = int(self.current_time + travel_time + self.vehicle_dwell_time)

            self.log_message("New operation {}".format(operation), lvl=10)

            # add the operation to the planning
            self.planning.append(operation)
            self.operations_needed[next_node] -= max_operations[next_node]
            self.current_time = end_time
            self.current_node = next_node
            max_operations = self.maximum_operations()

        self.append_depot_to_planning()

    def breaking_condition(self, end_time):
        # TODO : have a better breaking condition
        if self.time_limit is not None and end_time > self.time_limit:
            return True

        else:
            return False

    def compute_operations_needed(self):

        operations_needed = dict()

        for station in self.operator.stations.values():

            initial_stock = len(station.store.items)
            target_stock = self.compute_station_target_stock(station.id)
            operations_needed[station.id] = target_stock - initial_stock
            # self.log_message("So operations needed = {}".format(operations_needed[station.id]))

        return operations_needed

    def compute_station_target_stock(self, station_id):
        station = self.operator.stations[station_id]
        capacity = station.capacity

        if 0 < self.threshold["min"] < 1:
            threshold_min = int(self.threshold["min"] * capacity)
        else:
            threshold_min = self.threshold["min"]

        if 0 < self.threshold["max"] < 1:
            threshold_max = int((1 - self.threshold["max"]) * capacity)
        else:
            threshold_max = capacity - self.threshold["max"]

        # self.log_message("Station {}".format(station))
        # self.log_message("Current stock is {}".format(len(station.store.items)))
        variation = self.compute_station_variation(station_id)
        # self.log_message("|{}| < {}".format(variation, capacity - self.threshold["max"] - self.threshold["min"]))
        outrange = variation > threshold_max - threshold_min
        # self.log_message("Stock variation is {}".format(variation))
        target_stock = len(station.store.items) - variation

        if target_stock < threshold_min:

            if outrange and self.priority_threshold == "max":
                target_stock = max(0, threshold_max - variation)
            else:
                target_stock = threshold_min

        elif target_stock > threshold_max:

            if outrange and self.priority_threshold == "min":
                target_stock = min(capacity, threshold_min + variation)
            else:
                target_stock = threshold_max
        # self.log_message("So target stock is {}".format(target_stock))
        return target_stock

    def compute_station_variation(self, station_id):

        index = self.start_times.index(self.current_time)
        if index == len(self.start_times) - 1:
            horizon = self.sim.scenario["limit"]
        else:
            horizon = self.start_times[index + 1]

        station_demand = self.demand_dict[station_id]

        relevant_demand = []

        for demand in station_demand:
            if self.current_time < demand[0] < horizon:
                relevant_demand.append(demand)

        variation = 0
        for demand in relevant_demand:
            variation += demand[1]

        return variation

    def maximum_operations(self):

        max_operations = dict()

        current_load = 0
        for operation in self.planning:
            current_load -= operation.total

        for station in self.operator.stations.values():

            operation_needed = self.operations_needed[station.id]

            # positive operation corresponds to a dropoff
            if operation_needed > 0:
                maximum_operation = min(operation_needed, current_load)
            # negative operation corresponds to a pickup
            elif operation_needed < 0:
                maximum_operation = max(operation_needed, current_load - self.vehicle_capacity)
            # if no operation is needed, max operation is 0
            else:
                maximum_operation = 0

            max_operations[station.id] = maximum_operation

        return max_operations

    def select_next_neighbor(self, current_station_id, max_operations):

        # get the current station
        if current_station_id in self.operator.stations:
            current_station = self.operator.stations[current_station_id]
        else:
            current_station = self.depot

        travel_time = dict()
        # TODO : work on the stations of max_operations, to allow removing some
        for station in self.operator.stations.values():

            # ignore current station in neighbor evaluation
            if station.id == current_station_id:
                continue

            # compute travel time to other stations
            travel_time[station.id] = self.sim.environment.topologies[
                self.vehicle_mode
            ].shortest_path_length(current_station.position, station.position, None)

        # evaluate the next neighbor according to the neighbor parameter
        if self.neighbor == "nearest":
            neighbor = min(travel_time, key=travel_time.get)
        elif self.neighbor == "util":

            def utility(s):
                return float(abs(max_operations[s])) / max(1, travel_time[s])

            neighbor = max(travel_time, key=utility)
        elif self.neighbor == "random":
            neighbor = random.sample(list(travel_time.keys()), 1)[0]
        else:
            self.log_message("Unknown neighbor evaluation '{}'".format(self.neighbor))
            neighbor = None

        return neighbor, travel_time[neighbor]

    def append_depot_to_planning(self):

        operation = Operation(None, self.depot.position, 0, station_id=self.depot.id)
        self.planning.append(operation)

    def init_demand_dict(self):

        features = self.sim.dynamicInput.feature_list_from_file(
            self.sim.scenario["dynamic_input_file"]
        )
        self.sim.dynamicInput.pre_process_position_coordinates(features)
        demand_dict = {station: [] for station in self.operator.stations.keys()}

        for user_dict in features:
            origin = user_dict["properties"]["origin"]
            destination = user_dict["properties"]["destination"]
            origin_time = user_dict["properties"]["origin_time"]

            origin_station = self.sim.environment.euclidean_n_closest(
                origin, self.operator.stations.values(), 1
            )[0]

            travel_time = self.sim.environment.topologies["walk"].shortest_path_length(
                origin, origin_station.position, None
            )
            origin_station_time = origin_time + travel_time

            demand_dict[origin_station.id].append([origin_station_time, -1])

            destination_station = self.sim.environment.euclidean_n_closest(
                destination, self.operator.stations.values(), 1
            )[0]

            travel_time = self.sim.environment.topologies[
                self.operator.mode["fleet"]
            ].shortest_path_length(origin_station.position, destination_station.position, None)

            destination_station_time = origin_station_time + travel_time
            demand_dict[destination_station.id].append([destination_station_time, 1])

        for station in demand_dict.keys():
            demand_dict[station] = sorted(demand_dict[station], key=lambda x: x[0])

        return demand_dict
