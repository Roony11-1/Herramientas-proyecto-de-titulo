from typing import List
import networkx as nx
from utils.graph_utils import get_edge

def route_cost(G, route):
    # Sumamos 500 solo si el atributo 'toll' es True
    total = 0
    for u, v in zip(route[:-1], route[1:]):
        if G.edges[u, v, 0].get("toll"):
            total += 500
    return total