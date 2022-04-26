from starling_sim.basemodel.output.output_factory import OutputFactory
from starling_sim.basemodel.output.kpi_output import KpiOutput
from starling_sim.basemodel.output.kpis import (
    MoveKPI,
    SuccessKPI,
    DestinationReachedKPI,
    GetVehicleKPI,
    LeaveSimulationKPI,
)
from starling_sim.basemodel.output.information_factory import ActivityInformation


class Output(OutputFactory):
    def setup_kpi_output(self):

        # kpi output classes

        # users kpi
        move_kpi = MoveKPI()
        success_kpi = SuccessKPI(["nbFailedRequest"])
        destination_kpi = DestinationReachedKPI()
        leave_simulation_kpi = LeaveSimulationKPI()
        users_kpi_output = KpiOutput(
            "user", [move_kpi, success_kpi, destination_kpi, leave_simulation_kpi]
        )

        # vehicles kpi
        move_kpi = MoveKPI()
        get_vehicle_kpi = GetVehicleKPI()
        vehicles_kpi_output = KpiOutput("vehicle", [move_kpi, get_vehicle_kpi])

        self.kpi_outputs = [users_kpi_output, vehicles_kpi_output]

    def setup_geojson_output(self):

        super().setup_geojson_output()

        activity_information = ActivityInformation()

        information_factories = {"vehicle": [activity_information], "user": [activity_information]}

        self.geojson_output.set_information_factories(information_factories)
