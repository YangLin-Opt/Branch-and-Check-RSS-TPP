from MyData import *
from Clique import get_cliques


def clique_station_day():
    connections_s_d = {}
    cliques_s_d = {}
    for s in MD.set_station:
        for d in MD.set_days[1:]:
            connections_s_d[s, d] = MD.station_connections[s] & MD.day_connections[d]
            if MD.station_connections[s] & MD.day_connections[d]:
                cliques_s_d[s, d] = get_cliques(list(MD.station_connections[s] & MD.day_connections[d]))
            else:
                cliques_s_d[s, d] = []
    return connections_s_d, cliques_s_d


cn, cl = clique_station_day()
