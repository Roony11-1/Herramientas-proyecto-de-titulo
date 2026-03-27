import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
from typing import List

# --- ESTILOS GLOBALES ---
BG_COLOR = "black"
STREET_COLOR = "#F0F0F0"  # Blanco humo sutil
TOLL_COLOR = "#FFFF00"    # Amarillo Neón
STREET_WIDTH = 0.4
TOLL_WIDTH = 3.5          # Grosor masivo para que el TAG se note

def plot_graph_only(G: nx.MultiDiGraph) -> None:
    """Visualización básica del esqueleto urbano."""
    ox.plot_graph(
        G,
        node_size=0,
        edge_color=STREET_COLOR,
        edge_linewidth=STREET_WIDTH,
        bgcolor=BG_COLOR
    )

def plot_custom_route(G: nx.MultiDiGraph, route: List[int]) -> None:
    """Visualización de una ruta única con resalte de peajes."""
    route_edges = set(zip(route[:-1], route[1:]))
    edge_colors, edge_widths = [], []

    for u, v, k, data in G.edges(keys=True, data=True):
        # 1. Base: Calle blanca sutil
        color = STREET_COLOR
        width = STREET_WIDTH

        # 2. Resaltar Autopistas (Opcional, naranja sutil)
        highway = data.get("highway", "")
        if isinstance(highway, list): highway = highway[0]
        if highway == "motorway":
            color = "#FFA500" 
            width = 0.8
            
        # 3. TAGs (Prioridad visual media)
        if data.get("toll"):
            color = TOLL_COLOR
            width = TOLL_WIDTH

        # 4. RUTA (Prioridad máxima)
        if (u, v) in route_edges:
            color = "#FF0000" # Rojo brillante para la ruta única
            width = 2.5

        edge_colors.append(color)
        edge_widths.append(width)

    ox.plot_graph(
        G, edge_color=edge_colors, edge_linewidth=edge_widths,
        node_size=0, bgcolor=BG_COLOR
    )

def plot_multiple_routes(G, routes: List[List[int]], names: List[str] = None) -> None:
    """Comparativa de múltiples rutas con leyenda y tags destacados."""
    if names is None:
        names = [f"Ruta {i+1}" for i in range(len(routes))]
    
    # Colores eléctricos para las rutas
    # Paleta expandida de 10 colores de alto contraste para fondo negro
    # 1. Verde Neón, 2. Magenta, 3. Cian, 4. Naranja Eléctrico, 5. Azul Real, 
    # 6. Rojo Brillante, 7. Lima, 8. Violeta, 9. Turquesa, 10. Rosa Coral
    route_colors = [
        '#00FF00', '#FF00FF', '#00FFFF', '#FF4500', '#1E90FF', 
        '#FF0000', '#C0FF00', '#8A2BE2', '#40E0D0', '#FF6F61'
    ]
    route_edge_sets = [set(zip(r[:-1], r[1:])) if r else set() for r in routes]

    edge_colors, edge_widths = [], []

    for u, v, k, data in G.edges(keys=True, data=True):
        # 1. Base
        color = STREET_COLOR
        width = STREET_WIDTH
        
        # 2. PÓRTICOS (Se dibujan con el ancho máximo para que "brillen" bajo la ruta)
        if data.get("toll"):
            color = TOLL_COLOR
            width = TOLL_WIDTH
            
        # 3. RUTAS (Se superponen)
        for i in range(len(route_edge_sets)-1, -1, -1):
            if (u, v) in route_edge_sets[i]:
                color = route_colors[i % len(route_colors)]
                width = 2.2
                break

        edge_colors.append(color)
        edge_widths.append(width)

    fig, ax = ox.plot_graph(
        G, edge_color=edge_colors, edge_linewidth=edge_widths,
        node_size=0, bgcolor=BG_COLOR, show=False, close=False
    )

    # --- LEYENDA PRO ---
    custom_lines = [Line2D([0], [0], color=route_colors[i % len(route_colors)], lw=3) for i in range(len(routes))]
    custom_lines.append(Line2D([0], [0], color=TOLL_COLOR, lw=5))
    
    legend_labels = names + ["Pórtico TAG (Peaje)"]
    leg = ax.legend(custom_lines, legend_labels, loc='upper right', prop={'size': 9, 'weight': 'bold'})
    
    leg.get_frame().set_facecolor('#111111')
    leg.get_frame().set_edgecolor('white')
    for text in leg.get_texts(): text.set_color("white")

    plt.title("COMPARATIVA DE RUTAS Y COBRO DE PEAJES", color="white", fontsize=12, pad=10)
    plt.show()