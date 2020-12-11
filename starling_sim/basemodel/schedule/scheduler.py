"""
This module is dedicated to discrete event scheduling.
It allows the representation of a time flow inside the simulation.
"""

import simpy
import logging
from numbers import Integral


# For now, only one class exists, using the SimPy_ library. If other scheduling classes should be developed,
# we should make them inherit from a super class containing the common methods.
class Scheduler:
    """
    This class manages a discrete event schedule using the SimPy_ library.

    Along with containing a SimPy environment, this class also provides methods
    for the generation of SimPy Event objects (Process objects are events too).
    Yielding these events will suspend the current activity (e.g agent loop), which will
    resume once the event occurs (or before if the process is interrupted).

    This way, agents can yield processes corresponding to an action (move, wait, etc)
    and resume to their loop after the action has finished.

    .. _SimPy: https://simpy.readthedocs.io/en/latest/index.html
    """

    def __init__(self):
        """
        Creation of a SimPy environment and a runtime limit (set to 0).
        """
        self.env = simpy.Environment()
        self.time_limit = 0

    def run(self, run_time):
        """
        Update the runtime limit attribute and run the environment.

        :param run_time: duration of the simulation run
        """

        self.time_limit += run_time
        self.env.run(run_time)

    def now(self):
        """
        Get the current simulation step.

        :return: Current time of the simulation (arbitrary unit)
        """

        return self.env.now

    def timeout(self, duration="inf"):
        """
        Create a SimPy timeout event with the given duration

        :param duration: time to pass, in simulation units. Defaults to 'inf',
         ie end at the simulation time limit. Must be positive and integer-like
        :return: SimPy timeout event
        """

        if duration == "inf":
            duration = self.time_limit - self.now()

        if not isinstance(duration, Integral) or duration < 0:
            logging.error("Incorrect waiting duration given to scheduler")
            raise ValueError(duration)

        return self.env.timeout(duration)

    def new_event_object(self):
        """
        Create and return a new Event object

        :return: Event object
        """

        return simpy.events.Event(self.env)

    def new_process(self, generator):
        """
        Create a SimPy process from the given generator

        :param generator: Python generator (function containing the yield keyword)
        :return: SimPy Process object
        """

        return self.env.process(generator)

    def interrupt(process, message=""):
        """
        Interrupt the given SimPy process, e.g. an agent waiting in a queue

        :param process: simPy Process object
        :param message: interruption message, to be displayed in the agent's trace
        """

        process.interrupt(message)

    interrupt = staticmethod(interrupt)
