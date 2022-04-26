"""
This module contains the classes dedicated to trace agent activities
during the simulation. Events describes different kind of traced
activities and are generated during the simulation.

/!\\ It is should be mentioned that the event objects store in the trace
point to objects that may be modified by the end of the simulation.
For instance, given a GenerationEvent, display the 'position' attribute of the
generated agent at the end of the simulation will output its final
position in the simulation, and not its origin.
"""

from starling_sim.utils.simulation_logging import TRACED_LOGGER, AGENT_LEVEL
from starling_sim.basemodel.trace.events import LeaveSimulationEvent
from starling_sim.utils.constants import END_OF_SIM_LEAVE


class Trace:
    """
    This class represents the trace of a simulation element

    It contains events that describe their states and actions
    """

    def __init__(self):
        """
        Start with empty event list
        """
        self.eventList = []

    def add_event(self, event):
        """
        :param event: Event object, describing the traced event
        :return:
        """
        self.eventList.append(event)


class Traced:
    """
    This class represents a traced element of the simulation

    Other classes may extend it to be able to trace their actions
    """

    def __init__(self, element_id):
        """
        Construction of a new traced element
        The trace must have access to the simulation model
        :param: element_id: traced element id
        """

        self.sim = None
        self.id = element_id
        self.trace = Trace()

    def __str__(self):
        """
        Give a string display to the simulation element
        """

        return "[id={}]".format(self.id)

    def __repr__(self):
        """
        Give a string display to the simulation element
        """

        return self.__str__()

    def trace_event(self, event):
        """
        Adds a Event to the trace, with the current timestamp
        :param event: Traced event
        :return:
        """
        self.trace.add_event(event)

    def log_message(self, message, lvl=AGENT_LEVEL):
        """
        Logs the message in the logger using the class data

        :param message: Message displayed in agent log
        :param lvl: level value, default is AGENT_LEVEL
        """

        extra_params = {"id": self.id}

        if self.sim is not None:
            extra_params["timestamp"] = self.sim.scheduler.now()
        else:
            extra_params["timestamp"] = "--"

        TRACED_LOGGER.log(lvl, message, extra=extra_params)


def trace_simulation_end(simulation_model):
    """
    Adds a LeaveSimulationEvent with cause end of simulation to
    all agents that didn't leave during the simulation.
    """

    for agent in simulation_model.agentPopulation.get_total_population():
        if not isinstance(agent.trace.eventList[-1], LeaveSimulationEvent):
            agent.trace_event(
                LeaveSimulationEvent(simulation_model.scheduler.now(), agent, END_OF_SIM_LEAVE)
            )
