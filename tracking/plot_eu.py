import matplotlib.pyplot as plt

def plot_traces(file_name):
    traces = []  # List to store each trace
    current_trace = []  # Temporary list to store the current trace

    # Read the file and process the data
    with open(file_name, 'r') as file:
        for line in file:
            line = line.strip()
            if line == "!END_TRACE!":
                if current_trace:
                    traces.append(current_trace)  # Save the completed trace
                    current_trace = []  # Reset for the next trace
            else:
                try:
                    current_trace.append(float(line))  # Convert numbers to float
                except ValueError:
                    pass  # Ignore invalid lines

    plt.figure()
    plt.xlabel('Query (#)')
    plt.ylabel('Edge Utilization (%)')
    plt.title(f'Edge Utilization Graph')

    plt.grid(True)
    # Plot each trace
    for i, trace in enumerate(traces):
        plt.plot(range(len(trace)), trace, label=f'Query Set {i + 1}')

    plt.legend()

    plt.show()

# Usage

if __name__ == "__main__":
    plot_traces('../build/data/sift/res_track.txt')
