from starling_sim.basemodel.output.kpis import KPI

import logging
import pandas as pd
import os


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
        self.columns = None

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

        # setup kpis and get columns
        columns = [KPI.KEY_ID]
        for kpi in self.kpi_list:
            kpi.setup(simulation_model)
            columns += kpi.export_keys
        self.columns = columns

        if isinstance(self.population_names, list):
            self.populations = [
                simulation_model.agentPopulation[population_name]
                for population_name in self.population_names
            ]
        else:
            self.populations = [simulation_model.agentPopulation[self.population_names]]

    def write_kpi_table(self):
        """
        Write the KPI of the population in the csv file
        obtained from out file attributes
        The KPIs evaluated are defined by the kpi_list attribute
        """
        print(self.filename)
        # build the KPI table for all agents of each population
        kpi_table = self.build_kpi_table()

        # do not generate a kpi output if the kpi table is empty
        if kpi_table.empty:
            return
        print(kpi_table)
        path = str(os.path.join(self.folder, self.filename))
        try:
            # write the dataframe into a csv file
            kpi_table.to_csv(path, sep=";", index=False)

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

    def build_kpi_table(self) -> pd.DataFrame:
        """
        Build the output KPI table.

        KPIs from self.kpis are evaluated on each agent of each population from self.populations.

        :return: KPI DataFrame
        """

        kpi_tables = []
        # compute kpi tables for each population dict
        for population in self.populations:
            # compute a kpi table for each agent of the population
            for agent in population.values():
                kpi_tables.append(self.compute_agent_kpis(agent))

        return pd.concat(kpi_tables)

    def compute_agent_kpis(self, agent) -> pd.DataFrame:
        """
        Build a DataFrame containing indicator evaluated on the given agent.

        The DataFrame columns are defined by the KPIs `keys` attributes,
        with and additional column for the agent id, and an optional column
        for time profiling.

        The DataFrame can contain several rows, for instance when KPIs
        are profiled by time.

        :param agent: Agent on which KPIs are evaluated

        :return: DataFrame containing indicators evaluated on the given agent
        """

        df = dict()
        # evaluate indicators on agent
        for kpi in self.kpi_list:
            kpi_rows = kpi.evaluate_for_agent(agent)
            df.update(kpi_rows)

        # set agent id for all rows
        df[KPI.KEY_ID] = agent.id

        # convert dict to DataFrame
        df = pd.DataFrame(df, columns=self.columns)

        return df
