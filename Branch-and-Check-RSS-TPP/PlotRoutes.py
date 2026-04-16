# -*- coding: UTF-8 -*-

import matplotlib.pyplot as plt
from random import choice, sample

plt.rcParams['font.family'] = 'Times New Roman'

class Route(object):
    def __init__(self, _route, _data, _y):
        self.R = _route
        self.D = _data
        self.assignment = {key[0]: key[-1] for key in _y.keys()}

        self.assignment.update({key[1]: key[-1] for key in _y.keys()})

        self.max_time = 4420
        self.y_track = {}
        self.marker = ['o', 's', 'D', 'x']

        self.fig, self.ax = plt.subplots()
        self.run()

    def track_y(self):
        y = 0
        index = 0
        for _ in range(len(self.D.station_track)):
            for __ in range(self.D.station_track[_]):
                self.y_track[index] = y
                y += 0.2
                index += 1
            y += 1
        print(self.y_track)

    def plot_station(self):
        for i in self.y_track.values():
            star_point = (0, self.max_time)
            end_point = (i, i)
            plt.plot(star_point, end_point, color='black', linewidth=0.3)

    def plot_line(self):
        samp = sample(self.R.keys(), len(self.R.keys()))
        for key, value in self.R.items():
            if key in samp:
                x = []
                y = []
                for start, end in value:
                    atr = self.D.nodes['Attr'][start]
                    st = self.D.nodes['Station'][start]
                    if atr == 'ns':
                        y.append(self.y_track[min(self.D.station_p[st])] - 0.3)
                        x.append(self.D.node_time[start] + 200)
                    elif atr == 'mt':
                        y.append(self.y_track[min(self.D.station_p[st])] - 0.3)
                        x.append(self.D.node_time[start] + 100)
                    elif atr == 'sc':
                        y.append(self.y_track[min(self.D.station_p[st])] - 0.3)
                        x.append(self.D.node_time[start])
                    else:
                        y.append(self.y_track[self.assignment[start]])
                        x.append(self.D.node_time[start])
                x.append(self.D.node_time[value[-1][-1]])
                y.append(self.y_track[min(self.D.station_p[self.D.node_station[value[-1][-1]]])] - 0.3)
                plt.plot(x, y, marker=choice(self.marker), markersize=10, markerfacecolor='none')

    def plot_nodes(self):
        for _ in self.D.set_nodes:
            atr = self.D.nodes['Attr'][_]
            st = self.D.nodes['Station'][_]
            y = self.y_track[min(self.D.station_p[st])]
            if atr == 'ns':
                x = self.D.nodes['Time'][_] + 200
                plt.scatter(x, y - 0.3, marker='*', color='grey')
            elif atr == 'mt':
                x = self.D.nodes['Time'][_] + 100
                plt.scatter(x, y - 0.3, marker='^', color='grey')
            elif atr == 'sc':
                x = self.D.nodes['Time'][_]
                if self.D.nodes['Max_mile'][_] == 0:
                    plt.scatter(x, y - 0.3, marker='o', color='grey')
                else:
                    plt.scatter(x, y - 0.3, marker='o', color='black')
            elif atr == 'sk':
                x = self.D.nodes['Time'][_]
                if self.D.nodes['Max_mile'][_] == 7200:
                    plt.scatter(x, y - 0.3, marker='o', color='grey')
                else:
                    plt.scatter(x, y - 0.3, marker='o', color='black')
            else:
                x = self.D.nodes['Time'][_]
                y = self.y_track[self.D.nodes['Track'][_]]
                if _ in self.D.addition_nodes:
                    c = 'red'
                    s = 30
                elif _ in self.D.delete_nodes:
                    c = 'Blue'
                    s = 30
                else:
                    c = 'black'
                    s = 10
                plt.scatter(x, y, color=c, s=s)

    def run(self):
        self.track_y()
        self.plot_station()

        self.plot_line()
        self.plot_nodes()
        x = []
        x_name = []
        for _ in self.D.set_days:
            if 0 <= _ <= 3:
                x.append(1440 * (_ + 1) + 100)
                x.append(1440 * (_ + 1) + 200)
                x_name.append(f'M{_}')
                x_name.append(f'N{_}')

        plt.xticks(x, labels=x_name)
        print(self.assignment)
        plt.yticks([self.y_track[min(self.D.station_p[_])] for _ in range(len(self.D.set_station))],
                   labels=[f'station {_}' for _ in range(len(self.D.set_station))])
        plt.grid(linestyle="-", alpha=0.6, axis='x')
        plt.show()
