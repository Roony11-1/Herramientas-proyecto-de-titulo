import os
import osmnx as ox
import networkx as nx
import random

# Nombre del archivo cache
FILE = "santiago.graphml"

def get_graph():
    # Si el archivo existe, cargar desde disco
    if os.path.exists(FILE):
        print("Cargando grafo desde archivo...")
        G = ox.load_graphml(FILE)
    else:
        print("Descargando grafo desde OpenStreetMap...")
        G = ox.graph_from_place(
            "Santiago, Chile",
            network_type="drive",
            custom_filter='["highway"~"motorway|trunk|primary|secundary"]'
        )

        print("Guardando grafo en cache...")
        ox.save_graphml(G, FILE)

    return G

def generateRandomRoute(nodes):
    # Elegir nodos aleatorios del grafo
    orig_node = random.choice(nodes)
    dest_node = random.choice(nodes)

    print("Origen:", orig_node)
    print("Destino:", dest_node)

    # Calcular ruta más corta (por distancia)
    route = nx.shortest_path(G, orig_node, dest_node, weight="length")

    print("Ruta encontrada con", len(route), "nodos")

    # Visualizar ruta
    
    return route
    
def isOnTheRoute(node, route):
    """
    Checks if a given node ID is part of the calculated route list.
    """
    return node in route


if __name__ == "__main__":
    G = get_graph()
    
    nodes = list(G.nodes)

    # Debug
    viewGraph = False # Hace lo mismo lo dejo de legacy
    viewRoute = True
    
    route = generateRandomRoute(nodes)

    print(G)
    print("Nodos:", len(G.nodes))
    print("Edges:", len(G.edges))

    if viewGraph:
        ox.plot_graph(G)

    if viewRoute:
        ox.plot_graph_route(G, route)
        
    # Obtenemos un nodo al azar
    
        