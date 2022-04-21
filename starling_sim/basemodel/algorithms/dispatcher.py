import numpy as np
from abc import ABC


class Dispatcher(ABC):
    """
    This class describes a dispatcher for a transport service.

    The dispatcher is called to affect requests online or punctually.

    The Dispatcher class allows a complete specification (punctual and online)
    and separation (from the operator and the algorithms it uses) of the dispatching strategy.

    The parameters needed to initialise and run the dispatcher should be provided
    in the operator operationParameters attribute.
    """

    #: json schema for the operation parameters
    SCHEMA = {"type": "object", "properties": {}}

    def __init__(self, simulation_model, operator, verb=False):
        """
        Initialise the dispatcher and its algorithm.

        The operator's dispatcher is initialised only once. It is then called on
        various situations to realise a dispatch.

        :param simulation_model: SimulationModel
        :param operator: id of the operator of the dispatched service
        :param verb: verbose boolean
        """

        #: simulation object
        self.sim = simulation_model

        #: transport operator id
        self.operator = operator

        #: operation parameters
        self.operationParameters = None
        if operator is not None:
            self.operationParameters = self.operator.operationParameters

        #: verbose option
        self.verb = verb

        #: dispatch algorithm
        self.algorithm = None
        self.init_algorithm()

        #: algorithm result
        self.result = None

        #: online request, in case of online dispatch
        self.online_request = None

    @property
    def name(self):
        return self.__class__.__name__

    def init_algorithm(self):
        """
        Initialise the algorithm's structure used by the dispatcher.
        """

    def dispatch(self):
        """
        Realise the complete dispatch process.
        """

        # setup the algorithm and parameters
        self.setup_dispatch()

        # run the algorithm and store the result in punctual_result
        self.run_algorithm()

        # update the plannings according to the proposed solution
        self.update_from_solution()

    def setup_dispatch(self):
        """
        Setup the dispatch with current simulation data.
        """

    def run_algorithm(self):
        """
        Run the algorithm on the current problem instance.
        """

    def update_from_solution(self):
        """
        Update the operator plannings based on the dispatch solution.
        """

    # dispatching loop for punctual algorithms

    def dispatching_loop_(self):

        self.log_message("Dispatching loop not implemented", lvl=40)
        raise NotImplementedError

    # method for online dispatch of requests

    def online_dispatch(self, request):

        self.log_message("Online dispatch method not implemented", lvl=40)
        raise NotImplementedError

    # logs and trace

    def log_message(self, message, lvl=15):
        """
        Log a message using the operator's dedicated method.

        :param message:
        :param lvl:
        """

        if self.verb or lvl >= 30:

            # add the name of the dispatcher as a prefix
            message = "{} : {}".format(self.name, message)

            # log message using the operator method
            self.operator.log_message(message, lvl=lvl)

    # utils

    def compute_matrix_of(self, stop_points, dimension, mode):
        """
        Compute the distance matrix (in the given dimension) between the given stop points,
        on the given topology graph.

        :param stop_points: list of stop point ids
        :param dimension: dimension of the distance to compute
        :param mode: travel mode between modes

        :return: matrix[i, j] = distance from stop i to stop j.
        """

        matrix = np.zeros((len(stop_points), len(stop_points)))

        for i in range(len(stop_points)):

            origin = self.operator.stopPoints[stop_points[i]].position
            _, lengths = self.sim.environment.topologies[mode].compute_dijkstra_path(
                origin, None, dimension
            )

            for j in range(len(stop_points)):
                matrix[i, j] = int(lengths[self.operator.stopPoints[stop_points[j]].position])

        if dimension == "time":
            matrix = matrix.astype(int)

        return matrix
