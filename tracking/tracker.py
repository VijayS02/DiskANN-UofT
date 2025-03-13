import time
from abc import abstractmethod
from typing import List, Dict

import numpy as np
import zmq
import json
from tracking.abstract_trackers import AbstractConstructionTracker, AbstractMetricTracker, AbstractQueryTracker
import threading
import os
import subprocess

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




class ConstructionTrackingRunner(AbstractTrackingRunner):
    def __init__(self, executable_location, port=5556, metric_handlers: List[AbstractConstructionTracker]=None):
        self.executable_location = executable_location
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

    def build_index(self,title:str, exp_parent_folder, data_file, r=32, alpha=1.2, l_build=50,
                    print_out=False, tracking_port=5555, **kwargs):
        """Build index and track metrics via ZMQ"""


        exp_folder = os.path.join(exp_parent_folder, title)
        os.makedirs(exp_folder,exist_ok=True)

        index_path = os.path.join(exp_folder, "index")

        # Start tracking server first
        self.start_tracking_server(port=tracking_port)

        # Build command with all the arguments
        command = [
            self.executable_location,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--data_path", data_file,
            "--index_path_prefix", index_path,
            "-R", str(r),
            "-L", str(l_build),
            "--alpha", str(alpha),
            "--num_threads", "1",
            "--tracking_addr", f"tcp://localhost:{tracking_port}"
        ]

        # Add any additional arguments
        for key, value in kwargs.items():
            command.append(f"--{key}")
            if value is not None and value is not True:
                command.append(str(value))

        print(f"Executing: {' '.join(command)}")

        try:
            # Run the build command
            process = subprocess.Popen(
                command,
                stdout=None if print_out else subprocess.DEVNULL,
                stderr=None if print_out else subprocess.DEVNULL,
                text=True
            )

            # Wait for completion
            process.wait()

            # Give time for any final messages to be received
            time.sleep(1)

        finally:
            # Stop the tracking server
            self.stop_tracking_server()

        self.end_experiment(title)

        return {
            "exit_code": process.returncode,
        }


class QueryTrackerRunner(AbstractTrackingRunner):
    def __init__(self, build_memory_location, search_location, port=5556, metric_handlers: List[AbstractQueryTracker]=None):
        self.build_memory_location = build_memory_location
        self.search_exec = search_location
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

    def search_index(self, title: str, exp_parent_folder, base_file_path, query_file_path,
                     gt_file, r=32, l=100, alpha=1.2, l_build=50,
                     print_out=False, tracking_port=5555, **kwargs):
        """Build index, search index and track metrics via ZMQ"""

        experiment_folder = os.path.join(exp_parent_folder, title)
        os.makedirs(experiment_folder, exist_ok=True)

        index_prefix = os.path.join(experiment_folder, "index")
        result_path = os.path.join(experiment_folder, "res")


        if not os.path.exists(index_prefix+".data"):
            cmd2 = [
                self.build_memory_location,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--data_path", base_file_path,
                "--index_path_prefix", index_prefix,
                "-R", str(r),
                "--saturate_graph" if "saturate_graph" in kwargs else "",
                "-L", str(l_build),
                "--alpha", str(alpha),
                "--num_threads", "1",
                "--tracking_addr", "NONE"
            ]

            result = subprocess.run(
                cmd2,
                stdout=None if print_out else subprocess.DEVNULL,
                stderr=None if print_out else subprocess.DEVNULL,
                text=True
            )

            if result.returncode != 0:
                print(f"Error building index: {result.stderr}")
                exit(1)
        else:
            print("Index exists")



        # Start tracking server first
        self.start_tracking_server(port=tracking_port)

        # Search command with all the arguments
        command = [
            self.search_exec,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--index_path_prefix", index_prefix,
            "--query_file", query_file_path,
            "--gt_file", gt_file,
            "-K", "10",
            "-L", str(l),
            "--result_path", result_path,
            "--num_threads", "1",
            "--tracking_addr", f"tcp://localhost:{tracking_port}"
        ]

        print(f"Executing: {' '.join(command)}")

        try:
            # Run the build command
            process = subprocess.Popen(
                command,
                stdout=None if print_out else subprocess.DEVNULL,
                stderr=None if print_out else subprocess.DEVNULL,
                text=True
            )

            # Wait for completion
            process.wait()

            # Give time for any final messages to be received
            time.sleep(1)

        finally:
            # Stop the tracking server
            self.stop_tracking_server()

        self.end_experiment(title)

        return {
            "exit_code": process.returncode,
        }

