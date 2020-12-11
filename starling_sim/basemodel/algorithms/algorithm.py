from starling_sim.utils.simulation_logging import ALGO_LOGGER, ALGO_LEVEL


class Algorithm:
    """
    This class describes a generic structure for the algorithms of the simulation
    """

    NAME = "unnamed algorithm"

    def __init__(self, simulation_model=None, operator=None, verb=False):

        # simulation objects
        self.sim = simulation_model
        self.operator = operator

        # logging options
        self.verbose = verb

        # result attribute
        self.result = None

    def run(self):
        """
        Core method of the Algorithm class, called to run the algorithm.

        This method must be implemented for all algorithms.

        Algorithm inputs are accessed in the class attributes.

        :return: None, the algorithm result is stored in self.result
        """

        self.log_message("Start running the algorithm {}".format(self.NAME))

    def log_message(self, message, lvl=ALGO_LEVEL):
        """
        Logs the message in the logger using the class data

        :param message: message displayed in log
        :param lvl: level value, default is ALGO_LEVEL
        """

        if self.verbose or lvl >= 30:

            extra_params = {"alg_name": self.NAME}

            ALGO_LOGGER.log(lvl, message, extra=extra_params)

    def __str__(self):
        """
        Give a string display to the algorithm.

        :return: string with algorithm information
        """

        return "Algorithm ({})".format(self.NAME)
