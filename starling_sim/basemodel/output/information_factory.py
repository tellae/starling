from starling_sim.basemodel.trace.events import *
from starling_sim.basemodel.agent.vehicles.vehicle import Vehicle
from starling_sim.basemodel.agent.stations.vehicle_sharing_station import VehicleSharingStation
from starling_sim.utils.constants import END_OF_SIM_LEAVE

from abc import ABC
import logging


class InformationFactory(ABC):
    """
    Generic structure of a geojson information factory.

    Its subclasses put together specific information to add in the geojson features,
    in the 'information' property.
    """

    #: Default key used in the 'information' property
    DEFAULT_KEY = "key"

    def __init__(self, information_key=None):
        """
        Initialise the structures containing the information to add to each feature.

        Information is stored based on an event structure. An initial value is stored,
        and then only changes in the information value are listed, along with the
        timestamp of the change.

        :param information_key:
        """

        # simulation model
        self.sim = None

        # list of values for the information
        self.values = []

        # list of timestamps for the information
        self.timestamps = []

        # name of the information, used as a key in the information property dict
        if information_key is None:
            self.key = self.DEFAULT_KEY
        else:
            self.key = information_key

    def setup(self, simulation_model):
        """
        Setup method called during simulation setup.

        :param simulation_model:
        """
        self.sim = simulation_model

    def get_dict(self):
        """
        Get the dict to add in the 'information' property.

        :return: dict with keys 'values' and 'timestamps'.
        """

        # log a warning if values and timestamps are of different lengths
        if len(self.values) != len(self.timestamps):
            logging.warning(
                "Values and timestamps of information {} have different lengths.".format(self.key)
            )
            return dict()

        information_dict = {"values": self.values, "timestamps": self.timestamps}

        # reset the information structures
        self.new_information_dict()

        return information_dict

    def new_information_dict(self):
        """
        Reset the structures containing the information.
        """
        self.values = []
        self.timestamps = []

    def append_value_and_timestamp(self, value, timestamp):
        """
        Append a value and its timestamp to the information structures.

        Avoids appending only one of the structures.

        :param value:
        :param timestamp:
        """

        self.values.append(value)
        self.timestamps.append(timestamp)

    def update(self, event, agent):
        """
        Update the information structures according to the event content and agent.

        :param event:
        :param agent:
        """
        pass


class ActivityInformation(InformationFactory):
    """
    This factory traces the activity of agents.
    """

    DEFAULT_KEY = "activity"

    def update(self, event, agent):

        if isinstance(event, InputEvent):
            self.append_value_and_timestamp(0, 0)

            start_of_activity_timestamps = agent.trace.eventList[1].timestamp
            self.append_value_and_timestamp(1, start_of_activity_timestamps)

        if isinstance(event, LeaveSimulationEvent):
            end_of_activity_timestamps = agent.trace.eventList[-2].timestamp

            self.append_value_and_timestamp(0, end_of_activity_timestamps)


class StockInformation(InformationFactory):
    """
    This factory traces the stock of vehicles and stations.
    """

    DEFAULT_KEY = "stock"

    def update(self, event, agent):

        if isinstance(agent, VehicleSharingStation):

            if isinstance(event, InputEvent):
                self.append_value_and_timestamp(agent.initial_stock, 0)

            elif isinstance(event, RequestEvent) and event.request.success:

                request = event.request

                if request.type == request.GET_REQUEST:
                    value = self.values[-1] - 1
                elif request.type == request.PUT_REQUEST:
                    value = self.values[-1] + 1
                else:
                    return

                self.append_value_and_timestamp(value, event.timestamp)

        elif isinstance(agent, Vehicle):

            if isinstance(event, InputEvent):
                self.append_value_and_timestamp(0, 0)

            elif isinstance(event, GetVehicleEvent):

                value = self.values[-1] + 1
                self.append_value_and_timestamp(value, event.timestamp)

            elif isinstance(event, LeaveVehicleEvent):

                value = self.values[-1] - 1
                self.append_value_and_timestamp(value, event.timestamp)


class DelayInformation(InformationFactory):
    """
    This factory traces the delay of service vehicles compared to the timetable.
    """

    DEFAULT_KEY = "delay"

    def update(self, event, agent):

        if isinstance(event, InputEvent):

            self.append_value_and_timestamp(0, event.timestamp)

        elif isinstance(event, StopEvent):

            # get the theoretical departure time
            service_info = agent.operator.service_info
            stop_times = service_info.get_stop_times()
            theo_departure_time = stop_times[
                (stop_times["trip_id"] == event.trip) & (stop_times["stop_id"] == event.stop.id)
            ]["departure_time_num"].values[0]

            # compute the delay
            delay = int((event.pickup_time - theo_departure_time) / float(60))

            # format the delay information
            if delay > 0:
                delay = "+" + str(delay)
            else:
                delay = str(delay)

            # append the information
            self.append_value_and_timestamp(delay, event.pickup_time)
