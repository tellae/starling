from starling_sim.simulation_scenario import SimulationScenario
from starling_sim.utils import paths
from zipfile import ZipFile
import os
from loguru import logger



class ZipScenario:

    def __init__(self, scenario_path:str, target_filename:str=None, include_outputs:bool=False, force:bool=False):
        # create SimulationScenario object and check scenario folders
        self.scenario = SimulationScenario(scenario_path)
        # read simulation parameters
        self.scenario.get_scenario_parameters()

        # path to target zip file
        if target_filename is None:
            target_filename = self.scenario.name + ".zip"
        self.target_filepath = str(os.path.join(scenario_path, target_filename))

        # ZipFile instance
        self._zipfile = None

    def zip(self, force: bool = False, include_outputs: bool = False):

        if os.path.exists(self.target_filepath):
            if force:
                logger.info(f"Remove existing zip file: {self.target_filepath}")
                os.remove(self.target_filepath)
            else:
                raise FileExistsError

        logger.debug(f"Open zip file in write mode at {self.target_filepath}")
        with ZipFile(self.target_filepath, mode="x") as self._zipfile:
            self._add_input_files()

            self._add_topology_files()

            self._add_gtfs_timetables_file()

            if include_outputs:
                self._add_output_files()

        self._zipfile = None
        logger.success(f"Scenario has been zipped to {self.target_filepath}")

    def _add_input_files(self):
        # write all files present in inputs folder
        self._zip_scenario_folder(self.scenario.inputs_folder)

        # write agent input files present in common_inputs
        dynamic_file = self.scenario.get_dynamic_input_filepath()
        init_files = self.scenario.get_init_input_filepaths()
        agent_inputs = []
        if dynamic_file is not None:
            agent_inputs.append(dynamic_file)
        if init_files is not None:
            agent_inputs = agent_inputs + init_files

        for filepath in agent_inputs:
            if paths.COMMON_INPUTS_FOLDER in filepath:
                self._zip_scenario_file(filepath, [paths.COMMON_INPUTS_FOLDER])

    def _add_output_files(self):
        # write all files present in outputs folder
        self._zip_scenario_folder(self.scenario.outputs_folder)

    def _add_topology_files(self):
        topologies = self.scenario["topologies"]
        for mode in topologies.keys():
            info = self.scenario.get_topology_info(mode)
            if info is None:
                continue

            # add osm graph file
            graph_filepath = info["graph"]
            self._zip_scenario_file(graph_filepath, [paths.ENVIRONMENT_FOLDER_NAME, paths.OSM_GRAPHS_FOLDER_NAME])

            # add speeds if its a filepath
            speeds_info = info["speeds"]
            if isinstance(speeds_info, str):
                self._zip_scenario_file(speeds_info, [paths.ENVIRONMENT_FOLDER_NAME, paths.GRAPH_SPEEDS_FOLDER_NAME])

    def _add_gtfs_timetables_file(self):
        gtfs_timetable_filepath = self.scenario.get_gtfs_timetable_filepath()
        if gtfs_timetable_filepath is None:
            return
        self._zip_scenario_file(gtfs_timetable_filepath, [paths.ENVIRONMENT_FOLDER_NAME, paths.GTFS_FEEDS_FOLDER_NAME])


    def _zip_scenario_folder(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:

                relpath = os.path.relpath(
                        str(os.path.join(root, file)),
                        os.path.join(folder_path, '..')
                    )
                print(relpath)
                self._zipfile.write(
                    os.path.join(root, file),
                    relpath
                )

    def _zip_scenario_file(self, filepath, dest_folders_path):
        dest_filepath = os.path.join(*dest_folders_path, os.path.basename(filepath))
        logger.debug(f"Add {filepath} to zip at {dest_filepath}")
        self._zipfile.write(filepath, dest_filepath)



# def add_topology_files_to_zip(simulation_scenario, zipfile):
#     topologies = simulation_scenario["topologies"]
#     for mode in topologies.keys():
#         info = simulation_scenario.get_topology_info(mode)
#         if info is None:
#             continue
#
#         # add osm graph file
#         graph_filepath = info["graph"]
#         zipfile.write(graph_filepath, os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.OSM_GRAPHS_FOLDER_NAME, os.path.basename(graph_filepath)))
#
#         # add speeds if its a filepath
#         speeds_info = info["speeds"]
#         if isinstance(speeds_info, str):
#             zipfile.write(speeds_info, os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.GRAPH_SPEEDS_FOLDER_NAME, os.path.basename(speeds_info)))
#
# def add_gtfs_feed_to_zip(simulation_scenario, zipfile):
#     gtfs_timetable_filepath = simulation_scenario.get_gtfs_timetable_filepath()
#
#
#     if gtfs_timetable_filepath is None:
#         return
#
#     zipfile.write(gtfs_timetable_filepath,
#                   os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.GTFS_FEEDS_FOLDER_NAME, os.path.basename(gtfs_timetable_filepath)))
#
#
# def add_input_files_to_zip(simulation_scenario, zipfile):
#     # write all files present in inputs folder
#     write_folder_to_zip(simulation_scenario.inputs_folder, zipfile)
#
#     # write agent input files present in common_inputs
#     dynamic_file = simulation_scenario.get_dynamic_input_filepath()
#     init_files = simulation_scenario.get_init_input_filepaths()
#
#     agent_inputs = []
#     if dynamic_file is not None:
#         agent_inputs.append(dynamic_file)
#     if init_files is not None:
#         agent_inputs = agent_inputs + init_files
#
#     for filepath in agent_inputs:
#         basename = os.path.basename(filepath)
#         if paths.COMMON_INPUTS_FOLDER in filepath:
#             zipfile.write(filepath,
#                           os.path.join(paths.COMMON_INPUTS_FOLDER, basename))
#
#


# if os.path.exists("data/models/SB_VS/example_nantes/example_nantes.zip"):
#     os.remove("data/models/SB_VS/example_nantes/example_nantes.zip")
#
# ZipScenario("data/models/SB_VS/example_nantes", include_outputs=True).zip()
#
# if os.path.exists("data/models/PT/example/example.zip"):
#     os.remove("data/models/PT/example/example.zip")
#
# ZipScenario("data/models/PT/example", include_outputs=True).zip()
#
#
# print()
#
# print("MANAGE SIMLINKS")