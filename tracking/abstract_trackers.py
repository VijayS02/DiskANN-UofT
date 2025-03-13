from abc import abstractclassmethod, abstractmethod

from matplotlib.axes import Axes


class AbstractMetricTracker:
    def __init__(self, metric: str):
        self.metric = metric

    def get_metric_name(self) -> str:
        return self.metric

    @abstractmethod
    def handle_metric_event(self, metric_data):
        pass

    @abstractmethod
    def has_graph(self):
        pass

    @abstractmethod
    def generate_subplot(self,ax: Axes):
        pass

    @abstractmethod
    def has_text_output(self):
        pass

    @abstractmethod
    def print_text_output(self):
        pass

    @abstractmethod
    def end_experiment(self, title):
        pass

class AbstractQueryTracker(AbstractMetricTracker):

    def __init__(self, metric="NONE"):
        super().__init__(metric=metric)
        self.experiment_info = dict()

    def configure_experiment_stats(self, data):
        self.experiment_info = data

    @abstractmethod
    def end_query(self, data):
        pass


class AbstractConstructionTracker(AbstractMetricTracker):
    @abstractmethod
    def initialize_construction(self, construction_params):
        pass

