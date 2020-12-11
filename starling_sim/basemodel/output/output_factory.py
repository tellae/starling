from starling_sim.basemodel.output.geojson_output import new_geojson_output
from starling_sim.utils.utils import json_pretty_dump
from starling_sim.utils.constants import KPI_FORMAT, GEOJSON_FORMAT

import os


class OutputFactory:
    """
    Describes an output generation method

    This class should be extended to give a concrete implementation of the output generator
    e.g. writing a json containing all the simulation data
    """

    def __init__(self):
        """
        The constructor must be extended for the needs of the generation method
        """

        # list of KpiOutput objects, each will generate one kpi file
        self.kpi_outputs = None

        # GeojsonOutput object, will generate the visualisation output
        self.geojson_output = None

        self.sim = None

    def setup(self, simulation_model):
        """
        Setup method called during simulation setup.

        Sets values of the output factory attributes.

        :param simulation_model:
        """

        # set simulation model
        self.sim = simulation_model

        # get output folder
        output_folder = simulation_model.parameters["output_folder"]

        # get scenario
        scenario = simulation_model.parameters["scenario"]

        # setup kpi outputs

        self.setup_kpi_output()

        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        for kpi_output in self.kpi_outputs:

            # build the kpi output filename
            if "kpi_format" in simulation_model.parameters:
                kpi_format = simulation_model.parameters["kpi_format"]
            else:
                kpi_format = KPI_FORMAT

            kpi_filename = kpi_format.format(scenario=scenario, kpi_output=kpi_output.name)

            # set kpi output file
            kpi_output.setup(kpi_filename, output_folder, simulation_model)

        # setup geojson output

        self.setup_geojson_output()

        if self.geojson_output is not None:

            # build the geojson output filename
            if "geojson_format" in simulation_model.parameters:
                geojson_format = simulation_model.parameters["geojson_format"]
            else:
                geojson_format = GEOJSON_FORMAT

            geojson_filename = geojson_format.format(scenario=scenario)

            self.geojson_output.setup(simulation_model,
                                      geojson_filename,
                                      output_folder)

    def setup_kpi_output(self):
        """
        Set the kpi_outputs attribute as a list of KpiOutput objects.

        By default, no KPIs are set
        """

        self.kpi_outputs = []

    def setup_geojson_output(self):
        """
        Set the geojson_output attribute as a GeojsonOutput object.
        """

        self.geojson_output = new_geojson_output(self.sim.parameters)

    def extract_simulation(self, simulation_model):
        """
        This method will be called for the output generation.

        It must be extended to generate the output using specific methods.
        """

        if simulation_model.parameters["display_traces"]:
            self.print_traces(simulation_model)

        if "generate_summary" in simulation_model.parameters \
                and simulation_model.parameters["generate_summary"]:
            self.generate_run_summary(simulation_model)

        # kpi output
        if simulation_model.parameters["kpi_output"]:
            self.generate_kpi_output(simulation_model)

        # geojson output
        if simulation_model.parameters["geojson_output"]:
            self.generate_geojson_output(simulation_model)

    def generate_run_summary(self, simulation_model):
        """
        Generate a summary file of the simulation run.

        :param simulation_model:
        """
        filepath = simulation_model.parameters["output_folder"] + "/" \
            + simulation_model.parameters["scenario"] + "_summary.json"

        json_pretty_dump(simulation_model.runSummary, filepath)

    def generate_geojson_output(self, simulation_model):
        """
        Call the generation method of the geojson output attribute

        :param simulation_model:
        """

        self.geojson_output.add_population_features()

        self.geojson_output.generate_geojson()

    def generate_kpi_output(self, simulation_model):
        """
        Call the generation method of all the kpi outputs

        :param simulation_model:
        """

        for kpi_output in self.kpi_outputs:

            kpi_output.write_kpi_table()

    def print_traces(simulation_model):
        """
        Displays the traces of all agents in the console

        :param simulation_model:
        """

        print("Now displaying traces")

        print("\nTrace of dynamicInput")
        for event in simulation_model.dynamicInput.trace.eventList:
            print(event)

        for agent in simulation_model.agentPopulation.get_total_population():

            # don't display agents with empty trace
            if len(agent.trace.eventList) <= 2:
                continue

            print("\nTrace of agent " + str(agent.id))
            for event in agent.trace.eventList:
                print(event)

    print_traces = staticmethod(print_traces)
