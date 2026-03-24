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


def route_length(G: nx.MultiDiGraph, route: List[int]) -> float:
    return sum(
        _get_edge(G, u, v).get("length", 0)
        for u, v in zip(route[:-1], route[1:])
        if _get_edge(G, u, v)
    )


def route_time(G: nx.MultiDiGraph, route: List[int]) -> float:
    total = 0.0

    for u, v in zip(route[:-1], route[1:]):
        edge = _get_edge(G, u, v)
        if not edge:
            continue

        length = edge.get("length", 0)
        speed = edge.get("speed_kph", 50)

        if isinstance(speed, list):
            speed = speed[0]

        total += length / (speed * 1000 / 3600)

    return total


def route_cost(G: nx.MultiDiGraph, route: List[int]) -> int:
    cost = 0

    for u, v in zip(route[:-1], route[1:]):
        edge = _get_edge(G, u, v)
        if not edge:
            continue

        highway = edge.get("highway")

        if isinstance(highway, list):
            highway = highway[0]

        if highway == "motorway":
            cost += 100

    return cost


def _get_edge(G: nx.MultiDiGraph, u: int, v: int):
    data = G.get_edge_data(u, v)

    if data:
        return data[min(data.keys())]

    # fallback (por seguridad, aunque no debería pasar en rutas válidas)
    data = G.get_edge_data(v, u)
    if data:
        return data[min(data.keys())]

    return None