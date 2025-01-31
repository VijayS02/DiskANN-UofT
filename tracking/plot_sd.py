import json
import matplotlib.pyplot as plt

def plot_convergence_steps(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    plt.figure(figsize=(10, 6))

    for test, steps in data.items():
        x = [int(step) for step in steps.keys()]  # Number of steps taken
        y = [int(count) for count in steps.values()]  # Number of queries

        plt.plot(x, y, marker='o', linestyle='-', label=test)

    plt.xlabel("Number of Steps Taken to Converge")
    plt.ylabel("Number of Queries")
    plt.title("Convergence Step Distribution")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    # plt.xscale("log")  # Log scale to handle large variations
    plt.yscale("log")
    plt.show()

if __name__ == "__main__":
    plot_convergence_steps("../build/data/_steps_distribution.json")  # Replace with actual JSON file path
