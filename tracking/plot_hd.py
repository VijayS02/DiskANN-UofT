import json
import matplotlib.pyplot as plt

def plot_from_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure()
    for test, distribution in data.items():
        x = [int(k) for k in distribution.keys()]  # Number of edges used
        y = [int(v) for v in distribution.values()]  # Freq


        plt.scatter(x, y, label=test, alpha=0.7)
        # plt.savefig(f"{test.replace(' ', '_')}.png")  # Save as PNG
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xlabel('Number of edges used')
    plt.legend()
    plt.ylabel('Frequency')
    # plt.xscale('log')
    # plt.yscale('log')
    plt.title(f'Edge Exploration Distribution')
    plt.show()

if __name__ == "__main__":
    plot_from_json('../build/data/_hop_distribution.json')
