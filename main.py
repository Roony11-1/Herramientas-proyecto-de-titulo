from graph_service import load_graph
from route_service import generate_route_from_coords
from metrics_service import route_length, route_time
from cost_service import route_cost
from plot_service import plot_multiple_routes

def print_metrics(G, name, route):
    if not route:
        print(f"\n--- {name.upper()} ---")
        print("No se encontró ruta.")
        return

    print(f"\n--- {name.upper()} ---")
    distance = route_length(G, route)
    time = route_time(G, route)
    cost = route_cost(G, route)

    print(f"Distancia: {round(distance / 1000, 2)} km")
    print(f"Tiempo: {round(time / 60, 2)} min")
    print(f"Costo Peajes: ${int(cost)}")

def main():
    # 1. Carga o descarga del grafo
    G = load_graph()

    # 2. Coordenadas de prueba (Maipú a Vitacura)
    home_lat, home_lon = -33.467000, -70.758000  # Entrada Maipú (Pajaritos)
    metro_lat, metro_lon = -33.378000, -70.573000  # Vitacura (Lo Curro / Santa María)

    # 3. Generación de las 4 rutas con sus pesos específicos
    # Corta (Distancia)
    route_short = generate_route_from_coords(G, home_lat, home_lon, metro_lat, metro_lon, weight="length")
    # Rápida (Tiempo/Velocidad)
    route_fast = generate_route_from_coords(G, home_lat, home_lon, metro_lat, metro_lon, weight="time")
    # Barata (Solo peajes monetarios)
    route_cheap = generate_route_from_coords(G, home_lat, home_lon, metro_lat, metro_lon, weight="cost")
    # Equilibrada (Dinero + Valor del tiempo)
    route_balanced = generate_route_from_coords(G, home_lat, home_lon, metro_lat, metro_lon, weight="balanced")

    # 4. Mostrar métricas en consola
    print("\n=== MÉTRICAS DE RUTAS EN SANTIAGO ===")
    rutas_obj = [
        ("Corta", route_short),
        ("Rápida", route_fast),
        ("Barata", route_cheap),
        ("Equilibrada", route_balanced)
    ]

    for nombre, r in rutas_obj:
        print_metrics(G, nombre, r)

    # 5. Visualización Dinámica
    # Filtramos las rutas para que el plot no falle si alguna es None
    valid_routes = [r for name, r in rutas_obj if r is not None]
    valid_names = [name for name, r in rutas_obj if r is not None]

    if valid_routes:
        print("\n[PLOT] Generando mapa comparativo...")
        plot_multiple_routes(G, valid_routes, valid_names)
    else:
        print("\n[ERROR] No hay rutas válidas para mostrar en el mapa.")

if __name__ == "__main__":
    main()