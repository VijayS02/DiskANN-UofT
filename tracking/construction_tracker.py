from matplotlib.axes import Axes

from tracking.abstract_trackers import AbstractConstructionTracker
from tracking.basic_metric_types import FrequencyTracker, ChangeOverTimeTracker
from tracking.tracker import AbstractTrackingRunner
import subprocess
import time
import os

from tracking.util import download_sift, create_build


class ConstructionTrackingRunner(AbstractTrackingRunner):
    def __init__(self, executable_location, port=5556, metric_handlers=None):
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

    def build_index(self, data_file, r=32, alpha=1.2, l_build=50,
                    print_out=False, tracking_port=5555, **kwargs):
        """Build index and track metrics via ZMQ"""

        title = f"R{str(r)}_L{str(l_build)}_A{str(alpha)}"
        index_path = os.path.join(sift_folder, f"index_{base_file_name.replace('.fbin', '')}_R{str(r)}_L{str(l_build)}_A{str(alpha)}")

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



class AddEdgeCountTracker(FrequencyTracker, AbstractConstructionTracker):
    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_graph_props(self):
        return {"x": "Edge Counts", "y": "Frequency", "title": "Edge Count Distribution" }

    def initialize_construction(self, construction_params):
        print("Construction Started!")
        print(construction_params)


    def get_metric_name(self) -> str:
        return "add_edge_count"


class ConstructionPathLengthTracker(ChangeOverTimeTracker, AbstractConstructionTracker):
    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_graph_props(self):
        return {"x": "Step", "y": "Path Length", "title": "Path Length Over Steps" }

    def initialize_construction(self, construction_params):
        print("Construction Started!")
        print(construction_params)


    def get_metric_name(self) -> str:
        return "add_construction_path_length"


class ConstructionPathLengthFreqTracker(FrequencyTracker, AbstractConstructionTracker):
    def has_text_output(self):
        return False

    def print_text_output(self):
        return None

    def get_graph_props(self):
        return {"x": "Number of edges", "y": "Frequency", "title": "Construction Path Length Distribution", "ylog": True }

    def initialize_construction(self, construction_params):
        print("Construction Started!")
        print(construction_params)


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

    tracker = ConstructionTrackingRunner(build_memory_index, metric_handlers=[AddEdgeCountTracker(), ConstructionPathLengthTracker(), ConstructionPathLengthFreqTracker()])


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

        tracker.build_index(base_file, r=r, alpha=alpha, l_build=l_build, print_out=True)

    tracker.generate_graphs()
