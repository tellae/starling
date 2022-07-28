from starling_sim.utils.utils import (
    new_point_feature,
    new_line_string_feature,
    new_multi_polygon_feature,
)
from starling_sim.basemodel.trace.events import InputEvent, RouteEvent, PositionChangeEvent

import logging


def create_point_feature(geojson_output, element, agent_id=None, icon_type=None, agent_type=None):

    point = get_element_point(geojson_output, element)
    feature = new_point_feature(point_localisation=point)
    add_agent_id(feature, element, agent_id)
    add_icon_type(feature, element, icon_type)
    add_agent_type(feature, element, agent_type)

    return feature


def create_line_string_feature(
    geojson_output, element, agent_id=None, icon_type=None, agent_type=None
):

    localisations, timestamps = get_element_line_string(geojson_output, element)
    feature = new_line_string_feature(localisations)
    feature["properties"]["timestamps"] = timestamps
    add_agent_id(feature, element, agent_id)
    add_icon_type(feature, element, icon_type)
    add_agent_type(feature, element, agent_type)

    return feature


def create_multi_polygon_feature(
    geojson_output, element, agent_id=None, icon_type=None, agent_type=None
):

    polygon_list = get_element_multi_polygon(geojson_output, element)
    feature = new_multi_polygon_feature(polygon_list)
    add_agent_id(feature, element, agent_id)
    add_icon_type(feature, element, icon_type)
    add_agent_type(feature, element, agent_type)

    return feature


def get_element_point(geojson_output, element):

    return geojson_output.sim.environment.get_localisation(element.position)[::-1]


def get_element_multi_polygon(geojson_output, element):

    zone_polygon = element.serviceZone.loc[0, "geometry"]
    linear_ring_coordinates = []
    for coord in zone_polygon.exterior.coords:
        linear_ring_coordinates.append(list(coord))
    polygon = [linear_ring_coordinates]
    polygon_list = [polygon]

    return polygon_list


def get_element_line_string(geojson_output, element):

    agent = element

    if not hasattr(agent, "origin"):
        return None

    # lists of localisations [lng, lat] and timestamps
    localisations = []
    timestamps = []

    # we add a position at 0 for the viz
    localisations.append(geojson_output.sim.environment.get_localisation(agent.origin))
    timestamps.append(0)

    # get agent's trace
    trace_list = agent.trace.eventList

    # start processing the trace
    i = 0

    while i < len(trace_list):

        # get the current event
        event = trace_list[i]

        # for the input event, add origin and input time
        if isinstance(event, InputEvent):

            # the input event should always come first
            if i == 0:
                localisations.append(geojson_output.sim.environment.get_localisation(agent.origin))
                current_time = event.timestamp
                timestamps.append(current_time)
            else:
                logging.warning("InputEvent does not come first in {}'s trace".format(agent.id))

        # for a route event, add all localisations
        # of the route (origin and dest included)
        if isinstance(event, RouteEvent):

            # get route mode
            mode = event.mode

            # get the list of route localisations and timestamps
            route_positions, route_timestamps = route_localisations(
                event, geojson_output.sim.scenario["limit"], geojson_output.graphs[mode]
            )

            # add it to the agent's lists
            localisations = localisations + route_positions
            timestamps = timestamps + route_timestamps

        # for a position change event, add the localisations and timestamps
        elif isinstance(event, PositionChangeEvent):

            # get the move mode
            mode = event.mode

            # add it to the agent's lists
            localisations.append(geojson_output.graphs[mode].position_localisation(event.origin))
            timestamps.append(event.timestamp)

            localisations.append(
                geojson_output.graphs[mode].position_localisation(event.destination)
            )
            timestamps.append(event.timestamp + event.duration)

        i += 1

    # add a lasting position for viz
    localisations.append(localisations[-1])
    timestamps.append(99999)

    # reverse lat and lon
    new_locs = []
    for loc in localisations:
        new_locs.append([loc[1], loc[0]])
    localisations = new_locs

    return localisations, timestamps


def route_localisations(route_event, time_limit, topology):
    """
    Return the localisations and timestamps of the given event route.

    :param route_event: RouteEvent
    :param time_limit: time limit of the simulation
    :param topology: Topology object corresponding to the route used
    :return: tuple of lists, localisations and timestamps
    """
    route = route_event.data["route"]
    durations = route_event.data["time"]

    current_time = route_event.timestamp

    localisations = []
    timestamps = []

    for i in range(len(route)):

        # compute current time
        current_time += durations[i]

        # we stop at simulation time limit
        if current_time > time_limit:
            break

        # append the localisation and time data
        if isinstance(route[i], tuple):
            localisations.append(route[i])
        else:
            localisations.append(topology.position_localisation(route[i]))

        timestamps.append(current_time)

    return localisations, timestamps


def add_agent_id(feature, element, agent_id=None):
    if agent_id is None:
        agent_id = element.id
    feature["properties"]["agent_id"] = agent_id


def add_icon_type(feature, element, icon_type=None):
    if icon_type is None:
        icon_type = element.icon
    feature["properties"]["icon_type"] = icon_type


def add_agent_type(feature, element, agent_type=None):
    if agent_type is None:
        agent_type = element.type
    feature["properties"]["agent_type"] = agent_type
