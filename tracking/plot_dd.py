import json
import matplotlib.pyplot as plt

def plot_avg_distance(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure(figsize=(10, 6))

    for test, distances in data.items():
        steps = [int(step) for step in distances.keys()]
        avg_distances = [float(dist) for dist in distances.values()]

        plt.scatter(steps, avg_distances, marker='o', linestyle='-', label=test)

    plt.xlabel("Step in Query (Node Visited)")
    plt.ylabel("Average Distance")
    plt.title("Average Distance per Step Across Queries")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()

if __name__ == "__main__":
    plot_avg_distance("../build/data/_distance_distribution.json")  # Replace with actual JSON file path
