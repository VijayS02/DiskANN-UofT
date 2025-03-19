from collections import defaultdict

from matplotlib.axes import Axes
# import seaborn as sns


from tracking.lib.abstract_trackers import AbstractConstructionTracker
from tracking.lib.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from tracking.lib.tracker import ConstructionTrackingRunner
import subprocess
import time
import os

from tracking.lib.util import download_sift, create_build

class AddEdgeCountTracker(FrequencyTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_edge_count", bins=None)

    def handle_metric_event(self, metric_data):
        self.add_data_point(metric_data)

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_graph_props(self):
        return {"x": "Edge Counts", "y": "Frequency", "title": "Edge Count Distribution" }

    def initialize_construction(self, construction_params):
        print("Construction Started!")
        print(construction_params)

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
        print("Construction Started!")
        print(construction_params)

    def handle_metric_event(self, metric_data):
        self.add_data_point(metric_data)

    def get_metric_name(self) -> str:
        return "add_construction_path_length"


class ConstructionPathLengthOverTimeTracker(ChangeOverTimeTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_construction_path_length")

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

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
        super().__init__("node_info")
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
        if not self.data:
            return

        print(self.zeros, " ZERO DISTANCEs.")

        max_dist = 0
        for key in self.data:
            node_dists = self.data[key]
            max_dist = max(len(node_dists.keys()), max_dist)
            data = [node_dists[i] for i in sorted(node_dists.keys())]
            # ax.violinplot(data, showmeans=True, showmedians=True)
            ax.boxplot(data, positions=range(len(data)), patch_artist=True)

        ys = []
        for x in range(max_dist):
            ys.append(1.2 ** x)

        ax.plot(ys ,label="Exponential alpha (1.2^x)")

        ax.set_xlabel("Neighbor Index (Lower is closer)")
        ax.set_ylabel("Distance normalized (X[i] = x[i]/x[0])")
        ax.set_title("Distribution of Neighbor Distances by Index")
        ax.set_yscale('log')
        ax.legend()

    def has_text_output(self):
        return False

    def print_text_output(self):
        pass

    def end_experiment(self, title):
        """Stores the current experiment's data."""
        self.data[title] = dict(self.node_distances)
        self.node_distances.clear()

    def has_graph(self) -> bool:
        return True


class NodeDistanceDifferenceTracker(AbstractConstructionTracker):
    def __init__(self):
        super().__init__("node_info")
        self.node_distances = defaultdict(list)  # Stores distances per neighbor index
        self.data = dict()

    def initialize_construction(self, construction_params):
        pass

    def handle_metric_event(self, metric_data):
        """Stores sorted neighbor distances per index across nodes."""
        sorted_distances = sorted(metric_data['neighbor_distances'])
        if len(sorted_distances) > 1:
            for i in range(1, len(sorted_distances)):
                diff = sorted_distances[i]/max(sorted_distances[i-1], 1)
                self.node_distances[i - 1].append(diff)

    def generate_subplot(self, ax: Axes):
        """Generates a boxplot for each neighbor index."""
        if not self.data:
            return

        max_dist = 0
        for key in self.data:
            node_dists = self.data[key]
            max_dist = max(len(node_dists.keys()), max_dist)
            data = [node_dists[i] for i in sorted(node_dists.keys())]
            ax.boxplot(data, positions=range(len(data)), patch_artist=True)

        ys = [1.2 for i in range(max_dist)]
        ax.plot(ys ,label="Exponential alpha (1.2^x)")

        ax.set_xlabel("Neighbor Index")
        ax.set_ylabel("Difference Distance (x[i]/x[i-1])")
        ax.set_title("Distribution of Distances Differences by Index")
        ax.set_yscale('log')

    def has_text_output(self):
        return False

    def print_text_output(self):
        pass

    def end_experiment(self, title):
        """Stores the current experiment's data."""
        self.data[title] = dict(self.node_distances)
        self.node_distances.clear()

    def has_graph(self) -> bool:
        return True



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

    build_memory_index = os.path.join(apps_dir, "build_memory_index")

    base_file_name = "sift_learn.fbin"

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)

    tracker = ConstructionTrackingRunner(build_memory_index,
                                         metric_handlers=[AddEdgeCountTracker(), NodeDistanceTracker(), NodeDistanceDifferenceTracker()])


    tracking_port = 5555
    print_out = True

    experiments = [
        
        {
            'r':32,
            'l_build': 50,
            'alpha': 1.2,
            "saturate_graph": True,
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

    tracker.generate_graphs()
