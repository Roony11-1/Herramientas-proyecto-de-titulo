from typing import List
import networkx as nx
from utils.graph_utils import get_edge


def route_length(G: nx.MultiDiGraph, route: List[int]) -> float:
    return sum(
        get_edge(G, u, v).get("length", 0)
        for u, v in zip(route[:-1], route[1:])
        if get_edge(G, u, v)
    )


def route_time(G: nx.MultiDiGraph, route: List[int]) -> float:
    total = 0.0

    for u, v in zip(route[:-1], route[1:]):
        edge = get_edge(G, u, v)
        if not edge:
            continue

        length = edge.get("length", 0)
        speed = edge.get("speed_kph", 50)

        if isinstance(speed, list):
            speed = speed[0]

        total += length / (speed * 1000 / 3600)

    return total