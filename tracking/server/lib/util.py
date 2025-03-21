import os
import subprocess 
from pathlib import Path
import matplotlib.pyplot as plt

import re
import urllib.request
import tarfile
import sys

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

    process = subprocess.Popen(
        cmake_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True
    )

    for line in process.stdout:
        sys.stdout.write(line)  # Write to WebSocket (via stdout redirection)
        sys.stdout.flush()

    for line in process.stderr:
        sys.stderr.write(line)  # Write stderr to WebSocket
        sys.stderr.flush()

    process.wait()  # Wait for subprocess to complete

    print("\n\nRunning make...")

    # Run Make inside the build directory
    make_command = ["make", "-j"]

    process = subprocess.Popen(
        make_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True
    )

    for line in process.stdout:
        sys.stdout.write(line)  # Forward to WebSocket
        sys.stdout.flush()

    for line in process.stderr:
        sys.stderr.write(line)  # Forward stderr to WebSocket
        sys.stderr.flush()

    process.wait()

    print(f"Build completed successfully! Build artifacts are in {build_dir}")

    return build_dir

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


def plot_generic_distribution(ax, data, graph_props, label):
    """
    A generic plotting function that can produce line or scatter plots
    using graph properties defined in the JSON file.
    """
    x_label = graph_props.get("x_label", "X")
    y_label = graph_props.get("y_label", "Y")
    title = graph_props.get("title", "")
    x_log = graph_props.get("x_log", False)
    y_log = graph_props.get("y_log", False)
    sort_x = graph_props.get("sort_x", False)
    plot_type = graph_props.get("type", "line")
    marker = graph_props.get("marker", 'o')

    # Set labels
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    if x_log:
        ax.set_xscale('log')
    if y_log:
        ax.set_yscale('log')

    # Plot all series in the data
    x_vals = list(map(float, data.keys()))
    y_vals = list(map(float, data.values()))

    # Sort if necessary
    if sort_x:
        x_vals, y_vals = zip(*sorted(zip(x_vals, y_vals)))

    if plot_type == "line":
        ax.plot(x_vals, y_vals, marker=marker, linestyle='-', label=label)
    else:
        ax.scatter(x_vals, y_vals, marker=marker, alpha=0.7, label=label)

    ax.grid(True, linestyle='--', alpha=0.7)

