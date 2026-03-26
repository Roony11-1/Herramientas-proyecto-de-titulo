from config import FRICTION_FACTORS, TOLL_COSTS, CLP_PER_SECOND

def calculate_edge_metrics(data):
    """Procesa una sola arista y retorna sus 4 pesos."""
    # 1. Distancia
    length = data.get("length", 0)
    if isinstance(length, list): length = length[0]
    length = float(length)

    # 2. Tiempo Realista
    highway = data.get("highway", "unclassified")
    if isinstance(highway, list): highway = highway[0]
    
    max_speed = data.get("speed_kph", 50)
    if isinstance(max_speed, list): max_speed = max_speed[0]
    
    try:
        max_speed = float(max_speed)
    except:
        max_speed = 50.0

    factor = FRICTION_FACTORS.get(highway, FRICTION_FACTORS['unclassified'])
    real_speed_mps = (max_speed * factor) * 1000 / 3600
    time_seconds = length / real_speed_mps if real_speed_mps > 0 else 9999

    # 3. Costo Monetario
    toll_price = 0.0
    if data.get("toll"):
        toll_price = TOLL_COSTS.get(highway, TOLL_COSTS['default'])
    
    cost_weight = toll_price + (length * 0.000001)

    # 4. Peso Equilibrado
    balanced_weight = toll_price + (time_seconds * CLP_PER_SECOND)

    return {
        "length": length,
        "time": time_seconds,
        "cost": cost_weight,
        "balanced": balanced_weight
    }