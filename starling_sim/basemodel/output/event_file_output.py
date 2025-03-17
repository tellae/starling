import xml.etree.ElementTree as ET


class EventFileOutput:

    VERSION = "0.0.1"

    def __init__(self):
        self.document = ET.Element("document", event_file_version=self.VERSION)
        self.tree = ET.ElementTree(self.document)
        self.agents = ET.SubElement(self.document, "agents")

    def add_agent_traces(self, simulation_model):

        for agent in simulation_model.agentPopulation.get_total_population():
            # don't display agents with empty trace
            # if len(agent.trace.eventList) <= 2:
            #     continue

            traced_element = ET.Element("agent", attrib={"id": agent.id, "agentType": agent.type})

            for event in agent.trace.eventList:
                traced_element.append(event.to_xml())

            self.agents.append(traced_element)

    def tostring(self):
        ET.indent(self.document, space="\t", level=0)
        return ET.tostring(self.document, encoding="unicode")

    def write(self, filepath):
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(filepath)


