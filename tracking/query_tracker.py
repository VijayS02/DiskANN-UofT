from tracking.lib.abstract_trackers import AbstractQueryTracker
from tracking.lib.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker, ScatterPlotTracker
from tracking.lib.tracker import QueryTrackerRunner
import subprocess
import os

from tracking.lib.util import download_sift, create_build

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
        super().__init__("NONE")
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


class RecallPerNodeID(ScatterPlotTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("recall_per_node", average=True)
        self.pos = 0
        self.store = []

    def end_query(self, data):
        self.pos = 0

    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def handle_metric_event(self, metric_data):
        val = metric_data['recall']
        self.add_data_point(val, i=self.pos)
        self.pos += 1

    def get_graph_props(self):
        return {"x": "Node ID (Ascending by construction order)", "y": "Recall (%)", "title": "Recall per Node ID" }


from enum import Enum
class Dataset(Enum):
    SIFT_100k = 1 # learn
    SIFT_1M = 2 # base
    OPENAI_2M = 3

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

    """
    [CSC 2525]
    
    For now, the query_file and base_file is hard-coded here.
    Based on your experiment, you will need to tweak below values accordingly.
    Eventually, we want this to conditionally flip based on the dataset enum referred in the `experiments` list.
    """
    # query_file_name = "sift_query.fbin"
    # query_file_name = "sift_learn.fbin"
    # base_file_name = "sift_learn.fbin" # For 100k
    query_file_name = "sift_base.fbin"
    base_file_name = "sift_base.fbin" # For 1M.

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)
    gt_k = 100

    print_out = True
    tracking_port = 5555

    # Paths to dataset files
    query_file = os.path.join(sift_folder, query_file_name)
    gt_file = os.path.join(sift_folder, f"base:{base_file_name}_query:{query_file_name}.gt_{str(gt_k)}")
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
                                metric_handlers=[# NodeVisitedDistribution(), 
                                                RecallPerNodeID(),
                                                QueryTimeDistribution(), 
                                                #  AverageDistancePerStep(),
                                                #  MinDistanceConvergence(),
                                                 ])

    """
    [CSC 2525]
    
    Below `experiments` list outlines the series of experiments to be compared on a single plot.
    It can also serve as an automation tool for various index construction.
    """
    experiments = [
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_node_from_gt": 0,
        #     "n_pass": 1,
        #     "l_search": 10,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_100k # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_node_from_gt": 0,
        #     "n_pass": 2,
        #     "l_search": 10,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_100k # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_node_from_gt": 0,
        #     "n_pass": 1,
        #     "l_search": 10,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_100k # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 4,
        #     "n_node_from_gt": 0,
        #     "n_pass": 2,
        #     "l_search": 10,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_100k # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_node_from_gt": 4,
        #     "n_pass": 1,
        #     "l_search": 10,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_100k # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # naive
        #     'r':32,
        #     'l_build': 50,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_node_from_gt": 0,
        #     "n_pass": 1,
        #     "l_search": 50,
        #     "k_search": 50,
        #     "dataset": Dataset.SIFT_1M # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        { # only four nodes.
            'r':32,
            'l_build': 50,
            'alpha': 1.2,
            "saturate_graph": False,
            "n_node": 0,
            "n_node_from_gt": 0,
            "n_pass": 1,
            "l_search": 10,
            "k_search": 10,
            "dataset": Dataset.SIFT_1M # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        },
        { # only two pass.
            'r':32,
            'l_build': 50,
            'alpha': 1.2,
            "saturate_graph": False,
            "n_node": 0,
            "n_node_from_gt": 0,
            "n_pass": 2,
            "l_search": 10,
            "k_search": 10,
            "dataset": Dataset.SIFT_1M
        },
        # { # naive
        #     'r':70,
        #     'l_build': 75,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_pass": 1,
        #     "l_search": 50,
        #     "k_search": 10,
        #     "dataset": Dataset.SIFT_1M # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # only four nodes.
        #     'r':70,
        #     'l_build': 75,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 4,
        #     "n_pass": 1,
        #     "l_search": 50,
        #     "k_search": 50,
        #     "dataset": Dataset.SIFT_1M # TODO: For now, this enum is used for title generation. But we should use this to conditionally build new index.
        # },
        # { # only two pass.
        #     'r':70,
        #     'l_build': 75,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 0,
        #     "n_pass": 2,
        #     "l_search": 50,
        #     "k_search": 50,
        #     "dataset": Dataset.SIFT_1M
        # },
        # { # both.
        #     'r':70,
        #     'l_build': 75,
        #     'alpha': 1.2,
        #     "saturate_graph": False,
        #     "n_node": 4,
        #     "n_pass": 2,
        #     "l_search": 50,
        #     "k_search": 50,
        #     "dataset": Dataset.SIFT_1M
        # }
    ]

    for experiment in experiments:
        r = experiment['r']
        alpha = experiment['alpha']
        l_build=experiment['l_build']
        n_node=experiment['n_node']
        n_node_from_gt=experiment['n_node_from_gt']
        n_pass=experiment['n_pass']
        l_search = experiment['l_search']
        dataset=experiment['dataset']
        k_search=experiment['k_search']

        # index title should not be bothered with L_Search.
        # TODO: Vijay: Try saturating the graph. At least your edge utilization would be consistent.
        index_title = f"dataset:{dataset}_r{str(r)}_lbuild{str(l_build)}_a{str(alpha).replace(".", '-')}{"_sat" if experiment['saturate_graph'] else ""}_nnodes{n_node}_nnodes_gt{n_node_from_gt}_npass{n_pass}"
        # graph_title = f"{index_title}_ksearch{k_search}_lsearch{l_search}"
        graph_title = f"N-Pass method, N={n_pass}"

        experiment_folder = os.path.join(sift_folder, index_title)
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
                "--saturate_graph" if experiment.get("saturate_graph", False) else "",
                "-L", str(l_build),
                "--alpha", str(alpha),
                "--num_threads", "1",
                "--tracking_addr", "NONE", # [CSC 2525] New parameter introduced as part of our research.
                "--n_node", str(n_node), # [CSC 2525] New parameter introduced as part of our research.
                "--n_node_from_gt", str(n_node_from_gt), # [CSC 2525] New parameter introduced as part of our research.
                "--n_pass", str(n_pass) # [CSC 2525] New parameter introduced as part of our research.
            ]

            print(f"Executing: {' '.join(cmd2)}")

            result = subprocess.run(
                cmd2,
                stdout=None if print_out else subprocess.DEVNULL,
                stderr=None if print_out else subprocess.DEVNULL,
                text=True
            )

            if result.returncode != 0:
                print(f"Error building index: stderr: {result.stderr}. stdout: {result.stdout}")
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
                "-K", str(k_search),
                "-L", str(l_search),
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

        tracker.trace_program(graph_title, exec_func, tracking_port=tracking_port)

    tracker.generate_graphs()
