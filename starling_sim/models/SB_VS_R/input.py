from starling_sim.basemodel.input.dynamic_input import DynamicInput


class Input(DynamicInput):
    def pre_process_input_dict(self, input_dict):

        # TODO : use a default fleet and stations name when there is no operator

        if input_dict["agent_type"] == "station":

            operator = self.sim.agentPopulation.population["operator"][input_dict["operator_id"]]

            # add station population
            input_dict["population"] = operator.stations_dict_name

        elif input_dict["agent_type"] == "user":

            if "origin_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][input_dict["origin_station"]]
                input_dict["origin"] = user_station.position

            if "destination_station" in input_dict:
                user_station = self.sim.agentPopulation["station"][
                    input_dict["destination_station"]
                ]
                input_dict["destination"] = user_station.position

        elif input_dict["agent_type"] == "staff":

            # add origin at depot
            # TODO : adapt for multiple depots
            operator = self.sim.agentPopulation.population["operator"][input_dict["operator_id"]]
            input_dict["origin"] = list(operator.depotPoints.values())[0].position
