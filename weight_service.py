from config import FRICTION_FACTORS, ALL_GANTRY_DATA, TOLL_COSTS_DEFAULT, CLP_PER_SECOND

def get_real_time(length, highway, speed_kph):
    """Calcula el tiempo en segundos considerando la fricción urbana."""
    
    # 1. Limpiar speed_kph (Ya lo tenías, mantenlo)
    if isinstance(speed_kph, list): 
        speed_kph = speed_kph[0]
    
    # 2. LIMPIAR highway (El culpable del error)
    # Si es una lista, tomamos el primer elemento (el más importante según OSM)
    if isinstance(highway, list):
        highway = highway[0]

    try:
        max_speed = float(speed_kph)
    except (ValueError, TypeError):
        max_speed = 50.0

    # Ahora highway es un string, el .get() funcionará perfecto
    factor = FRICTION_FACTORS.get(highway, FRICTION_FACTORS['unclassified'])
    
    real_speed_mps = (max_speed * factor) * 1000 / 3600
    
    return length / real_speed_mps if real_speed_mps > 0 else 999999

def get_monetary_cost(length, highway, edge_data, exclude_highways=None):
    """Calcula el costo CLP. Retorna inf si la autopista está excluida."""
    exclude_highways = exclude_highways or []

    # 1. Caso base: No es peaje
    if not edge_data.get("toll"):
        return float(length * 0.000001)

    # 2. Obtener y Limpiar el ID del pórtico (Ref)
    gantry_id = edge_data.get("ref")
    
    # Manejo de listas de OSMnx
    if isinstance(gantry_id, list): 
        gantry_id = gantry_id[0]
    
    # Normalización: "pa-32" -> "PA32" (crucial para que coincida con tu diccionario)
    if gantry_id:
        gantry_id = str(gantry_id).strip().upper().replace(" ", "").replace("-", "")
    
    # 3. Buscar en tu base de datos (ALL_GANTRY_DATA)
    gantry_info = ALL_GANTRY_DATA.get(gantry_id)
    
    if gantry_info:
        # Bloqueo por nombre de concesionaria/autopista
        if gantry_info.get("highway_name") in exclude_highways:
            return float('inf') 
        toll_price = gantry_info["price"]
    else:
        # 4. FALLBACK: Si OSM dice que hay toll pero no tenemos el ID mapeado
        # Normalizamos highway para evitar el error de 'unhashable type: list'
        highway_key = highway[0] if isinstance(highway, list) else highway
        
        # Asignamos precio por defecto según el tipo de vía
        toll_price = TOLL_COSTS_DEFAULT.get(highway_key, TOLL_COSTS_DEFAULT.get('default', 650))
        
        # Opcional: Log para saber qué IDs te faltan por mapear
        print(f"[MISSING DATA] Pórtico '{gantry_id}' en '{highway_key}' no mapeado. Usando default: ${toll_price}")
    
    return float(toll_price)

def get_balanced_weight(u, v, edge_data, exclude_highways=None):
    """
    Esta es la función que NetworkX llamará. 
    Debe retornar un solo número (el peso).
    """
    # OSMnx MultiDiGraph devuelve un dict de dicts en edge_data
    data = edge_data[0] 
    
    length = data.get("length", 0)
    highway = data.get("highway", "unclassified")
    if isinstance(highway, list): highway = highway[0]

    # 1. Costo de Peaje (o Infinito si está excluido)
    cost = get_monetary_cost(length, highway, data, exclude_highways)
    
    if cost == float('inf'):
        return float('inf')

    # 2. Costo del Tiempo (Tiempo en seg * $/seg)
    time_seconds = get_real_time(length, highway, data.get("maxspeed", 50))
    time_cost_clp = time_seconds * CLP_PER_SECOND

    # 3. Peso final: ¿Cuántos pesos chilenos me cuesta este arco?
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