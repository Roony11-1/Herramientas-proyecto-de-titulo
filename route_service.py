import osmnx as ox
import networkx as nx
from typing import List, Dict, Any
from config import ALL_GANTRY_DATA, TOLL_COSTS_DEFAULT, CLP_PER_SECOND
from weight_service import get_real_time

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

    def weight_logic(u, v, edge_data):
        data = edge_data[0]
        node_u = G.nodes[u]
        
        highway = data.get("highway", "unclassified")
        if isinstance(highway, list): highway = highway[0]
        
        gantry_ref = node_u.get("ref")
        if isinstance(gantry_ref, list): gantry_ref = gantry_ref[0]
        # Limpieza de ID
        if gantry_ref: gantry_ref = str(gantry_ref).strip().upper().replace(" ", "")

        # 1. Lógica de Costo (Consistente)
        cost = 0
        if node_u.get("toll"):
            if gantry_ref in ALL_GANTRY_DATA:
                # Verificar exclusión
                if weight_type != "length" and ALL_GANTRY_DATA[gantry_ref]["highway_name"] in exclude_highways:
                    return float('inf')
                cost = ALL_GANTRY_DATA[gantry_ref]["price"]
            else:
                # Fallback si el ID no está en nuestro dict
                cost = TOLL_COSTS_DEFAULT.get(highway, 650)

        # 2. Retorno según criterio
        if weight_type == "cost":
            return float(cost + (data.get("length", 0) * 0.000001))
        
        if weight_type == "length":
            return float(data.get("length", 0))

        time_sec = get_real_time(data.get("length", 0), highway, data.get("maxspeed", 50))
        
        if weight_type == "time":
            return float(time_sec)
            
        # Balanced: Costo + (Tiempo * Valor del tiempo)
        return float(cost + (time_sec * CLP_PER_SECOND))

    try:
        # 3. Cálculo de la ruta
        path = nx.shortest_path(G, orig_node, dest_node, weight=weight_logic)
        
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
        
        dist = data.get("length", 0)
        total_distance += dist
        
        highway = data.get("highway", "unclassified")
        if isinstance(highway, list): highway = highway[0]
        
        time_segment = get_real_time(dist, highway, data.get("maxspeed", 50))
        total_time += time_segment
        
        if node_u.get("toll"):
            ref = node_u.get("ref")
            if isinstance(ref, list): ref = ref[0]
            if ref: ref = str(ref).strip().upper().replace(" ", "")
            
            # Buscamos el precio (Real o Fallback)
            if ref in ALL_GANTRY_DATA:
                price = ALL_GANTRY_DATA[ref]["price"]
                h_name = ALL_GANTRY_DATA[ref]["highway_name"]
            else:
                price = TOLL_COSTS_DEFAULT.get(highway, 650)
                h_name = f"Desconocida ({ref if ref else 'Sin ID'})"

            # Evitar duplicados por segmentos cortados
            if not passed_gantries or passed_gantries[-1]['ref'] != ref:
                passed_gantries.append({
                    "ref": ref,
                    "highway": h_name,
                    "price": price
                })
                total_toll += price
                
    return passed_gantries, total_toll, total_time, total_distance