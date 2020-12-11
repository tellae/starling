class AgentPopulation:
    """
    Describes one or several collections of agents

    This class must be extended to give a concrete implementation of the storage of the
    simulation's population(s), e.g. using a dict {ID : Agent}
    """

    def __init__(self):
        """
        The constructor must be extended for the needs of the storage method
        """

        self.population = None

    def get_total_population(self):
        """
        Give access to the total population of the simulation

        :return: list of Agent objects
        """

    def get_agent(self, agent_id, agent_population=None):
        """
        Get the agent corresponding to the given id.

        The agent population may be provided, or it can be
        left to None if it is unknown.

        :param agent_id: id of the agent
        :param agent_population: population of the agent, None if unknown

        :return: agent
        """

    def new_population(self, population_name):
        """
        Return a population with the given name.

        If the population does not exist, it is created.

        :param population_name: str
        :return: population associated to the given name
        """

    def new_agent_in(self, agent, population_names):
        """
        Add the agent to the given population(s)

        :param agent: Agent object
        :param population_names: list or str corresponding to population names
        """
