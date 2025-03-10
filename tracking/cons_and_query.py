import os
from util import create_build, download_sift, run_and_parse_output

import subprocess

print_out = True

def gen_id(params):
    return f"t_{"1" if params.get('tracking', False) else "0"}_r_{params['r']}_a_{params['alpha']}"


if __name__ == "__main__":
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    print("BASE directory:", parent_dir)

    num_trials = 15  # Number of times each experiment is repeated

    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    print("BASE directory:", parent_dir)

    build_dir = os.path.join(parent_dir, "build")
    data_folder = os.path.join(build_dir, "data")
    build_output = os.path.join(parent_dir, "build", "script_output")
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

    if not os.path.exists(compute_groundtruth):
        create_build(parent_dir)

    # Paths to dataset files
    base_file = os.path.join(sift_folder, base_file_name)
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

    l_base = [10]

    experiments = [
        {
            "ls": l_base,
            "alpha": 1.2,
            "r": 32,
            "l_build": 50,
            "tracking": False,
            "saturate_graph": False
        },
    ]

    RESULTS = dict()

    for experiment in experiments:
        tracking = experiment.get("tracking", False)
        ls = experiment["ls"]
        r = experiment["r"]
        l_build = experiment['l_build']
        alpha = experiment["alpha"]
        saturate_graph = experiment.get("saturate_graph", False)
        exp_id = gen_id(experiment)

        build_output = create_build(parent_dir, tracking=tracking)

        experiment_folder = os.path.join(sift_folder, exp_id)
        os.makedirs(experiment_folder, exist_ok=True)

        index_prefix = os.path.join(experiment_folder, f"index_{base_file_name.replace('.fbin', '')}_R{str(r)}_L{str(l_build)}_A{str(alpha)}")
        result_path = os.path.join(experiment_folder, "res")

        qps_results = {l: [] for l in ls}
        recall_results = {l: [] for l in ls}

        for trial in range(num_trials):
            print(f"Running trial {trial+1}/{num_trials} for experiment {exp_id}...")
            tracking_path = os.path.join(experiment_folder, "tracking.bin")
            tracking_args = ["--tracking_path", tracking_path] if tracking else []

            cmd2 = [
                build_memory_index,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--data_path", base_file,
                "--index_path_prefix", index_prefix,
                *tracking_args,
                "-R", str(r),
                "-L", str(l_build),
                "--alpha", str(alpha),
                "--num_threads", "1",
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



            cmd3 = [
                search_memory_index,
                "--data_type", "float",
                "--dist_fn", "l2",
                "--index_path_prefix", index_prefix,
                "--query_file", query_file,
                "--gt_file", gt_file,
                "-K", "10",
                "--saturate_graph" if saturate_graph else "",
                "-L", *[str(l) for l in ls],
                "--result_path", result_path,
                "--num_threads", "1"
            ]

            results, nodes, out_edges = run_and_parse_output(cmd3, print_out=print_out)

            for i, result in enumerate(results):
                RESULTS.setdefault(ls[i], {})
                RESULTS[ls[i]].setdefault("QPS", {}).setdefault(exp_id, []).append(result[1])
                RESULTS[ls[i]].setdefault("Recall", {}).setdefault(exp_id, []).append(result[5])

        # Remove non-json files
        for f in os.listdir(experiment_folder):
            if not f.endswith(".json"):
                os.remove(os.path.join(experiment_folder, f))

    print(RESULTS)
    print("\n\n")

    for l in RESULTS:
        for metric in RESULTS[l]:
            for exp in RESULTS[l][metric]:
                average = sum(RESULTS[l][metric][exp]) / num_trials
                print(f"AVG {metric} for {exp} with L={l}: {average}")

