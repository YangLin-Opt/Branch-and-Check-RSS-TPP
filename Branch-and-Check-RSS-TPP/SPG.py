# -*- coding: UTF-8 -*-

from tools import split_var
from gurobipy import *
from dataCliques import *

class SPG(object):
    def __init__(self, key, value, all_connections):
        self.real_connections = value
        self.station, self.day = key
        self.all_connections = all_connections
        self.x = value
        self.cliques = cl[key[0], key[1]]
        self.P = MD.station_p[self.station]
        self.model = Model()
        self._y = {}
        self._z = {}
        self.run()

    def get_cliques(self):
        return self.cliques

    def variables(self):
        for (_, __) in self.all_connections:
            for p in self.P:
                self._y[_, __, p] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f'p[{_},{__},{p}]')
            self._z[_, __] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f'z[{_},{__}]')

    def constraints(self):
        self.model.addConstrs(
            (quicksum([self._y[_, __, p] for p in self.P]) == self._z[_, __] for (_, __) in self.all_connections),
            name='lamd')

        for clique in self.cliques:
            self.model.addConstrs(
                (quicksum([self._y[_, __, p] for (_, __) in clique]) <= 1 for p
                 in self.P), name=f'mu[{self.cliques.index(clique)}]')

        self.model.addConstrs((self._z[_, __] == self.x[_, __] for (_, __) in self.all_connections), name='pi')

    def objectives(self):
        obj = quicksum(
            [(MD.node_track_cost[_, p] + MD.node_track_cost[__, p]) * (self._y[_, __, p]) for (_, __) in
             self.all_connections for p in self.P])

        self.model.setObjective(obj, GRB.MINIMIZE)

    def dual_value(self):
        pi = {}
        for con in self.model.getConstrs():
            if 'pi' in con.ConstrName:
                var_name, key = split_var(con.ConstrName)
                pi[key[0], key[1]] = con.Pi
        z = {key: value.x for key, value in self._z.items()}
        return pi, z

    def value_y(self):
        y = {key: 1 for key, value in self._y.items() if value.x >= 0.9}
        return y

    def obj_value(self):
        return self.model.objVal

    def run(self):
        print(f'model start {self.station},{self.day}')
        self.variables()
        self.constraints()
        self.objectives()
        self.model.Params.OutputFlag = 0
        self.model.optimize()
        print('model end')
