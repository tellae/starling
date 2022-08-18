from starling_sim.basemodel.output.geojson_output import new_geojson_output
from starling_sim.utils.utils import json_pretty_dump, create_file_information
from starling_sim.utils.config import config
from starling_sim.utils.constants import RUN_SUMMARY_FILENAME

import logging
import os


class OutputFactory:
    """
    Describes an output generation method

    This class should be extended to give a concrete implementation of the output generator
    e.g. writing a json containing all the simulation data
    """

    GENERATION_ERROR_FORMAT = "Error while generating {} output"

    def __init__(self):
        """
        The constructor must be extended for the needs of the generation method
        """

        # list of output files and associated information
        self.output_files = []

        # list of KpiOutput objects, each will generate one kpi file
        self.kpi_outputs = None

        # GeojsonOutput object, will generate the visualisation output
        self.geojson_output = None

        self.sim = None

    def setup(self, simulation_model):
        """
        Setup method called during simulation setup.

        Set values of the output factory attributes.

        :param simulation_model:
        """

        # set simulation model
        self.sim = simulation_model

        # get output folder
        output_folder = simulation_model.scenario.outputs_folder

        # get scenario
        scenario = simulation_model.scenario.name

        # setup kpi outputs

        self.setup_kpi_output()

        for kpi_output in self.kpi_outputs:

            # build the kpi output filename
            kpi_filename = config["kpi_format"].format(
                scenario=scenario, kpi_output=kpi_output.name
            )

            # set kpi output file
            kpi_output.setup(kpi_filename, output_folder, simulation_model)

        # setup geojson output

        self.setup_geojson_output()

        if self.geojson_output is not None:

            # build the geojson output filename
            geojson_filename = config["geojson_format"].format(scenario=scenario)

            self.geojson_output.setup(simulation_model, geojson_filename, output_folder)

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

        self.geojson_output = new_geojson_output()

    def new_output_file(
        self,
        filepath: str,
        mimetype: str,
        compressed_mimetype: str = None,
        content: str = None,
        subject: str = None,
    ):
        """
        Add a new file and its information to the output dict.

        This method should be called after generating an output file.

        :param filepath: output file path
        :param mimetype: file mimetype
        :param compressed_mimetype: compressed mimetype (defaults to file mimetype)
        :param content: content metadata (mandatory)
        :param subject: subject
        """

        output_file_information = create_file_information(
            filepath,
            mimetype,
            compressed_mimetype=compressed_mimetype,
            content=content,
            subject=subject,
        )

        logging.info(
            "Generated {} output in file {}".format(
                output_file_information["metadata"]["content"], filepath
            )
        )

        self.output_files.append(output_file_information)

    def extract_simulation(self, simulation_model):
        """
        This method will be called for the output generation.

        It must be extended to generate the output using specific methods.
        """

        # traces output
        if simulation_model.scenario["traces_output"]:
            try:
                self.generate_trace_output(simulation_model)
            except:
                logging.warning(self.GENERATION_ERROR_FORMAT.format("traces"))

        # kpi output
        if simulation_model.scenario["kpi_output"]:
            self.generate_kpi_output(simulation_model)

        # geojson output

        if simulation_model.scenario["visualisation_output"]:
            try:
                self.generate_geojson_output(simulation_model)
            except:
                logging.warning(self.GENERATION_ERROR_FORMAT.format("visualisation"))

        # run summary output
        self.generate_run_summary(simulation_model.scenario)

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
            try:
                kpi_output.write_kpi_table()
            except:
                logging.warning(self.GENERATION_ERROR_FORMAT.format(kpi_output.name + " kpi"))

    def generate_trace_output(self, simulation_model):
        """
        Generate a text file containing the event traces of the agents.

        :param simulation_model:
        """

        # get the scenario information and outfile
        scenario = simulation_model.scenario.name
        model_code = simulation_model.scenario.model
        output_folder = simulation_model.scenario.outputs_folder
        filepath = output_folder + config["traces_format"].format(scenario=scenario)

        # open the trace file in write mode
        with open(filepath, "w") as outfile:

            # write header with scenario information
            outfile.write("Traces of scenario {}, model {}".format(scenario, model_code))

            # write the trace of the dynamic input
            outfile.write("\nTrace of dynamicInput")
            for event in simulation_model.dynamicInput.trace.eventList:
                outfile.write("\n")
                outfile.write(str(event))

            # write the trace of the simulation agents
            for agent in simulation_model.agentPopulation.get_total_population():

                # don't display agents with empty trace
                if len(agent.trace.eventList) <= 2:
                    continue

                outfile.write("\nTrace of agent " + str(agent.id))
                for event in agent.trace.eventList:
                    outfile.write("\n")
                    outfile.write(str(event))

        self.sim.outputFactory.new_output_file(filepath, "text/plain", content="traces")

    def generate_run_summary(self, simulation_scenario):
        """
        Generate a summary file of the simulation run.

        :param simulation_scenario: SimulationScenario object
        """
        filepath = simulation_scenario.outputs_folder + RUN_SUMMARY_FILENAME

        # add run summary to output files
        self.sim.outputFactory.new_output_file(filepath, "application/json", content="run_summary")

        # set output files in run summary and dump it in a file
        simulation_scenario.runSummary["output_files"] = self.output_files
        json_pretty_dump(simulation_scenario.runSummary, filepath)
