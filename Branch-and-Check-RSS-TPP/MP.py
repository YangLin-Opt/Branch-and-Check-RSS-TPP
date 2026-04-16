# -*-coding:utf-8 -*-

from gurobipy import *
from MyCallback import callback
import ctools
from PlotRoutes import Route
from SPG import SPG
from dataCliques import *


class MP(object):
    def __init__(self):
        self._x = {}
        self._q = None
        self._m = {}
        self._cuts = {'maintenance': [0, 0], 'feasibility': 0, 'optimality': [0, 0]}
        self.max_value = 10000
        self.MD = MyData()
        self.model = Model()
        self.run()

    def variables_rsp(self):
        for key in self.MD.arcs:
            _, __ = key
            for ___ in self.MD.arc_units[_, __]:
                self._x[_, __, ___] = self.model.addVar(vtype=GRB.BINARY, lb=0, ub=1, name=f'x[{_},{__},{___}]')
        self._q = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=GRB.INFINITY, column=None, obj=1,
                                    name=f'q')
        for _ in self.MD.station_track.keys():
            for __ in self.MD.set_days[1:]:
                self._m[_, __] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=GRB.INFINITY, column=None, obj=1,
                                                   name=f'm[{_},{__}]')

        for _, __, ___ in MD.initial_arc_unit: # warm-start strategy
            self._x[_, __, ___].start = 1

    def constraints_rsp(self):
        # constraints (1b)
        for s in self.MD.station_i_nodes.keys():
            if self.MD.station_i_nodes[s] & self.MD.set_source:
                sc = (self.MD.station_i_nodes[s] & self.MD.set_source).pop()
                self.model.addConstrs(
                    (quicksum([self._x[sc, n, u] for n in self.MD.node_i_suc[sc] if (sc, n, u) in self._x.keys()]) ==
                     1 for u in self.MD.source_units[sc]),
                    name=f'constraint_source[{sc}]')

        # constraints (1c)-(1d)
        self.model.addConstrs(
            (quicksum([self._x[n, n1, u] for n1 in self.MD.node_i_suc[n] for u in self.MD.arc_units[n, n1]]) == 1 for n
             in self.MD.set_dpt),
            name='constraints_trip')

        # constraints (1e)
        for _ in self.MD.addition_pairs:
            self.model.addConstr(
                (quicksum([self._x[s, e, u] for (s, e) in _ for u in (self.MD.arc_units[s, e] - {0})]) <= 1))

        # constraints (1f)
        self.model.addConstrs(
            (quicksum([self._x[n, n1, u] for n1 in self.MD.node_i_suc[n] if (n, n1, u) in self._x.keys()]) == quicksum(
                [self._x[n2, n, u] for n2 in self.MD.node_i_pre[n] if (n2, n, u) in self._x.keys()]) for n in
             self.MD.set_arv | self.MD.set_dpt | self.MD.set_maintain | self.MD.set_stays for u in
             self.MD.set_unit_D | self.MD.set_unit_D2 | self.MD.set_unit_G | self.MD.set_unit_G2),
            name='constraint_balance')

        # constraints (13)
        self.model.addConstrs(
            (quicksum([self._x[n, n1, u] for n1 in self.MD.node_i_suc[n] if (n, n1, u) in self._x.keys()]) <= 1 for n in
             self.MD.set_stays for u in
             self.MD.set_unit_D | self.MD.set_unit_D2 | self.MD.set_unit_G | self.MD.set_unit_G2), 'deadhead_one')


        # constraints (14)
        for u in self.MD.set_unit_D | self.MD.set_unit_D2:
            if self.MD.units['Day'][u] == 1:
                self.model.addConstr((quicksum([self._x[_, __, u] for _ in self.MD.set_maintain & (
                        self.MD.day_i_nodes[0] | self.MD.day_i_nodes[1]) for __ in
                                                self.MD.node_i_suc[_]]) >= 1), name=f'maintain_days_D[{u}]')
            elif self.MD.units['Day'][u] == 2:
                self.model.addConstr((quicksum([self._x[_, __, u] for _ in self.MD.set_maintain & (
                    self.MD.day_i_nodes[0]) for __ in
                                                self.MD.node_i_suc[_]]) >= 1), name=f'maintain_days_D[{u}]')

        for u in self.MD.set_unit_G | self.MD.set_unit_G2:
            if self.MD.units['Day'][u] == 1:
                self.model.addConstr((quicksum([self._x[_, __, u] for _ in self.MD.set_maintain & (
                    self.MD.day_i_nodes[0]) for __ in
                                                self.MD.node_i_suc[_]]) >= 1), name=f'maintain_days_G[{u}]')
            elif self.MD.units['Day'][u] == 0:
                self.model.addConstr((quicksum([self._x[_, __, u] for _ in self.MD.set_maintain & (
                        self.MD.day_i_nodes[0] | self.MD.day_i_nodes[1]) for __ in
                                                self.MD.node_i_suc[_]]) >= 1), name=f'maintain_days_G[{u}]')

    def track_basic_cut(self):
        # constraints (15)
        self.model.addConstr(self._q >= quicksum(
            [MD.set_connection_cost[_, __] * self._x[_, __, u] for (_, __) in MD.set_connection_cost.keys() for u in
             self.MD.set_unit_D | self.MD.set_unit_D2 | self.MD.set_unit_G | self.MD.set_unit_G2 if
             (_, __, u) in self._x.keys()]),
                             name='track')

        # q >= sum(q_sd)
        self.model.addConstr(
            self._q >= quicksum([self._m[_, __] for _ in self.MD.station_track.keys() for __ in self.MD.set_days[1:]]),
            name='total')


    def iis(self):
        self.model.computeIIS()
        self.model.write("model.ilp")

    def objectives(self):
        obj = 0
        for arc in self.MD.arcs:
            _, __ = arc
            for ___ in self.MD.arc_units[_, __]:
                obj += self._x[_, __, ___] * self.MD.arc_costs[_, __][___]
        self.model.setObjective(obj + self.MD.weight_q * self._q, GRB.MINIMIZE)

    def print_objectives(self):
        obj1 = 0
        for arc in self.MD.arcs:
            _, __ = arc
            if _ in self.MD.set_dpt:
                for ___ in self.MD.arc_units[_, __]:
                    obj1 += self._x[_, __, ___].x * self.MD.arc_costs[_, __][___]
        print('obj1:', obj1)

        obj2 = self.MD.weight_q * self._q.x
        print('obj2:', obj2)

    def print_components(self, chain):
        num_trips, num_f_trips, num_u_all, num_u_3, num_tc = 0, 0, 0, 0, 0
        num_flex_trips = len(MD.delete_trains)
        print('num_flex_trips:', num_flex_trips)
        tu_types = ['D', 'D2', 'G', 'G2']
        tu_sets = [self.MD.set_unit_D, self.MD.set_unit_D2, self.MD.set_unit_G, self.MD.set_unit_G2]
        tu_dict = dict(zip(tu_types, tu_sets))
        for unit, path in chain.items():
            no_use_flag = True
            no_use_flag_day3 = True
            for start, end in path:
                if start in self.MD.set_dpt and end in self.MD.set_arv:
                    num_trips += 1
                    if MD.file_trains['Type'][start] == 0:
                        num_f_trips += 1
                    tu_type = self.MD.nodes['Unit'][start]
                    if unit not in tu_dict[tu_type]:
                        num_tc += 1
                    no_use_flag = False
                    if start in self.MD.day_i_nodes[2]:
                        no_use_flag_day3 = False
            if no_use_flag:
                num_u_all += 1
            if no_use_flag_day3:
                num_u_3 += 1
        num_all_trips = MD.file_trains.shape[0] - round(0.5 * len(MD.addition_trains))

        print('num_c-trips,num_cf-trips, num_u_all, num_u_3, num_tc', num_all_trips - num_trips,
              len(MD.delete_trains) - num_f_trips, num_u_all, num_u_3, num_tc)

    def print_data(self):
        status = self.model.status
        if status == GRB.Status.UNBOUNDED:
            print('The model cannot be solved because it is unbounded')
            exit(0)
        if status == GRB.Status.OPTIMAL or status == GRB.TIME_LIMIT:
            x = {key: value.x for key, value in self._x.items()}
            q = self._q.x
            m = {key: value.x for key, value in self._m.items()}
            chain, unit, flag, var_l, var_d = ctools.get_chains(x, nodes_sets, arc_params, mile_params, day_params)
            print('Optimal solution:')
            station_day_connections = ctools.get_station_day_connections(x, MD.set_station, MD.set_days[1:],
                                                                         MD.set_arv,
                                                                         MD.set_dpt, MD.node_station, MD.node_day,
                                                                         MD.station_connections, MD.day_connections,
                                                                         MD.set_unit_D | MD.set_unit_D2 | MD.set_unit_G | MD.set_unit_G2)
            print('station_day_connections', station_day_connections)
            y = {}
            obj_v_sp = 0
            in_fea_station = []
            for key, value in station_day_connections.items():
                if value:
                    arc_cliques = get_cliques(value)
                    arc_clique = max(arc_cliques, key=len)
                    if len(arc_clique) > MD.station_track[key[0]]:  # infeasible cut
                        in_fea_station.append(key)
                        print(key, value, 'clique bad')
                    else:
                        all_connections = cn[key[0], key[1]]
                        new_value = {(_, __): 1 if (_, __) in value else 0 for (_, __) in all_connections}
                        # print(key)
                        # print(arc_cliques)
                        spg = SPG(key, new_value, all_connections)
                        # print(spg.get_cliques())
                        v = spg.value_y()
                        # print(v)
                        y.update(v)
                        obj_v_sp += spg.obj_value()

            print('obj_v_sp', obj_v_sp)
            print('in_fea_station', in_fea_station)
            self.print_components(chain)
            try:
                Route(chain, self.MD, y)
                keys = list(chain.keys())
                keys.sort()
            except:
                print(chain, unit, flag)
            self.print_objectives()
            print(self._cuts)

    def run(self):
        self.variables_rsp()
        self.constraints_rsp()
        self.track_basic_cut()
        self.objectives()
        # self.iis()
        self.model._vars = [self._x, self._m, self._q]
        self.model._cut_vars = [self._cuts]
        self.model._call_flag = True
        self.model.Params.Method = 1
        self.model.Params.NodeMethod = 1
        self.model.Params.Threads = 4
        self.model.Params.timeLimit = 3600
        # self.model.setParam(GRB.Param.LogFile, 'mp.log')
        self.model.Params.lazyConstraints = 1
        self.model.optimize(callback)
        self.print_data()


if __name__ == '__main__':
    MP()
