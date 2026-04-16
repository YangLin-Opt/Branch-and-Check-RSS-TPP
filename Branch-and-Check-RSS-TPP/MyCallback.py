# -*-coding:utf-8 -*-

from Cuts import *
import ctools
from SPG import SPG
from dataCliques import *


def callback(model, where):
    if where == GRB.Callback.MIPSOL:
        model._call_flag = True
        print('-------MIPSOL here-------')
        x = model.cbGetSolution(model._vars[0])
        chain, unit, flag, var_l, var_d = ctools.get_chains(x, nodes_sets, arc_params, mile_params, day_params)

        if flag == 'days':
            start = chain[0]
            end = chain[-1]
            if end[-1] in MD.set_sink:
                days = MD.nodes['Day'][end[-1]] - MD.unit_node_max_day[unit, end[-1]] - 1
                add_sink_day_cut(model, unit, days, end)
                model._cut_vars[0]['maintenance'][0] += 1
            else:
                days = MD.units['Max_D'][unit] - MD.unit_init_day[unit]
                add_source_day_cut(model, start, unit, days)
                model._cut_vars[0]['maintenance'][0] += 1

        elif flag == 'miles':
            As = {a for a in chain if MD.arc_length[a] > 1}
            days = list(range(int(MD.nodes['Day'][chain[0][0]]), int(MD.nodes['Day'][chain[-1][-1]])))
            Am = set()
            for _ in days[1:]:
                Am = Am | (MD.day_arcs[_, _] & MD.maintenance_arcs)
            add_mile_cut(model, As, Am, unit)
            model._cut_vars[0]['maintenance'][1] += 1

        else:
            station_day_connections = ctools.get_station_day_connections(x, MD.set_station, MD.set_days[1:], MD.set_arv,
                                                                         MD.set_dpt, MD.node_station, MD.node_day,
                                                                         MD.station_connections, MD.day_connections,
                                                                         MD.set_unit_D | MD.set_unit_D2 | MD.set_unit_G | MD.set_unit_G2)
            for key, value in station_day_connections.items():
                if value:
                    arc_cliques = get_cliques(value)
                    arc_clique = max(arc_cliques, key=len)
                    if len(arc_clique) > MD.station_track[key[0]]:  # infeasible cut
                        add_clique_cut(model, MD.set_unit_D | MD.set_unit_D2 | MD.set_unit_G | MD.set_unit_G2,
                                       arc_clique, key[0])
                        model._cut_vars[0]['feasibility'] += 1
                    else:
                        all_connections = cn[key[0], key[1]]
                        if all_connections:
                            new_value = {(_, __): 1 if (_, __) in value else 0 for (_, __) in all_connections}
                            spg = SPG(key, new_value, all_connections)
                            pi, z = spg.dual_value()
                            obj = spg.obj_value()
                            add_optimal_lazy(model, key, pi, z, obj)
                            model._cut_vars[0]['optimality'][0] += 1
                            if abs(obj - round(obj)) > 0.1:
                                add_integer_optimal_cut(model, key, new_value, obj)
                                model._cut_vars[0]['optimality'][1] += 1

