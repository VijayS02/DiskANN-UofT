from abc import ABC, abstractmethod

import numpy as np

from tracking.lib.abstract_trackers import AbstractMetricTracker


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
    """
    Tracks the frequency distribution of a metric over multiple experiments.

    The `FrequencyTracker` class stores data points related to a specific metric and allows visualization
    of their frequency distribution across multiple experiments. It supports histogram-based visualization
    using Matplotlib and ensures consistent binning across experiments.

    Attributes:
        counts (List[float]): A list storing the frequency data points for the current experiment.
        experiments (Dict[str, List[float]]): A dictionary storing frequency data for multiple experiments,
            where keys are experiment titles and values are lists of data points.
        bins (int): Number of bins to use when plotting histograms.
    """
    def __init__(self, metric: str, bins=100, text=False):
        super().__init__(metric, graph=True, text=text)
        self.counts = []
        self.experiments = dict()
        self.bins = bins


    @abstractmethod
    def get_graph_props(self):
        pass

    def add_data_point(self, data):
        self.counts.append(data)

    def end_experiment_graph(self, title):
        if len(self.counts) == 0:
            self.experiments[title] = None

        self.experiments[title] = self.counts
        self.counts = []

    def end_experiment(self, title):
        self.end_experiment_graph(title)

    def generate_subplot(self,ax):
        """Plots the edge count occurrences as a bar chart."""
        min_value = 999999999999999999999999
        max_value = -999999999999999999999999

        for title in self.experiments:
            min_value = min(min_value, min(self.experiments[title]))
            max_value = max(max_value, max(self.experiments[title]))

        # print(min_value, max_value)
        if self.bins is not None:
            bins = np.linspace(min_value, max_value, self.bins)
        else:
            bins = max(max_value - min_value, 1)

        for title in self.experiments:
            data = self.experiments[title]
            ax.hist(data, bins=bins, edgecolor='black', label=title, alpha=0.5)

        set_graph_props(ax, self.get_graph_props())
        ax.legend()


class ChangeOverTimeTracker(AbstractMetricTracker, ABC):
    """
    Tracks how a metric changes over time across multiple experiments.

    The `ChangeOverTimeTracker` class records time-series data for a given metric, supporting
    both cumulative and averaged tracking. It allows visualization of trends by plotting
    changes over time using Matplotlib.

    Attributes:
        time_series (List[float]): A list storing time-based metric values for the current experiment.
        experiments (Dict[str, Tuple[np.ndarray, List[float]]]): A dictionary storing time-series data
            for multiple experiments, where keys are experiment titles, and values are tuples
            containing x-values (time indices) and y-values (metric values).
        average (bool): If `True`, the tracker stores counts and computes the average value
            for each time step.
        counts (List[int]): A list tracking the number of data points contributing to each time step
            (used only when `average=True`).
    """
    def __init__(self, metric: str, average=False, text=False):
        super().__init__(metric, graph=True, text=text)
        self.time_series = []
        self.experiments = dict()
        self.average = average
        self.counts = []

    @abstractmethod
    def get_graph_props(self):
        pass

    def print_text_output(self):
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
