# -*-coding:utf-8 -*-

from Graph import Graph
from MyData import *
from ctools import get_vertexes_edges, points_to_arcs


def get_cliques(s):
    # print('A connection:', s)
    node = [MD.set_arv, MD.set_dpt, MD.set_stays, MD.set_maintain, MD.set_source, MD.set_sink]
    vertexes, edges = get_vertexes_edges(s, MD.node_time, node)
    g = Graph(vertexes, edges)
    clique = g.max_clique
    arc_cliques = []
    for _ in clique:
        arc_cliques.append(points_to_arcs(_, s))
    return arc_cliques

