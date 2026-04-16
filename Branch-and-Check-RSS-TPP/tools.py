# -*- coding: utf-8 -*-

import re
import ctools

def split_var(x):
    a = r'(.*?)\['
    var_name = re.findall(a, x)[0]
    a1 = r'\[(.*?)]'
    find_str = re.findall(a1, x)
    x = find_str[0].split(',')
    key = [int(_) for _ in x]
    return var_name, key


def get_chains(connection, chains):
    print(connection)
    print(chains)
    while connection:
        for __ in chains:
            for _ in connection:
                if _[0] == __[-1]:
                    __.append(_[-1])
                    connection.remove(_)
                    break
    return chains


def track_assignment(_x, _md, SPG):
    y = {}
    for st in _md.set_station:
        for day in _md.set_days[1:]:
            key = (st, day)
            all_connections = _md.station_connections[st] & _md.day_connections[day]
            if all_connections:
                value = {
                    (_, __): max([_x[_, __, u] for u in _md.set_unit_1 | _md.set_unit_2 if (_, __, u) in _x.keys()])
                    for (_, __) in all_connections}
                print(f'station {st} day {day}:', value)
                spg = SPG(key, value, all_connections)
                variable = spg.value_y()
                print(f'station {st} day {day}:', variable)
                y.update(variable)

    return y
