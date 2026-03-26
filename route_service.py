import osmnx as ox
import networkx as nx
from typing import List, Optional


def generate_route_from_coords(
    G: nx.MultiDiGraph,
    orig_lat: float,
    orig_lon: float,
    dest_lat: float,
    dest_lon: float
) -> Optional[List[int]]:

    orig_node = ox.distance.nearest_nodes(G, orig_lon, orig_lat)
    dest_node = ox.distance.nearest_nodes(G, dest_lon, dest_lat)

    if not _validate_node_distance(G, orig_node, orig_lat, orig_lon):
        return None

    if not _validate_node_distance(G, dest_node, dest_lat, dest_lon):
        return None

    try:
        return nx.shortest_path(G, orig_node, dest_node, weight="length")
    except nx.NetworkXNoPath:
        return None


def _validate_node_distance(
    G: nx.MultiDiGraph,
    node: int,
    lat: float,
    lon: float,
    max_dist: float = 500
) -> bool:

    node_data = G.nodes[node]

    dist = ox.distance.great_circle(
        lat, lon,
        node_data["y"], node_data["x"]
    )

    print(f"Distancia al nodo: {dist:.2f} m")

    return dist <= max_dist