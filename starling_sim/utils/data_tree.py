"""
This module contains functions for the creation of the data folder tree and
the import of example scenarios from Tellae's Google Drive.
"""

import logging
import os
import subprocess

from starling_sim.utils import paths
from starling_sim.utils.utils import create_if_not_exists
from starling_sim.utils.test_models import TEST_DATA_FOLDER


# data tree generation


def create_data_tree():
    """
    Create the data tree according to the paths stored in paths.py.
    """

    logging.info("Creating data tree as described in simulator_sim.utils.paths\n")

    # data folder
    logging.info("Creating folder {}".format(paths.data_folder()))
    create_if_not_exists(paths.data_folder())

    logging.info("Creating folder {}".format(paths.common_inputs_folder()))
    create_if_not_exists(paths.common_inputs_folder())

    # environment folder
    logging.info("Creating folder {}".format(paths.environment_folder()))
    create_if_not_exists(paths.environment_folder())

    # OSM graphs folder
    logging.info("Creating folder {}".format(paths.osm_graphs_folder()))
    create_if_not_exists(paths.osm_graphs_folder())

    # graph speeds folder
    logging.info("Creating folder {}".format(paths.graph_speeds_folder()))
    create_if_not_exists(paths.graph_speeds_folder())

    # GTFS feeds folder
    logging.info("Creating folder {}".format(paths.gtfs_feeds_folder()))
    create_if_not_exists(paths.gtfs_feeds_folder())

    # models folder
    logging.info("Creating folder {}".format(paths.models_folder()))
    create_if_not_exists(paths.models_folder())


# TODO : do a nicer import, without the demand files at root the reference and outputs folders,
#  and accept a list of modes to import.
def import_examples():
    """
    Import the example scenarios from the test folders.
    """

    # import the scenarios from the test data folder
    import_examples_from_test_data(TEST_DATA_FOLDER)

    # if we're not in the starling folder, also get the scenarios from the starling folder
    list_dir = os.listdir(".")
    if "starling_sim" not in list_dir:
        import_examples_from_test_data(paths.starling_folder() + TEST_DATA_FOLDER)


def import_examples_from_test_data(test_data_folder):
    """
    Copy the example data from the given test folder to the data folder.

    Caution : this will reproduce the folder tree of the test folder. Only the
    custom data folder will be used.

    :param test_data_folder: data folder to copy
    """

    logging.info("Copying contents of {}".format(test_data_folder))

    list_dir = os.listdir(test_data_folder)

    dest = paths.data_folder()

    for name in list_dir:
        path = test_data_folder + name

        sh_copy(path, dest)


def sh_copy(src, dst):
    """
    Copy the source file/folder in the destination folder.

    We use the recursive option of cp, so folders will be copied recursively.

    :param src: path to the source folder
    :param dst: path to the destination folder
    """

    subprocess.run(["cp", "-r", src, dst])


# # example scenarios import functions
#
# def import_example_scenario(model_code):
#     """
#     Import example scenarios of the model from the remote server.
#
#     :param model_code: code of the model to import
#     """
#
#     # check the existence of the data folder
#     if not os.path.exists(paths.data_folder()):
#         raise ModuleNotFoundError("The data folder tree must be created before importing example scenarios")
#
#     # import example scenarios of the model
#     if model_code not in example_scenarios:
#         logging.info("No example scenario is available for model {} yet".format(model_code))
#         return
#     else:
#         logging.info("Importing example scenarios for model {}".format(model_code))
#
#     # get the link of the examples archive file
#     file_id = example_scenarios[model_code]
#
#     # import and unzip the archive
#     import_folder_from_file_id(file_id, model_code, paths.models_folder())
#
#
# def import_example_environment():
#     """
#     Import the examples environment data from the remote server.
#     """
#
#     logging.info("Importing environment for example scenarios")
#
#     # import osm graphs for examples
#     import_folder_from_file_id(OSM_GRAPHS_ID, "osmGraph", paths.osm_graphs_folder(), files_only=True)
#
#     # import graph speeds for examples
#     import_folder_from_file_id(GRAPH_SPEEDS_ID, "graphSpeeds", paths.graph_speeds_folder(), files_only=True)
#
#     # import gtfs feeds for example
#     pass

# def import_folder_from_file_id(file_id, folder_name, destination_path, files_only=False):
#     """
#     Download files from the given link and delete the archive.
#
#     This method is implemented for use with dropbox links leading to folders.
#
#     :param file_id: id of the file to download
#     :param folder_name: name of the downloaded folder
#     :param destination_path: path to download destination
#     :param files_only: only import files and not the folder tree
#     """
#
#     archive_name = folder_name + ".zip"
#     archive_path = destination_path + archive_name
#
#     # build the download link from file id
#     dl_link = google_drive_download_format.format(file_id)
#
#     logging.info("Downloading files from {} in {}\n".format(dl_link, destination_path))
#
#     # download files from the link
#
#     os.system("wget --no-check-certificate -O {} '{}'".format(archive_path, dl_link))
#
#     # extract the archive. If files_only, ignore the folder tree (-j option of unzip)
#     if files_only:
#         os.system("unzip -u -j -d {} {}".format(destination_path, archive_path))
#     else:
#         os.system("unzip -u -d {} {}".format(destination_path, archive_path))
#
#     # delete the archive
#     os.system("rm {}".format(archive_path))
#
#     # add a newline
#     print()
