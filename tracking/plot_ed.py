import json
import matplotlib.pyplot as plt

def plot_from_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure()
    for test, distribution in data.items():
        # res = [(int(k), int(distribution[k])) for k in distribution]
        #
        # res = sorted(res, key=lambda item: item[0])
        # x = []
        # y = []
        # for i, v in enumerate(res):
        #     x.append(i)
        #     y.append(v[1])

        x = [int(k) for k in distribution.keys()]  # Times explored
        y = [int(v) for v in distribution.values()]  # Edge counts


        plt.scatter(x, y, label=test, alpha=0.7)
        # plt.savefig(f"{test.replace(' ', '_')}.png")  # Save as PNG
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xlabel('Edge Count Rank')
    plt.legend()
    plt.ylabel('Number of Edges')
    plt.xscale('log')
    plt.yscale('log')
    plt.title(f'Edge Exploration Distribution')
    plt.show()

if __name__ == "__main__":
    plot_from_json('../build/data/_edge_visits.json')
