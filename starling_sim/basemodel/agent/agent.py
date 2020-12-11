from starling_sim.basemodel.trace.trace import Traced
from starling_sim.basemodel.trace.events import InputEvent, WaitEvent


class Agent(Traced):
    """
    This class describes the basic features of a simulation agent.

    It should be extended (through several layers) to give more specific features and behaviours
    (represented by their available methods), to finally implement a concrete agent that can be
    simulated in a specific model.
    """

    def __init__(self, simulation_model, agent_id, agent_type=None, mode=None, icon=None, **kwargs):
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
        self.name = None
        self.loop_process = None
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

        wait_event = WaitEvent(time=self.sim.scheduler.now(), reason=reason, waiting_time=duration, message=message)

        yield self.execute_process(self.spend_time_(duration))

        self.trace_event(wait_event)

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
