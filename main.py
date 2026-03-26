from graph_service import load_graph
from route_service import generate_route_from_coords
from metrics_service import route_length, route_time
from cost_service import route_cost
from plot_service import plot_custom_route, plot_graph_only


def main():
    G = load_graph()

    # plot_graph_only(G)

    # gran avenida av central
    home_lat = -33.568327
    home_lon = -70.686342

    # Av vitacura padre hurtado norte
    metro_lat = -33.383657
    metro_lon = -70.551090

    route = generate_route_from_coords(
        G,
        home_lat, home_lon,
        metro_lat, metro_lon
    )

    if not route:
        print("No se pudo generar ruta")
        return

    print("\n--- MÉTRICAS ---")

    distance = route_length(G, route)
    time = route_time(G, route)
    cost = route_cost(G, route)

    print("Distancia (m):", round(distance, 2))
    print("Tiempo (s):", round(time, 2))
    print("Costo:", cost)

    plot_custom_route(G, route)


if __name__ == "__main__":
    main()