#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt

def load_data(json_file):
    """
    Load data from a JSON file and return the parsed object.
    """
    with open(json_file, 'r') as f:
        return json.load(f)

# def plot_exact_conv(ax, data):
#     """
#     Plot for '_exact_conv.json' style data.
#     (Proportion of nodes visited vs. number of queries, log scale on y-axis)
#     """
#     for test, distances in data.items():
#         kv = sorted(distances.items(), key=lambda x: float(x[0]))
#         prop = [float(k) for k, _ in kv]
#         count = [int(v) for _, v in kv]
#         ax.plot(prop, count, marker='o', linestyle='-', label=test)
#
#     ax.set_xlabel("Proportion of nodes visited until best K nodes were found")
#     ax.set_ylabel("Number of queries")
#     ax.set_yscale('log')
#     ax.set_title("Convergence Step Distribution")
#     ax.legend()
#     ax.grid(True, linestyle="--", alpha=0.7)
#
# def plot_distance_distribution(ax, data):
#     """
#     Plot for '_distance_distribution.json' style data.
#     (Step in query vs. average distance)
#     """
#     for test, distances in data.items():
#         steps = [int(k) for k in distances.keys()]
#         avg_dist = [float(v) for v in distances.values()]
#         ax.scatter(steps, avg_dist, label=test, marker='o')
#
#     ax.set_xlabel("Step in Query (Node Visited)")
#     ax.set_ylabel("Average Distance")
#     ax.set_title("Average Distance per Step")
#     ax.legend()
#     ax.grid(True, linestyle="--", alpha=0.7)
#
# def plot_edge_visits(ax, data):
#     """
#     Plot for '_edge_visits.json' style data.
#     (Edge count rank vs. number of edges, log-log)
#     """
#     for test, distribution in data.items():
#         x = [int(k) for k in distribution.keys()]
#         y = [int(v) for v in distribution.values()]
#         ax.scatter(x, y, label=test, alpha=0.7)
#     ax.set_xlabel('Edge Count Rank')
#     ax.set_ylabel('Number of Edges')
#     ax.set_xscale('log')
#     ax.set_yscale('log')
#     ax.set_title('Edge Exploration Distribution')
#     ax.legend()
#     ax.grid(axis='y', linestyle='--', alpha=0.7)
#
# def plot_edge_utilization(ax, data):
#     """
#     Plot for '_edge_utilization.json' style data.
#     (Time step vs. edge utilization)
#     """
#     for test, utilization in data.items():
#         x = [int(k) for k in utilization.keys()]
#         y = [float(v) for v in utilization.values()]
#         ax.scatter(x, y, label=test)
#
#     ax.set_xlabel('Time Step')
#     ax.set_ylabel('Edge Utilization')
#     ax.set_title('Edge Utilization Over Time')
#     ax.legend()
#     ax.grid(True, linestyle="--", alpha=0.7)
#
# def plot_hop_distribution(ax, data):
#     """
#     Plot for '_hop_distribution.json' style data.
#     (Number of edges used vs. number of queries)
#     """
#     for test, distribution in data.items():
#         x = [int(k) for k in distribution.keys()]
#         y = [int(v) for v in distribution.values()]
#         ax.scatter(x, y, label=test, alpha=0.7)
#
#     ax.set_xlabel('Number of edges used')
#     ax.set_ylabel('Number of queries')
#     ax.set_title('Edge Exploration Distribution')
#     ax.grid(axis='y', linestyle='--', alpha=0.7)
#     ax.legend()
#
# def plot_latest_distribution(ax, data):
#     """
#     Plot for '_latest_distribution.json' style data.
#     (Proportion vs. number of queries, log scale)
#     """
#     for test, distances in data.items():
#         kv = sorted(distances.items(), key=lambda x: float(x[0]))
#         prop = [float(k) for k, _ in kv]
#         count = [int(v) for _, v in kv]
#         ax.plot(prop, count, marker='o', linestyle='-', label=test)
#
#     ax.set_xlabel("Proportion of nodes visited until lowest distance was found")
#     ax.set_ylabel("Number of queries")
#     ax.set_yscale('log')
#     ax.set_title("Convergence Step Distribution")
#     ax.legend()
#     ax.grid(True, linestyle="--", alpha=0.7)
#
# def plot_steps_distribution(ax, data):
#     """
#     Plot for '_steps_distribution.json' style data.
#     (Number of steps to converge vs. number of queries, y-axis log scale)
#     """
#     for test, steps in data.items():
#         x = [int(k) for k in steps.keys()]
#         y = [int(v) for v in steps.values()]
#         ax.plot(x, y, marker='o', linestyle='-', label=test)
#
#     ax.set_xlabel("Number of Steps Taken to Converge")
#     ax.set_ylabel("Number of Queries")
#     ax.set_yscale("log")
#     ax.set_title("Convergence Step Distribution")
#     ax.legend()
#     ax.grid(True, linestyle="--", alpha=0.7)
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


def main():
    """
    Main function that loads all data files, plots them into subplots on the same window,
    and shows the figure once at the end.
    """
    # Adjust paths to match your actual JSON file locations:
    data_exact_conv          = load_data("../build/data/_exact_conv.json")
    data_distance_distribution = load_data("../build/data/_distance_distribution.json")
    data_edge_visits         = load_data("../build/data/_edge_visits.json")
    data_edge_utilization    = load_data("../build/data/_edge_utilization.json")
    data_hop_distribution    = load_data("../build/data/_hop_distribution.json")
    data_latest_distribution = load_data("../build/data/_latest_distribution.json")
    data_steps_distribution  = load_data("../build/data/_steps_distribution.json")

    # Create a figure with enough subplots for all your plots.
    # We'll do 4 rows × 2 columns = 8 subplots, which is more than
    # your 7 needed. We'll remove or ignore the extra if not used.
    fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(14, 20))
    axes = axes.flatten()  # Flatten into a 1D array

    # 1) _exact_conv
    plot_generic_distribution(
        ax=axes[0],
        data=data_exact_conv,
        x_parser=float,
        y_parser=int,
        plot_type='line',
        x_label="Proportion of nodes visited until best K nodes were found",
        y_label="Number of queries",
        title="Convergence Step Distribution",
        y_log=True,    # Use log scale on y
        sort_x=True    # We want sorted x-values
    )

    # 2) _distance_distribution
    plot_generic_distribution(
        ax=axes[1],
        data=data_distance_distribution,
        x_parser=int,
        y_parser=float,
        plot_type='scatter',
        x_label="Step in Query (Node Visited)",
        y_label="Average Distance",
        title="Average Distance per Step",
        x_log=False,
        y_log=False,
        sort_x=False
    )

    # 3) _edge_visits
    plot_generic_distribution(
        ax=axes[2],
        data=data_edge_visits,
        x_parser=int,
        y_parser=int,
        plot_type='scatter',
        x_label="Edge Count Rank",
        y_label="Number of Edges",
        title="Edge Exploration Distribution",
        x_log=True,
        y_log=True,
        sort_x=False
    )

    # 4) _edge_utilization
    plot_generic_distribution(
        ax=axes[3],
        data=data_edge_utilization,
        x_parser=int,
        y_parser=float,
        plot_type='scatter',
        x_label="Time Step",
        y_label="Edge Utilization",
        title="Edge Utilization Over Time",
        x_log=False,
        y_log=False
    )

    # 5) _hop_distribution
    plot_generic_distribution(
        ax=axes[4],
        data=data_hop_distribution,
        x_parser=int,
        y_parser=int,
        plot_type='scatter',
        x_label="Number of edges used",
        y_label="Number of queries",
        title="Edge Exploration Distribution",
        x_log=False,
        y_log=False
    )

    # 6) _latest_distribution
    plot_generic_distribution(
        ax=axes[5],
        data=data_latest_distribution,
        x_parser=float,
        y_parser=int,
        plot_type='line',
        x_label="Proportion of nodes visited until lowest distance was found",
        y_label="Number of queries",
        title="Convergence Step Distribution",
        y_log=True,
        sort_x=True
    )

    # 7) _steps_distribution
    plot_generic_distribution(
        ax=axes[6],
        data=data_steps_distribution,
        x_parser=int,
        y_parser=int,
        plot_type='line',
        x_label="Number of Steps Taken to Converge",
        y_label="Number of Queries",
        title="Convergence Step Distribution",
        y_log=True
    )

    # Remove any extra subplot if needed (we made 8, but only used 7)
    fig.delaxes(axes[7])
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
