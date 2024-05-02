from starling_sim.basemodel.output.kpis import KPI

import logging
import pandas as pd
import os
from datetime import datetime, time, timedelta


class KpiOutput:
    def __init__(self, population_names, kpi_list, time_profiling=None, kpi_name=None):
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

        # dict containing kpi values
        self.kpi_rows = None
        self.time_profile = None
        if time_profiling:
            self.time_profile = [0] + time_profiling

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
        if self.time_profile:
            columns.append("time")
        for kpi in self.kpi_list:
            kpi.setup(self, simulation_model)
            kpi.kpi_output = self
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

        # build the KPI table for all agents of each population
        kpi_table = self.build_kpi_table()

        if self.time_profile:
            kpi_table["time"] = kpi_table["time"].apply(lambda x: (datetime.min + timedelta(seconds=x)).strftime("%H:%M:%S"))

        # do not generate a kpi output if the kpi table is empty
        if kpi_table.empty:
            return

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

        result = pd.concat(kpi_tables)
        return result

    def compute_agent_kpis(self, agent):
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

        self.kpi_rows = {key: [] for key in self.columns}

        # evaluate indicators on agent
        for kpi in self.kpi_list:
            kpi.evaluate_for_agent(agent)

        self.kpi_rows[KPI.KEY_ID] = agent.id
        if self.time_profile:
            self.kpi_rows["time"] = self.time_profile

        res = pd.DataFrame(self.kpi_rows, columns=self.columns)

        return res
