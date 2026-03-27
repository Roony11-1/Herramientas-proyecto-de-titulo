from graph_service import load_graph
from route_service import generate_route_with_details
from plot_service import plot_multiple_routes

def print_metrics(name, route_data):
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
    
    gantries = route_data.get("gantries_detected", [])
    if gantries:
        print(f"Pórticos: {len(gantries)} cruzados")
        highways = set([g['highway'] for g in gantries])
        print(f"Autopistas: {', '.join(highways)}")
        
def generate_3_point_route(G, lat1, lon1, lat2, lon2, lat3, lon3, **kwargs):
    res1 = generate_route_with_details(G, lat1, lon1, lat2, lon2, **kwargs)
    
    res2 = generate_route_with_details(G, lat2, lon2, lat3, lon3, **kwargs)
    
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
    
    all_gantries = res1.get("gantries_detected", []) + res2.get("gantries_detected", [])

    return {
        "success": True,
        "type": kwargs.get("weight_type", "balanced"),
        "path": full_path,
        "summary": combined_summary,
        "gantries_detected": all_gantries
    }

def main():
    G = load_graph()

    puntos_a = {
        "orig": (-33.610153, -70.554998), 
        "dest": (-33.357953, -70.747694)
    }

    print("\n" + "="*50)

    # --- GENERACIÓN DE ESCENARIOS ---

    # A. EQUILIBRADA: El algoritmo decide el mejor mix Tiempo/Dinero
    res_balanced = generate_route_with_details(
        G, *puntos_a["orig"], *puntos_a["dest"], 
        weight_type="balanced"
    )

    # B. SÚPER AHORRO: Bloqueo total de TAG (Obliga a ir por calles locales)
    autopistas_tag = ["Autopista Central", "Costanera Norte", "Vespucio Norte", "Vespucio Sur"]
    res_cheap = generate_route_with_details(
        G, *puntos_a["orig"], *puntos_a["dest"], 
        exclude_highways=autopistas_tag,
        weight_type="cost"
    )

    # C. PRIORIDAD TIEMPO: No importa el costo, solo llegar rápido
    res_fast = generate_route_with_details(
        G, *puntos_a["orig"], *puntos_a["dest"], 
        weight_type="time"
    )

    # D. DISTANCIA CORTA: Mínimos metros (Callejeo puro)
    res_shortest = generate_route_with_details(
        G, *puntos_a["orig"], *puntos_a["dest"], 
        weight_type="length"
    )

    # --- PROCESAMIENTO Y RESUMEN ---

    rutas_para_comparar = [
        ("Ruta Equilibrada (Sugerida)", res_balanced),
        ("Ruta Súper Ahorro (Sin TAG)", res_cheap),
        ("Ruta Ejecutiva (Solo Tiempo)", res_fast),
        ("Ruta Distancia Corta (Metros)", res_shortest)
    ]

    print("\n" + "*"*40)
    print("      RESUMEN COMPARATIVO FINAL")
    print("*"*40)
    
    for nombre, res in rutas_para_comparar:
        if res and res.get("success"):
            print_metrics(nombre, res)
        else:
            print(f"--- {nombre} ---")
            print(f"Error: {res.get('error', 'Desconocido')}\n")

    # --- VISUALIZACIÓN ---

    valid_paths = [r["path"] for n, r in rutas_para_comparar if r and r.get("success")]
    valid_names = [n for n, r in rutas_para_comparar if r and r.get("success")]

    if valid_paths:
        print("\n[SISTEMA] Generando visualización de capas en mapa...")
        plot_multiple_routes(G, valid_paths, valid_names)
    else:
        print("\n[ERROR] No hay rutas válidas para graficar. Revisa los puntos de origen/destino.")

if __name__ == "__main__":
    main()