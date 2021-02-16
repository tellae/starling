from starling_sim.basemodel.input.dynamic_input import DynamicInput


class Input(DynamicInput):

    def new_agent_input(self, feature):

        new_agent = super().new_agent_input(feature)

        input_dict = feature["properties"]

        if input_dict["agent_type"] == "vehicle":
            if "station" in input_dict:
                vehicle_station = self.sim.agentPopulation["station"][input_dict["station"]]
            else:
                vehicle_station = self.sim.environment.get_agent_at(new_agent.position,
                                                                    self.sim.agentPopulation["station"].values())
                if vehicle_station is None:
                    self.log_message("No station found for vehicle {}".format(new_agent), 40)
                    exit(1)
            vehicle_station.store.items.append(new_agent)
            vehicle_station.initial_stock += 1

    def pre_process_input_dict(self, input_dict):

        if input_dict["agent_type"] == "user":

            if "origin_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][input_dict["origin_station"]]
                input_dict["origin"] = user_station.position

            if "destination_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][input_dict["destination_station"]]
                input_dict["destination"] = user_station.position

        elif input_dict["agent_type"] == "vehicle":
            vehicle_station = self.sim.agentPopulation["station"][input_dict["station"]]
            input_dict["origin"] = vehicle_station.position
