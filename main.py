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
        
def generate_3_point_route(G, lat1, lon1, lat2, lon2, lat3, lon3, **kwargs):
    """
    Calcula la ruta pasando por un punto intermedio (A -> B -> C)
    y devuelve un objeto con la misma estructura que generate_route_with_details.
    """
    
    # Tramo 1: Origen al Punto de Paso (A -> B)
    res1 = generate_route_with_details(G, lat1, lon1, lat2, lon2, **kwargs)
    
    # Tramo 2: Punto de Paso al Destino (B -> C)
    res2 = generate_route_with_details(G, lat2, lon2, lat3, lon3, **kwargs)
    
    # Si cualquiera de los dos tramos falla, la ruta completa falla
    if not res1["success"]:
        return {"success": False, "error": f"Tramo 1 falló: {res1.get('error')}"}
    if not res2["success"]:
        return {"success": False, "error": f"Tramo 2 falló: {res2.get('error')}"}

    # --- UNIÓN DE CAMINOS ---
    # El último nodo de path1 es el mismo que el primero de path2.
    # Usamos [1:] para no duplicar el nodo intermedio en la lista.
    full_path = res1["path"] + res2["path"][1:]
    
    # --- UNIÓN DE MÉTRICAS (SUMA DE SUMMARIES) ---
    s1 = res1["summary"]
    s2 = res2["summary"]
    
    combined_summary = {
        "total_toll_cost": round(s1["total_toll_cost"] + s2["total_toll_cost"], 2),
        "total_time_minutes": round(s1["total_time_minutes"] + s2["total_time_minutes"], 1),
        "total_distance_km": round(s1["total_distance_km"] + s2["total_distance_km"], 2),
        # Llaves críticas para compatibilidad total con print_metrics y cálculos internos:
        "total_time_seconds": round(s1["total_time_seconds"] + s2["total_time_seconds"], 2),
        "total_distance_meters": round(s1["total_distance_meters"] + s2["total_distance_meters"], 2)
    }
    
    # --- UNIÓN DE PÓRTICOS ---
    # Combinamos ambas listas de pórticos detectados
    all_gantries = res1.get("gantries_detected", []) + res2.get("gantries_detected", [])

    return {
        "success": True,
        "type": kwargs.get("weight_type", "balanced"),
        "path": full_path,
        "summary": combined_summary,
        "gantries_detected": all_gantries
    }

def main():
    # 1. Carga del grafo
    G = load_graph()

    # --- CONFIGURACIÓN DE PUNTOS ---
    # Origen: Maipú (Sector Pajaritos)
    lat_orig, lon_orig = -33.4820, -70.7620
    # Este punto está ANTES del nudo con Costanera Norte
    lat_mid, lon_mid = -33.4615, -70.6625
    # Destino: Vitacura (Parque Bicentenario)
    lat_dest, lon_dest = -33.3980, -70.5900

    print("\n=== CALCULANDO ESCENARIOS DE RUTA EN SANTIAGO ===")

    # ESCENARIO A: Equilibrada (Directa)
    res_balanced = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        weight_type="balanced"
    )

    # ESCENARIO B: Súper Ahorro (Sin TAG)
    autopistas_tag = ["Autopista Central", "Costanera Norte", "Vespucio Norte", "Vespucio Sur"]
    res_cheap = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        exclude_highways=autopistas_tag,
        weight_type="cost"
    )

    # ESCENARIO C: Evitando solo Autopista Central
    res_no_central = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        exclude_highways=["Autopista Central"],
        weight_type="balanced"
    )

    # ESCENARIO D: Distancia Corta (Solo metros)
    res_shortest = generate_route_with_details(
        G, lat_orig, lon_orig, lat_dest, lon_dest, 
        weight_type="length"
    )

    # NUEVO ESCENARIO E: Ruta Forzada (3 Puntos: Maipú -> Central/Costanera -> Vitacura)
    # Este escenario garantiza que pase por el nudo de autopistas para probar los cobros
    res_forced = generate_3_point_route(
        G, 
        lat_orig, lon_orig,   # Punto 1
        lat_mid, lon_mid,     # Punto 2 (Paso)
        lat_dest, lon_dest,   # Punto 3
        weight_type="balanced"
    )

    # 3. Lista para procesar y graficar
    rutas_para_comparar = [
        ("Equilibrada (Sugerida)", res_balanced),
        ("Súper Ahorro (Sin TAG)", res_cheap),
        ("Evitando A. Central", res_no_central),
        ("Distancia Corta", res_shortest),
        ("Forzada (Central + Costanera)", res_forced) # <--- Nueva ruta en la comparativa
    ]

    # 4. Mostrar métricas en consola
    print("\n" + "="*40)
    print("      RESUMEN COMPARATIVO DE RUTAS")
    print("="*40)
    
    for nombre, res in rutas_para_comparar:
        print_metrics(nombre, res)

    # 5. Visualización en el Mapa
    valid_paths = [r["path"] for n, r in rutas_para_comparar if r and r.get("success")]
    valid_names = [n for n, r in rutas_para_comparar if r and r.get("success")]

    if valid_paths:
        print("\n[SISTEMA] Abriendo mapa comparativo...")
        # El plot mostrará todas las rutas y los pórticos en amarillo neón
        plot_multiple_routes(G, valid_paths, valid_names)
    else:
        print("\n[ERROR] No se pudo generar ninguna ruta válida para graficar.")

if __name__ == "__main__":
    main()