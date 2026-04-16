# -*-coding:utf-8 -*-

import networkx as nx


class Graph(object):
    def __init__(self, vertexes, edges):
        self.graph = nx.Graph()
        self.graph.add_nodes_from(vertexes)
        self.graph.add_edges_from(edges)

    @property
    def max_clique(self):
        cliques = list(nx.algorithms.clique.find_cliques(self.graph))
        return cliques
