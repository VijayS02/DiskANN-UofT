import time
from abc import abstractmethod
from typing import List, Dict

import numpy as np
import zmq
import json
from lib.abstract_trackers import AbstractConstructionTracker, AbstractMetricTracker, AbstractQueryTracker
import threading

import matplotlib.pyplot as plt


class AbstractTrackingRunner:

    def __init__(self, port=5555, metric_handlers: List[AbstractMetricTracker] = None):
        self.tracking_thread = None
        self.port = port
        self.metric_handlers : Dict[str, List[AbstractMetricTracker]] = dict()
        self.stop_tracking = False
        for metric_handler in metric_handlers:
            self.metric_handlers.setdefault(metric_handler.get_metric_name(), []).append(metric_handler)


    @abstractmethod
    def handle_metric_event(self, data):
        pass


    def iterate_trackers(self):
        for metric in self.metric_handlers:
            tracker_list = self.metric_handlers[metric]
            for tracker in tracker_list:
                yield tracker, metric


    def generate_text(self):
        text_trackers = [tracker for tracker, _ in self.iterate_trackers() if tracker.has_text_output()]

        for tracker in text_trackers:
            tracker.print_text_output()

    def generate_graphs(self):
        valid_trackers = [tracker for tracker, _ in self.iterate_trackers() if tracker.has_graph()]
        if not valid_trackers:
            print("No graphs to generate.")
            return

        num_trackers = len(valid_trackers)



        # Compute the closest square layout (rows x cols)
        ncols = int(np.ceil(np.sqrt(num_trackers)))  # Columns should be sqrt of count
        nrows = int(np.ceil(num_trackers / ncols))  # Compute rows to fit all plots

        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))

        # Flatten axes array for easier iteration (handles cases where ncols > 1)
        axes = np.array(axes).reshape(-1)  # Reshape in case of single row or column

        for ax, tracker in zip(axes, valid_trackers):
            tracker.generate_subplot(ax)

        # Hide unused subplots if any
        for ax in axes[num_trackers:]:
            ax.axis("off")

        plt.tight_layout()
        plt.show()

    def end_experiment(self, title):
        for (tracker, metric) in self.iterate_trackers():
            tracker.end_experiment(title)

    def start_tracking_server(self, port=5556):
        """Start a ZMQ server in a separate thread to collect metrics"""
        self.stop_tracking = False

        def tracker_thread():
            context = zmq.Context()
            socket = context.socket(zmq.PULL)
            socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout for clean shutdown
            socket.setsockopt(zmq.LINGER, 0)

            try:
                socket.bind(f"tcp://*:{port}")
                print(f"Listening for metrics on port {port}...")

                while not self.stop_tracking:
                    try:
                        msg = socket.recv_string()
                        data = json.loads(msg)
                        self.handle_metric_event(data)
                    except zmq.Again:
                        # Timeout occurred, just continue
                        pass
                    except json.JSONDecodeError:
                        print("Invalid JSON format received, skipping...")

            except zmq.error.ZMQError as e:
                print(f"Error in ZMQ server: {e}")
            finally:
                socket.close()
                context.term()
                print("Tracking server stopped")

        self.tracking_thread = threading.Thread(target=tracker_thread)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()

    def stop_tracking_server(self):
        """Stop the ZMQ tracking server thread"""
        if self.tracking_thread:
            self.stop_tracking = True
            self.tracking_thread.join(timeout=5)
            self.tracking_thread = None


    def trace_program(self, title:str, trace_function, tracking_port=5555):
        """Build index, search index and track metrics via ZMQ"""
        try:
            # Start tracking server first
            self.start_tracking_server(port=tracking_port)

            return_v = trace_function()

            # Give time for any final messages to be received
            time.sleep(1)

        finally:
            # Stop the tracking server
            self.stop_tracking_server()

        self.end_experiment(title)

        return return_v


class ConstructionTrackingRunner(AbstractTrackingRunner):
    def __init__(self, port=5556, metric_handlers: List[AbstractConstructionTracker]=None):
        super().__init__(port=port, metric_handlers=metric_handlers)

    def handle_metric_event(self, data):
        metric_name = data["metric_name"]

        if metric_name == "construction_start":
            for (tracker,metric) in self.iterate_trackers():
                tracker.initialize_construction(data['value'])
        else:
            if metric_name in self.metric_handlers:
                for tracker in self.metric_handlers[metric_name]:
                    tracker.handle_metric_event(data['value'])

class QueryTrackerRunner(AbstractTrackingRunner):
    def __init__(self, port=5556, metric_handlers: List[AbstractQueryTracker]=None):
        self.experiment_stats = dict()
        self.completed_queries = 0
        super().__init__(port=port, metric_handlers=metric_handlers)

    def handle_metric_event(self, data):
        metric_name = data["metric_name"]
        # print(data)

        if metric_name == "end_query":
            self.completed_queries += 1
            # if self.completed_queries / self.experiment_stats['queries']:
            for (tracker, metric) in self.iterate_trackers():
                tracker.end_query(data['value'])
        elif metric_name == "configure_experiment":
            self.completed_queries = 0
            self.experiment_stats = data['value']
            for (tracker, metric) in self.iterate_trackers():
                tracker.configure_experiment_stats(data['value'])
        else:
            if metric_name in self.metric_handlers:
                for tracker in self.metric_handlers[metric_name]:
                    tracker.handle_metric_event(data['value'])


