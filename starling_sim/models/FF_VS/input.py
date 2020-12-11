from starling_sim.basemodel.input.dynamic_input import DynamicInput


class Input(DynamicInput):

    def pre_process_input_dict(self, input_dict):

        if input_dict["agent_type"] == "vehicle":
            # add vehicle origin position
            self.add_key_position_with_mode(input_dict, "origin", [input_dict["mode"], "walk"])
