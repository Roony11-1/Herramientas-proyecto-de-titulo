import osmnx as ox
import matplotlib.pyplot as plt
import networkx as nx
from typing import List

def plot_graph_only(G: nx.MultiDiGraph) -> None:
    ox.plot_graph(
        G,
        node_size=0,
        edge_color="white",
        edge_linewidth=0.5,
        bgcolor="black"
    )

def plot_custom_route(G: nx.MultiDiGraph, route: List[int]) -> None:
    route_edges = set(zip(route[:-1], route[1:]))

    edge_colors = []
    edge_widths = []

    for u, v, k, data in G.edges(keys=True, data=True):
        highway = data.get("highway")

        # normalizar (puede venir como lista)
        if isinstance(highway, list):
            highway = highway[0]

        # --- BASE ---
        color = "white"
        width = 0.5

        # --- AUTOPISTAS ---
        if highway == "motorway":
            color = "orange"
            width = 1.5
            
        # --- PEAJES ---
        if data.get("toll"):
            color = "yellow"
            width = 2

        # --- RUTA ---
        if (u, v) in route_edges:
            color = "red"
            width = 3

        edge_colors.append(color)
        edge_widths.append(width)

    fig, ax = ox.plot_graph(
        G,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        node_size=0,
        bgcolor="black",
        show=False,
        close=False
    )

    plt.show()