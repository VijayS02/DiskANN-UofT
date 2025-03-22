from matplotlib.axes import Axes

from lib.abstract_trackers import AbstractQueryTracker
from lib.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from lib.tracker import QueryTrackerRunner
import subprocess
import os

from lib.util import download_sift, create_build

class NodeVisitedDistribution(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("visited_node", bins=None)
        self.edges_visited = 0

    def end_query(self, _):
        self.add_data_point(self.edges_visited)
        self.edges_visited = 0

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def handle_metric_event(self, metric_data):
        self.edges_visited += 1

    def get_graph_props(self):
        return {"x": "Number of Nodes Visited In Query", "y": "Frequency", "title": "Nodes Visited Distribution",
                'ylog': True }

class QueryTimeDistribution(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("NONE", bins=30)
        self.edges_visited = 0
    def end_query(self, data):
        self.add_data_point(data['querytime'])

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def handle_metric_event(self, metric_data):
        pass

    def get_graph_props(self):
        return {"x": "Query Time (ms)", "y": "Frequency", "title": "Query Time Distribution", 'ylog': True }

class AverageDistancePerStep(ChangeOverTimeTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("visited_node", average=True)
        self.pos = 0
        self.store = []
    def end_query(self, data):
        self.pos = 0

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def handle_metric_event(self, metric_data):
        val = metric_data['distance']
        self.add_data_point(val, i=self.pos)
        self.pos += 1


    def get_graph_props(self):
        return {"x": "Step", "y": "Average Distance", "title": "Average distance per step" }


class MinDistanceConvergence(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("visited_node",bins=50)
        self.min_dist = 999999999999
        self.index = 0
        self.min_index = -1
    def end_query(self, data):
        self.add_data_point(self.min_index / self.index)
        self.min_dist = 9999999999999
        self.index = 0
        self.min_index = -1


    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def handle_metric_event(self, metric_data):
        dist = metric_data['distance']
        if dist < self.min_dist:
            self.min_dist = dist
            self.min_index = self.index
        self.index += 1


    def get_graph_props(self):
        return {"x": "Portion of steps taken to reach min", "y": "Freq", "title": "Steps to Closest Node Dist" }



class BestKParentMetric(AbstractQueryTracker):
    def __init__(self):
        super().__init__("node_connection", json="BestKParentMetric")
        self.parents = dict()
        self.computed = False
        self.results = []

    def generate_path(self, next_node):
        if next_node not in self.parents:
            return [next_node]
        else:
            return self.generate_path(self.parents[next_node]) + [next_node]

    def end_query(self, data):
        if len(data['best_k']) != 0:
            best_k = data['best_k']
            paths = []
            for node in best_k:
                paths.append(self.generate_path(node))
            self.results.append(paths)

    def handle_metric_event(self, metric_data):
        if metric_data['child'] not in self.parents:
            self.parents[metric_data['child']] = metric_data['parent']

    def end_experiment(self, title):
        pass

    def get_json(self):
        return self.results


def initialize_query_tracker():
    tracker = QueryTrackerRunner(metric_handlers=[NodeVisitedDistribution(), QueryTimeDistribution(), AverageDistancePerStep(),
                                                 MinDistanceConvergence(), BestKParentMetric()])
    return tracker


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

    print_out = True
    tracking_port = 5555

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

    tracker = initialize_query_tracker()

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
    l = 100

    for experiment in experiments:
        r = experiment['r']
        alpha = experiment['alpha']
        l_build=experiment['l_build']
        title = f"R{str(r)}_L{str(l_build)}_A{str(alpha).replace(".", '-')}{"_SAT" if experiment['saturate_graph'] else ""}"

        experiment_folder = os.path.join(sift_folder, title)
        os.makedirs(experiment_folder, exist_ok=True)

        index_prefix = os.path.join(experiment_folder, "index")
        result_path = os.path.join(experiment_folder, "res")


        if not os.path.exists(index_prefix+".data"):
            cmd2 = [
                build_memory_index,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--data_path", base_file,
                "--index_path_prefix", index_prefix,
                "-R", str(r),
                "--saturate_graph" if "saturate_graph" in experiment and experiment["saturate_graph"] else "",
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

        def exec_func():
            # Search command with all the arguments
            command = [
                search_memory_index,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--index_path_prefix", index_prefix,
                "--query_file", query_file,
                "--gt_file", gt_file,
                "-K", "10",
                "-L", str(l),
                "--result_path", result_path,
                "--num_threads", "1",
                "--tracking_addr", f"tcp://localhost:{tracking_port}"
            ]

            print(f"Executing: {' '.join(command)}")

            # Run the build command
            process = subprocess.Popen(
                command,
                stdout=None if print_out else subprocess.DEVNULL,
                stderr=None if print_out else subprocess.DEVNULL,
                text=True
            )

            # Wait for completion
            process.wait()

            return {
                "exit_code": process.returncode,
            }

        tracker.trace_program(title, exec_func, tracking_port=tracking_port)

    tracker.generate_graphs()
