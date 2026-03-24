from graph_service import load_graph
from route_service import (
    generate_route_from_coords,
    route_length,
    route_time,
    route_cost
)
from plot_service import plot_custom_route

def main():
    G = load_graph()

    # blanco encalada hipodromo
    home_lat = -33.457208
    home_lon = -70.664937

    # independencia hipodromo chile
    metro_lat = -33.407140
    metro_lon = -70.660949

    route = generate_route_from_coords(
        G,
        home_lat, home_lon,
        metro_lat, metro_lon
    )

    if not route:
        print("No se pudo generar ruta")
        return

    print("\n--- MÉTRICAS ---")
    print("Distancia (m):", round(route_length(G, route), 2))
    print("Tiempo (s):", round(route_time(G, route), 2))
    print("Costo:", route_cost(G, route))

    plot_custom_route(G, route)
    


if __name__ == "__main__":
    main()