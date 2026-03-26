import osmnx as ox
import matplotlib.pyplot as plt
import networkx as nx
from typing import List

def plot_graph_only(G: nx.MultiDiGraph) -> None:
    ox.plot_graph(
        G,
        node_size=0,
        edge_color="white",
        edge_linewidth=0.5,
        bgcolor="black"
    )

def plot_custom_route(G: nx.MultiDiGraph, route: List[int]) -> None:
    route_edges = set(zip(route[:-1], route[1:]))

    edge_colors = []
    edge_widths = []

    for u, v, k, data in G.edges(keys=True, data=True):
        highway = data.get("highway")

        # normalizar (puede venir como lista)
        if isinstance(highway, list):
            highway = highway[0]

        # --- BASE ---
        color = "white"
        width = 0.5

        # --- AUTOPISTAS ---
        if highway == "motorway":
            color = "orange"
            width = 1.5
            
        # --- PEAJES ---
        if data.get("toll"):
            color = "yellow"
            width = 0.7

        # --- RUTA ---
        if (u, v) in route_edges:
            color = "red"
            width = 2

        edge_colors.append(color)
        edge_widths.append(width)

    fig, ax = ox.plot_graph(
        G,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        node_size=0,
        bgcolor="black",
        show=False,
        close=False
    )

    plt.show()
    
import osmnx as ox
import matplotlib.pyplot as plt
from typing import List

def plot_multiple_routes(G, routes: List[List[int]], names: List[str] = None) -> None:
    # 1. Definir paleta de colores dinámica
    # Si no hay nombres, usamos genéricos
    if names is None:
        names = [f"Ruta {i+1}" for i in range(len(routes))]
    
    # Colores vivos para que resalten sobre el fondo negro
    colors = ['#00FF00', '#0000FF', '#FF0000', '#FF00FF', '#00FFFF', '#FFA500']
    
    # 2. Pre-procesar las rutas como sets de aristas para búsqueda rápida O(1)
    route_edge_sets = []
    for r in routes:
        if r: # Validar que la ruta no sea None
            route_edge_sets.append(set(zip(r[:-1], r[1:])))
        else:
            route_edge_sets.append(set())

    edge_colors = []
    edge_widths = []

    # 3. Iterar sobre las aristas del grafo una sola vez
    for u, v, k, data in G.edges(keys=True, data=True):
        # Valores base (calles normales)
        color = "#CACACA" # Gris oscuro para el fondo
        width = 0.5
        
        # Resaltar peajes (opcional, fondo sutil)
        if data.get("toll"):
            color = "#444400" # Amarillo muy oscuro
            width = 0.8

        # Verificar si la arista pertenece a alguna de las rutas
        # Lo hacemos en orden inverso para que la primera ruta de la lista 
        # quede "arriba" si se solapan
        for i in range(len(route_edge_sets)-1, -1, -1):
            if (u, v) in route_edge_sets[i]:
                color = colors[i % len(colors)]
                width = 2.5 # Un poco más gruesa para que se vea bien
                break # Si ya encontramos que es de una ruta, paramos

        edge_colors.append(color)
        edge_widths.append(width)

    # 4. Dibujar el mapa
    fig, ax = ox.plot_graph(
        G,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        node_size=0,
        bgcolor="black",
        show=False,
        close=False
    )

    # 5. Añadir Leyenda Dinámica
    from matplotlib.lines import Line2D
    custom_lines = [
        Line2D([0], [0], color=colors[i % len(colors)], lw=3) 
        for i in range(len(routes))
    ]
    ax.legend(custom_lines, names, loc='upper right', prop={'size': 10}, frameon=True)

    plt.title("Comparativa de Rutas - Santiago", color="white")
    plt.show()