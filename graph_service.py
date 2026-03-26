import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from typing import List

from weight_service import calculate_edge_metrics

FILE = "santiago_urbano.graphml"
TOLLS_FILE = "tolls.geojson"

# Lista de comunas para el área de Santiago
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

def load_graph() -> nx.MultiDiGraph:
    print("=== INICIO load_graph ===")

    # 1. Intentar cargar desde Caché
    if os.path.exists(FILE):
        try:
            print("[CACHE] Cargando grafo desde archivo...")
            G = ox.load_graphml(FILE)
            
            # Verificación de integridad de datos (pesos)
            sample_edge = next(iter(G.edges(data=True)))[2]
            
            needs_prepare = (
                "time" not in sample_edge or 
                "cost" not in sample_edge or 
                "length" not in sample_edge or
                "balanced" not in sample_edge or
                isinstance(sample_edge.get("cost"), (str, list))
            )

            if needs_prepare:
                print("[INFO] Pesos incompletos o corruptos. Recalculando...")
                _prepare_weights(G)
                print("[CACHE] Guardando grafo actualizado...")
                ox.save_graphml(G, FILE)
            
            # Si llegó aquí, el grafo está perfecto
            _print_graph_info(G)
            _debug_tolls(G)
            return G

        except Exception as e:
            print(f"[ERROR] Archivo GraphML corrupto o vacío: {e}")
            print("[REINTENTO] Eliminando archivo dañado y descargando de nuevo...")
            if os.path.exists(FILE):
                os.remove(FILE)
            # Al no retornar aquí, el código seguirá naturalmente al bloque de descarga
    
    # 2. Descarga desde cero (Si no hay archivo o estaba corrupto)
    print("[DOWNLOAD] Iniciando descarga de Santiago Urbano...")
    G = _download_graph(places)
    
    print("[CLEAN] Limpiando grafo (componentes desconectados)...")
    G = _clean_graph(G)

    # 3. Procesar Peajes
    toll_gdf = load_toll_points()
    if toll_gdf is not None:
        mark_tolls_in_graph(G, toll_gdf)
        propagate_tolls_to_edges(G)

    # 4. Preparar pesos (length, time, cost, balanced)
    print("[WEIGHTS] Calculando métricas de ruteo...")
    _prepare_weights(G)

    # 5. Guardar Caché final
    print(f"[CACHE] Guardando grafo en {FILE}...")
    ox.save_graphml(G, FILE)

    _print_graph_info(G)
    _debug_tolls(G)
    return G

def _prepare_weights(G):
    print("[WEIGHTS] Aplicando modelo de costos y fricción...")
    for u, v, k, data in G.edges(keys=True, data=True):
        metrics = calculate_edge_metrics(data)
        
        # Seteamos los nuevos pesos en el grafo
        data["length"] = metrics["length"]
        data["time"] = metrics["time"]
        data["cost"] = metrics["cost"]
        data["balanced"] = metrics["balanced"]

# ======================
# TOLLS & DOWNLOAD (Mantenidos igual, con mejoras de estabilidad)
# ======================
def load_toll_points() -> gpd.GeoDataFrame | None:
    if os.path.exists(TOLLS_FILE):
        print("[TOLLS CACHE] Cargando desde archivo...")
        return gpd.read_file(TOLLS_FILE)

    print("[TOLLS] Descargando pórticos...")
    tags = {"highway": ["toll_gantry"], "barrier": ["toll_booth"], "toll": ["yes"]}
    gdfs = []

    for place in places:
        try:
            gdf = ox.features_from_place(place, tags)
            if not gdf.empty: gdfs.append(gdf)
        except Exception: continue

    if not gdfs: return None
    result = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    result.to_file(TOLLS_FILE, driver="GeoJSON")
    return result

def _download_graph(places: List[str]) -> nx.MultiDiGraph:
    gdfs = [ox.geocode_to_gdf(place) for place in tqdm(places, desc="Geocodificando")]
    gdf_all = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    polygon = gdf_all.unary_union
    return ox.graph_from_polygon(polygon, network_type="drive")

def _clean_graph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    largest_cc = max(nx.weakly_connected_components(G), key=len)
    return G.subgraph(largest_cc).copy()

def mark_tolls_in_graph(G: nx.MultiDiGraph, gdf: gpd.GeoDataFrame) -> None:
    print("[TOLLS] Marcando nodos...")
    for _, row in gdf.iterrows():
        point = row.geometry.centroid
        try:
            node = ox.distance.nearest_nodes(G, point.x, point.y)
            G.nodes[node]["toll"] = True
        except: continue

def propagate_tolls_to_edges(G: nx.MultiDiGraph) -> None:
    for u, v, k, data in G.edges(keys=True, data=True):
        if G.nodes[u].get("toll") or G.nodes[v].get("toll"):
            data["toll"] = True

def _debug_tolls(G):
    total = sum(1 for _, _, _, d in G.edges(keys=True, data=True) if d.get("toll"))
    print(f"[TOLLS] Edges con peaje: {total}")

def _print_graph_info(G: nx.MultiDiGraph) -> None:
    print(f"\n=== INFO GRAFO ===\nNodos: {len(G.nodes)}\nEdges: {len(G.edges)}\n=== FIN ===\n")