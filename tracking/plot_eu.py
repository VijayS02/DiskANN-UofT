import json
import matplotlib.pyplot as plt

def plot_utilization(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure(figsize=(10, 5))

    for test, utilization in data.items():
        x = [int(k) for k in utilization.keys()]  # Time steps
        y = [float(v) for v in utilization.values()]  # Utilization values

        plt.scatter(x, y, label=test)

    plt.xlabel('Time Step')
    plt.ylabel('Edge Utilization')
    plt.title('Edge Utilization Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    plot_utilization("../build/data/edge_util.json")
