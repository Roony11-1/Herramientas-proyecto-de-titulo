from config import FRICTION_FACTORS, ALL_GANTRY_DATA, TOLL_COSTS_DEFAULT, CLP_PER_SECOND

def get_real_time(length, highway, speed_kph):
    """Calcula el tiempo en segundos considerando la fricción urbana."""
    
    # 1. Limpieza de highway (Defensivo contra None)
    if highway is None:
        highway = 'unclassified'
    if isinstance(highway, list): 
        highway = highway[0]
    
    # 2. Limpieza de speed_kph (Defensivo contra None/Listas)
    if speed_kph is None:
        speed_kph = 50.0
    if isinstance(speed_kph, list): 
        speed_kph = speed_kph[0]

    # 3. Conversión segura a float
    try:
        max_speed = float(speed_kph)
    except (ValueError, TypeError):
        max_speed = 50.0

    # 4. Obtención del factor (Si el tag no existe en tu dict, usa unclassified)
    factor = FRICTION_FACTORS.get(highway, FRICTION_FACTORS.get('unclassified', 0.4))
    
    # 5. Cálculo de velocidad real en metros por segundo
    # (km/h * factor) / 3.6 es lo mismo que (km/h * factor) * 1000 / 3600
    real_speed_mps = (max_speed * factor) / 3.6
    
    # 6. Retorno con fail-safe (Evitar división por cero o velocidades ridículas)
    if real_speed_mps < 0.5: # Menos de 1.8 km/h es caminar lento
        real_speed_mps = 0.5
        
    return length / real_speed_mps

def get_monetary_cost(length, highway, gantry_id, is_toll, exclude_highways=None):
    if not is_toll: return float(length * 0.000001)
    
    clean_id = str(gantry_id).strip().upper().replace(" ", "").replace("-", "")
    
    # Intentamos encontrar el ID con los prefijos conocidos
    # Esto resuelve el problema de tener varios "P1"
    possible_keys = [
        clean_id,           # ID directo (PA2, etc)
        f"AC_{clean_id}",    # Autopista Central
        f"CN_{clean_id}",    # Costanera
        f"VN_{clean_id}",    # Vespucio Norte
        f"VS_{clean_id}"     # Vespucio Sur
    ]
    
    gantry_info = None
    for key in possible_keys:
        if key in ALL_GANTRY_DATA:
            gantry_info = ALL_GANTRY_DATA[key]
            break

    if gantry_info:
        if gantry_info["highway_name"] in (exclude_highways or []):
            return float('inf')
        return float(gantry_info["price"])
    
    # Fallback si nada funciona
    highway_key = highway[0] if isinstance(highway, list) else highway
    return float(TOLL_COSTS_DEFAULT.get(highway_key, 650))

def get_balanced_weight(u, v, edge_data, G, weight_type="balanced", exclude_highways=None):
    """
    Versión Profesional: Detección Triple-Check (u, v, edge) y manejo de fallos.
    Optimizado para evitar costos $0 en autopistas concesionadas de Santiago.
    """
    # 1. Extracción segura de datos de la arista
    # OSMnx usa MultiDiGraph, por lo que edge_data suele ser un diccionario dentro de una lista o un dict directo
    data = edge_data[0] if isinstance(edge_data, (list, dict)) and 0 in edge_data else edge_data
    if isinstance(edge_data, list): data = edge_data[0]

    # 2. Normalización de atributos básicos
    length = float(data.get("length", 0))
    highway = data.get("highway", "unclassified")
    if isinstance(highway, list): highway = highway[0]
    
    # 3. TRIPLE-CHECK DE PEAJE (La clave del éxito)
    # Revisamos el nodo de salida, el de llegada y la arista misma.
    node_u = G.nodes[u]
    node_v = G.nodes[v]
    
    is_toll = (
        node_u.get("toll") == True or 
        node_v.get("toll") == True or 
        str(data.get("toll")).lower() == "true"
    )

    cost = 0.0
    if is_toll:
        # Buscamos el ID del pórtico (ref) en cualquier rincón disponible
        ref = node_u.get("ref") or node_v.get("ref") or data.get("ref")
        if isinstance(ref, list): ref = ref[0]
        
        # Llamamos a tu servicio de costos con el ID encontrado
        # Si get_monetary_cost devuelve 'inf', Dijkstra descartará esta ruta (evitar peajes)
        cost = get_monetary_cost(length, highway, ref, exclude_highways)
    else:
        # Si no hay peaje, aplicamos un micro-costo por distancia para 
        # desempatar rutas con el mismo tiempo.
        cost = length * 0.000001

    # 4. Manejo de exclusión (Si la ruta es infinita, se corta aquí)
    if cost == float('inf'):
        return float('inf')

    # 5. Lógica según el tipo de peso solicitado
    if weight_type == "length":
        return length

    # Cálculo de tiempo real (considerando velocidades de Santiago)
    time_seconds = get_real_time(length, highway, data.get("maxspeed", 50))
    
    if weight_type == "time":
        return float(time_seconds)

    # 6. Métrica Balanced (Dinero + Tiempo convertido a Dinero)
    # Esto es lo que hace que el algoritmo sea "inteligente"
    time_cost_clp = time_seconds * CLP_PER_SECOND
    
    return float(cost + time_cost_clp)

# Lista maestra de campos que CADA arco del grafo debe tener
REQUIRED_METRICS = ["length", "time", "cost", "balanced"]

def calculate_edge_metrics(data):
    """
    Calcula el set completo de métricas definidas en REQUIRED_METRICS.
    """
    length = data.get("length", 0)
    if isinstance(length, list): length = length[0]
    
    highway = data.get("highway", "unclassified")
    if isinstance(highway, list): highway = highway[0]
    
    # Valores base
    time_val = get_real_time(length, highway, data.get("maxspeed", 50))
    cost_val = get_monetary_cost(length, highway, data)
    
    # Retornamos el diccionario mapeado a la lista maestra
    return {
        "length": float(length),
        "time": float(time_val),
        "cost": float(cost_val),
        "balanced": float(cost_val + (time_val * CLP_PER_SECOND))
    }