import re
from pathlib import Path
import os
import urllib.request
import tarfile
import subprocess
import combined_plotter


def download_sift(base_dir, apps_dir):
    tar_file_path = os.path.join(base_dir, "sift.tar.gz")
    extracted_folder = os.path.join(base_dir, "sift")

    sift_learn_fvecs = os.path.join(extracted_folder, "sift_learn.fvecs")
    sift_query_fvecs = os.path.join(extracted_folder, "sift_query.fvecs")

    sift_learn_fbin = os.path.join(extracted_folder, "sift_learn.fbin")
    sift_query_fbin = os.path.join(extracted_folder, "sift_query.fbin")

    util_dir = os.path.join(apps_dir, 'utils')

    # Ensure the directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Check if the dataset is already extracted
    if not os.path.exists(extracted_folder):
        print("Dataset not found. Downloading...")

        # Download the file if not present
        if not os.path.exists(tar_file_path):
            url = "ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz"
            print(f"Downloading {url} ...")
            urllib.request.urlretrieve(url, tar_file_path)
            print("Download complete!")

        # Extract the tar.gz file
        print("Extracting dataset...")
        with tarfile.open(tar_file_path, "r:gz") as tar:
            tar.extractall(base_dir)
        print("Extraction complete!")

    else:
        print("Dataset already exists. Skipping download and extraction.")

    # Convert .fvecs to .fbin if necessary
    if os.path.exists(sift_learn_fvecs) and not os.path.exists(sift_learn_fbin):
        print("Converting sift_learn.fvecs to sift_learn.fbin...")
        subprocess.run([os.path.join(util_dir, "fvecs_to_bin"), "float", sift_learn_fvecs, sift_learn_fbin], check=True)
        print("Conversion complete!")

    if os.path.exists(sift_query_fvecs) and not os.path.exists(sift_query_fbin):
        print("Converting sift_query.fvecs to sift_query.fbin...")
        subprocess.run([os.path.join(util_dir, "fvecs_to_bin"), "float", sift_query_fvecs, sift_query_fbin], check=True)
        print("Conversion complete!")

    print("SIFT dataset is ready.")

def create_build(project_root, build_subdir="script_output", type="Release", tracking=True):
    # Define the build directory (inside `build/`)
    build_dir = os.path.join(project_root, "build", build_subdir)

    # Ensure build directory exists
    os.makedirs(build_dir, exist_ok=True)

    os.chdir(build_dir)

    # Run CMake configuration
    cmake_command = [
        "cmake",
        f"-DCMAKE_BUILD_TYPE={type}",
        f"-DTRACKING_ENABLED={'ON' if tracking else 'OFF'}",
        project_root
    ]
    subprocess.run(cmake_command, check=True)

    print("\n\nRunning make...")

    # Run Make inside the build directory
    make_command = ["make", "-j"]
    subprocess.run(make_command, check=True)

    print(f"Build completed successfully! Build artifacts are in {build_dir}")

    return build_dir




def run_data_extractor(sift_folder, apps_folder):
    raw_edges_file = os.path.join(sift_folder, "res_raw_edges.bin")
    data_extractor = os.path.join(apps_folder, "tracking", "data_extractor")
    output_folder = os.path.join(sift_folder, "stats")

    os.makedirs(output_folder, exist_ok=True)

    extractor = [
        data_extractor,
        raw_edges_file,
        os.path.join(output_folder, 'r'),
        "latest_dist",
        "hop_dist",
        "distance_dist",
        "exact_conv"
    ]

    result = subprocess.run(extractor, stdout=None, stderr=None, text=True)
    if result.returncode != 0:
        print(f"Error in data extraction: {result.stderr}")
        return False



def run_and_parse_output(cmd, print_out=False):
    total_nodes = 0
    total_out_edges = 0
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    output_lines = []
    graph_pattern = re.compile(
        r"Index has\s+(\d+)\s+nodes\s+and\s+(\d+)\s+out-edges"
    )

    for line in iter(process.stdout.readline, ''):
        if print_out:
            print(line, end='')  # Print in real-time
        output_lines.append(line.strip())  # Store for later parsing
        graph_match = graph_pattern.search(line)
        if graph_match:
            total_nodes = int(graph_match.group(1))
            total_out_edges = int(graph_match.group(2))




    process.stdout.close()
    process.wait()

    if process.returncode != 0:
        print("Error running command:", process.stderr.read())
        return None

    # Parse output after printing
    data = []
    pattern = re.compile(r"\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")

    for line in output_lines:
        match = pattern.match(line)
        if match:
            data.append([float(match.group(i)) for i in range(1, 7)])  # Convert values to float

    if not data:
        print("No data extracted.")
        return []

    # columns = ["Ls", "QPS", "Avg dist cmps", "Mean Latency (mus)", "99.9 Latency", "Recall@10"]
    return data, total_nodes, total_out_edges


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent  # Current script directory
    parent_dir = current_dir.parent  # One level up

    print("Current directory:", current_dir)
    print("Parent directory:", parent_dir)

    tracking = False

    build_output = create_build(parent_dir, tracking=tracking)

    build_dir = os.path.join(parent_dir, "build")
    data_folder = os.path.join(build_dir, "data")
    apps_dir = os.path.join(build_output, "apps")

    os.makedirs(data_folder, exist_ok=True)
    download_sift(data_folder, apps_dir)

    sift_folder = os.path.join(data_folder, 'sift')

    # Paths to executables
    compute_groundtruth = os.path.join(apps_dir, "utils/compute_groundtruth")
    build_memory_index = os.path.join(apps_dir, "build_memory_index")
    search_memory_index = os.path.join(apps_dir, "search_memory_index")

    query_file_name = "sift_query.fbin"
    base_file_name = "sift_learn.fbin"
    gt_k = 100

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)
    query_file = os.path.join(sift_folder, query_file_name)
    gt_file = os.path.join(sift_folder, query_file+ f".gt_{str(gt_k)}")

    if not os.path.exists(gt_file):
        # Step 1: Compute ground truth
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

    l_base = [10, 20, 30, 40, 50, 100]

    print_out = False

    experiments = [
        {
            "ls":l_base,
            "alpha": 1.2,
            "r":32,
            "l_build":50
        },
        {
            "ls":l_base,
            "alpha": 1.2,
            "r":64,
            "l_build":50
        },
        {
            "ls":l_base,
            "alpha": 1.1,
            "r":32,
            "l_build":50
        },
        {
            "ls":l_base,
            "alpha": 1.1,
            "r":64,
            "l_build":50
        },
    ]

    for experiment in experiments:
        ls = experiment["ls"]
        r = experiment["r"]
        l_build = experiment['l_build']
        alpha = experiment["alpha"]

        exp_id = f"r{r}-a{alpha}"

        experiment_folder = os.path.join(sift_folder, exp_id)
        os.makedirs(os.path.join(sift_folder, exp_id), exist_ok=True)

        index_prefix = os.path.join(experiment_folder, f"index_{base_file_name.replace(".fbin",'')}_R{str(r)}_L{str(l_build)}_A{str(alpha)}")
        result_path = os.path.join(experiment_folder,"res")

        for i in range(len(ls)):
            ls[i] = str(ls[i])


        # Step 2: Build memory index
        cmd2 = [
            build_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--data_path", base_file,
            "--index_path_prefix", index_prefix,
            "-R", str(r),
            "-L", str(l_build),
            "--alpha", str(alpha)
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

        # Step 3: Search memory index
        cmd3 = [
            search_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--index_path_prefix", index_prefix,
            "--query_file", query_file,
            "--gt_file", gt_file,
            "-K", "10",
            "-L", *ls,
            "--result_path", result_path,
            "--num_threads", "1"
        ]

        results, nodes, out_edges = run_and_parse_output(cmd3, print_out=print_out)

        max_edges = nodes * r

        edges_used = (out_edges/max_edges) * 100


        print(f"\n\nAlpha: {alpha}, R: {r}")
        print(f"All steps completed successfully. {edges_used: >5.3f}% edges used")
        for result in results:
            print(f"{result[1]: >10.2f} QPS, for L : {result[0]}")

    if tracking:
        run_data_extractor(sift_folder, apps_dir)
        combined_plotter.plot_graphs(os.path.join(sift_folder, "stats"), 'r')
