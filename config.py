# Parámetros Económicos
CLP_PER_HOUR = 12000.0
CLP_PER_SECOND = CLP_PER_HOUR / 3600.0

# Fricción Urbana: Velocidad real vs teórica según tipo de vía
FRICTION_FACTORS = {
    'motorway': 1.0,        # Autopista: Fluidez total
    'primary': 0.8,         # Avenidas: Semáforos moderados
    'secondary': 0.65,      # Avenidas medias
    'tertiary': 0.5,        # Calles colectoras
    'residential': 0.35,    # Pasajes y calles con lomos de toro
    'unclassified': 0.4
}

# ==========================================
# Tarifas de Peaje Específicas (Autopista Central)
# Basado en el campo 'ref' de tu GeoJSON
# ==========================================
GANTRY_PRICES_AUTOPISTA_CENTRAL = {
    # Autopista central
    "PA2": 1170.18,
    "PA3": 1755.28,
    "PA5": 571.58,
    "PA6": 924.92,
    "PA7": 904.14,
    "PA8": 669.27,
    "PA9": 1170.18,
    "PA10": 462.46,
    "PA11": 425.04,
    "PA12": 181.86,
    "PA13": 368.93,
    "PA14": 285.79,
    "PA15": 392.83,
    "PA16": 452.06,
    "PA17": 334.63,
    "PA18": 585.09,
    "PA30": 868.37,
    "PA31": 1755.28,
    "PA32": 1003.90,
    "PA37": 1106.79,
}

GANTRY_PRICES_COSTANERA = {
    "P1": 535.00,
    "P2.1": 364.87,
    "P2.2": 239.68,
    "P3": 715.83,
    "P4": 413.02,
    "P5": 306.02,
    "P6.1": 264.29,
    "P6.2": 425.86,
    "P7": 449.40,
    "P8.0": 149.80,
    "P8.1": 149.80,
    "P8.2": 149.80,
    "P8.3": 149.80,
    "P9": 239.68
}

GANTRY_PRICES_VESPUCIO_NORTE = {
    "P1": 120.59,
    "P2": 211.03,
    "P3": 351.71,
    "P4": 452.20,
    "P5": 452.20,
    "P6": 653.18,
    "P7": 104.51,
    "P8": 653.18,
    "P9": 548.67,
    "P10": 301.47,
    "P11": 301.47,
    "P12": 69.34,
    "P13": 412.00,
    "P14": 483.35,
    "P15": 140.68,
    "P16": 482.35,
    "P17": 391.91
}

GANTRY_PRICES_VESPUCIO_SUR = {
    "1.3": 1065.18,
    "2.2": 502.45,
    "3.4": 241.17,
    "3.2": 944.60,
    "4.3": 90.44,
    "4.2": 532.59,
    "5.4": 765.73,
    "6.2": 580.38,

    "5.1": 2431.18,
    "5.3": 1103.37,
    "4.1": 623.03,
    "3.1": 665.24,
    "3.3": 520.53,
    "2.1": 502.45,
    "1.1": 1065.18
}

ALL_GANTRY_DATA = {
    # Autopista Central
    **{k: {"price": v, "highway_name": "Autopista Central"} for k, v in GANTRY_PRICES_AUTOPISTA_CENTRAL.items()},
    # Costanera Norte
    **{k: {"price": v, "highway_name": "Costanera Norte"} for k, v in GANTRY_PRICES_COSTANERA.items()},
    # Vespucio Norte
    **{k: {"price": v, "highway_name": "Vespucio Norte"} for k, v in GANTRY_PRICES_VESPUCIO_NORTE.items()},
    # Vespucio Sur
    **{k: {"price": v, "highway_name": "Vespucio Sur"} for k, v in GANTRY_PRICES_VESPUCIO_SUR.items()},
}

# Fallbacks si el ID no existe o es otra autopista
TOLL_COSTS_DEFAULT = {
    'motorway': 1450.0,      # Valor genérico para Troncales
    'motorway_link': 750.0,  # Valor genérico para Salidas
    'default': 500.0         # Otros peajes
}