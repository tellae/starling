import logging

from starling_sim.basemodel.population.agent_population import AgentPopulation


class DictPopulation(AgentPopulation):
    """
    Stores the agent populations of the simulation in Python dictionaries
    Theses dicts are stored in a global dict
    """

    def __init__(self, population_names):
        """
        Initialises the dicts with the given names
        :param population_names: list of names for the populations
        """

        super().__init__()

        self.population = {}
        self.base_names = population_names

        for name in population_names:
            self.new_population(name)

    def get_total_population(self):

        agents = []

        for name in self.base_names:
            agents = agents + list(self.population[name].values())

        return agents

    def get_agent(self, agent_id, agent_population=None):

        if agent_population is not None:
            pop_dict = self.population[agent_population]
            if agent_id in pop_dict:
                return pop_dict[agent_id]

        else:
            for pop_dict in self.population.values():
                if agent_id in pop_dict:
                    return pop_dict[agent_id]

    def new_population(self, population_name):

        if population_name in self.population:
            return self.population[population_name]
        else:
            new_population = dict()
            self.population[population_name] = new_population
            return new_population

    def new_agent_in(self, agent, population_names):

        if isinstance(population_names, str):
            population_names = [population_names]

        for population_name in population_names:
            # raise KeyError exception if agent already exists (and then cancel agent add)
            if agent.id in self.population[population_name]:
                logging.error(
                    "Agent {} already exists in population {}, cancelled introduction of duplicate".format(
                        agent.id, population_name
                    )
                )
                raise KeyError

            self.population[population_name][agent.id] = agent

    def __getitem__(self, item):
        """
        Method called when using agentPopulation[item]
        :param item: name of the population accessed
        :return: self.population[item]
        """

        if item not in self.population:
            logging.warning("Trying to get unknown population " + item)
            return None
        return self.population[item]

    # useless ?
    def __setitem__(self, key, value):
        """
        Method called when using agentPopulation[key] = value
        :param key: name of the population accessed
        :param value: population dict
        :return:
        """

        if key in self.population:
            logging.warning("Assigning dict to an existing population " + key)
        self.population[key] = value
