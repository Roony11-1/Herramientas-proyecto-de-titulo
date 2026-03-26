# Parámetros Económicos
CLP_PER_HOUR = 12000.0
CLP_PER_SECOND = CLP_PER_HOUR / 3600.0

# Fricción Urbana (Penalización de velocidad real vs teórica)
FRICTION_FACTORS = {
    'motorway': 1.0,
    'primary': 0.8,
    'secondary': 0.65,
    'tertiary': 0.5,
    'residential': 0.35,
    'unclassified': 0.4
}

# Costos de Infraestructura (TAG)
TOLL_COSTS = {
    'motorway': 1450.0,
    'motorway_link': 700.0,
    'default': 450.0
}