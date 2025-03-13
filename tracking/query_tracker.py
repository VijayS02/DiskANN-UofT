from typing import List

from matplotlib.axes import Axes

from tracking.abstract_trackers import AbstractConstructionTracker, AbstractQueryTracker
from tracking.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from tracking.tracker import AbstractTrackingRunner
import subprocess
import time
import os

from tracking.util import download_sift, create_build


class QueryTrackerRunner(AbstractTrackingRunner):
    def __init__(self, build_memory_location, search_location, port=5556, metric_handlers: List[AbstractQueryTracker]=None):
        self.build_memory_location = build_memory_location
        self.search_exec = search_location
        super().__init__(port=port, metric_handlers=metric_handlers)

    def handle_metric_event(self, data):
        metric_name = data["metric_name"]

        if metric_name == "query_end":
            for (tracker, metric) in self.iterate_trackers():
                tracker.end_query()
        else:
            if metric_name in self.metric_handlers:
                for tracker in self.metric_handlers[metric_name]:
                    tracker.handle_metric_event(data['value'])

    def search_index(self, query_file_name, r=32, l=100, alpha=1.2, l_build=50,
                    print_out=False, tracking_port=5555, **kwargs):
        """Build index, search index and track metrics via ZMQ"""

        title = f"R{str(r)}_L{str(l_build)}_A{str(alpha)}"

        experiment_folder = os.path.join(sift_folder, title)
        os.makedirs(experiment_folder, exist_ok=True)

        index_prefix = os.path.join(experiment_folder, f"index_")
        result_path = os.path.join(experiment_folder, "res")


        if not os.path.exists(index_prefix+".data"):
            cmd2 = [
                build_memory_index,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--data_path", base_file,
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
            search_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--index_path_prefix", index_prefix,
            "--query_file", query_file_name,
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

class DistanceDistributionTracker(FrequencyTracker, AbstractQueryTracker):
    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_value(self, raw_data):
        return round(raw_data['distance'], -2)

    def get_graph_props(self):
        return {"x": "Distance", "y": "Frequency", "title": "Distance Frequency Graph" }

    def get_metric_name(self) -> str:
        return "visited_node"



if __name__ == "__main__":
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    print("BASE directory:", parent_dir)


    build_dir = os.path.join(parent_dir, "build")
    data_folder = os.path.join(build_dir, "data")


    build_output = create_build(parent_dir, tracking=True, type="Release")

    apps_dir = os.path.join(build_output, "apps")

    os.makedirs(data_folder, exist_ok=True)
    download_sift(data_folder, apps_dir)

    sift_folder = os.path.join(data_folder, 'sift')

    compute_groundtruth = os.path.join(apps_dir, "utils/compute_groundtruth")
    build_memory_index = os.path.join(apps_dir, "build_memory_index")
    search_memory_index = os.path.join(apps_dir, "search_memory_index")

    query_file_name = "sift_query.fbin"
    base_file_name = "sift_learn.fbin"

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)
    gt_k = 100

    # Paths to dataset files
    query_file = os.path.join(sift_folder, query_file_name)
    gt_file = os.path.join(sift_folder, query_file + f".gt_{str(gt_k)}")
    stats_folder = os.path.join(sift_folder, "stats")
    construction_stats = os.path.join(stats_folder, "construction_stats")

    if not os.path.exists(gt_file):
        cmd1 = [
            compute_groundtruth,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--base_file", base_file,
            "--query_file", query_file,
            "--gt_file", gt_file,
            "--K", str(gt_k)
        ]
        result = subprocess.run(cmd1, stdout=None, stderr=None, text=True)
        if result.returncode != 0:
            print(f"Error computing ground truth: {result.stderr}")
            exit(1)
        else:
            print("Ground truth file already exists, skipping gt calculation.")

    tracker = QueryTrackerRunner(build_memory_index, search_memory_index,
                                metric_handlers=[DistanceDistributionTracker()])


    experiments = [
        {
            'r':32,
            'l_build': 50,
            'alpha': 1.2
        },
        {
            'r':64,
            'l_build': 50,
            'alpha': 1.2
        }
    ]

    for experiment in experiments:
        r = experiment['r']
        alpha = experiment['alpha']
        l_build=experiment['l_build']

        tracker.search_index(query_file, r=r, alpha=alpha, l_build=l_build, print_out=True)

    tracker.generate_graphs()
