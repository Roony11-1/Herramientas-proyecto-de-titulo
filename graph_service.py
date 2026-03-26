import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from typing import List

FILE = "santiago_urbano.graphml"
TOLLS_FILE = "tolls.geojson"

places: List[str] = [
    "Cerrillos, Chile", "La Reina, Chile", "Pudahuel, Chile",
    "Cerro Navia, Chile", "Las Condes, Chile", "Quilicura, Chile",
    "Conchalí, Chile", "Lo Barnechea, Chile", "Quinta Normal, Chile",
    "El Bosque, Chile", "Lo Espejo, Chile", "Recoleta, Chile",
    "Estación Central, Chile", "Lo Prado, Chile", "Renca, Chile",
    "Huechuraba, Chile", "Macul, Chile", "San Miguel, Chile",
    "Independencia, Chile", "Maipú, Chile", "San Joaquín, Chile",
    "La Cisterna, Chile", "Ñuñoa, Chile", "San Ramón, Chile",
    "La Florida, Chile", "Pedro Aguirre Cerda, Chile", "Santiago, Chile",
    "La Pintana, Chile", "Peñalolén, Chile", "Vitacura, Chile",
    "La Granja, Chile", "Providencia, Chile"
]


# ======================
# TOLLS
# ======================
def load_toll_points() -> gpd.GeoDataFrame | None:
    if os.path.exists(TOLLS_FILE):
        print("[TOLLS CACHE] Cargando desde archivo...")
        return gpd.read_file(TOLLS_FILE)

    print("[TOLLS] Descargando pórticos...")

    tags = {
        "highway": ["toll_gantry"],
        "barrier": ["toll_booth"],
        "toll": ["yes"]
    }

    gdfs = []

    for place in places:
        try:
            print(f"[TOLLS] {place}")
            gdf = ox.features_from_place(place, tags)

            if not gdf.empty:
                gdfs.append(gdf)

        except Exception as e:
            print(f"[TOLLS ERROR] {place}: {e}")

    if not gdfs:
        print("[TOLLS] No encontrados")
        return None

    result = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

    print(f"[TOLLS] Total: {len(result)}")

    # 🔥 guardar cache
    result.to_file(TOLLS_FILE, driver="GeoJSON")

    return result


# ======================
# GRAPH
# ======================
def load_graph() -> nx.MultiDiGraph:
    print("=== INICIO get_graph ===")

    if os.path.exists(FILE):
        print("[CACHE] Grafo cargado")
        G: nx.MultiDiGraph = ox.load_graphml(FILE)
    else:
        print("[DOWNLOAD] Grafo")

        G = _download_graph(places)

        # limpiar grafo
        G = _clean_graph(G)

        # --- TOLLS ---
        toll_gdf = load_toll_points()

        if toll_gdf is not None:
            mark_tolls_in_graph(G, toll_gdf)
            propagate_tolls_to_edges(G)

        print("[CACHE] Guardando grafo con tolls")
        ox.save_graphml(G, FILE)

    _print_graph_info(G)
    _debug_tolls(G)

    return G


def _download_graph(places: List[str]) -> nx.MultiDiGraph:
    with tqdm(total=3, desc="Progreso") as pbar:
        gdfs = []

        for place in places:
            print(f"[GEOCODING] {place}")
            gdf = ox.geocode_to_gdf(place)
            gdfs.append(gdf)

        pbar.update(1)

        gdf_all = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        polygon = gdf_all.unary_union

        pbar.update(1)

        G = ox.graph_from_polygon(polygon, network_type="drive")

        pbar.update(1)

    return G


def _clean_graph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    components = list(nx.weakly_connected_components(G))
    largest_cc = max(components, key=len)
    return G.subgraph(largest_cc).copy()


# ======================
# TOLL PROCESSING
# ======================
def mark_tolls_in_graph(G: nx.MultiDiGraph, gdf) -> None:
    print("[TOLLS] Marcando nodos...")

    for _, row in gdf.iterrows():
        geom = row.geometry
        point = geom.centroid if geom.geom_type != "Point" else geom

        try:
            node = ox.distance.nearest_nodes(G, point.x, point.y)
            G.nodes[node]["toll"] = True
        except Exception:
            continue


def propagate_tolls_to_edges(G: nx.MultiDiGraph) -> None:
    print("[TOLLS] Propagando a edges...")

    for u, v, k, data in G.edges(keys=True, data=True):
        if G.nodes[u].get("toll") or G.nodes[v].get("toll"):
            data["toll"] = True


# ======================
# DEBUG
# ======================
def _debug_tolls(G):
    total = sum(
        1 for _, _, _, d in G.edges(keys=True, data=True)
        if d.get("toll")
    )
    print(f"[TOLLS] Edges con peaje: {total}")


def _print_graph_info(G: nx.MultiDiGraph) -> None:
    print("\n=== INFO GRAFO ===")
    print("Nodos:", len(G.nodes))
    print("Edges:", len(G.edges))
    print("=== FIN ===\n")