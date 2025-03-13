from abc import abstractclassmethod, abstractmethod


class AbstractMetricTracker:
    @abstractmethod
    def get_metric_name(self) -> str:
        pass

    @abstractmethod
    def handle_metric_event(self, metric_data):
        pass

    @abstractmethod
    def plot_resulting_data(self):
        pass


class AbstractQueryTracker(AbstractMetricTracker):
    @abstractmethod
    def initialize_query(self, search_params):
        pass

    @abstractmethod
    def handle_query_end(self):
        pass

    @abstractmethod
    def handle_query_begin(self):
        pass


class AbstractConstructionTracker(AbstractMetricTracker):
    @abstractmethod
    def initialize_construction(self, construction_params):
        pass

