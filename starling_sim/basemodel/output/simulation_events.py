import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ElementTree
from collections.abc import Iterable
from starling_sim.utils.utils import (
    gz_compression,
    gz_decompression
)

VERSION = "0.0.1"


class SimulationEvents:
    """
    Class for generating an event file output from a simulation.
    """

    def __init__(self):
        self.tree: ElementTree = None
        self.root: Element = None
        self.agents: Element = None
        self.version = None

    def create_empty_root(self):
        self.root = ET.Element("document", event_file_version=VERSION)
        self.tree = ET.ElementTree(self.root)
        self.agents = ET.SubElement(self.root, "agents")
        self.version = VERSION

    def set_tree(self, element_tree: ElementTree):
        self.tree = element_tree
        self.root = element_tree.getroot()
        assert self.root.tag == "document"
        self.agents = self.root.find("agents")
        assert self.agents is not None
        self.version = self.root.get("event_file_version")

    def add_agent(self, agent_element):
        self.agents.append(agent_element)

    # init methods

    def from_simulation_model(simulation_model):
        """
        Create a SimulationEvents instance from a simulation.

        Add events for all the agents of the population.

        :param simulation_model: SimulationModel instance

        :return: SimulationEvents instance
        """
        instance = SimulationEvents()

        instance.create_empty_root()

        for agent in simulation_model.agentPopulation.get_total_population():
            # don't display agents with empty trace
            # if len(agent.trace.eventList) <= 2:
            #     continue

            agent_element = ET.Element("agent", attrib={"id": agent.id, "agentType": agent.type})

            for event in agent.trace.eventList:
                agent_element.append(event.to_xml())

            instance.add_agent(agent_element)

        return instance

    from_simulation_model = staticmethod(from_simulation_model)

    def from_file(filepath):
        """
        Create a SimulationEvents instance from a simulation event file.

        :param filepath: path to the event file

        :return: SimulationEvents instance
        """
        # decrompress file if necessary
        if filepath.endswith(".gz"):
            gz_decompression(filepath, delete_source=False)
            filepath = filepath[:-3]

        tree = ET.parse(filepath)
        instance = SimulationEvents()
        instance.set_tree(tree)

        return instance

    from_file = staticmethod(from_file)

    # event browsing

    def agents_events(self, agent_type: str = None) -> list:
        """
        Return an iterable over the "agent"-tagged elements.

        If an agent type is provided, return only the agents of the matching agent type.

        :param agent_type: agent type filter

        :return: list of "agent" elements matching the agent type
        """
        agent_list = []
        for agent in self.agents:
            if agent_type is not None and agent.get("agentType") != agent_type:
                continue

            agent_list.append(agent)

        return agent_list

    def agent_element(self, agent_id: str) -> Element | None:
        """
        Find the "agent" element corresponding to the given id.

        :param agent_id: agent id to find in the events

        :return: "agent" element matching the id, or None if it is not found
        """
        for agent in self.agents:
            if agent.get("id") == agent_id:
                return agent
        return None

    # utils

    def tostring(self) -> str:
        """
        Convert the tree to an indented string.

        :return: tree as a string
        """
        ET.indent(self.root, space="\t", level=0)
        return ET.tostring(self.root, encoding="unicode")

    def write(self, filepath):
        """
        Write the tree to a XML file.

        If the filepath ends with ".gz", the output file is compressed.

        :param filepath: path to the target file
        """

        # check gz extension
        if filepath.endswith(".gz"):
            to_gz = True
            filepath = filepath[:-3]
        else:
            to_gz = False

        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(filepath)

        if to_gz:
            gz_compression(filepath)


