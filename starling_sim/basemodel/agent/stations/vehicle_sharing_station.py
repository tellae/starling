import simpy

from starling_sim.basemodel.agent.stations.station import Station
from starling_sim.basemodel.agent.requests import StationRequest


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
                "minimum": 0
            }
        },
        "required": ["capacity"]
    }

    def __init__(self, simulation_model, agent_id, origin, capacity, **kwargs):

        Station.__init__(self, simulation_model, agent_id, origin, **kwargs)

        self.capacity = capacity
        self.initial_stock = 0
        self.store = simpy.Store(self.sim.scheduler.env, capacity=capacity)

    def __str__(self):

        return "[id={}, position={}, capacity={}, initialStock={}]" \
            .format(self.id, self.position, self.capacity, self.initial_stock)

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

        request = StationRequest(agent, self.sim.scheduler.now(),
                                 self, StationRequest.GET_REQUEST)

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

            request = StationRequest(agent, self.sim.scheduler.now(),
                                     self, StationRequest.PUT_REQUEST)

            request.set_request_event(self.store.put(product))

            return request
        else:
            self.log_message("Received wrong type of product ({}) from {}"
                             .format(type(product), agent.id))
            return None

    def set_products(self, products):
        """
        Sets the products contained in the store
        :param products: list of products, type is not checked
        :return:
        """

        self.store.items = products
