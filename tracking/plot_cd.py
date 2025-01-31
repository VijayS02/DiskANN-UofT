import json
import matplotlib.pyplot as plt

def plot_avg_distance(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure(figsize=(10, 6))


    for test, distances in data.items():
        kv = [(k, distances[k]) for k in distances]
        kv = sorted(kv, key=lambda x: x[0])
        prop = [float(item[0]) for item in kv]
        count = [int(item[1]) for item in kv]

        plt.plot(prop, count, marker='o', linestyle='-', label=test)

    plt.xlabel("Proportion of nodes visited until best K nodes were found")
    plt.ylabel("Number of queries")
    plt.title("Convergence Step Distribution")
    plt.yscale('log')
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()

if __name__ == "__main__":
    plot_avg_distance("../build/data/_exact_conv.json")  # Replace with actual JSON file path
