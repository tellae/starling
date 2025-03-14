import xml.etree.ElementTree as ET


class EventFileOutput:

    def __init__(self):
        self.root = ET.Element("root")
        self.tree = ET.ElementTree(self.root)



        self.agents = ET.SubElement(self.root, "agents")

        self.paths = None

    def add_agent_traces(self, simulation_model):

        for agent in simulation_model.agentPopulation.get_total_population():
            # don't display agents with empty trace
            # if len(agent.trace.eventList) <= 2:
            #     continue
            self.traced_to_xml(agent)



    def traced_to_xml(self, traced):

        traced_element = ET.Element("agent", attrib={"id": traced.id})

        for event in traced.trace.eventList:
            traced_element.append(event.to_xml())

        self.agents.append(traced_element)


    def tostring(self):
        ET.indent(self.root, space="\t", level=0)
        return ET.tostring(self.root, encoding="unicode")

    def write(self, filepath):
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(filepath)


