from starling_sim.basemodel.input.dynamic_input import DynamicInput


class Input(DynamicInput):
    def pre_process_input_dict(self, input_dict):

        if input_dict["agent_type"] == "user":

            if "origin_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][input_dict["origin_station"]]
                input_dict["origin"] = user_station.position

            if "destination_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][
                    input_dict["destination_station"]
                ]
                input_dict["destination"] = user_station.position
