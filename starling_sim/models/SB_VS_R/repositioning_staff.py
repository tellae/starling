from starling_sim.basemodel.agent.vehicles.repositioning_vehicle import RepositioningVehicle


class RepositioningStaff(RepositioningVehicle):
    """
    This class describes the repositioning staff of the SB_VS_R model.
    """

    SCHEMA = {"properties": {}, "required": ["dwell_time"]}

    def __init__(self, simulation_model, agent_id, origin, dwell_time, seats, **kwargs):
        super().__init__(simulation_model, agent_id, origin, seats, dwell_time=dwell_time, **kwargs)

    def loop_(self):

        while True:

            # be idle if planning is empty
            yield self.execute_process(self.test_idle_())

            next_stop = self.planning[0]

            # move to next stop
            self.tempDestination = next_stop.position
            yield self.execute_process(self.move_())

            # wait for the fixed processing time
            if (
                next_stop.arrivalTime is not None
                and next_stop.arrivalTime > self.sim.scheduler.now()
            ):
                yield self.execute_process(
                    self.wait_(next_stop.arrivalTime - self.sim.scheduler.now())
                )

            # process the stop
            yield self.execute_process(self.process_stop_(next_stop))
