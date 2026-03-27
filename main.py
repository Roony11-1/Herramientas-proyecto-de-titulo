from graph_service import load_graph
from route_service import generate_route_with_details
from plot_service import plot_multiple_routes

def print_metrics(name, route_data):
    """Muestra los resultados de forma legible en consola."""
    if not route_data or not route_data.get("success"):
        print(f"\n--- {name.upper()} ---")
        error_msg = route_data.get('error', 'No se encontró ruta.') if route_data else 'Sin respuesta'
        print(f"Estado: Error ({error_msg})")
        return

    summary = route_data["summary"]
    print(f"\n--- {name.upper()} ---")
    print(f"Distancia: {summary.get('total_distance_km', round(summary['total_distance_meters']/1000, 2))} km")
    print(f"Tiempo: {summary['total_time_minutes']} min")
    print(f"Costo Peajes: ${int(summary['total_toll_cost'])}")
    
    # Detalle de pórticos si existen
    gantries = route_data.get("gantries_detected", [])
    if gantries:
        print(f"Pórticos: {len(gantries)} cruzados")
        # Opcional: imprimir los nombres de las autopistas usadas
        highways = set([g['highway'] for g in gantries])
        print(f"Autopistas: {', '.join(highways)}")

def main():
    # 1. Carga del grafo con todos los pesos pre-calculados
    G = load_graph()

    # 2. Coordenadas de prueba (Maipú a Vitacura)
    # Asegúrate de usar nombres de variables consistentes
    lat_orig, lon_orig = -33.467000, -70.758000
    lat_dest, lon_dest = -33.378000, -70.573000

    print("\n=== CALCULANDO ESCENARIOS DE RUTA EN SANTIAGO ===")

    # ESCENARIO A: Equilibrada (La mejor relación Tiempo/Dinero)
    res_balanced = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        weight_type="balanced"
    )

    # ESCENARIO B: Súper Ahorro (Evitando TODAS las autopistas con TAG)
    autopistas_tag = ["Autopista Central", "Costanera Norte", "Vespucio Norte", "Vespucio Sur"]
    res_cheap = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        exclude_highways=autopistas_tag,
        weight_type="cost"
    )

    # ESCENARIO C: Evitando solo Autopista Central (Restricción específica)
    res_no_central = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        exclude_highways=["Autopista Central"],
        weight_type="balanced"
    )

    # ESCENARIO D: Distancia Corta (Ignora costos y tráfico, solo metros)
    res_shortest = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        weight_type="length"
    )

    # 3. Lista para procesar y graficar
    rutas_para_comparar = [
        ("Equilibrada (Sugerida)", res_balanced),
        ("Súper Ahorro (Sin TAG)", res_cheap),
        ("Evitando A. Central", res_no_central),
        ("Distancia Corta", res_shortest)
    ]

    # 4. Mostrar métricas en consola
    print("\n" + "="*40)
    print("      RESUMEN COMPARATIVO DE RUTAS")
    print("="*40)
    
    for nombre, res in rutas_para_comparar:
        print_metrics(nombre, res)

    # 5. Visualización en el Mapa
    # Filtramos solo las que tuvieron éxito para que el plot no explote
    valid_paths = [r["path"] for n, r in rutas_para_comparar if r and r.get("success")]
    valid_names = [n for n, r in rutas_para_comparar if r and r.get("success")]

    if valid_paths:
        print("\n[SISTEMA] Abriendo mapa comparativo...")
        plot_multiple_routes(G, valid_paths, valid_names)
    else:
        print("\n[ERROR] No se pudo generar ninguna ruta válida para graficar.")

if __name__ == "__main__":
    main()