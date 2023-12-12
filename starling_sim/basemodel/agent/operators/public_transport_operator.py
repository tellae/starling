from starling_sim.basemodel.agent.operators.operator import Operator
from starling_sim.utils.utils import get_sec, new_point_feature, stop_table_from_gtfs
from starling_sim.utils.constants import PUBLIC_TRANSPORT_TYPE
import pandas as pd
import numpy as np
import sys


class PublicTransportOperator(Operator):
    """
    Class describing an operator of a public transport service
    """

    SCHEMA = {
        "remove_props": ["fleet_dict", "stop_points_from"],
        "properties": {
            "extend_graph_with_stops": {
                "advanced": True,
                "title": "Extend graph with stops",
                "description": "Indicate if the transport network should be extended with stop points",
                "type": "boolean",
                "default": True,
            }
        },
    }

    OPERATION_PARAMETERS_SCHEMA = {
        "properties": {
            "use_shortest_path": {
                "title": "Use shortest path between stops",
                "description": "Follow the network shortest path between stops."
                " Otherwise, the trajectory is a straight line",
                "type": "boolean",
                "default": False,
            },
            "nb_seats": {
                "type": "object",
                "properties": {
                    "0": {
                        "title": "Tramways capacity",
                        "description": "Number of seats of tramways",
                        "type": "integer",
                        "minimum": 0,
                        "default": 440,
                    },
                    "1": {
                        "title": "Subways capacity",
                        "description": "Number of seats of subways",
                        "type": "integer",
                        "minimum": 0,
                        "default": 722,
                    },
                    "2": {
                        "title": "Trains capacity",
                        "description": "Number of seats of trains",
                        "type": "integer",
                        "minimum": 0,
                        "default": 2600,
                    },
                    "3": {
                        "title": "Buses capacity",
                        "description": "Number of seats of buses",
                        "type": "integer",
                        "minimum": 0,
                        "default": 166,
                    },
                },
                "required": ["0", "1", "2", "3"],
            },
            "service_vehicle_prefix": {
                "title": "Service vehicle prefix",
                "description": "Prefix of the service vehicles ids, prepended to the trip id",
                "type": "string",
                "minLength": 1,
                "default": "V-",
            },
            "line_shapes_file": {
                "type": "string",
                "title": "Line shapes file",
                "description": "Name of the file containing shapes of public transport lines (stored with GTFS feeds)",
                "pattern": "(.)*(.csv)",
            },
        },
        "required": ["use_shortest_path", "nb_seats", "service_vehicle_prefix"],
    }

    ROUTE_TYPE_ICONS = {"0": "tram", "1": "subway", "2": "train", "3": "bus"}

    FLEET_TYPE = PUBLIC_TRANSPORT_TYPE

    def __init__(
        self, simulation_model, agent_id, fleet_dict, extend_graph_with_stops=True, **kwargs
    ):
        super().__init__(
            simulation_model,
            agent_id,
            fleet_dict,
            stop_points_from="gtfs",
            extend_graph_with_stops=extend_graph_with_stops,
            **kwargs
        )

    def init_service_info(self):
        # get the complete timetables from simulation model
        feed = self.sim.gtfs

        # filter feed using simulation parameters

        # filter gtfs date
        date = self.sim.scenario["date"]
        feed = feed.restrict_to_dates([date])

        # filter gtfs routes
        if "routes" in self.operationParameters:
            feed = feed.restrict_to_routes(self.operationParameters["routes"])

        if feed.stop_times.empty:
            self.log_message(
                "Filtered gtfs is empty. Are you sure that there "
                "are trips running on the given date ?",
                30,
            )

        # keep all stops from the original gtfs
        feed.stops = self.sim.gtfs.stops

        self.service_info = feed

    def _stops_table_from_gtfs(self):
        # only keep active stop points
        stops_table = stop_table_from_gtfs(self.service_info, active_stops_only=True)

        return stops_table

    def init_trips(self):
        # add the active trips of the gtfs
        stop_times = self.service_info.get_stop_times()

        # only keep the first arrival time and filter with simulation time limit
        min_stop_sequence = stop_times["stop_sequence"].min()
        stop_times = stop_times[stop_times["stop_sequence"] == min_stop_sequence]
        stop_times = stop_times.sort_values(by="arrival_time")
        stop_times["arrival_time_num"] = stop_times["arrival_time"].apply(get_sec)
        stop_times = stop_times[stop_times["arrival_time_num"] < self.sim.scenario["limit"]]

        # create the planning of each trip
        for index, row in stop_times.iterrows():
            trip_planning = self.build_planning_of_trip(row["trip_id"])
            self.add_trip(None, trip_planning, trip_id=row["trip_id"])

    def get_route_and_direction_of_trip(self, trip_id):
        """
        Evaluate the route and direction of a trip using the service info.

        :param trip_id:
        :return:
        """

        trips = self.service_info.get_trips()

        route_id = trips.loc[trips["trip_id"] == trip_id, "route_id"].values[0]
        direction_id = trips.loc[trips["trip_id"] == trip_id, "direction_id"].values[0]

        return route_id, direction_id

    def create_public_transport_fleet(self):
        """
        Create a fleet for the public transport service.

        Services vehicles are generated using the block_id field of the gtfs.
        When no block id is provided for a trip, a vehicle dedicated to this single
        trip is generated.
        """

        # get trips ordered by first arrival time
        trips = self.service_info.get_trips()
        stop_times = self.service_info.get_stop_times()
        min_stop_sequence = stop_times["stop_sequence"].min()
        stop_times = stop_times[stop_times["stop_sequence"] == min_stop_sequence]
        stop_times["arrival_time_num"] = stop_times["arrival_time"].apply(get_sec)
        stop_times = stop_times[stop_times["arrival_time_num"] < self.sim.scenario["limit"]]
        trips = pd.merge(trips, stop_times, on="trip_id")
        trips = trips.sort_values(by="arrival_time")

        # get the block_id values
        if "block_id" not in trips.columns:
            trips["block_id"] = np.nan
            block_ids = [np.nan]
        else:
            block_ids = trips.drop_duplicates(subset="block_id")["block_id"].values

        for block_id in block_ids:
            if pd.isna(block_id):
                block_trips = trips[pd.isna(trips["block_id"])]["trip_id"].values
                # if block_id is nan, generate separate vehicles for each trip
                for trip_id in block_trips:
                    vehicle_id = self.operationParameters["service_vehicle_prefix"] + trip_id
                    self.create_service_vehicle(vehicle_id, [trip_id])
            else:
                block_trips = trips[trips["block_id"] == block_id]["trip_id"].values
                # otherwise, generate a vehicle with multiple with multiple trips
                vehicle_id = self.operationParameters["service_vehicle_prefix"] + block_id
                self.create_service_vehicle(vehicle_id, block_trips)

    def create_service_vehicle(self, agent_id, trip_id_list):
        """
        Create a new service vehicle in the simulation.

        :param agent_id: id of the new vehicle
        :param trip_id_list: list of trips to be realised by service the vehicle
        """

        # get the route type from the first trip of the vehicle
        trips = self.service_info.get_trips()
        trip_id = trip_id_list[0]
        route_id = trips.loc[trips["trip_id"] == trip_id, "route_id"].iloc[0]
        routes = self.service_info.get_routes()
        route_type = str(routes.loc[routes["route_id"] == route_id, "route_type"].iloc[0])

        # get the agent icon from route type
        if route_type in self.ROUTE_TYPE_ICONS:
            agent_icon = self.ROUTE_TYPE_ICONS[route_type]
        else:
            self.log_message("Route type {} not in icon dict".format(route_type), 30)
            agent_icon = "bus"

        # get the number of seats from route type
        nb_seats_dict = self.operationParameters["nb_seats"]
        if route_type in nb_seats_dict:
            nb_seats = nb_seats_dict[route_type]
        else:
            self.log_message("Route type {} not in nb_seats dict".format(route_type), 30)
            nb_seats = sys.maxsize

        # get the origin from the first planning
        origin = self.trips[trip_id][1][0].position

        # build the service vehicle properties dict
        input_properties = {
            "agent_id": agent_id,
            "origin": origin,
            "operator_id": self.id,
            "seats": nb_seats,
            "agent_type": self.FLEET_TYPE,
            "mode": self.mode["fleet"],
            "icon": agent_icon,
        }

        # build a geojson feature
        feature = new_point_feature(properties=input_properties)

        # generate the service vehicle in the simulation
        new_vehicle = self.new_service_vehicle(feature)

        # set the new vehicle trip list
        new_vehicle.tripList = trip_id_list

        for trip_id in trip_id_list:
            self.trips[trip_id][0] = agent_id

    def build_planning_of_trip(self, trip_id):
        """
        Build the planning corresponding to the trip from the gtfs.

        :param trip_id: gtfs trip_id
        :return: trip planning, list of StopPoint objects
        """

        trip_planning = []

        # get the trip stop times
        stop_times = self.service_info.get_stop_times()
        stop_times = stop_times[stop_times["trip_id"] == trip_id]

        for index, row in stop_times.iterrows():
            stop_point = self.stopPoints[row["stop_id"]]

            # append stop point to planning
            trip_planning += [stop_point]

            # set service times in stop point
            if trip_id not in stop_point.arrivalTime:
                stop_point.arrivalTime[trip_id] = [get_sec(row["arrival_time"])]
            else:
                stop_point.arrivalTime[trip_id] += [get_sec(row["arrival_time"])]

            if trip_id not in stop_point.departureTime:
                stop_point.departureTime[trip_id] = [get_sec(row["departure_time"])]
            else:
                stop_point.departureTime[trip_id] += [get_sec(row["departure_time"])]

        return trip_planning

    def loop_(self):
        self.create_public_transport_fleet()
        yield self.execute_process(self.spend_time_(1))
