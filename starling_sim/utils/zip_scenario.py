from starling_sim.simulation_scenario import SimulationScenario
from starling_sim.utils import paths
from zipfile import ZipFile
import os
from loguru import logger


class ScenarioZipper:
    """
    Regroup all files relevant to a scenario in a zip file.
    """

    def __init__(self, scenario_path:str, target_filename:str=None):
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
        """
        Zip scenario files into a zip file.

        :param force: overwrite zip file if already exists
        :param include_outputs: include scenario outputs in zip file
        """

        # check if target file exists
        if os.path.exists(self.target_filepath):
            if force:
                logger.info(f"Remove existing zip file: {self.target_filepath}")
                os.remove(self.target_filepath)
            else:
                raise FileExistsError

        # open zip file
        logger.debug(f"Open zip file in write mode at {self.target_filepath}")
        with ZipFile(self.target_filepath, mode="x") as self._zipfile:
            self._add_input_files()

            self._add_topology_files()

            self._add_gtfs_timetables_file()

            if include_outputs:
                self._add_output_files()

        # log success and file details
        logger.success(f"Scenario has been zipped to {self.target_filepath}:")
        logger.success("\t %-70s %19s %12s" % ("File Name", "Modified    ", "Size"))
        for zinfo in self._zipfile.infolist():
            date = "%d-%02d-%02d %02d:%02d:%02d" % zinfo.date_time[:6]
            logger.success("\t %-70s %s %12d" % (zinfo.filename, date, zinfo.file_size))

        self._zipfile = None

    def _add_input_files(self):
        """
        Add scenario input files to zip.
        """
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
        """
        Add scenario output files to zip.
        """
        # write all files present in outputs folder
        self._zip_scenario_folder(self.scenario.outputs_folder)

    def _add_topology_files(self):
        """
        Add topology related files to zip.
        """
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
        """
        Add GTFS file to zip.
        """
        gtfs_timetable_filepath = self.scenario.get_gtfs_timetable_filepath()
        if gtfs_timetable_filepath is None:
            return
        self._zip_scenario_file(gtfs_timetable_filepath, [paths.ENVIRONMENT_FOLDER_NAME, paths.GTFS_FEEDS_FOLDER_NAME])


    def _zip_scenario_folder(self, folder_path):
        """
        Add all folder contents (including its subfolders) to zip.

        :param folder_path: path to folder
        """
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = str(os.path.join(root, file))
                relpath = os.path.relpath(
                        full_path,
                        os.path.join(folder_path, '..')
                    )
                self._zip_scenario_file(full_path, relpath.split(os.sep)[:-1])


    def _zip_scenario_file(self, filepath, dest_folders_path):
        """
        Add file to zip.

        :param filepath: path to original file
        :param dest_folders_path: list of zip folders to put the file in.
        """
        dest_filepath = os.path.join(*dest_folders_path, os.path.basename(filepath))
        logger.debug(f"Add {filepath} to zip at {dest_filepath}")
        self._zipfile.write(filepath, dest_filepath)


def zip_scenario_from_args(args):
    zipper = ScenarioZipper(args.scenario_path, args.outfile)

    try:
        zipper.zip(force=args.force, include_outputs=args.include_outputs)
    except FileExistsError:
        raise FileExistsError(f"The file {zipper.target_filepath} already exists. Use the -f (or --force) option to overwrite it.")


def add_zip_unzip_actions(subparsers):
    """
    Add a subparser for the zip action.

    :param subparsers: argparse subparsers
    """

    zip_parser = subparsers.add_parser(
        "zip",
        description="Zip simulation scenarios for simpler transfers. "
                    "Best used with the unzip action. The resulting zip file will be placed in the scenario folder",
        help="Zip a simulation scenario",
    )

    zip_parser.add_argument(
        "scenario_path",
        help="path to scenario folder",
        type=str
    )

    zip_parser.add_argument(
        "-f",
        "--force",
        help="force zip creation even if the file already exists",
        action="store_true"
    )

    zip_parser.add_argument(
        "--include-outputs",
        help="include scenario outputs in the zip file",
        action="store_true"
    )

    zip_parser.add_argument(
        "-o",
        "--outfile",
        help="name of the output file",
        type=str,
        default=None
    )

    # store exec function in parser
    zip_parser.set_defaults(zip=zip_scenario_from_args)
