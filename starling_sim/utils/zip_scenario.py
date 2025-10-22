import json
import shutil
from starling_sim.simulation_scenario import SimulationScenario
from starling_sim.utils import paths
from starling_sim.utils.utils import DataFolderError
from zipfile import ZipFile
import os
from loguru import logger
from abc import ABC, abstractmethod


class ScenarioZipping(ABC):
    """
    Base for classes that manage scenario zipping.
    """

    def __init__(self, zipfile_path):
        # SimulationScenario instance pointing to the target scenario
        self.scenario = None

        # path to the zip file
        self.zipfile_path = zipfile_path

        # ZipFile instance
        self._zipfile = None

    def _set_scenario(self, scenario_path):
        # create SimulationScenario object and check scenario folders
        self.scenario = SimulationScenario(scenario_path)

    @abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError


class ScenarioZipper(ScenarioZipping):
    """
    Regroup all files relevant to a scenario in a zip file.
    """

    def __init__(self, scenario_path: str, target_filename: str = None):
        # set scenario folder
        self._set_scenario(scenario_path)
        # read simulation parameters
        self.scenario.get_scenario_parameters()

        # path to target zip file
        if target_filename is None:
            target_filename = self.scenario.name + ".zip"
        zipfile_path = str(os.path.join(scenario_path, target_filename))

        super().__init__(zipfile_path)

    def run(self, force: bool = False, include_outputs: bool = False):
        """
        Zip scenario files into a zip file.

        :param force: overwrite zip file if already exists
        :param include_outputs: include scenario outputs in zip file
        """

        # check if target file exists
        if os.path.exists(self.zipfile_path):
            if force:
                logger.info(f"Remove existing zip file: {self.zipfile_path}")
                os.remove(self.zipfile_path)
            else:
                raise FileExistsError

        # open zip file
        logger.debug(f"Open zip file in write mode at {self.zipfile_path}")
        with ZipFile(self.zipfile_path, mode="x") as self._zipfile:
            self._add_input_files()

            self._add_topology_files()

            self._add_gtfs_timetables_file()

            if include_outputs:
                self._add_output_files()

        # log success and file details
        logger.success(f"Scenario has been zipped to {self.zipfile_path}:")
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
            self._zip_scenario_file(
                graph_filepath, [paths.ENVIRONMENT_FOLDER_NAME, paths.OSM_GRAPHS_FOLDER_NAME]
            )

            # add speeds if its a filepath
            speeds_info = info["speeds"]
            if isinstance(speeds_info, str):
                self._zip_scenario_file(
                    speeds_info, [paths.ENVIRONMENT_FOLDER_NAME, paths.GRAPH_SPEEDS_FOLDER_NAME]
                )

    def _add_gtfs_timetables_file(self):
        """
        Add GTFS file to zip.
        """
        gtfs_timetable_filepath = self.scenario.get_gtfs_timetable_filepath()
        if gtfs_timetable_filepath is None:
            return
        self._zip_scenario_file(
            gtfs_timetable_filepath, [paths.ENVIRONMENT_FOLDER_NAME, paths.GTFS_FEEDS_FOLDER_NAME]
        )

    def _zip_scenario_folder(self, folder_path):
        """
        Add all folder contents (including its subfolders) to zip.

        :param folder_path: path to folder
        """
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = str(os.path.join(root, file))
                relpath = os.path.relpath(full_path, os.path.join(folder_path, ".."))
                self._zip_scenario_file(full_path, relpath.split(os.sep)[:-1])

    def _zip_scenario_file(self, filepath, dest_folders_path):
        """
        Add file to zip.

        :param filepath: path to original file
        :param dest_folders_path: list of zip folders to put the file in.
        """
        dest_filepath = os.path.join(*dest_folders_path, os.path.basename(filepath))
        logger.debug(f"Add {filepath} to zip at {dest_filepath}")
        self._zipfile.write(filepath, str(dest_filepath))


class ScenarioUnzipper(ScenarioZipping):

    def __init__(self, filepath):
        super().__init__(filepath)

    def run(self, force: bool = False, force_common_files: bool = False):
        """
        Unzip the scenario zip in the data folder tree.

        :param force: overwrite scenario folder if it already exists
        :param force_common_files: overwrite common files (environment, common inputs) if they already exist
        """

        # open zip file
        logger.debug(f"Open zip file {self.zipfile_path} in read mode")
        with ZipFile(self.zipfile_path, mode="r") as self._zipfile:

            scenario_folder_path = self._get_scenario_folder_path()

            # check if scenario folder already exists
            if os.path.exists(scenario_folder_path):
                if force:
                    logger.info(f"Remove existing scenario folder: {scenario_folder_path}")
                    shutil.rmtree(scenario_folder_path)
                else:
                    raise FileExistsError(scenario_folder_path)

            # create scenario folders
            logger.info(f"Create scenario folders at {scenario_folder_path}")
            os.mkdir(scenario_folder_path)
            inputs_folder = paths.scenario_inputs_folder(scenario_folder_path)
            os.mkdir(inputs_folder)
            self._set_scenario(scenario_folder_path)

            # extract scenario files
            self._extract_scenario_files(force_common_files)

        # log success and file details
        logger.success(
            f"Scenario has been unzipped to {scenario_folder_path} and in environment subfolders ({paths.environment_folder()})"
        )
        self._zipfile = None

    def _extract_scenario_files(self, force_common_files):
        """
        Extract zip files to the relevant data folders.

        :param force_common_files: overwrite common files if they already exist
        """
        logger.info(f"Start extraction of scenario zip: {self.zipfile_path}")

        for zip_info in self._zipfile.infolist():

            filename = zip_info.filename
            logger.debug(f"Prepare to extract {filename}")

            if filename.startswith(paths.INPUT_FOLDER_NAME):
                folder_path = self.scenario.scenario_folder
            elif filename.startswith(paths.OUTPUT_FOLDER_NAME):
                folder_path = self.scenario.scenario_folder
            elif filename.startswith(paths.COMMON_INPUTS_FOLDER):
                folder_path = paths.data_folder()
            elif filename.startswith(
                os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.OSM_GRAPHS_FOLDER_NAME)
            ):
                folder_path = paths.data_folder()
            elif filename.startswith(
                os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.GRAPH_SPEEDS_FOLDER_NAME)
            ):
                folder_path = paths.data_folder()
            elif filename.startswith(
                os.path.join(paths.ENVIRONMENT_FOLDER_NAME, paths.GTFS_FEEDS_FOLDER_NAME)
            ):
                folder_path = paths.data_folder()
            else:
                logger.warning(
                    f"Unrecognized path type: {filename}. File is ignored, please manually extract to the correct folder."
                )
                continue

            self._extract_to(zip_info, folder_path, force_common_files)

    def _extract_to(self, zip_info, folder, force_common_files):
        """
        Extract the zipped file to the given folder.

        The final path will be the folder path and the relative zip path joined together.

        :param zip_info: ZipInfo instance or relative filepath in zip
        :param folder: folder to extract zipinfo
        :param force_common_files: whether to extract common files or not
        """
        filename = zip_info.filename

        filepath = os.path.join(folder, filename)

        # check if file already exists (environment files)
        if os.path.exists(filepath) and not force_common_files:
            logger.warning(f"Common file {filepath} already exists and was not extracted")
        else:
            logger.info(f"Extract {filename} from zip to {filepath}")
            self._zipfile.extract(zip_info, path=folder)

    def _get_scenario_folder_path(self):
        """
        Evaluate scenario path from the parameters file contained inside the zip.

        :return: path to the target scenario folder
        """
        # get path to parameters file in zip
        parameters_file = os.path.join(paths.INPUT_FOLDER_NAME, paths.PARAMETERS_FILENAME)

        # read parameters file
        with self._zipfile.open(parameters_file) as params:
            param_dict = json.loads(params.read())

            # get model code and scenario name
            model = param_dict["code"]
            scenario_name = param_dict["scenario"]

            # check model folder existence
            model_folder = paths.model_folder(model)
            if not os.path.exists(model_folder):
                raise DataFolderError(f"Missing model folder {model_folder}")

            scenario_path = os.path.join(model_folder, scenario_name)

        return scenario_path


def zip_scenario_from_args(args):
    zipper = ScenarioZipper(args.scenario_path, args.outfile)

    try:
        zipper.run(force=args.force, include_outputs=args.include_outputs)
    except FileExistsError:
        logger.error(
            f"The file {zipper.zipfile_path} already exists. Use the -f (or --force) option to overwrite it."
        )


def unzip_scenario_from_args(args):
    unzipper = ScenarioUnzipper(args.zip_path)

    try:
        unzipper.run(force=args.force, force_common_files=args.force_common_files)
    except FileExistsError as e:
        logger.error(
            f"The scenario folder {str(e)} already exists. Use the -f (or --force) option to overwrite it"
        )
    except DataFolderError as e:
        logger.error(
            f"{str(e)}. Use the --data-folder option to specify the data folder, or run starling-sim data --data-tree to generate the data folder tree."
        )


def add_zip_unzip_actions(subparsers):
    """
    Add a subparser for the zip and unzip actions.

    :param subparsers: argparse subparsers
    """
    # parser for zipping scenarios
    zip_parser = subparsers.add_parser(
        "zip",
        description="Zip simulation scenarios for simpler transfers. "
        "Best used with the unzip action. The resulting zip file will be placed in the scenario folder",
        help="Zip a simulation scenario",
    )

    zip_parser.add_argument("scenario_path", help="path to scenario folder", type=str)

    zip_parser.add_argument(
        "-f",
        "--force",
        help="force zip creation even if the file already exists",
        action="store_true",
    )

    zip_parser.add_argument(
        "--include-outputs", help="include scenario outputs in the zip file", action="store_true"
    )

    zip_parser.add_argument(
        "-o", "--outfile", help="name of the output file", type=str, default=None
    )

    # store exec function in parser
    zip_parser.set_defaults(zip=zip_scenario_from_args)

    # parser for unzipping scenarios
    unzip_parser = subparsers.add_parser(
        "unzip",
        description="Unzip a zipped scenario. "
        "Best used with the zip action. The resulting scenario file will be placed in the relevant model folder",
        help="Unzip a simulation scenario",
    )

    unzip_parser.add_argument("zip_path", help="path to scenario zip", type=str)

    unzip_parser.add_argument(
        "-f", "--force", help="delete scenario folder if it already exists", action="store_true"
    )

    unzip_parser.add_argument(
        "--force-common-files",
        help="overwrite common scenario files (environment, common inputs)",
        action="store_true",
    )

    # store exec function in parser
    unzip_parser.set_defaults(unzip=unzip_scenario_from_args)
