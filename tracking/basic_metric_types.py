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

    def __init__(self):
        self.counts = dict()
        self.experiments = dict()


    def get_value(self, raw_data):
        return raw_data

    @abstractmethod
    def get_graph_props(self):
        pass

    def handle_metric_event(self, metric_data):
        data = self.get_value(metric_data)
        if data in self.counts:
            self.counts[data] += 1
        else:
            self.counts[data] = 1

    def has_graph(self):
        return True

    def end_experiment(self, title):
        if not self.counts:
            self.experiments[title] = None


        sorted_items = sorted(self.counts.items())
        x_values, y_values = zip(*sorted_items)  # Unpacking sorted keys and counts

        self.experiments[title] = (x_values,y_values)

    def generate_subplot(self,ax):
        """Plots the edge count occurrences as a bar chart."""

        for title in self.experiments:
            (x,y) = self.experiments[title]
            ax.bar(x, y, edgecolor='black', label=title, alpha=0.5)

        set_graph_props(ax, self.get_graph_props())
        ax.legend()

        # ax.grid(axis='y', linestyle='--', alpha=0.7)


class ChangeOverTimeTracker(AbstractMetricTracker, ABC):

    def __init__(self):
        self.time_series = []
        self.experiments = dict()

    @abstractmethod
    def get_graph_props(self):
        pass

    def handle_metric_event(self, metric_data):
        self.time_series.append(metric_data)

    def has_graph(self):
        return True

    def end_experiment(self, title):
        if not self.time_series:
            self.experiments[title] = None


        x_values =  np.arange(len(self.time_series))
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
