from typing import List
import networkx as nx
from utils.graph_utils import get_edge


def route_cost(G: nx.MultiDiGraph, route: List[int]) -> int:
    cost = 0

    for u, v in zip(route[:-1], route[1:]):
        edge = get_edge(G, u, v)
        if not edge:
            continue

        highway = edge.get("highway")

        if isinstance(highway, list):
            highway = highway[0]

        # --- COSTO BASE ---
        if highway == "motorway":
            cost += 0
        elif highway in ["trunk", "primary"]:
            cost += 0
        elif highway in ["secondary"]:
            cost += 0

        # --- PEAJE ---
        if edge.get("toll"):
            cost += 500

    return cost