import os
import osmnx as ox
import networkx as nx
from tqdm import tqdm
from typing import List

FILE = "santiago_urbano.graphml"


def load_graph() -> nx.MultiDiGraph:
    print("=== INICIO get_graph ===")

    if os.path.exists(FILE):
        print(f"[CACHE] Archivo encontrado: {FILE}")
        G: nx.MultiDiGraph = ox.load_graphml(FILE)
        print("[CACHE] Grafo cargado correctamente")
    else:
        print("[DOWNLOAD] Descargando grafo...")

        places: List[str] = [
            "Santiago, Chile",
            "Independencia, Chile"
        ]

        G = _download_graph(places)

        print("[CACHE] Guardando grafo...")
        ox.save_graphml(G, FILE)

    _print_graph_info(G)

    return G


def _download_graph(places: List[str]) -> nx.MultiDiGraph:
    steps = ["Geocoding", "Uniendo polígonos", "Descargando grafo"]

    with tqdm(total=len(steps), desc="Progreso") as pbar:
        gdfs = [ox.geocode_to_gdf(p) for p in places]
        pbar.update(1)

        polygon = gdfs[0].union_all()
        for gdf in gdfs[1:]:
            polygon = polygon.union(gdf.union_all())

        pbar.update(1)

        G: nx.MultiDiGraph = ox.graph_from_polygon(
            polygon,
            network_type="drive"
        )
        pbar.update(1)

    return G


def _print_graph_info(G: nx.MultiDiGraph) -> None:
    print("\n=== INFO GRAFO ===")
    print("Nodos:", len(G.nodes))
    print("Edges:", len(G.edges))

    highways = set()
    for _, _, data in G.edges(data=True):
        hw = data.get("highway")
        if isinstance(hw, list):
            highways.update(hw)
        elif hw:
            highways.add(hw)

    print("Highways:", sorted(highways))
    print("=== FIN ===\n")