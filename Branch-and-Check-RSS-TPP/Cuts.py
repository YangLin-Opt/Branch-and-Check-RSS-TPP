# -*-coding:utf-8 -*-

from gurobipy import *
from MyData import *


def add_sink_day_cut(model, unit, days, end):
    model.cbLazy(quicksum(
        [model._vars[0][_, __, unit] for day in range(int(days), max(MD.day_i_nodes.keys())) for _ in
         (MD.day_i_nodes[day] & MD.set_maintain) for __ in
         MD.node_i_suc[_] if (_, __, unit) in model._vars[0].keys()]) >= model._vars[0][end[0], end[-1], unit])

def add_source_day_cut(model, start, unit, days):
    model.cbLazy(quicksum(
        [model._vars[0][_, __, unit] for day in range(0, days) for _ in (MD.day_i_nodes[day] & MD.set_maintain)
         for __ in MD.node_i_suc[_] if (_, __, unit) in model._vars[0].keys()]) >= quicksum(
        [model._vars[0][start[0], suc, unit] for suc in MD.node_i_suc[start[0]] if
         (start[0], suc, unit) in model._vars[0].keys()]))

def add_mile_cut(model, As, Am, unit):
    model.cbLazy(quicksum([model._vars[0][_, __, unit] for (_, __) in As]) - quicksum(
        [model._vars[0][_, __, unit] for (_, __) in Am]) - len(As) + 1 <= 0)

def add_clique_cut(model, units, clique, station):
    model.cbLazy(quicksum(
        [model._vars[0][_, __, u] for (_, __) in clique for u in units if (_, __, u) in model._vars[0].keys()]) <=
                 MD.station_track[station])


def add_optimal_lazy(model, key, pi, z, obj):
    model.cbLazy(model._vars[1][key] >= obj + quicksum([pi[_, __] * (quicksum(
        [model._vars[0][_, __, u] for u in MD.set_unit_D | MD.set_unit_D2 | MD.set_unit_G | MD.set_unit_G2
         if (_, __, u) in model._vars[0].keys()]) - z[_, __]) for (_, __) in pi.keys()]))

def add_integer_optimal_cut(model, key, new_value, obj):
    model.cbLazy(model._vars[1][key] >= obj + GRB.INFINITY * (quicksum(
        [model._vars[0][_, __, u] for (_, __) in new_value.keys() for u in
         MD.set_unit_D | MD.set_unit_D2 | MD.set_unit_G | MD.set_unit_G2
         if (_, __, u) in model._vars[0].keys()]) - len(new_value)))


