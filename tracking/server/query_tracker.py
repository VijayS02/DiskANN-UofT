from collections import defaultdict
from matplotlib.axes import Axes

from lib.abstract_trackers import AbstractQueryTracker, IndividualQueryTracker, JsonMetricTracker, TextMetricTracker
from lib.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from lib.tracker import QueryTrackerRunner
import subprocess
import os

from lib.util import download_sift, create_build

class NodeVisitedDistribution(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("visited_distribution", metrics=["visited_node"], bins=None, label="Node Visited Distribution")
        self.edges_visited = 0

    def end_query(self, _):
        self.add_data_point(self.edges_visited)
        self.edges_visited = 0

    def handle_metric_event(self, metric_name, metric_data):
        self.edges_visited += 1

    def get_graph_props(self):
        return {"x": "Number of Nodes Visited In Query", "y": "Frequency", "title": "Nodes Visited Distribution",
                'ylog': True }

class QueryTimeDistribution(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("query_time_dist", metrics=["NONE"], bins=30, label="Query Time Distribution")
        self.query_times = []

    def end_query(self, data):
        self.add_data_point(data['querytime'])

    def handle_metric_event(self, metric_name, metric_data):
        pass

    def get_graph_props(self):
        return {"x": "Query Time (ms)", "y": "Frequency", "title": "Query Time Distribution", 'ylog': True }

class AverageDistancePerStep(ChangeOverTimeTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__('avg_dist_per_step', metrics=["visited_node"], average=True, label="Average Distance Per Step")
        self.pos = 0
        self.store = []
    def end_query(self, data):
        self.pos = 0

    def handle_metric_event(self, metric_name, metric_data):
        val = metric_data['distance']
        self.add_data_point(val, i=self.pos)
        self.pos += 1


    def get_graph_props(self):
        return {"x": "Step", "y": "Average Distance", "title": "Average distance per step" }


class MinDistanceConvergence(FrequencyTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__('min_dist_convg', metrics=["visited_node"],bins=50, label="Min Distance Convergence")
        self.min_dist = 999999999999
        self.index = 0
        self.min_index = -1

    def end_query(self, data):
        self.add_data_point(self.min_index / self.index)
        self.min_dist = 9999999999999
        self.index = 0
        self.min_index = -1

    def handle_metric_event(self, metric_name, metric_data):
        dist = metric_data['distance']
        if dist < self.min_dist:
            self.min_dist = dist
            self.min_index = self.index
        self.index += 1


    def get_graph_props(self):
        return {"x": "Portion of steps taken to reach min", "y": "Freq", "title": "Steps to Closest Node Dist" }



class NodeExplorationIndividual(JsonMetricTracker, IndividualQueryTracker):
    def __init__(self):
        super().__init__("IndividualQueryNodeExploration", "indiv_node_explore_graph", metrics=["visited_node"], label="Node exploration (Individual)")
        self.parents = dict()
        self.results = dict()
        self.visit_order = []

    def end_query(self, data):
        if len(data['best_k']) != 0:
            visit_set = set(self.visit_order)
            self.parents = {node: parent for node, parent in self.parents.items() if node in visit_set}
            self.results['best_k'] = data['best_k']
            self.results['parents'] = self.parents
            self.results['gt_results'] = data['ground_truth']
            self.results['visit_order'] = self.visit_order
            self.parents = dict()
            self.visit_order = []


    def handle_metric_event(self, metric_name, metric_data):
        if not self.graph:
            raise ValueError("Graph not set")
        self.visit_order.append(metric_data['nodeid'])
        for child in self.graph[metric_data['nodeid']]:
            if child not in self.parents:
                self.parents[child] = metric_data['nodeid']

    def end_experiment(self, title):
        pass

    def get_json(self):
        return self.results


class DistancePerStepIndiv(ChangeOverTimeTracker, IndividualQueryTracker):
    def __init__(self):
        super().__init__('indv_dist_per_step', metrics=["visited_node"], label="Distance Per Step (Individual)")
        self.pos = 0
        self.store = []

    def end_query(self, data):
        self.end_experiment('Query')

    def handle_metric_event(self, metric_name, metric_data):
        val = metric_data['distance']
        self.add_data_point(val, i=self.pos)
        self.pos += 1

    def get_graph_props(self):
        return {"x": "Step", "y": "Distance", "title": "Distance per step" }


class RecallDistribution(FrequencyTracker, TextMetricTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__('recall_dist', metrics=[], bins=20, label="Recall Distribution")
        self.queries = 0
        self.recall_vals = []
    
    def end_query(self, data):
        gt_results = data['ground_truth']
        best_k = data['best_k']

        # compute recall by checking how many of the ground truth results are in the best_k
        recall = len(set(gt_results).intersection(set(best_k))) / len(gt_results)
        self.add_data_point(recall)
        if recall == 0:
            print(f"Recall is 0 for query {self.queries}")

        self.queries += 1
        self.recall_vals.append(recall)

    def print_text_output(self):
        print(f"Avg Recall: {(sum(self.recall_vals) / self.queries)*100:.2f}%")

    def get_graph_props(self):
        return {"x": "Recall", "y": "Frequency", "title": "Recall Distribution", "ylog": True }
    

class UsefulEdgesDistribution(FrequencyTracker,TextMetricTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("UsefulEdgesDistribution", bins=30, metrics=["visited_node"], label="Useful Edges Distribution")
        self.parents = dict()
        self.edge_uses = defaultdict(int)
        self.unused_edges = 0

    def handle_metric_event(self, metric_name, metric_data):
        if not self.graph:
            raise ValueError("Graph not set")

        for child in self.graph[metric_data['nodeid']]:
            if child not in self.parents:
                self.parents[child] = metric_data['nodeid']
        
        if metric_data['nodeid'] in self.parents:
            edge = (self.parents[metric_data['nodeid']], metric_data['nodeid'])
            self.edge_uses[edge] += 1

    def end_query(self, data):
        self.parents.clear()

    def end_experiment(self, title):
        total_used_edges = len(self.edge_uses)
        self.unused_edges = 0
        if self.index_info and "edges" in self.index_info:
            self.unused_edges = self.index_info["edges"] - total_used_edges
        
        for i in range(self.unused_edges):
            self.add_data_point(0)

        for edge, uses in self.edge_uses.items():
            self.add_data_point(uses)
        self.end_experiment_graph(title)

    def print_text_output(self):
        print("Top 10 edges by use:")
        for edge, uses in sorted(self.edge_uses.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"{edge}: {uses}")
        
        print(f"Number of unused edges: {self.unused_edges}")

    
    def get_graph_props(self):
        return {"x": "Edge Uses", "y": "Frequency", "title": "Edge Use Distribution", "ylog": True }

class KUsefulEdges(FrequencyTracker,TextMetricTracker, AbstractQueryTracker):
    def __init__(self):
        super().__init__("KUsefulEdges", bins=30, metrics=["visited_node"], label="K-Useful Edges Distribution")
        self.parents = dict()
        self.edge_uses = defaultdict(int)
        self.unused_edges = 0

    def handle_metric_event(self, metric_name, metric_data):
        if not self.graph:
            raise ValueError("Graph not set")

        for child in self.graph[metric_data['nodeid']]:
            if child not in self.parents:
                self.parents[child] = metric_data['nodeid']

    def trace_path(self, node):
        current = node
        visited = set()

        while current in self.parents:
            if current in visited:  # Cycle detected!
                break

            visited.add(current)
            parent = self.parents[current]
            edge = (parent, current)
            self.edge_uses[edge] += 1  # Track edge usage count
            current = parent  # Move up the path

    def end_query(self, data):
        best_k = data['best_k']
        for node in best_k:
            self.trace_path(node)
        self.parents.clear()

    def end_experiment(self, title):
        total_used_edges = len(self.edge_uses)
        self.unused_edges = 0
        if self.index_info and "edges" in self.index_info:
            self.unused_edges = self.index_info["edges"] - total_used_edges
        
        for i in range(self.unused_edges):
            self.add_data_point(0)

        for edge, uses in self.edge_uses.items():
            self.add_data_point(uses)
        self.end_experiment_graph(title)

    def print_text_output(self):
        print("Top 10 USEFUL edges by use:")
        for edge, uses in sorted(self.edge_uses.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"{edge}: {uses}")
        
        print(f"Number of non-useful edges: {self.unused_edges}")

    
    def get_graph_props(self):
        return {"x": "Useful Edge Uses", "y": "Frequency", "title": "K-Useful Edge Use Distribution", "ylog": True }




METRIC_LIST = [
    NodeVisitedDistribution,
    QueryTimeDistribution,
    AverageDistancePerStep,
    MinDistanceConvergence,
    NodeExplorationIndividual,
    DistancePerStepIndiv,
    RecallDistribution,
    UsefulEdgesDistribution,
    KUsefulEdges
]


METRICS = {metric().get_id(): {"label": metric().get_label(), "class": metric} for metric in METRIC_LIST}

def initialize_query_tracker(selected_metrics, exp_folder, **kwargs):
    metric_handlers = [METRICS[metric]['class']() for metric in selected_metrics if metric in METRICS]

    tracker = QueryTrackerRunner(exp_folder, metric_handlers=metric_handlers, **kwargs)
    return tracker


def get_available_query_metrics():
    # Get metrics without the class
    return {key: {"label": value["label"]} for key, value in METRICS.items()}


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
