from matplotlib.axes import Axes

from tracking.abstract_trackers import AbstractConstructionTracker
from tracking.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from tracking.tracker import AbstractTrackingRunner, ConstructionTrackingRunner
import subprocess
import time
import os

from tracking.util import download_sift, create_build

class AddEdgeCountTracker(FrequencyTracker, AbstractConstructionTracker):
    def __init__(self):
        super().__init__("add_edge_count")

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
                                         metric_handlers=[AddEdgeCountTracker(), ConstructionPathLengthFreqTracker()])


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

        title = f"R{str(r)}_L{str(l_build)}_A{str(alpha).replace(".","-")}"
        tracker.build_index(title, sift_folder, base_file, r=r, alpha=alpha, l_build=l_build, print_out=True)

    tracker.generate_graphs()
