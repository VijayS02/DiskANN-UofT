from abc import ABC, abstractmethod

import numpy as np

from tracking.abstract_trackers import AbstractMetricTracker


def set_graph_props(ax, graph_props):
    """Set graph properties dynamically, including log scales if specified."""
    ax.set(
        xlabel=graph_props.get('x', 'X'),
        ylabel=graph_props.get('y', 'Y'),
        title=graph_props.get('title', '<>')
    )

    # Apply logarithmic scaling if requested
    if graph_props.get('xlog', False):
        ax.set_xscale('log')
    if graph_props.get('ylog', False):
        ax.set_yscale('log')



class FrequencyTracker(AbstractMetricTracker, ABC):

    def __init__(self, metric: str, bins=100):
        super().__init__(metric)
        self.counts = []
        self.experiments = dict()
        self.bins = bins


    @abstractmethod
    def get_graph_props(self):
        pass

    def add_data_point(self, data):
        self.counts.append(data)

    def has_graph(self):
        return True

    def end_experiment(self, title):
        if len(self.counts) == 0:
            self.experiments[title] = None

        self.experiments[title] = self.counts
        self.counts = []

    def generate_subplot(self,ax):
        """Plots the edge count occurrences as a bar chart."""
        min_value = 999999999999999999999999
        max_value = -999999999999999999999999

        for title in self.experiments:
            min_value = min(min_value, min(self.experiments[title]))
            max_value = max(max_value, max(self.experiments[title]))

        # print(min_value, max_value)
        bins = np.linspace(min_value, max_value, self.bins)

        for title in self.experiments:
            data = self.experiments[title]
            ax.hist(data, bins=bins, edgecolor='black', label=title, alpha=0.5)

        set_graph_props(ax, self.get_graph_props())
        ax.legend()


class ChangeOverTimeTracker(AbstractMetricTracker, ABC):

    def __init__(self, metric: str, average=False):
        super().__init__(metric)
        self.time_series = []
        self.experiments = dict()
        self.average = average
        self.counts = []

    @abstractmethod
    def get_graph_props(self):
        pass

    def add_data_point(self, metric_data, i=-1):
        if i == -1:
            self.time_series.append(metric_data)
            if self.average:
                self.counts.append(1)
        elif i >= len(self.time_series):
            self.time_series.append(metric_data)
            if self.average:
                self.counts.append(1)
        else:
            self.time_series[i] = self.time_series[i] + metric_data
            if self.average:
                self.counts[i] += 1

    def has_graph(self):
        return True

    def end_experiment(self, title):
        if not self.time_series:
            self.experiments[title] = None

        x_values =  np.arange(len(self.time_series))

        if self.average:
            y_values = [self.time_series[i] / self.counts[i] if self.counts[i] != 0 else 0
                        for i in range(len(self.time_series))]
        else:
             y_values = self.time_series

        print(len(self.time_series))
        self.experiments[title] = (x_values,y_values)

        self.time_series = []

    def generate_subplot(self,ax):
        """Plots the edge count occurrences as a bar chart."""

        for title in self.experiments:
            (x,y) = self.experiments[title]
            ax.plot(x, y, label=title, alpha=0.5)


        set_graph_props(ax, self.get_graph_props())
        ax.legend()


        # ax.grid(axis='y', linestyle='--', alpha=0.7)
