import os
from queue import Queue
import time
from abc import abstractmethod
from typing import List, Dict

import numpy as np
import zmq
import json
from lib.abstract_trackers import AbstractConstructionTracker, AbstractMetricTracker, AbstractQueryTracker, GraphMetricTracker, IndividualQueryTracker, JsonGraphMetricTracker, JsonMetricTracker, TextMetricTracker
import threading
from tqdm import tqdm 
import msgpack
import zstandard as zstd
from collections import defaultdict
import pandas as pd



import matplotlib.pyplot as plt

def convert_numpy_to_python(obj):
    """Recursively convert NumPy objects to Python native types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert NumPy array to list
    elif isinstance(obj, np.integer):
        return int(obj)  # Convert NumPy int to Python int
    elif isinstance(obj, np.floating):
        return float(obj)  # Convert NumPy float to Python float
    elif isinstance(obj, np.bool_):
        return bool(obj)  # Convert NumPy bool to Python bool
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}  # Recursively process dict
    elif isinstance(obj, list):
        return [convert_numpy_to_python(v) for v in obj]  # Recursively process list
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_python(v) for v in obj)  # Recursively process tuple
    return obj  # Return the object if it doesn't need conversion
    

class AbstractTrackingRunner:

    def __init__(self, port=5555, metric_handlers: List[AbstractMetricTracker] = None):
        self.tracking_thread = None
        self.port = port
        self.metric_handlers : Dict[str, List[AbstractMetricTracker]] = dict()
        self.stop_tracking = False
        self.message_queue = Queue()
        self.grouped = defaultdict(list)
        for metric_handler in metric_handlers:
            for metric_name in metric_handler.get_subscribed_metrics():
                self.metric_handlers.setdefault(metric_name, []).append(metric_handler)


    @abstractmethod
    def handle_metric_event(self, data):
        pass


    def iterate_trackers(self):
        for metric in self.metric_handlers:
            tracker_list = self.metric_handlers[metric]
            for tracker in tracker_list:
                yield tracker, metric

    def iterate_unique_trackers(self):
        trackers = set()
        for tracker, metric in self.iterate_trackers():
            if tracker.get_id() not in trackers:
                trackers.add(tracker.get_id())
                yield tracker, tracker.get_subscribed_metrics()


    def generate_text(self):
        text_trackers = [tracker for tracker, _ in self.iterate_unique_trackers() if isinstance(tracker, TextMetricTracker)]

        for tracker in text_trackers:
            tracker.print_text_output()

    def generate_graphs(self, filename_prefix=None, single_query=False):
        valid_trackers = [tracker for tracker, _ in self.iterate_unique_trackers() if isinstance(tracker, GraphMetricTracker) and (single_query == isinstance(tracker, IndividualQueryTracker))]
        if not valid_trackers:
            print("No graphs to generate.")
            return

        num_trackers = len(valid_trackers)

        if filename_prefix:
            for tracker in valid_trackers:
                fig, ax = plt.subplots(figsize=(8, 8), dpi=600)
                tracker.generate_subplot(ax)
                filename = os.path.join(filename_prefix, f"{tracker.id}.png")
                plt.savefig(filename, dpi=300, bbox_inches="tight")  # Save each graph as its own file
                print(f"Graph saved to {filename}")
                plt.close(fig)
        else:
            # Compute the closest square layout (rows x cols)
            ncols = int(np.ceil(np.sqrt(num_trackers)))  # Columns should be sqrt of count
            nrows = int(np.ceil(num_trackers / ncols))  # Compute rows to fit all plots

            fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))
            axes = np.array(axes).reshape(-1)  # Reshape in case of single row or column

            for ax, tracker in zip(axes, valid_trackers):
                tracker.generate_subplot(ax)

            # Hide unused subplots if any
            for ax in axes[num_trackers:]:
                ax.axis("off")

            plt.tight_layout()
            plt.show()  # Display graph

    def generate_json_graphs(self, filename, single_query=False):
        json_trackers = [tracker for tracker, _ in self.iterate_unique_trackers() if isinstance(tracker, JsonGraphMetricTracker) and (single_query == isinstance(tracker, IndividualQueryTracker))]

        data = {}
        for tracker in json_trackers:
            data[tracker.get_id()] = {
                "data": tracker.get_graph_json(),
                "metadata": tracker.get_json_graph_props()
            }
        
        # Recursively convert all NumPy data before writing
        data_serializable = convert_numpy_to_python(data)

        # Write using MessagePack
        with open(filename, "wb") as f:  # Use "wb" since msgpack writes binary data
            f.write(msgpack.packb(data_serializable))

        print(f"JSON graph data written to {filename}")

    def generate_parquet(self, output_dir: str, compression: str = "zstd"):
        """Write events to separate Parquet files per metric_name."""
        os.makedirs(output_dir, exist_ok=True)

        metrics = []
        for metric, records in self.grouped.items():
            df = pd.DataFrame(records)
            metrics.append(metric)
            filename = os.path.join(output_dir, f"{metric}.parquet")
            df.to_parquet(filename, engine="pyarrow", compression=compression, index=False)
            print(f"Wrote {len(records)} records to {filename}")
        return metrics

    def end_experiment(self, title):
        for (tracker, metrics) in self.iterate_unique_trackers():
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
                        self.message_queue.put(msg)
                    except zmq.Again:
                        # Timeout occurred, just continue
                        pass
                    except json.JSONDecodeError:
                        print("Invalid JSON format received, skipping...")
                
                print("Received shutdown signal, processing metrics...")
                qid = 0
                evtId = 0
                msg_q_len = self.message_queue.qsize()
                for _ in tqdm(range(msg_q_len)):
                    event = json.loads(self.message_queue.get())
                    # self.events.append(data)
                    metric = event.get("metric_name", "unknown")
                    
                    metric_data = event.get("value", {})
                    metric_data['qid'] = qid
                    metric_data['evtId'] = evtId
                    self.grouped[metric].append(metric_data)
                    if metric == "end_query":
                        qid += 1
                    evtId += 1
                    # self.handle_metric_event(data)

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

            while not self.message_queue.empty():
                time.sleep(0.1)

            self.tracking_thread.join(timeout=5)
            self.tracking_thread = None


    def trace_program(self, title:str, trace_function, tracking_port=5555):
        """Build index, search index and track metrics via ZMQ"""
        try:
            # Start tracking server first
            self.start_tracking_server(port=tracking_port)

            return_v = trace_function()

            # Give time for any final messages to be received
            time.sleep(3)

        except Exception as e:
            print(f"Error in tracing program: {e}")
            raise e
        finally:
            # Stop the tracking server
            self.stop_tracking_server()

        self.end_experiment(title)

        return return_v
    
    def generate_json(self, single_query=False):
        json_trackers = [tracker for tracker, _ in self.iterate_unique_trackers() if isinstance(tracker, JsonMetricTracker) and (single_query == isinstance(tracker, IndividualQueryTracker))]
        data = dict()
        for tracker in json_trackers:
            data[tracker.get_json_key()] = tracker.get_json()
        return data
    
    def generate_output_dict(self, single_query=False):
        def get_type(InstanceType):
            return [tracker.get_id() for tracker, _ in self.iterate_unique_trackers() if isinstance(tracker, InstanceType) and (single_query == isinstance(tracker, IndividualQueryTracker))]
        
        return {
            "json": get_type(JsonMetricTracker),
            "text": get_type(TextMetricTracker),
            "graph": get_type(GraphMetricTracker),
            "json_graph": get_type(JsonGraphMetricTracker)
        }

class ConstructionTrackingRunner(AbstractTrackingRunner):
    def __init__(self, port=5556, metric_handlers: List[AbstractConstructionTracker]=None):
        super().__init__(port=port, metric_handlers=metric_handlers)

    def handle_metric_event(self, data):
        metric_name = data["metric_name"]

        if metric_name == "construction_start":
            for (tracker,_) in self.iterate_unique_trackers():
                tracker.initialize_construction(data['value'])
        else:
            if metric_name in self.metric_handlers:
                for tracker in self.metric_handlers[metric_name]:
                    tracker.handle_metric_event(metric_name, data['value'])

class QueryTrackerRunner(AbstractTrackingRunner):
    def __init__(self, exp_folder, index_info=None, graph=None, individualQDataCount=10, port=5556, metric_handlers: List[AbstractQueryTracker]=None):
        self.experiment_stats = dict()
        self.completed_queries = 0
        self.individualQDataCount = individualQDataCount
        self.exp_folder = exp_folder
        super().__init__(port=port, metric_handlers=metric_handlers)

        for (tracker, _) in self.iterate_unique_trackers():
            tracker.set_graph(graph)
            tracker.set_index_info(index_info)

    def handle_metric_event(self, data):
        metric_name = data["metric_name"]
        # print(data)

        if metric_name == "end_query":
            for (tracker, _) in self.iterate_unique_trackers():
                tracker.end_query(data['value'])

            if self.completed_queries < self.individualQDataCount:
                query_dir = os.path.join(self.exp_folder, f"query_{self.completed_queries}")
                os.makedirs(query_dir, exist_ok=True)
                self.generate_graphs(filename_prefix=query_dir, single_query=True)
                json_data = self.generate_json(single_query=True)
                with open(os.path.join(query_dir, "metrics.json"), "w") as f:
                    json.dump(json_data, f, indent=4)
            self.completed_queries += 1
            
        elif metric_name == "configure_experiment":
            self.completed_queries = 0
            self.experiment_stats = data['value']
            for (tracker, metrics) in self.iterate_unique_trackers():
                tracker.configure_experiment_stats(data['value'])
        else:
            if metric_name in self.metric_handlers:
                for tracker in self.metric_handlers[metric_name]:
                    tracker.handle_metric_event(metric_name, data['value'])


