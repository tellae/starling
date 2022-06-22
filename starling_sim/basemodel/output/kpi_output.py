from starling_sim.basemodel.output.kpis import KPI

import logging
import pandas as pd


class KpiOutput:
    def __init__(self, population_names, kpi_list, kpi_name=None):

        # simulation model access
        self.sim = None

        # name of the kpi, will compose the kpi filename : <kpi_name>.csv
        if kpi_name is None:
            if isinstance(population_names, list):
                self.name = "_&_".join(population_names) + "_kpi"
            else:
                self.name = population_names + "_kpi"
        else:
            self.name = kpi_name

        # population of agent to evaluate
        self.population_names = population_names
        self.populations = None

        # list of kpi to evaluate the given agents
        self.kpi_list = kpi_list

        # output file
        self.filename = None
        self.folder = None

    def setup(self, filename, folder, simulation_model):
        """
        Setup method called during simulation setup.

        Sets the values of out file and folder, and call setup for KPIs.

        :param filename: .csv file
        :param folder:
        :param simulation_model:
        :return:
        """

        self.sim = simulation_model
        self.filename = filename
        self.folder = folder

        for kpi in self.kpi_list:
            kpi.setup(simulation_model)

        if isinstance(self.population_names, list):
            self.populations = [
                simulation_model.agentPopulation[population_name]
                for population_name in self.population_names
            ]
        else:
            self.populations = [simulation_model.agentPopulation[self.population_names]]

    def agent_kpi_dict(self, agent):
        """
        Computes the KPIs for the given agent
        by calling their update method for all its trace
        :param agent:
        :return:
        """

        indicators_dict = dict()

        # get agent trace
        events = agent.trace.eventList

        # evaluate all indicators in a single pass
        for event in events:
            for kpi in self.kpi_list:
                kpi.update(event, agent)

        # merge all completed indicators
        for kpi in self.kpi_list:

            indicators_dict.update(kpi.indicator_dict)

            # raising a warning with sphinx
            # indicators_dict = {**indicators_dict, **kpi.indicator_dict}

            # reset kpi values
            kpi.new_indicator_dict()

        # return complete indicator dict
        return indicators_dict

    def write_kpi_table(self):
        """
        Write the KPI of the population in the csv file
        obtained from out file attributes
        The KPIs evaluated are defined by the kpi_list attribute
        """

        # first row is always agent's id, then we add the kpi_list keys
        header_list = [KPI.KEY_ID]
        for kpi in self.kpi_list:
            header_list += kpi.keys

        path = self.folder + self.filename

        kpi_table = pd.DataFrame()

        # compute the kpi table for each population dict
        for population in self.populations:
            kpi_table = pd.concat([kpi_table, self.compute_population_kpi_table(population)])

        # do not generate a kpi output if the kpi table is empty
        if kpi_table.empty:
            return

        try:
            # write the dataframe into a csv file
            kpi_table.to_csv(path, sep=";", index=False, columns=header_list)

            # signal new file to output factory
            mimetype = "text/csv"
            if path.endswith("gz"):
                mimetype = "application/gzip"
            self.sim.outputFactory.new_output_file(
                path,
                mimetype,
                compressed_mimetype="text/csv",
                content="kpi",
                subject=self.name,
            )

        except KeyError as e:
            logging.warning(
                "Could not generate kpi output {}, " "error occurred : {}".format(path, e)
            )

    def compute_population_kpi_table(self, population):
        """
        Compute a kpi table for the given population dict.

        :param population: population dict {id: agent}
        :return: DataFrame containing the KPI values
        """

        df_output = pd.DataFrame()

        for agent in population.values():

            # create kpi dict for the agent
            agent_indicators = self.agent_kpi_dict(agent)

            # build a dataframe from the dict
            if isinstance(agent_indicators[KPI.KEY_ID], list):
                df = pd.DataFrame(agent_indicators)
            else:
                df = pd.DataFrame(agent_indicators, index=[0])

            # append the dataframe to the total output
            df_output = pd.concat([df_output, df])

        return df_output
