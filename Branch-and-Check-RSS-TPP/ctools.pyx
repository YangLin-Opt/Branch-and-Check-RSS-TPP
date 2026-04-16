def get_chains(var, nodes_sets, arc_params, mile_params, day_params):
    cdef dict var_x = dict(var)
    cdef set sources, stays, maintains, sinks
    cdef dict arc_length, arc_day_dif
    cdef dict unit_init_mile, unit_node_min_mile, unit_node_max_mile
    cdef dict unit_init_day, unit_node_min_day, unit_node_max_day
    cdef dict connections, chains

    sources, stays, maintains, sinks = nodes_sets
    arc_length, arc_day_dif = arc_params
    unit_init_mile, unit_node_min_mile, unit_node_max_mile = mile_params
    unit_init_day, unit_node_min_day, unit_node_max_day = day_params

    connections, chains, var_l, var_d = get_connections(var_x, sources, maintains, arc_length, arc_day_dif,
                                                        unit_init_mile,
                                                        unit_init_day)
    chain, unit, flag = check_chains(chains, connections, var_l, var_d, maintains, sinks, arc_length,
                                     arc_day_dif, unit_init_mile, unit_init_day, unit_node_max_mile, unit_node_max_day)

    return chain, unit, flag, var_l, var_d

cdef get_connections(dict var_x, set source, set maintains, dict arc_length, dict arc_day_diff, dict unit_init_mile,
                     dict unit_init_day):
    cdef tuple key
    cdef dict var_l = {}, var_d = {}, chains = {}, connections = {_: [] for _ in unit_init_day.keys()}
    cdef float value
    cdef int start, end, unit
    for key, value in var_x.items():
        start, end, unit = key
        if value >= 0.95 and unit != 0:
            if start in source:
                chains[unit] = [(start, end)]
                var_l[start, unit] = unit_init_mile[unit]
                var_d[start, unit] = unit_init_day[unit]
                if end in maintains:
                    var_l[end, unit] = 0
                    var_d[end, unit] = -1
                else:
                    var_l[end, unit] = var_l[start, unit] + arc_length[start, end]
                    var_d[end, unit] = var_d[start, unit] + arc_day_diff[start, end]
            else:
                connections[unit].append((start, end))
    return connections, chains, var_l, var_d

cdef check_chains(dict chains, dict connections, dict var_l, dict var_d, set maintains, set sinks, dict arc_length,
                  dict arc_day_dif, dict unit_init_mile, dict unit_init_day, dict unit_node_max_mile,
                  dict unit_node_max_day):
    cdef tuple rear, _
    cdef list chain, connection
    cdef int unit, last, start, end, __
    for unit, chain in chains.items():
        connection = connections[unit]
        rear = chain[-1]
        last = rear[-1]
        index_1 = 0
        index_2 = 1
        # print('initial connection set:', connection)
        while connection:
            for _ in connection:
                start, end = _
                if start == last:
                    chain.append((start, end))
                    last = end
                    connection.remove(_)
                    index_2 += 1
                    if end in maintains:
                        index_1 = index_2
                        var_l[end, unit] = 0
                        var_d[end, unit] = -1
                    else:
                        var_l[end, unit] = var_l[start, unit] + arc_length[start, end]
                        var_d[end, unit] = var_d[start, unit] + arc_day_dif[start, end]
                        if var_d[end, unit] > unit_node_max_day[unit, end]:
                            return [chain[index_1:index_2], unit, 'days']
                        if var_l[end, unit] > unit_node_max_mile[unit, end]:
                            return [chain[index_1:index_2], unit, 'miles']
            if chain[-1][-1] in sinks:
                break
    return [chains, 'all', 'right']

cpdef get_station_day_connections(_x, list stations, list days, set set_arv, set set_dpt, dict node_station,
                                  dict node_day, dict station_connections, dict day_connections, set set_units):
    cdef dict station_day_connections = {}, x = dict(_x)
    cdef int st, day, _, __, u

    for st in stations:
        for day in days:
            station_day_connections[st, day] = [(_, __) for (_, __) in station_connections[st] & day_connections[day]
                                                if
                                                sum([x[_, __, u] for u in set_units if (_, __, u) in x.keys()]) >= 0.99]
    return station_day_connections

cpdef get_vertexes_edges(list s, dict node_time, node):
    cdef int n_nodes = len(s), start_1, end_1, start_2, end_2, _, __
    cdef tuple connection_1, connection_2
    cdef list vertexes = [], edges = []
    cdef set arv, dpt, stays, maintains, sc, sk
    arv, dpt, stays, maintains, sc, sk = node
    for _ in range(len(s) - 1):
        vertexes.append(_)
        for __ in range(_ + 1, len(s)):
            connection_1 = s[_]
            connection_2 = s[__]
            start_1, end_1 = connection_1
            start_2, end_2 = connection_2

            if start_1 in stays | sc and end_1 in dpt:
                start_time_1 = node_time[end_1] - 10
                end_time_1 = node_time[end_1]
            elif start_1 in arv and end_1 in sk | stays | sk | maintains:
                start_time_1 = node_time[start_1]
                end_time_1 = node_time[start_1] + 10
            else:
                start_time_1 = node_time[start_1]
                end_time_1 = node_time[end_1]

            if start_2 in stays | sc and end_2 in dpt:
                start_time_2 = node_time[end_2] - 10
                end_time_2 = node_time[end_2]
            elif start_2 in arv and end_2 in sk | stays | sk | maintains:
                start_time_2 = node_time[start_2]
                end_time_2 = node_time[start_2] + 10
            else:
                start_time_2 = node_time[start_2]
                end_time_2 = node_time[end_2]

            if start_time_2 < start_time_1 < end_time_2 or start_time_1 < start_time_2 < end_time_1:
                edges.append((_, __))
    vertexes.append(n_nodes - 1)
    return vertexes, edges

cpdef points_to_arcs(list clique, list s):
    cdef list arc_clique = []
    cdef int _
    for _ in clique:
        arc_clique.append(s[_])
    return arc_clique

cpdef x_station_connections(x, list stations, list days, set set_arv, set set_dpt, dict node_station,
                            dict node_day):
    cdef dict connections = dict(x)
    cdef tuple key
    cdef float value
    cdef int start, end, station_start, station_end, day_start, day_end, unit
    cdef dict station_connections = {(_, __): [] for _ in stations for __ in days[1:]}

    for key, value in connections.items():
        if value >= 0.5:
            start, end, unit = key
            if start in set_arv and end in set_dpt:
                station_start = node_station[start]
                station_end = node_station[end]
                day_start = node_day[start]
                day_end = node_day[end]
                if station_start == station_end and day_start == day_end:
                    station_connections[station_start, day_start].append((start, end))
    return station_connections
