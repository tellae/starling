from starling_sim.models.SB_VS.user import User as SB_VS_user


class User(SB_VS_user):
    """
    This class describes a station-based vehicle-sharing user with possibility of round trips
    """

    def loop_(self):
        """
        Main loop of a station-based vehicle-sharing user
        """

        # loop on trying to get vehicle at closest station
        yield self.execute_process(self.request_loop_(self.maxTries))

        if self.vehicle is None:
            # if failed to get a vehicle, leave the system
            self.leave_simulation("FAIL_GET")
        else:

            # if round trip, move to current position with duration equal to round_trip parameter
            # if "origin_station" in self.profile and "destination_station" in self.profile \
            #         and self.profile["origin_station"] == self.profile["destination_station"]:
            #     self.log_message("Round trip !")
            #     self.tempDestination = self.sim.agentPopulation["station"][self.profile["destination_station"]].position
            #     yield self.execute_process(self.move_shortest_with_vehicle_(duration=self.profile["round_trip"]))

            # loop on trying to leave vehicle at station closest to dest
            yield self.execute_process(self.request_loop_())

            # should not have a vehicle
            if self.vehicle is not None:
                self.simulation_error("Did not return its vehicle")
            else:
                # end trip
                yield self.execute_process(self.walk_to_destination_())

            return

