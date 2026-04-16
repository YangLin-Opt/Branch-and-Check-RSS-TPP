# -*-coding:utf-8 -*-

import pandas as pd
import numpy as np


class MyData(object):
    def __init__(self):
        self.weight_q = 50
        self.instance_path = ".\\instances\\CD-5%-35\\"
        self.import_trains()
        self.station_track = {}
        self.station_p = {}
        self.import_tracks()
        self.nodes = None
        self.set_dpt = None
        self.set_arv = None
        self.set_stays = None
        self.set_maintain = None
        self.set_sink = None
        self.set_nodes = None
        self.node_i_pre = None
        self.node_i_suc = None
        self.units = None
        self.node_min_mile = None
        self.node_max_mile = None
        self.node_min_day = None
        self.node_max_day = None
        self.node_station = None
        self.node_day = None
        self.node_time = None
        self.node_track_cost = None
        self.unit_init_mile = {}
        self.unit_init_day = {}
        self.same_units_i = {}
        self.source_units = {}
        self.arcs = set()
        self.arc_length = {}
        self.arc_units = {}
        self.arc_costs = {}
        self.set_unit = set()
        self.set_unit_D = set()
        self.set_unit_D2 = set()
        self.set_unit_G = set()
        self.set_unit_G2 = set()
        self.station_i_nodes = {}
        self.day_i_nodes = {}
        self.arc_day_diff = {}
        self.station_connections = {_: set() for _ in self.station_track.keys()}
        self.day_connections = {_: set() for _ in range(5)}
        self.day_arcs = {}
        self.set_connection_cost = {}

        self.import_nodes()
        self.import_sets()
        self.import_pre_suc()
        self.import_station_i_nodes()
        self.import_day_i_nodes()
        self.import_units()

        self.unit_node_min_mile = {}
        self.unit_node_max_mile = {}
        self.unit_node_min_day = {}
        self.unit_node_max_day = {}
        self.unit_node_data()

        self.import_arcs()
        self.day_diff()
        self.get_units_data()
        self.set_station = list(self.station_i_nodes.keys())
        self.set_days = list(self.day_i_nodes.keys())
        self.maintain_arcs()

        self.all_connections = {}
        self.clique_s_d = {}

        self.initial_arc_unit = []
        self.import_initial_arc_unit()

    def import_trains(self):
        self.file_trains = pd.read_csv(self.instance_path + 'trains.csv')
        num_dpt_nodes = self.file_trains.shape[0]
        self.delete_trains = list(self.file_trains[self.file_trains['Type'] == 0].index)
        self.delete_nodes = self.delete_trains + [_ + num_dpt_nodes for _ in self.delete_trains]

        self.addition_trains = list(self.file_trains[self.file_trains['Type'] == 2].index)
        self.addition_nodes = self.addition_trains + [_ + num_dpt_nodes for _ in self.addition_trains]
        half_length = round(len(self.addition_trains) / 2)
        self.addition_pairs = []
        for _ in range(half_length):
            pair = [(self.addition_trains[_], self.addition_trains[_] + num_dpt_nodes),
                    (self.addition_trains[_ + half_length], self.addition_trains[_ + half_length] + num_dpt_nodes)]
            self.addition_pairs.append(pair)

    def import_tracks(self):
        file = pd.read_csv(self.instance_path + 'tracks.csv')
        index = 0
        for _ in range(file.shape[0]):
            self.station_track[file['station'][_]] = file['tracks'][_]
            self.station_p[file['station'][_]] = set(range(index, index + file['tracks'][_]))
            index += file['tracks'][_]

    def import_nodes(self):
        self.nodes = pd.read_csv(self.instance_path + 'nodes.csv')
        self.set_nodes = set(range(self.nodes.shape[0]))
        self.node_station = {_: self.nodes['Station'][_] for _ in range(self.nodes.shape[0])}
        self.node_day = {_: self.nodes['Day'][_] for _ in range(self.nodes.shape[0])}
        self.node_time = {_: self.nodes['Time'][_] for _ in range(self.nodes.shape[0])}

    def unit_node_data(self):
        for u in self.set_unit_D | self.set_unit_D2 | self.set_unit_G | self.set_unit_G2:
            for n in self.set_nodes:
                if n in self.set_source:
                    self.unit_node_min_mile[u, n] = self.units['Mile'][u]
                    self.unit_node_min_day[u, n] = self.units['Day'][u]
                    self.unit_node_max_mile[u, n] = self.units['Mile'][u]
                    self.unit_node_max_day[u, n] = self.units['Day'][u]
                elif n in self.set_maintain:
                    self.unit_node_min_mile[u, n] = 0
                    self.unit_node_min_day[u, n] = -1
                    self.unit_node_max_mile[u, n] = 0
                    self.unit_node_max_day[u, n] = -1
                elif n in self.set_sink:
                    self.unit_node_min_mile[u, n] = self.nodes['Min_mile'][n]
                    self.unit_node_min_day[u, n] = self.nodes['Min_day'][n]
                    self.unit_node_max_mile[u, n] = self.units['Max_L'][u] * (
                            self.units['Max_D'][u] - 0.25 * self.nodes['Max_mile'][n]) / self.units['Max_D'][u]
                    self.unit_node_max_day[u, n] = self.units['Max_D'][u]
                else:
                    self.unit_node_min_mile[u, n] = self.nodes['Min_mile'][n]
                    self.unit_node_min_day[u, n] = self.nodes['Min_day'][n]
                    self.unit_node_max_mile[u, n] = min(self.units['Max_L'][u], self.nodes['Max_mile'][n])
                    self.unit_node_max_day[u, n] = min(self.units['Max_D'][u], self.nodes['Max_day'][n])

    def import_sets(self):
        row = []
        file = np.array(pd.read_csv(self.instance_path + "set_nodes.csv", header=None))
        for _ in range(file.shape[0]):
            __ = set(file[_])
            __.discard(-1)
            row.append(__)
        self.set_dpt, self.set_arv, self.set_stays, self.set_maintain, self.set_source, self.set_sink = row

        self.node_track_cost = np.ones(shape=(len(self.set_nodes), sum(self.station_track.values())))
        for _ in self.set_arv | self.set_dpt:
            if _ in self.addition_nodes:
                self.node_track_cost[_] = 0
            else:
                self.node_track_cost[_, self.nodes['Track'][_]] = 0
        self.node_track_cost[len(self.set_arv | self.set_dpt):, :] = 0

    def import_pre_suc(self):
        self.node_i_pre = {_: set() for _ in self.nodes}
        self.node_i_suc = {_: set() for _ in self.nodes}
        file_pre = np.array(pd.read_csv(self.instance_path + "node_i_pre.csv", header=None))
        file_suc = np.array(pd.read_csv(self.instance_path + "node_i_suc.csv", header=None))
        for _ in range(file_pre.shape[0]):
            pre = set(file_pre[_])
            suc = set(file_suc[_])
            pre.discard(-1)
            suc.discard(-1)
            self.node_i_pre[_] = pre
            self.node_i_suc[_] = suc

    def import_units(self):
        self.units = pd.read_csv(self.instance_path + "units.csv")
        self.source_units = {_: set() for _ in self.set_source}
        for _ in range(self.units.shape[0]):
            self.set_unit.add(_)
            if self.units['Type'][_] == 'D':
                self.set_unit_D.add(_)
            elif self.units['Type'][_] == 'D2':
                self.set_unit_D2.add(_)
            elif self.units['Type'][_] == 'G':
                self.set_unit_G.add(_)
            elif self.units['Type'][_] == 'G2':
                self.set_unit_G2.add(_)

            if self.units['Station'][_] != -1:
                self.unit_init_mile[_] = self.units['Mile'][_]
                self.unit_init_day[_] = self.units['Day'][_]
                source = (self.station_i_nodes[self.units['Station'][_]] & self.set_source).pop()
                self.source_units[source].add(_)

    def import_arcs(self):
        file_length = np.array(pd.read_csv(self.instance_path + "arc_length.csv", header=None))
        file_cost = np.array(pd.read_csv(self.instance_path + "arc_cost.csv", header=None))
        file_unit = np.array(pd.read_csv(self.instance_path + "arc_unit.csv", header=None))
        self.day_arcs = {(_, __): set() for _ in set(self.nodes['Day']) for __ in set(self.nodes['Day']) if _ <= __}
        for _ in range(file_length.shape[0]):
            start, end, length = file_length[_]
            start = int(start)
            end = int(end)
            cost = file_cost[_]
            unit = set(file_unit[_])
            unit.discard(-1)
            self.arcs.add((start, end))
            self.arc_length[start, end] = length
            self.arc_costs[start, end] = cost
            self.arc_units[start, end] = unit
            self.day_arcs[self.nodes['Day'][start], self.nodes['Day'][end]].add((start, end))
            if start in self.set_arv and end in self.set_dpt:
                st = self.nodes['Station'][start]
                day = self.nodes['Day'][start]
                self.station_connections[st].add((start, end))
                self.day_connections[day].add((start, end))
                if self.nodes['Track'][start] == self.nodes['Track'][end]:
                    self.set_connection_cost[start, end] = 0
                else:
                    if start not in self.addition_nodes and end not in self.addition_nodes:
                        self.set_connection_cost[start, end] = 1
                    else:
                        self.set_connection_cost[start, end] = 0

            elif start in self.set_stays | self.set_source and end in self.set_dpt:
                st = self.nodes['Station'][end]
                day = self.nodes['Day'][end]
                self.station_connections[st].add((start, end))
                self.day_connections[day].add((start, end))
                self.set_connection_cost[start, end] = 0

            elif start in self.set_arv and end in self.set_sink | self.set_stays | self.set_sink | self.set_maintain:
                st = self.nodes['Station'][start]
                day = self.nodes['Day'][start]
                self.station_connections[st].add((start, end))
                self.day_connections[day].add((start, end))
                self.set_connection_cost[start, end] = 0

    def import_station_i_nodes(self):
        file = np.array(pd.read_csv(self.instance_path + "station_i_nodes.csv", header=None))
        for _ in range(file.shape[0]):
            nodes = set(file[_])
            nodes.discard(-1)
            self.station_i_nodes[_] = nodes

    def import_day_i_nodes(self):
        file = np.array(pd.read_csv(self.instance_path + "day_i_nodes.csv", header=None))
        for _ in range(file.shape[0]):
            nodes = set(file[_])
            nodes.discard(-1)
            self.day_i_nodes[_ - 1] = nodes

    def day_diff(self):
        self.arc_day_diff = {(_, __): self.nodes['Day'][__] - self.nodes['Day'][_] for (_, __) in self.arcs}
        for key, value in self.arc_day_diff.items():
            if key[0] in self.set_source:
                self.arc_day_diff[key] = 0

    def get_units_data(self):
        types = [self.set_unit_D, self.set_unit_D2, self.set_unit_G, self.set_unit_G2]
        sources = self.source_units.values()
        for ty in types:
            for sor in sources:
                for _ in ty & sor:
                    self.same_units_i[_] = ty & sor

    def maintain_arcs(self):
        self.maintenance_arcs = {(_, list(self.node_i_suc[_])[0]) for _ in self.set_maintain}

    def import_initial_arc_unit(self):
        file = np.array(pd.read_csv(self.instance_path + 'initial_trip_unit.csv', header=None))
        for _ in range(file.shape[0]):
            self.initial_arc_unit.append(tuple(file[_]))


np.set_printoptions(linewidth=np.inf, threshold=np.inf)
MD = MyData()
nodes_sets = [MD.set_source, MD.set_stays, MD.set_maintain, MD.set_sink]
arc_params = [MD.arc_length, MD.arc_day_diff]
mile_params = [MD.unit_init_mile, MD.unit_node_min_mile, MD.unit_node_max_mile]
day_params = [MD.unit_init_day, MD.unit_node_min_day, MD.unit_node_max_day]

