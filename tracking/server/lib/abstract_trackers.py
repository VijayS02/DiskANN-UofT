from abc import abstractmethod
from typing import List

from matplotlib.axes import Axes


class AbstractMetricTracker:
    def __init__(self, id, metrics: List[str]=[], label="Label"):
        if not metrics:
            self.metrics = [id]
        else:
            self.metrics = metrics
        self.id = id
        self.label = label

    def get_label(self):
        return self.label
    
    def get_id(self):
        return self.id
    
    def get_subscribed_metrics(self) -> List[str]:
        return self.metrics

    @abstractmethod
    def handle_metric_event(self, metric_name, metric_data):
        """
        Handle the data when this metric's event fires. This should update any internal state in accordance with the
        data provided in the metric_data.

        :param metric_data: Metric_data is exactly the data provided as the second argument to `MetricTracker::Track`.
        """
        pass


    @abstractmethod
    def end_experiment(self, title):
        """
        Event notifying this metric that the current experiment has ended. 
        :param title: Title of the experiment that has just ended.
        """
        pass

class JsonMetricTracker(AbstractMetricTracker):

    def __init__(self, json: str, *args, **kwargs):
        self.json_key = json
        super().__init__(*args, **kwargs)

    @abstractmethod
    def get_json(self):
        pass

    def get_json_key(self):
        return self.json_key

class GraphMetricTracker(AbstractMetricTracker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def generate_subplot(self, ax: Axes):
        pass


class TextMetricTracker(AbstractMetricTracker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def print_text_output(self):
        pass


class AbstractQueryTracker(AbstractMetricTracker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.experiment_info = dict()
        self.graph = None
        self.index_info = None

    def set_graph(self, graph):
        self.graph = graph

    def set_index_info(self, index_info):
        self.index_info = index_info

    def configure_experiment_stats(self, data):
        self.experiment_info = data

    @abstractmethod
    def end_query(self, data):
        """
        Event notifying this metric that the current query has ended. 
        :param data: Data relating to the query - fired by the end_query event.
        """
        pass

class IndividualQueryTracker(AbstractQueryTracker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class AbstractConstructionTracker(AbstractMetricTracker):
    @abstractmethod
    def initialize_construction(self, construction_params):
        """
        Event notifying this metric that construction has begun. 
        :param construction_params: Params relevant to construction passed by the construction_start event.
        """
        pass

