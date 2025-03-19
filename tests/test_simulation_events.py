from builtins import isinstance
from starling_sim.basemodel.output.simulation_events import SimulationEvents
from starling_sim.utils import paths
from xml.etree.ElementTree import Element
import pytest


class TestSimulationEvents:

    @pytest.fixture(scope="class")
    def event_file(self):
        return paths.model_folder("SB_VS") + "example_nantes/reference/events.xml"

    @pytest.fixture(scope="class")
    def instance(self, event_file):
        return SimulationEvents.from_file(event_file)

    def test_from_file(self, event_file):

        res = SimulationEvents.from_file(event_file)

        assert isinstance(res, SimulationEvents)

    def test_agents_events(self, instance):

        user_events = instance.agents_events(agent_type="user")

        assert len(user_events) == 46
        assert isinstance(user_events[0], Element)
        assert user_events[0].get("agentType") == "user"

    def test_agent_element(self, instance):

        agent = instance.agent_element("user-0.1")

        assert isinstance(agent, Element)
        assert agent.get("id") == "user-0.1"

