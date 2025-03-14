from starling_sim.basemodel.output.event_file_output import EventFileOutput
from starling_sim.basemodel.trace.events import *
from starling_sim.basemodel.trace.trace import Traced

import pytest


class TestEventFileOutput:

    @pytest.fixture(scope="class")
    def traced(self):
        traced = Traced("user-0.1")
        traced.trace.eventList = [
            InputEvent(2000, None),
            RouteEvent(5000, {"route": [100, 200], "time": [0, 20], "length": [0, 45]}, "walk"),
            StopEvent(6000, "OPR", "S1", "trip_id", "stop_id")
        ]
        return traced

    def test_agent_events(self, traced):

        evt_output = EventFileOutput()

        evt_output.traced_to_xml(traced)

        print(evt_output.tostring())

        # evt_output.write()