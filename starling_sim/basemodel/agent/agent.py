from starling_sim.basemodel.trace.trace import Traced
from starling_sim.basemodel.trace.events import InputEvent, WaitEvent, LeaveSimulationEvent
from starling_sim.utils.utils import SimulationError, LeavingSimulation
from starling_sim.utils.constants import DEFAULT_LEAVE, SIM_ERROR_LEAVE

import traceback
import copy
import logging


class Agent(Traced):
    """
    This class describes the basic features of a simulation agent.

    It should be extended (through several layers) to give more specific features and behaviours
    (represented by their available methods), to finally implement a concrete agent that can be
    simulated in a specific model.
    """

    SCHEMA = {
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "title": "Agent ID", "description": "Unique identifier"},
            "agent_type": {
                "type": "string",
                "title": "Agent type",
                "description": "One of the model's agent types",
            },
            "mode": {
                "type": "string",
                "title": "Default network",
                "description": "Road network used by the agent",
            },
            "icon": {"type": "string", "title": "Agent icon", "description": "Display icon"},
        },
        "required": ["agent_id", "agent_type", "mode", "icon"],
    }

    @classmethod
    def get_schema(cls):
        """
        Compute and return the class parameters schema.

        This is the place to add eventual schema post-processing

        :return: class schema
        """
        return cls.compute_schema()

    @classmethod
    def compute_schema(cls):
        """
        Get the json schema that specifies the class init parameters.

        The schema is generated recursively, by adding/mixing the properties
        of the current class to the schema of its parent class.

        :return: json schema of the class init parameters
        """

        # stop recursion at Agent class
        parent_class = cls.__bases__[0]
        if issubclass(parent_class, Agent):

            # start by evaluating the schema of the parent class
            schema = copy.deepcopy(parent_class.compute_schema())

            # if the current class has a specific schema, update the parent schema
            class_schema = cls.SCHEMA
            if class_schema and parent_class.SCHEMA != class_schema:
                cls.update_class_schema(schema, class_schema, cls)

        else:
            schema = cls.SCHEMA

        return schema

    def update_class_schema(base_schema, class_schema, the_class, catch_error=True):
        try:
            for keyword in class_schema.keys():

                # custom remove_props keyword, used for removing properties of parent schema
                if keyword == "remove_props":
                    for prop in class_schema["remove_props"]:
                        # remove the property from the base schema
                        del base_schema["properties"][prop]
                        # remove the property from the base schema required
                        if prop in base_schema["required"]:
                            base_schema["required"].remove(prop)

                # add the required properties to the parent schema
                elif keyword == "required":
                    for prop in class_schema["required"]:
                        if prop not in base_schema["required"]:
                            base_schema["required"].append(prop)

                # update and complete the parent schema properties
                elif keyword == "properties":
                    base_schema["properties"].update(class_schema["properties"])

                # add/replace other attributes
                else:
                    base_schema[keyword] = class_schema[keyword]

        except Exception as e:
            if catch_error:
                raise SimulationError(
                    "Schema generation of class {} failed with the following error: {}".format(
                        the_class.__name__, str(e)
                    )
                )
            else:
                raise e

    update_class_schema = staticmethod(update_class_schema)

    def __init__(self, simulation_model, agent_id, agent_type, mode, icon=None, **kwargs):
        """
        Initialize an agent with basic attributes (id, simulation model, etc).

        :param simulation_model:
        :param agent_id:
        :param agent_type: information about the agent's type
        :param mode: main mode of the agent, corresponds to a topology
        :param icon: icon used for the visualisation
        :param kwargs:
        """

        super().__init__(agent_id)

        self.sim = simulation_model
        self.type = agent_type
        self.mode = mode
        self.icon = icon

        # the agent profile contains all the additional properties of the input dict
        self.profile = kwargs

        self.name = None
        self.main_process = None
        self.current_process = None

        self.trace_event(InputEvent(self.sim.scheduler.now(), self))

    def execute_process(self, generator, store_process=False):
        """
        Create a process from the given generator and make it current process.

        The process is obtained from the given generator using the scheduler.
        It can be set as the current_process attribute in order to access it later,
        for interrupting it for instance.

        :param generator: Python generator method
        :param store_process: indicates if the process should be stored in self.current_process
        :return: Created SimPy Process object
        """

        process = self.sim.scheduler.new_process(generator)

        if store_process:
            self.current_process = process

        return process

    def spend_time_(self, duration="inf"):
        """
        Allow the simulation to flow while realising something, for the given duration.

        :param duration: wait duration, default is "inf" and leads to simulation limit
        :return: yield a timeout event with provided duration
        """

        # check that duration is integer
        if duration != "inf":
            int_duration = int(duration)

            if duration - int_duration != 0:
                self.log_message("Non integer time to spend : {}".format(duration), 40)
            else:
                duration = int_duration

        yield self.sim.scheduler.timeout(duration)

    def wait_(self, duration="inf", reason=None, message=""):
        """
        Wait during the given duration and trace a WaitEvent.

        :param duration: wait duration.
            Default is "inf" and leads to simulation limit.
        :param reason: reason of the wait time.
            Default is None.
        :param message: message for the wait event.
            Default is "".

        :return: yield a spend_time process with provided duration
        """

        wait_event = WaitEvent(
            time=self.sim.scheduler.now(), reason=reason, waiting_time=duration, message=message
        )

        yield self.execute_process(self.spend_time_(duration))

        self.trace_event(wait_event)

    def simpy_loop_(self):
        """
        Run the loop of the agent and catch simulation exceptions.

        This method is the main SimPy process of the agent, added to the
        SimPy environment by the DynamicInput class.
        """

        # set a default cause, to identify unmonitored leaving cases
        cause = DEFAULT_LEAVE

        # run the agent loop
        try:
            yield self.execute_process(self.loop_())

        # catch the LeavingSimulation exceptions
        except LeavingSimulation as e:

            # for simulation errors, log an specific message
            if isinstance(e, SimulationError):
                self.log_message("Encountered simulation error with message : {}".format(e), 40)
                self.log_message(traceback.print_exc(), 10)
                cause = SIM_ERROR_LEAVE

            # otherwise, log the cause description
            else:
                cause = str(e)
                cause_desc = self.sim.leaving_codes[cause]
                self.log_message("Leaving simulation: {} ({})".format(cause_desc, cause))

        # trace a LeaveSimulationEvent containing the leaving code
        event = LeaveSimulationEvent(self.sim.scheduler.now(), self, cause)
        self.trace_event(event)

        return

    def loop_(self):
        """
        This method represents the life cycle of an agent.

        The loop process will be added to the simulation environment
        after the agent creation. Agents may perform actions that have a duration.
        They must then yield other processes such as waiting or moving, and will
        resume at the end of their action.

        The loop must be extended to represent a specific behavior,
        using possibly inherited methods.
        """

        yield self.execute_process(self.spend_time_())

    def leave_simulation(self, cause):
        """
        Raise a LeavingSimulation exception to make the agent leave its loop and terminate its process.

        The cause is a leaving code that should be listed in the simulation model.
        It corresponds to a specific reason for the agent to leave the simulation.

        :param cause: leaving code
        :raises LeavingSimulation:
        """

        raise LeavingSimulation(cause)

    def simulation_error(self, description):
        """
        Raise a SimulationError exception to make the agent leave the
        simulation following a simulation error.

        This method should be called when an unwanted
        event occurs in a simulation, like saying "We shouldn't be here".

        :param description: description of the unwanted event
        :raises SimulationError:
        """

        raise SimulationError(description)

    def interrupt(self, message=""):
        """
        Interrupts the process contained in the current_process attribute.

        This process must handle the interruption exception
        """

        log_message = "Interrupted in its current process"

        if message != "":
            log_message += " with message : '{}'".format(message)

        self.log_message(log_message)

        self.sim.scheduler.interrupt(self.current_process, message=message)
