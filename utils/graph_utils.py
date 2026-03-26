import networkx as nx


def get_edge(G: nx.MultiDiGraph, u: int, v: int):
    data = G.get_edge_data(u, v)

    if data:
        return data[min(data.keys())]

    # fallback
    data = G.get_edge_data(v, u)
    if data:
        return data[min(data.keys())]

    return None