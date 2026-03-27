import osmnx as ox
import networkx as nx
from typing import List, Dict, Any
from config import ALL_GANTRY_DATA, TOLL_COSTS_DEFAULT, CLP_PER_SECOND
from weight_service import get_real_time, get_balanced_weight

def generate_route_with_details(
    G: nx.MultiDiGraph,
    orig_lat: float, orig_lon: float,
    dest_lat: float, dest_lon: float,
    exclude_highways: List[str] = None,
    weight_type: str = "balanced"  # Opciones: 'balanced', 'length', 'time', 'cost'
) -> Dict[str, Any]:
    
    exclude_highways = exclude_highways or []

    # 1. Encontrar y validar nodos
    orig_node = ox.distance.nearest_nodes(G, orig_lon, orig_lat)
    dest_node = ox.distance.nearest_nodes(G, dest_lon, dest_lat)

    if not _validate_node_distance(G, orig_node, orig_lat, orig_lon): 
        return {"success": False, "error": "Origen fuera de rango"}
    if not _validate_node_distance(G, dest_node, dest_lat, dest_lon): 
        return {"success": False, "error": "Destino fuera de rango"}

    try:
        # En lugar de weight='balanced', usa una lambda para pasar el Grafo G
        path = nx.shortest_path(
            G, orig_node, dest_node, 
            weight=lambda u, v, d: get_balanced_weight(
                u, v, d, G, 
                weight_type=weight_type,
                exclude_highways=exclude_highways
            )
        )
        
        # 4. Métricas finales (Siempre calculamos todo para el resumen)
        gantries, total_toll, total_time, total_distance = _get_route_metrics(G, path)
        
        return {
            "success": True,
            "type": weight_type,
            "path": path,
            "summary": {
                "total_toll_cost": round(total_toll, 2),
                "total_time_minutes": round(total_time / 60, 1),
                "total_distance_km": round(total_distance / 1000, 2),
                "total_time_seconds": round(total_time, 2),
                "total_distance_meters": round(total_distance, 2)
            },
            "gantries_detected": gantries
        }
    except nx.NetworkXNoPath:
        return {"success": False, "error": f"No hay ruta disponible para el criterio: {weight_type}"}
    
def _validate_node_distance(
    G: nx.MultiDiGraph,
    node: int,
    lat: float,
    lon: float,
    max_dist: float = 500  # Distancia máxima en metros
) -> bool:
    """
    Verifica que el nodo encontrado por OSMnx esté realmente cerca 
    de las coordenadas proporcionadas por el usuario.
    """
    # 1. Extraer coordenadas del nodo en el grafo
    node_data = G.nodes[node]
    node_lat = node_data["y"]
    node_lon = node_data["x"]

    # 2. Calcular la distancia real (en línea recta/círculo máximo) entre el click y el nodo
    # ox.distance.great_circle es ideal porque entrega metros
    dist = ox.distance.great_circle(lat, lon, node_lat, node_lon)

    print(f"DEBUG: Distancia del click al nodo más cercano: {dist:.2f} metros")

    # 3. Retornar True si está dentro del rango aceptable (ej: 500 metros)
    if dist <= max_dist:
        return True
    else:
        print(f"ERROR: El punto seleccionado está muy lejos de la red vial ({dist:.2f}m)")
        return False

def _get_route_metrics(G, path):
    total_toll, total_time, total_distance = 0, 0, 0
    passed_gantries = []
    
    for u, v in zip(path[:-1], path[1:]):
        data = G.get_edge_data(u, v)[0]
        node_u = G.nodes[u]
        node_v = G.nodes[v]
        
        # 1. Acumular distancia y tiempo
        dist = data.get("length", 0)
        total_distance += dist
        highway = data.get("highway", "unclassified")
        if isinstance(highway, list): highway = highway[0]
        
        total_time += get_real_time(dist, highway, data.get("maxspeed", 50))
        
        # 2. Detección de Peaje (Consistente con el ruteo)
        is_toll = node_u.get("toll") or node_v.get("toll") or data.get("toll")
        
        if is_toll:
            ref = node_u.get("ref") or node_v.get("ref") or data.get("ref")
            if isinstance(ref, list): ref = ref[0]
            clean_id = str(ref).strip().upper().replace(" ", "").replace("-", "") if ref else "S_ID"

            # BUSQUEDA CON PREFIJOS (Igual que en weight_service)
            gantry_info = None
            for prefix in ["", "AC_", "CN_", "VN_", "VS_"]:
                test_key = f"{prefix}{clean_id}" if prefix and not clean_id.startswith(prefix) else clean_id
                if test_key in ALL_GANTRY_DATA:
                    gantry_info = ALL_GANTRY_DATA[test_key]
                    break

            if gantry_info:
                price = gantry_info["price"]
                h_name = gantry_info["highway_name"]
            else:
                # Fallback si sigue siendo desconocido
                price = TOLL_COSTS_DEFAULT.get(highway, 650)
                h_name = f"Desconocida ({clean_id})"

            # Evitar duplicados (un pórtico suele ser un solo nodo, pero por si acaso)
            if not passed_gantries or passed_gantries[-1]['ref'] != clean_id:
                passed_gantries.append({
                    "ref": clean_id,
                    "highway": h_name,
                    "price": price
                })
                total_toll += price
                
    return passed_gantries, total_toll, total_time, total_distance