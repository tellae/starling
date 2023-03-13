from starling_sim.basemodel.output.output_factory import OutputFactory
from starling_sim.basemodel.output.kpi_output import KpiOutput
from starling_sim.basemodel.output.kpis import (
    MoveKPI,
)
from starling_sim.utils.constants import PUBLIC_TRANSPORT_TYPE


class Output(OutputFactory):
    def setup_kpi_output(self):
        # kpi output classes

        # vehicles kpi
        move_kpi = MoveKPI()
        vehicles_kpi_output = KpiOutput(PUBLIC_TRANSPORT_TYPE, [move_kpi])

        self.kpi_outputs = [
            vehicles_kpi_output,
        ]
