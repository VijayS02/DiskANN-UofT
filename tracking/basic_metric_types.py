from abc import ABC, abstractmethod

from tracking.abstract_trackers import AbstractMetricTracker


class FrequencyTracker(AbstractMetricTracker, ABC):

    def __init__(self):
        self.counts = dict()
        self.experiments = dict()

    @abstractmethod
    def get_graph_props(self):
        pass

    def handle_metric_event(self, metric_data):
        if metric_data in self.counts:
            self.counts[metric_data] += 1
        else:
            self.counts[metric_data] = 1

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

        ax.legend()
        labels = self.get_graph_props()
        ax.set_xlabel(labels['x'])
        ax.set_ylabel(labels['y'])
        ax.set_title(labels['title'])

        ax.grid(axis='y', linestyle='--', alpha=0.7)
