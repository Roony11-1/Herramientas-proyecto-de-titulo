import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from typing import List

from weight_service import REQUIRED_METRICS, calculate_edge_metrics

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

    if os.path.exists(FILE):
        try:
            print("[CACHE] Cargando grafo desde archivo...")
            G = ox.load_graphml(FILE)
            
            # --- NORMALIZACIÓN DE TIPOS (EL FIX CRÍTICO) ---
            # GraphML guarda booleanos como strings "True"/"False". Hay que revertirlo.
            for u, v, k, data in G.edges(keys=True, data=True):
                # 1. Corregir Peajes (evita que todo sea peaje al recargar)
                if "toll" in data:
                    # Si el valor es el string "True", se vuelve booleano True, sino False
                    data["toll"] = str(data["toll"]).lower() == "true"
                else:
                    data["toll"] = False
                
                # 2. Corregir IDs de pórticos (asegurar que no sean listas)
                if "ref" in data and isinstance(data["ref"], list):
                    data["ref"] = data["ref"][0]

                # 3. Corregir Métricas numéricas (asegurar que sean float)
                for field in REQUIRED_METRICS:
                    if field in data:
                        # Forzamos la conversión a float puro
                        val = data[field]
                        if isinstance(val, str):
                            # Limpiamos posibles caracteres raros del XML
                            val = val.replace('[', '').replace(']', '').replace("'", "")
                        try:
                            data[field] = float(val)
                        except:
                            data[field] = 0.0

            # --- VALIDACIÓN DE CONSISTENCIA ---
            sample_edge = next(iter(G.edges(data=True)))[2]
            # Si faltan métricas o siguen siendo basura, recalculamos
            needs_prepare = any(
                field not in sample_edge or not isinstance(sample_edge.get(field), (int, float))
                for field in REQUIRED_METRICS
            )

            if needs_prepare:
                print(f"[INFO] Grafo inconsistente en disco. Re-calculando métricas...")
                _prepare_weights(G)
                ox.save_graphml(G, FILE)
            
            _print_graph_info(G)
            _debug_tolls(G)
            return G

        except Exception as e:
            print(f"[ERROR] Fallo en caché al procesar tipos: {e}")
            if os.path.exists(FILE): os.remove(FILE)

    # 2. Descarga y Limpieza (Flujo Normal si no hay caché o falló)
    print("[DOWNLOAD] Iniciando descarga fresca de Santiago...")
    G = _download_graph(places)
    G = _clean_graph(G)

    # 3. Peajes (Marcado y Propagación)
    toll_gdf = load_toll_points()
    if toll_gdf is not None:
        mark_tolls_in_graph(G, toll_gdf)
        propagate_tolls_to_edges(G) # Esto pone toll=True/False REALES

    # 4. Preparación de Pesos
    _prepare_weights(G)

    print(f"[CACHE] Guardando grafo normalizado en {FILE}...")
    ox.save_graphml(G, FILE)
    
    _debug_tolls(G)
    return G

def _prepare_weights(G):
    """Aplica el cálculo masivo a todas las aristas."""
    print(f"[WEIGHTS] Procesando {len(G.edges)} aristas...")
    
    # IMPORTANTE: keys=True para que devuelva (u, v, k, data)
    for u, v, k, data in tqdm(G.edges(keys=True, data=True), desc="Calculando pesos"):
        metrics = calculate_edge_metrics(data)
        data.update(metrics)

def propagate_tolls_to_edges(G: nx.MultiDiGraph) -> None:
    print("[DEBUG] Iniciando propagación de peajes a aristas...")
    edges_with_toll = 0
    
    for u, v, k, data in G.edges(keys=True, data=True):
        # 1. Miramos si el nodo de origen (u) O el de destino (v) es peaje
        u_is_toll = G.nodes[u].get("toll", False)
        v_is_toll = G.nodes[v].get("toll", False)
        
        if u_is_toll or v_is_toll:
            data["toll"] = True
            # Priorizamos el ref del nodo que sea peaje
            ref_node = G.nodes[u] if u_is_toll else G.nodes[v]
            ref = ref_node.get("ref")
            data["ref"] = ref[0] if isinstance(ref, list) else ref
            edges_with_toll += 1
        else:
            data["toll"] = False
            data["ref"] = None
            # Aseguramos que el costo no traiga basura de sesiones previas
            data["cost"] = 0.0 

    print(f"[DEBUG] Propagación terminada. Aristas con peaje real: {edges_with_toll}")

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
    print("[TOLLS] Marcando nodos y asignando IDs...")
    found_counter = 0
    
    # 1. FILTRADO CRÍTICO: Solo queremos los puntos (Pórticos)
    # Ignoramos las geometrías tipo LineString o MultiLineString que representan la calle completa
    # Y nos aseguramos de que el highway sea 'toll_gantry'
    gdf_puntos = gdf[gdf.geometry.type == 'Point'].copy()
    
    for _, row in gdf_puntos.iterrows():
        # Solo procesamos si es un pórtico real con ID
        gantry_ref = row.get("ref")
        if not gantry_ref:
            continue
            
        point = row.geometry
        
        try:
            # Encontrar el nodo más cercano al punto exacto del pórtico
            node = ox.distance.nearest_nodes(G, point.x, point.y)
            
            # Asignar atributos al NODO
            G.nodes[node]["toll"] = True
            # Limpiamos el ref por si viene como lista o con basura
            clean_ref = gantry_ref[0] if isinstance(gantry_ref, list) else gantry_ref
            G.nodes[node]["ref"] = str(clean_ref).strip().upper()
            
            found_counter += 1
        except Exception as e:
            print(f"[ERROR] No se pudo marcar nodo para ref {gantry_ref}: {e}")
            continue
            
    print(f"[DEBUG] Nodos marcados como peaje: {found_counter} (de {len(gdf_puntos)} puntos en GeoJSON)")

def _debug_tolls(G):
    total = sum(1 for _, _, _, d in G.edges(keys=True, data=True) if d.get("toll"))
    print(f"[TOLLS] Edges con peaje: {total}")

def _print_graph_info(G: nx.MultiDiGraph) -> None:
    print(f"\n=== INFO GRAFO ===\nNodos: {len(G.nodes)}\nEdges: {len(G.edges)}\n=== FIN ===\n")