from starling_sim.utils.utils import json_load

from abc import ABC, abstractmethod
import pandas as pd


class NetworkEdgeSpeed(ABC):
    """
    Abstract class for speed evaluation on topologies.
    """
    
    def __init__(self):
        # data structure containing the information used to evaluate speeds
        self._speeds_data = None

    @property
    def speeds_data(self):
        """
        Access the speeds data structure
        """
        return self._speeds_data

    @abstractmethod
    def __call__(self, u, v, d) -> float:
        """
        Get the edge's speed from the data stored in self._speeds_data

        :param u: origin node
        :param v: destination node
        :param d: edge data

        :return: speed in km/h
        """
        pass


class ConstantSpeed(NetworkEdgeSpeed):
    """
    Evaluate a constant speed independently of the edge.
    """
    def __init__(self, speed: float):
        super().__init__()
        self._speeds_data = speed
        
    def __call__(self, u, v, d) -> float:
        return self._speeds_data


class SpeedByHighwayType(NetworkEdgeSpeed):
    """
    Evaluate the edge speed based on its "highway" tag.

    This class uses a speed mapper that maps "highway" tag values to speed values.
    The mapper has the following format: { <tag>: { "speed": <speed_value> } }.

    If a list of tags is provided, use the first one.
    If the tag ends with '_links' and is not found in the speed mapper,
    look for the tag value without the '_link' suffix.
    If the tag is still not found in the mapper, use the 'other' value of the mapper.
    """
    def __init__(self, speeds_json_file: str):
        """
        :param speeds_json_file: path to a json file containing the speed mapper
        """
        super().__init__()
        self._speeds_datas = json_load(speeds_json_file)
    
    def __call__(self, u, v, d) -> float:
        # choose the first tag if several are provided
        if isinstance(d["highway"], list):
            d["highway"] = d["highway"][0]

        # differentiate speeds among the link types
        if d["highway"] in self._speeds_datas:
            speed = self._speeds_datas[d["highway"]]["speed"]
        elif d["highway"].endswith("_link") and d["highway"][:-5] in self._speeds_datas:
            speed = self._speeds_datas[d["highway"][:-5]]["speed"]
        else:
            speed = self._speeds_datas["other"]["speed"]
            
        return speed


class SpeedByEdge(NetworkEdgeSpeed):
    """
    Evaluate speed individually for each network edge.

    This class uses a mapper that maps (origin, destination) tuples to speed values.
    The mapper is read from a CSV file that contains "origin", "destination" and "speed" columns.

    The mapper must contain exactly one value for each (directed) edge of the graph.
    """
    def __init__(self, speeds_table_file: str):
        super().__init__()

        speeds_csv = pd.read_csv(speeds_table_file)
        assert set(speeds_csv.columns) >= {"origin", "destination", "speed"}, (
            f"Missing columns in speed file {speeds_table_file}. "
            f"Expected columns are ['origin', 'destination', 'speed']")

        speeds_dict = dict()
        for _, row in speeds_csv.iterrows():
            od = (row["origin"], row["destination"])
            assert od not in speeds_dict, f"Several speed values found for edge: {od[0]} -> {od[1]}"

            speeds_dict[od] = row["speed"]
            
        self._speeds_datas = speeds_dict
            
    def __call__(self, u, v, d) -> float:
        od = (u, v)
        if od not in self._speeds_datas:
            raise ValueError(f"Missing speed value for edge: {u} -> {v}")
        return self._speeds_datas[od]
        
    