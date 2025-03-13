from abc import ABC, abstractmethod

from tracking.abstract_trackers import AbstractMetricTracker


class FrequencyTracker(AbstractMetricTracker, ABC):

    def __init__(self):
        self.counts = dict()

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

    def generate_subplot(self,ax):
        """Plots the edge count occurrences as a bar chart."""
        if not self.counts:
            ax.text(0.5, 0.5, "No Data", fontsize=12, ha='center', va='center')
            return

            # Sort data by keys (edge count values)
        sorted_items = sorted(self.counts.items())
        x_values, y_values = zip(*sorted_items)  # Unpacking sorted keys and counts

        ax.bar(x_values, y_values, color='skyblue', edgecolor='black')

        labels = self.get_graph_props()
        ax.set_xlabel(labels['x'])
        ax.set_ylabel(labels['y'])
        ax.set_title(labels['title'])

        ax.grid(axis='y', linestyle='--', alpha=0.7)
