from starling_sim.basemodel.output.output_factory import OutputFactory
from starling_sim.basemodel.output.kpi_output import KpiOutput
from starling_sim.basemodel.output.kpis import (
    MoveKPI,
    WaitKPI,
    SuccessKPI,
    DestinationReachedKPI,
    GetVehicleKPI,
    StationOccupationKPI,
    LeaveSimulationKPI,
)
from starling_sim.basemodel.output.information_factory import ActivityInformation, StockInformation


class Output(OutputFactory):
    """
    Class realising the outputs of the station-based vehicle-sharing model
    """

    def setup_kpi_output(self):

        # kpi output classes

        # users kpi
        move_kpi = MoveKPI()
        wait_kpi = WaitKPI()
        success_kpi = SuccessKPI(["nbFailedRequest"])
        destination_kpi = DestinationReachedKPI()
        leave_simulation_kpi = LeaveSimulationKPI()
        users_kpi_output = KpiOutput(
            "user", [move_kpi, wait_kpi, success_kpi, destination_kpi, leave_simulation_kpi]
        )

        # vehicle kpi
        move_kpi = MoveKPI()
        get_vehicle_kpi = GetVehicleKPI()
        vehicles_kpi_output = KpiOutput("vehicle", [move_kpi, get_vehicle_kpi])

        # stations kpi
        success_kpi = SuccessKPI(["nbSuccessGet", "nbFailedGet", "nbSuccessPut", "nbFailedPut"])
        wait_kpi = WaitKPI()
        availability_kpi = StationOccupationKPI()
        stations_kpi_output = KpiOutput("station", [success_kpi, wait_kpi, availability_kpi])

        self.kpi_outputs = [users_kpi_output, vehicles_kpi_output, stations_kpi_output]

    def setup_geojson_output(self):

        super().setup_geojson_output()

        stock_factory = StockInformation()
        activity_information = ActivityInformation()

        information_factories = {"station": [stock_factory], "user": [activity_information]}

        self.geojson_output.set_information_factories(information_factories)
