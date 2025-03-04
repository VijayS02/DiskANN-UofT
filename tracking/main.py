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

import subprocess
import os

def run_sift_pipeline(sift_folder, apps_folder):
    # Paths to executables
    compute_groundtruth = os.path.join(apps_folder, "utils/compute_groundtruth")
    build_memory_index = os.path.join(apps_folder, "build_memory_index")
    search_memory_index = os.path.join(apps_folder, "search_memory_index")

    # Paths to dataset files
    base_file = os.path.join(sift_folder, "sift_learn.fbin")
    query_file = os.path.join(sift_folder, "sift_query.fbin")
    gt_file = os.path.join(sift_folder, "sift_query_learn_gt100")
    index_prefix = os.path.join(sift_folder, "index_sift_learn_R32_L50_A1.2")
    result_path = os.path.join(sift_folder, "res")

    # Step 1: Compute ground truth
    cmd1 = [
        compute_groundtruth,
        "--data_type", "float",
        "--dist_fn", "l2",
        "--base_file", base_file,
        "--query_file", query_file,
        "--gt_file", gt_file,
        "--K", "100"
    ]

    # Step 2: Build memory index
    cmd2 = [
        build_memory_index,
        "--data_type", "float",
        "--dist_fn", "l2",
        "--data_path", base_file,
        "--index_path_prefix", index_prefix,
        "-R", "32",
        "-L", "50",
        "--alpha", "1.2"
    ]

    # Step 3: Search memory index
    cmd3 = [
        search_memory_index,
        "--data_type", "float",
        "--dist_fn", "l2",
        "--index_path_prefix", index_prefix,
        "--query_file", query_file,
        "--gt_file", gt_file,
        "-K", "10",
        "-L", "10", "20", "30", "40", "50", "100",
        "--result_path", result_path,
        "--num_threads", "1"
    ]

    # Execute commands
    for i, cmd in enumerate([cmd1, cmd2, cmd3], 1):
        print(f"\n\nRunning step {i}: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=None, stderr=None, text=True)
        if result.returncode != 0:
            print(f"Error in step {i}: {result.stderr}")
            return False
        print(f"Step {i} completed successfully.")

    print("All steps completed successfully.")
    return True



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

    run_sift_pipeline(sift_folder, apps_dir)

    if tracking:
        run_data_extractor(sift_folder, apps_dir)
        combined_plotter.plot_graphs(os.path.join(sift_folder, "stats"), 'r')
