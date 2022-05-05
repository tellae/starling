from starling_sim.basemodel.agent.vehicles.service_vehicle import ServiceVehicle
from starling_sim.basemodel.trace.events import StaffOperationEvent


class RepositioningVehicle(ServiceVehicle):
    def process_stop_(self, stop):

        if stop.type == stop.REPOSITIONING:
            yield self.execute_process(self.process_repositioning_(stop))
            self.planning.remove(stop)
        elif stop.type is None:
            self.planning.remove(stop)
            return
        else:
            self.log_message("Unsupported stop type to process {}".format(stop.type), 30)

        # compute the dwell time duration
        dwell_time = self.compute_dwell_time(stop)

        yield self.execute_process(self.spend_time_(dwell_time))

    # TODO : refactor and cleanup
    def process_repositioning_(self, stop):
        """
        Realise the repositioning operation described by the stop.

        If 'total' attribute is negative, the service vehicle takes
        objects from the station. The operations are realised respecting
        the service vehicle and station capacity constraints.

        :param stop: stop with type REPOSITIONING
        """

        if stop.station not in self.operator.stations:
            return

        station = self.operator.stations[stop.station]
        self.log_message("Processing stop {}".format(stop))
        successful_operations = 0
        targets = []
        if stop.total < 0:

            for i in range(-stop.total):

                if self.load() == self.seats:
                    break

                request = station.get_from_store(self)

                # TODO : works with 0 ?
                result = yield request.event_ | self.sim.scheduler.timeout(0)

                if request.event_ in result:

                    request.success = True
                    request.result = result[request.event_]
                    # end request
                    request.event_.cancel()

                    successful_operations -= 1
                    targets.append(request.result)
                    self.add_passenger(request.result)
                else:
                    break

        else:

            for i in range(stop.total):

                if self.load() == 0:
                    break

                occupant = self.occupants[-1]
                request = station.return_to_store(self, occupant)

                # TODO : works with 0 ?
                result = yield request.event_ | self.sim.scheduler.timeout(0)

                if request.event_ in result:
                    request.success = True
                    # end request
                    request.event_.cancel()

                    successful_operations += 1
                    targets.append(occupant)
                    self.remove_passenger(occupant)
                else:
                    break

        operation_event = StaffOperationEvent(
            self.sim.scheduler.now(),
            self,
            successful_operations,
            stop.total,
            targets=targets,
            structure=station,
        )
        self.trace_event(operation_event)

    # def repositioning(self, action_type, station):
    #
    #     # get the action information and request
    #     if action_type == -1:
    #         limit = self.seats
    #         request = station.get_from_store(self)
    #     elif action_type == 1:
    #         limit = 0
    #         occupant = self.occupants[-1]
    #         request = station.return_to_store(self, occupant)
    #     else:
    #         self.log_message("Unknown action type for repositioning {}".format(action_type), 30)
    #         return False
    #
    #     # try to execute the repositioning action
    #     result = yield request.event | self.sim.scheduler.timeout(0)
    #
    #     if request.event in result:
    #         request.success = True
    #         request.result = result[request.event]
    #         # end request
    #         request.event.cancel()
    #         self.get_passenger(request.result)
    #         if
    #
    #     else:
    #         break
