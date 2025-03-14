from abc import abstractclassmethod, abstractmethod

from matplotlib.axes import Axes


class AbstractMetricTracker:
    def __init__(self, metric: str):
        self.metric = metric

    def get_metric_name(self) -> str:
        return self.metric

    @abstractmethod
    def handle_metric_event(self, metric_data):
        """
        Handle the data when this metric's event fires. This should update any internal state in accordance with the
        data provided in the metric_data.

        :param metric_data: Metric_data is exactly the data provided as the second argument to `MetricTracker::Track`.
        """
        pass

    @abstractmethod
    def has_graph(self) -> bool:
        """
        Return whether this metric tracker generates a graph using generate_subplot or not.
        :return: Boolean - does this metric have a graph?
        """
        pass

    @abstractmethod
    def generate_subplot(self,ax: Axes):
        """
        Given an axis, plot the relevant data across multiple experiments related to this metric.
        :param ax: Matplotlib Axes to plot data onto.
        """
        pass

    @abstractmethod
    def has_text_output(self):
        """
        Unused. 
        """
        pass

    @abstractmethod
    def print_text_output(self):
        """
        Unused. 
        """
        pass

    @abstractmethod
    def end_experiment(self, title):
        """
        Event notifying this metric that the current experiment has ended. 
        :param title: Title of the experiment that has just ended.
        """
        pass

class AbstractQueryTracker(AbstractMetricTracker):

    def __init__(self, metric="NONE"):
        super().__init__(metric=metric)
        self.experiment_info = dict()

    def configure_experiment_stats(self, data):
        self.experiment_info = data

    @abstractmethod
    def end_query(self, data):
        """
        Event notifying this metric that the current query has ended. 
        :param data: Data relating to the query - fired by the end_query event.
        """
        pass


class AbstractConstructionTracker(AbstractMetricTracker):
    @abstractmethod
    def initialize_construction(self, construction_params):
        """
        Event notifying this metric that construction has begun. 
        :param construction_params: Params relevant to construction passed by the construction_start event.
        """
        pass

