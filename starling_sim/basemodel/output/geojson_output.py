"""
This module contains tools for the generation of a geojson output,
used for visualisation purposes, after the simulation run
"""

from starling_sim.basemodel.agent.requests import StopPoint
from starling_sim.basemodel.agent.agent import Agent
from starling_sim.basemodel.agent.spatial_agent import SpatialAgent
from starling_sim.basemodel.agent.moving_agent import MovingAgent
from starling_sim.basemodel.agent.operators.operator import Operator
from starling_sim.basemodel.output.feature_factory import *
from starling_sim.basemodel.agent.stations.station import Station
from starling_sim.utils.utils import (
    json_dump,
    new_feature_collection,
    gz_compression,
    gz_decompression,
)
from starling_sim.utils.config import config

from abc import ABC

# list of supported icons for the geojson format
ICON_LIST = [
    "user",
    "user-01",
    "user-02",
    "user-03",
    "user-04",
    "user-05",
    "user-06",
    "user-07",
    "user-08",
    "user-09",
    "user-10",
    "stop_point",
    "station",
    "car",
    "bike",
    "bus",
    "subway",
    "tram",
    "train",
    "odt",
    "truck",
]

# default version of the geojson output format
CURRENT_GEOJSON_VERSION = 1


# Abstract Base Class for the geojson output generation


class GeojsonOutput(ABC):
    """
    Manage the generation of a geojson output, mainly for visualisation purposes.
    """

    #: Version of the geojson output generator
    VERSION = "X.X.X"

    def __init__(self):
        """
        Create a new object for the generation of a geojson file.

        Most attributes are initialised within the setup method.
        """

        # simulation information

        # simulation model from which information is extracted
        self.sim = None

        # dict of the simulation topologies
        self.graphs = None

        # construction of the output structure as a FeatureCollection

        # dict giving the information factories for each agent type
        self.information_factories = dict()

        # list of features of the final output
        self.features = None

        # current element converted as a feature
        self.current_element = None

        # feature of the current agent
        self.current_feature = None

        # output file

        # output folder
        self.folder = None

        # output filename
        self.filename = None

    def setup(self, simulation_model, filename, folder):
        """
        Set the values of the simulation model, topologies and outfile

        This setup method is called during simulation setup

        :param simulation_model:
        :param filename:
        :param folder:
        """

        self.sim = simulation_model
        self.graphs = simulation_model.environment.topologies
        self.features = []
        self.filename = filename
        self.folder = folder

        for factories in self.information_factories.values():

            for factory in factories:

                factory.setup(simulation_model)

    def set_information_factories(self, information_factories):

        self.information_factories = information_factories

    def add_population_features(self, population=None):
        """
        Build and add features for the given population, with additional information
        provided by the information factories.

        These are added to the features attributes, used to build the final FeatureCollection.

        If population is

        :param population: population key, population list or None.
        """

        if isinstance(population, str) and population in self.sim.agentPopulation:
            population_list = self.sim.agentPopulation[population].values()
        elif isinstance(population, list):
            population_list = population
        elif population is None:
            population_list = self.sim.agentPopulation.get_total_population()
        else:
            raise TypeError("Unsupported type for population : {}".format(population.__class__))

        for element in population_list:
            self.add_element_feature(element)

    def add_element_feature(self, element):

        self.init_element_feature(element)

        self.add_factories_information()

        if self.current_feature is not None:
            self.features.append(self.current_feature)

    def init_element_feature(self, element):
        pass

    def add_factories_information(self):
        pass

    def generate_geojson(self):
        """
        Write the geojson feature collection in a file.
        """

        # generate a feature collection from the geojson features
        feature_collection = new_feature_collection(self.features)

        # add a version field
        feature_collection["version"] = self.VERSION

        # build file path
        path = self.folder + self.filename

        # check bz2 extension
        if path.endswith(".gz"):
            to_gz = True
            path = path[:-3]
        else:
            to_gz = False

        # write the geojson file
        json_dump(feature_collection, path)

        # compress to bz2 if necessary
        mimetype = "application/json"
        if to_gz:
            path = gz_compression(path)
            mimetype = "application/gzip"

        # signal new file to output factory
        self.sim.outputFactory.new_output_file(
            path, mimetype, compressed_mimetype="application/json", content="visualisation"
        )


# Classes for the generation of geojson output


class GeojsonOutput1(GeojsonOutput):

    VERSION = "1.0"

    def init_element_feature(self, element):
        """
        Initialise a geojson feature for the element regarding its class.

        The current_feature attribute is set with a geojson feature or None.

        :param element: simulation element
        """

        self.current_element = element
        self.current_feature = None

        if isinstance(element, MovingAgent):
            self.current_feature = create_line_string_feature(self, element)

        elif isinstance(element, StopPoint):
            self.current_feature = create_point_feature(self, element, icon_type="stop_point")

        elif isinstance(element, SpatialAgent):
            self.current_feature = create_point_feature(self, element)

        elif isinstance(element, Operator):

            if len(element.stopPoints.values()) != 0:
                self.add_population_features(list(element.stopPoints.values()))

            self.current_element = element
            if element.serviceZone is not None:
                self.current_feature = create_multi_polygon_feature(self, element, icon_type="")

    def add_factories_information(self):

        if not isinstance(self.current_element, Agent):
            return

        if self.current_element.type not in self.information_factories:
            return

        information_dict = dict()
        factories = self.information_factories[self.current_element.type]

        for event in self.current_element.trace.eventList:

            for factory in factories:
                factory.update(event, self.current_element)

        for factory in factories:
            information_dict[factory.key] = factory.get_dict()

        self.current_feature["properties"]["information"] = information_dict


class GeojsonOutput0(GeojsonOutput):

    VERSION = "0.1"

    def init_element_feature(self, element):

        self.current_element = element
        self.current_feature = None

        if isinstance(element, Operator):

            if len(element.stopPoints.values()) != 0:
                self.add_population_features(list(element.stopPoints.values()))

            self.current_element = element
            if element.serviceZone is not None:
                self.current_feature = create_multi_polygon_feature(self, element, icon_type="")

        elif isinstance(element, StopPoint):

            self.current_feature = create_point_feature(self, element, icon_type="stop_point")
            self.current_feature["properties"]["position"] = [
                self.current_feature["geometry"]["coordinates"]
            ] * 2
            self.current_feature["properties"]["duration"] = [0, 99999]

        elif isinstance(element, Station):

            self.current_feature = create_point_feature(self, element, icon_type="station")
            self.current_feature["properties"]["position"] = [
                self.current_feature["geometry"]["coordinates"]
            ] * 2
            self.current_feature["properties"]["duration"] = [0, 99999]

        elif isinstance(element, SpatialAgent):
            self.current_feature = create_point_feature(self, element)
            localisations, timestamps = get_element_line_string(self, element)
            self.current_feature["geometry"]["coordinates"] = localisations[0]
            self.current_feature["properties"]["position"] = localisations
            self.current_feature["properties"]["duration"] = timestamps


# function for the creation of a geojson output instance of the correct version


def new_geojson_output():
    """
    Create a new GeojsonOutput instance.

    Use the version provided in the 'geojson_version' field of parameters,
    and the default version if not provided.

    :return: GeojsonOutput instance
    """

    # get the geojson version
    geojson_version = config["geojson_version"]
    if geojson_version is None:
        geojson_version = CURRENT_GEOJSON_VERSION

    # create the geojson output
    if geojson_version == 0:
        geojson_output = GeojsonOutput0()
    elif geojson_version == 1:
        geojson_output = GeojsonOutput1()
    else:
        logging.warning(
            "Unknown geojson format version {}. Give only the main version number.".format(
                geojson_version
            )
        )
        geojson_output = None

    return geojson_output
