import struct
import csv

def load_graph_from_binary(filename):
    """Reads a binary graph file and reconstructs the adjacency list."""
    with open(filename, "rb") as f:
        num_nodes = struct.unpack("I", f.read(4))[0]
        
        graph = {}  # Change from list to dict
        for i in range(num_nodes):
            degree = struct.unpack("I", f.read(4))[0]
            neighbors = list(struct.unpack(f"{degree}I", f.read(4 * degree)))
            graph[i] = neighbors  # Store in a dictionary
    
    print(len(graph))
    return graph

def count_edges_from_binary(filename):
    """
    Reads a binary graph file and counts the number of edges efficiently.
    
    Args:
        filename (str): Path to the binary file.
    
    Returns:
        int: Total number of edges.
    """
    total_edges = 0
    with open(filename, "rb") as f:
        num_nodes = struct.unpack("I", f.read(4))[0]  # Read number of nodes

        for _ in range(num_nodes):
            degree = struct.unpack("I", f.read(4))[0]  # Read degree
            total_edges += degree  # Count edges
            f.read(4 * degree)  # Skip neighbors in the file

    return total_edges

def get_bin_file_info(filename):
    """
    Reads a binary file and returns the number of nodes (points) and their dimensions.
    
    Args:
        filename (str): Path to the binary file.
    
    Returns:
        tuple: (Number of nodes, Number of dimensions per node)
    """
    with open(filename, "rb") as f:
        # Read first 8 bytes: [4 bytes for npts] + [4 bytes for ndims]
        npts, ndims = struct.unpack("ii", f.read(8))  # Read two int32 values
        return npts, ndims

def load_graph_from_csv(filename):
    """Reads a CSV file and returns a graph as an adjacency list (dict[int, list[int]])."""
    graph = {}
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            node = int(row[0])
            neighbors = list(map(int, row[1:])) if len(row) > 1 else []
            graph[node] = neighbors
    print(len(graph))
    return graph

def compare_graphs(graph1, graph2):
    """
    Compares two adjacency list graphs and prints differences.
    Checks for:
    1. Missing nodes in either graph.
    2. Different neighbors for the same node.
    """
    nodes1, nodes2 = set(graph1.keys()), set(graph2.keys())

    # Find missing nodes
    missing_in_g2 = nodes1 - nodes2
    missing_in_g1 = nodes2 - nodes1

    if missing_in_g2:
        print(f"Nodes in Graph 1 but missing in Graph 2: {sorted(missing_in_g2)}")
    if missing_in_g1:
        print(f"Nodes in Graph 2 but missing in Graph 1: {sorted(missing_in_g1)}")

    # Find differing edges
    common_nodes = nodes1 & nodes2
    for node in common_nodes:
        neighbors1 = set(graph1[node])
        neighbors2 = set(graph2[node])

        added = neighbors2 - neighbors1
        removed = neighbors1 - neighbors2

        if added:
            print(f"Node {node}: Added neighbors in Graph 2 -> {sorted(added)}")
        if removed:
            print(f"Node {node}: Removed neighbors in Graph 2 -> {sorted(removed)}")

    if not missing_in_g1 and not missing_in_g2 and not any(added or removed for node in common_nodes):
        print("Graphs are identical.")
