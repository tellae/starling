from starling_sim.basemodel.topology.network_weight import NetworkWeight
import random


class BikeWeightOSM(NetworkWeight):
    """
    Improve bike routing by defining a better weight on bike networks.

    This weight is defined on OSM attributes. The necessary attributes are:
        - 'cycleway', 'cycleway:right', 'cycleway:left'
        - 'bridge'

    """

    DEFAULT_PARAMETERS = {
        "length": 2.25,
        "link_constant": 1.61,
        "upslope>4.length": 3.24,
        "facility.length": -0.74,
        "separate_facility.length": -1.80,
        "bridge": 5.41,
        "bridge.facility": -2.83,
    }

    def pre_process_edge(self, u, v, d):
        # d["slope"] = random.randint(-8, 8)*random.random()

        cycleway = None

        if "highway" in d and d["highway"] == "cycleway":
            cycleway = "separate"

        elif "cycleway" in d:
            cycleway = d["cycleway"]
        elif "cycleway:left" in d:
            cycleway = d["cycleway:left"]
        elif "cycleway:right" in d:
            cycleway = d["cycleway:right"]

        if cycleway == "no":
            bike_facility = "no"
        elif cycleway == "track" or cycleway == "separate":
            bike_facility = "separate"
        else:
            bike_facility = "yes"

        d["bike_facility"] = bike_facility

    def compute_edge_weight(self, u, v, d, parameters):

        total_weight = 0
        length = d["length"]

        total_weight += parameters["link_constant"]

        total_weight += parameters["length"] * length

        # if d["slope"] > 4:
        #     total_weight += parameters["upslope>4.length"]*length

        if d["bike_facility"] == "separate":
            total_weight += parameters["separate_facility.length"] * length
        elif d["bike_facility"] == "yes":
            total_weight += parameters["facility.length"] * length

        if "bridge" in d and d["bridge"] == "yes":
            total_weight += parameters["bridge"]

            if d["bike_facility"] in ["separate", "yes"]:
                total_weight += parameters["bridge.facility"]

        if total_weight < 0:
            total_weight = 0.01

        return total_weight
