#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import os

def load_data(json_file):
    """
    Load data from a JSON file and return the parsed object.
    """
    with open(json_file, 'r') as f:
        return json.load(f)

def plot_generic_distribution(
        ax,
        data,
        x_parser=int,
        y_parser=float,
        plot_type='line',   # or 'scatter'
        x_label='X',
        y_label='Y',
        title='',
        x_log=False,
        y_log=False,
        sort_x=False,
        marker='o',
        alpha=0.7
):
    """
    A generic plotting function that can produce line or scatter plots
    from a dictionary-of-dictionaries. Each sub-dictionary is plotted
    as a separate series (labeled by its key).
    """
    for test_name, distribution in data.items():
        # distribution is typically a dict of { x_str: y_str }
        # We parse them using x_parser/y_parser
        x_vals = [x_parser(k) for k in distribution.keys()]
        y_vals = [y_parser(v) for v in distribution.values()]

        # Optionally sort on x (useful if the x-values are not inherently sorted)
        if sort_x:
            # zip them together, sort by x, then unzip
            xy_sorted = sorted(zip(x_vals, y_vals), key=lambda tup: tup[0])
            x_vals, y_vals = zip(*xy_sorted)

        if plot_type == 'line':
            ax.plot(x_vals, y_vals, marker=marker, linestyle='-', label=test_name)
        else:
            ax.scatter(x_vals, y_vals, marker=marker, alpha=alpha, label=test_name)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if x_log:
        ax.set_xscale('log')
    if y_log:
        ax.set_yscale('log')
    if title:
        ax.set_title(title)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)



def plot_graphs(data_folder, file_prefix):
    """
    Dynamically loads JSON data files matching the given prefix and plots them.
    """
    # Define possible suffixes and their plotting configurations
    file_configurations = {
        "_exact_conv.json":          (float, int, 'line', "Proportion of nodes visited until best K nodes were found", "Number of queries", "Convergence Step Distribution", False, True, True),
        "_distance_dist.json": (int, float, 'scatter', "Step in Query (Node Visited)", "Average Distance", "Average Distance per Step", False, False, False),
        "_edge_visits.json":          (int, int, 'scatter', "Edge Count Rank", "Number of Edges", "Edge Exploration Distribution", True, True, False),
        "_edge_utilization.json":     (int, float, 'scatter', "Time Step", "Edge Utilization", "Edge Utilization Over Time", False, False, False),
        "_hop_dist.json":     (int, int, 'scatter', "Number of edges used", "Number of queries", "Edge Exploration Distribution", False, False, False),
        "_latest_dist.json":  (float, int, 'line', "Proportion of nodes visited until lowest distance was found", "Number of queries", "Convergence Step Distribution", False, True, True),
        "_steps_distribution.json":   (int, int, 'line', "Number of Steps Taken to Converge", "Number of Queries", "Convergence Step Distribution", False, True, False),
    }

    # Find existing files
    available_files = {}
    for suffix in file_configurations.keys():
        file_path = os.path.join(data_folder, file_prefix + suffix)
        if os.path.exists(file_path):
            available_files[suffix] = file_path
            print(f"Found {file_path}")

    if not available_files:
        print("No matching files found.")
        return

    # Set up subplots dynamically based on available files
    num_plots = len(available_files)
    num_cols = 2  # Keep a two-column layout
    num_rows = (num_plots + num_cols - 1) // num_cols  # Round up
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(14, 5 * num_rows))

    if num_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Iterate through found files and plot
    for idx, (suffix, file_path) in enumerate(available_files.items()):
        data = load_data(file_path)
        if data is None:
            continue

        x_parser, y_parser, plot_type, x_label, y_label, title, x_log, y_log, sort_x = file_configurations[suffix]
        plot_generic_distribution(
            ax=axes[idx],
            data=data,
            x_parser=x_parser,
            y_parser=y_parser,
            plot_type=plot_type,
            x_label=x_label,
            y_label=y_label,
            title=title,
            x_log=x_log,
            y_log=y_log,
            sort_x=sort_x
        )

    # Hide unused subplots if any
    for i in range(num_plots, len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()
    plt.show()
