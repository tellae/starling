import simpy

from starling_sim.basemodel.agent.stations.station import Station
from starling_sim.basemodel.agent.vehicles.station_based_vehicle import StationBasedVehicle
from starling_sim.basemodel.agent.requests import StationRequest
from starling_sim.utils.utils import new_point_feature


class VehicleSharingStation(Station):
    """
    Station dedicated to a shared vehicle system
    """

    SCHEMA = {
        "properties": {
            "capacity": {
                "type": "integer",
                "title": "Station capacity",
                "description": "Maximum storing capacity of the station",
                "minimum": 0,
            },
            "stock_generation": {
                "title": "Stock generation information",
                "description": "Information for the dynamic generation of vehicles at the station. "
                "Generation is performed after the initialisation of the static inputs.",
                "type": "object",
                "properties": {
                    "generated_stock": {
                        "title": "Generated stock",
                        "description": "Generated vehicle stock of the station",
                        "type": "integer",
                        "minimum": 0,
                        "default": 0,
                    },
                    "id_format": {
                        "title": "ID format",
                        "description": "ID format of the generated agents. Placeholders: {station}, {count}",
                        "type": "string",
                        "default": "B-{station}-{count}",
                    },
                    "seats": {
                        "title": "Vehicles seats",
                        "description": "Number of seats of the generated vehicles",
                        "type": "integer",
                        "minimum": 0,
                        "default": 1,
                    },
                    "icon": {
                        "title": "Vehicles icon",
                        "description": "Icon of the generated vehicles",
                        "type": "string",
                        "default": "bike",
                    },
                },
            },
        },
        "required": ["capacity"],
    }

    def __init__(
        self, simulation_model, agent_id, origin, capacity, stock_generation=None, **kwargs
    ):

        Station.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.capacity = capacity
        self.initial_stock = 0
        self.store = simpy.Store(self.sim.scheduler.env, capacity=capacity)

        self.stock_generation = stock_generation

    def __str__(self):

        return "[id={}, position={}, capacity={}, initialStock={}]".format(
            self.id, self.position, self.capacity, self.initial_stock
        )

    def create_station_based_vehicles(self, stock_generation):

        generated_stock = stock_generation["generated_stock"]

        if generated_stock > self.capacity:
            raise ValueError(
                "Provided initial stock exceeds the station's capacity "
                "(initialising station {})".format(self.id)
            )

        # get agent_type of the model StationBasedVehicle agent
        station_based_vehicle_type = None
        for agent_type in self.sim.agent_type_class:
            if issubclass(self.sim.agent_type_class[agent_type], StationBasedVehicle):
                station_based_vehicle_type = agent_type
                break
        if station_based_vehicle_type is None:
            raise ValueError(
                "Could not find an agent class that corresponds to a station-based vehicle"
            )

        for i in range(generated_stock):

            input_dict = {
                "agent_id": stock_generation["id_format"].format(
                    station=self.id, count=self.initial_stock
                ),
                "agent_type": station_based_vehicle_type,
                "mode": self.mode,
                "icon": stock_generation["icon"],
                "seats": stock_generation["seats"],
                "station": self.id,
            }

            if self.operator is not None:
                input_dict["operator_id"] = self.operator.id

            self.sim.dynamicInput.new_agent_input(new_point_feature(properties=input_dict))

    def get_store(self):
        """
        Returns the station's store
        :return:
        """
        return self.store

    def nb_products(self):
        """
        Returns the number of products in store
        :return:
        """
        return len(self.store.items)

    def get_from_store(self, agent):
        """
        Requests a product from the station's store
        :param agent: requesting agent
        :return: StationRequest object
        """

        request = StationRequest(agent, self.sim.scheduler.now(), self, StationRequest.GET_REQUEST)

        request.set_request_event(self.store.get())

        return request

    def check(product):
        """
        Tests the type of the product according to the type of store
        This method must be extended for specific stations
        :param product: product to be tester
        :return:
        """

        return True

    check = staticmethod(check)

    def return_to_store(self, agent, product):
        """
        Tries to return a product in the station's store
        :param agent: agent returning product
        :param product: returned product
        :return: StationRequest object
        """

        if self.check(product):

            request = StationRequest(
                agent, self.sim.scheduler.now(), self, StationRequest.PUT_REQUEST
            )

            request.set_request_event(self.store.put(product))

            return request
        else:
            self.log_message(
                "Received wrong type of product ({}) from {}".format(type(product), agent.id)
            )
            return None

    def set_products(self, products):
        """
        Sets the products contained in the store
        :param products: list of products, type is not checked
        :return:
        """

        self.store.items = products

    def loop_(self):

        # generate vehicles at this station
        if self.stock_generation is not None:
            self.create_station_based_vehicles(self.stock_generation)

        yield self.execute_process(self.spend_time_())
