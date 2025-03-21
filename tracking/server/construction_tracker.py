from collections import defaultdict

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
import seaborn as sns


from lib.abstract_trackers import AbstractConstructionTracker
from lib.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from lib.tracker import ConstructionTrackingRunner
import subprocess
import time
import os

from lib.util import download_sift, create_build

class AddEdgeCountTracker(FrequencyTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_edge_count", bins=None, text=True)
        self.const_data = dict()
        self.total_edges = 0
        self.edge_usage = dict()
        self.exp_text_data = dict()

    def handle_metric_event(self, metric_data):
        self.add_data_point(metric_data)
        self.total_edges += metric_data

    def print_text_output(self):
        for exp in self.exp_text_data:
            print(f"\n{exp}")
            print(f"{self.exp_text_data[exp] * 100:>6.2f}% Edge Utilization")

    def end_experiment(self, title):
        self.end_experiment_graph(title)
        self.exp_text_data[title] = self.total_edges / (self.const_data['range'] * self.const_data['n_nodes'])
        self.total_edges = 0

    def get_graph_props(self):
        return {"x": "Edge Counts", "y": "Frequency", "title": "Edge Count Distribution" }

    def initialize_construction(self, construction_params):
        self.const_data = construction_params

class ConstructionPathLengthFreqTracker(FrequencyTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_construction_path_length")

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_graph_props(self):
        return {"x": "Number of edges", "y": "Frequency", "title": "Construction Path Length Distribution", "ylog": True }

    def initialize_construction(self, construction_params):
        pass

    def handle_metric_event(self, metric_data):
        self.add_data_point(metric_data)

    def get_metric_name(self) -> str:
        return "add_construction_path_length"


class ConstructionPathLengthOverTimeTracker(ChangeOverTimeTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_construction_path_length")

    def get_graph_props(self):
        return {"x": "Query", "y": "Number of Hops", "title": "Construction Path Length Over Time"}

    def initialize_construction(self, construction_params):
        print("Construction Started!")
        print(construction_params)

    def handle_metric_event(self, metric_data):
        self.add_data_point(metric_data)

    def get_metric_name(self) -> str:
        return "add_construction_path_length"


class NodeDistanceTracker(AbstractConstructionTracker):
    def __init__(self):
        super().__init__("node_info", graph=True, text=False)
        self.node_distances = defaultdict(list)  # Stores distances per neighbor index
        self.data = dict()
        self.zeros = 0

    def initialize_construction(self, construction_params):
        pass

    def handle_metric_event(self, metric_data):
        """Stores sorted neighbor distances per index across nodes."""
        sorted_distances = sorted(metric_data['neighbor_distances'])
        for i, dist in enumerate(sorted_distances):
            if dist == 0 :
                self.zeros += 1
            self.node_distances[i].append(dist/max(sorted_distances[0], 1))

    def generate_subplot(self, ax: Axes):
        """Generates a boxplot for each neighbor index."""
        # Convert self.data to a Pandas DataFrame for Seaborn
        plot_data = []
        for key, node_dists in self.data.items():
            for neighbor_idx, distances in node_dists.items():
                for value in distances:
                    plot_data.append({"Experiment": key, "Neighbor Index": neighbor_idx, "Difference Distance": value})

        df = pd.DataFrame(plot_data)

        # Set Seaborn theme for better aesthetics
        sns.set_theme(style="ticks", palette="pastel")

        # Create the boxplot
        sns.boxplot(
            x="Neighbor Index", y="Difference Distance",
            hue="Experiment",  # Groups by experiment
            data=df, palette="pastel", ax=ax
        )

        # Plot exponential reference line
        max_dist = df["Neighbor Index"].max()
        ys = [1.2 ** x for x in range(max_dist)]
        ax.plot(ys, label="Exponential alpha (1.2^x)", color="black", linestyle="dashed")

        # Customize labels and legend
        ax.set_yscale('log')
        ax.set_xlabel("Neighbor Index")
        ax.set_ylabel("Distance Normalized")
        ax.set_title("Distribution of Distance Differences by Index")
        ax.legend(title="Experiment")

        sns.despine(offset=10, trim=True)  # Clean up plot edges


    def end_experiment(self, title):
        """Stores the current experiment's data."""
        self.data[title] = dict(self.node_distances)
        self.node_distances.clear()


def initialize_tracking_runner():
    return ConstructionTrackingRunner(metric_handlers=[AddEdgeCountTracker(), ConstructionPathLengthFreqTracker(), ConstructionPathLengthOverTimeTracker(), NodeDistanceTracker()]
    )


if __name__ == "__main__":
    parent_dir = '/home/vijay/Documents/DiskANN-UofT/'
    # print("BASE directory:", parent_dir)


    build_dir = os.path.join(parent_dir, "build")
    data_folder = os.path.join(build_dir, "data")


    build_output = create_build(parent_dir, tracking=True, type="Release")

    apps_dir = os.path.join(build_output, "apps")

    os.makedirs(data_folder, exist_ok=True)
    download_sift(data_folder, apps_dir)

    sift_folder = os.path.join(data_folder, 'sift')

    build_memory_index = os.path.join(apps_dir, "build_memory_index")

    base_file_name = "sift_learn.fbin"

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)

    tracker = ConstructionTrackingRunner(build_memory_index,
                                         metric_handlers=[AddEdgeCountTracker(), NodeDistanceTracker()])


    tracking_port = 5555
    print_out = True

    experiments = [
        {
            'r':32,
            'l_build': 50,
            'alpha': 1.2,
            "saturate_graph": True,
        },
        {
            'r':32,
            'l_build': 50,
            'alpha': 1.2,
            "saturate_graph": False,
        },
    ]

    for experiment in experiments:
        r = experiment['r']
        alpha = experiment['alpha']
        l_build=experiment['l_build']

        title = f"R{str(r)}_L{str(l_build)}_A{str(alpha).replace(".","-")}{"_SAT" if experiment['saturate_graph'] else ""}"
        exp_folder = os.path.join(sift_folder, title)
        os.makedirs(exp_folder,exist_ok=True)

        index_path = os.path.join(exp_folder, "index")

        # Build command with all the arguments
        command = [
            build_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--data_path", base_file,
            "--index_path_prefix", index_path,
            "-R", str(r),
            "-L", str(l_build),
            "--alpha", str(alpha),
            "--num_threads", "1",
            "--tracking_addr", f"tcp://localhost:{tracking_port}",
            "--saturate_graph" if "saturate_graph" in experiment and experiment["saturate_graph"] else "",
        ]

        print(command)

        def trace_function():
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

            return {
                "exit_code": process.returncode,
            }

        tracker.trace_program(title, trace_function, tracking_port=tracking_port)


    tracker.generate_text()

    tracker.generate_graphs()


