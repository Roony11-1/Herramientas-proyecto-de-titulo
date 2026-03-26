from typing import List
import networkx as nx
from utils.graph_utils import get_edge


def route_length(G, route):
    return sum(G.edges[u, v, 0].get("length", 0) for u, v in zip(route[:-1], route[1:]))

def route_time(G, route):
    return sum(G.edges[u, v, 0].get("time", 0) for u, v in zip(route[:-1], route[1:]))