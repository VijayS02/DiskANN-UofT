import numpy as np
from flask import Blueprint, request, jsonify, send_file
from services import stream_func
import os 
from config import RESULT_PATH, INDEX_DIR, INDEX_PREFIX, SOCKETIO, SANDBOX_GRAPHS, SANDBOX_CODE, UPLOADS_DIR
import json
import pandas as pd
import msgpack
import msgpack_numpy as m
import heapq
from tqdm import tqdm

m.patch()



from lib.read_utils import load_bin_to_numpy, load_graph_from_binary
from lib.tracker import convert_numpy_to_python

code_bp = Blueprint("code", __name__, url_prefix='/code')

def compute_dist(v1, v2):
    return np.sum((v1 - v2) ** 2)


def extract_edges_simple(visited_order, graph):
    seen = set([visited_order[0]])
    parents = {}  # child -> parent
    edges = []

    for node in visited_order:
        for neighbor in graph.get(node, []):
            if neighbor not in seen:
                seen.add(neighbor)
                parents[neighbor] = node
        
        parent = parents.get(node, -1)
        edges.append((parent, node))

    return edges[1:]



class DataProvider():
    def list_experiments(self):
        if not os.path.exists(RESULT_PATH):
            return []
        results = os.listdir(RESULT_PATH)
        results = [os.path.join(RESULT_PATH, result) for result in results]
        results = [result for result in results if os.path.exists(os.path.join(result, "query_info.json"))]
        results = [json.load(open(os.path.join(result, "query_info.json"))) for result in results]
        return results

    def list_indexes(self):
        if not os.path.exists(INDEX_DIR):
            return []
        indexes = os.listdir(INDEX_DIR)
        # Load json files with data about indexes
        indexes = [os.path.join(INDEX_DIR, index) for index in indexes]
        indexes = [index for index in indexes if os.path.exists(os.path.join(index, "index_info.json"))]
        indexes = [json.load(open(os.path.join(index, "index_info.json"))) for index in indexes]
        return indexes

    def get_experiment(self,experiment_id):
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        if not os.path.exists(exp_folder):
            raise ValueError("Experiment does not exist")
        return json.load(open(os.path.join(exp_folder, "query_info.json")))

    def load_query_metric(self, experiment_id, parquet_name):
        print("Loading query metric")
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        if not os.path.exists(exp_folder):
            raise ValueError("Experiment does not exist")

        parquet_file = os.path.join(exp_folder, parquet_name) + ".parquet"
        if not os.path.exists(parquet_file):
            raise ValueError("Parquet file does not exist")
        
        return pd.read_parquet(parquet_file)

    def load_construction_metric(self, index_name, parquet_name):
        print("Loading construction metric")
        index_dir = os.path.join(INDEX_DIR, index_name)
        if not os.path.exists(index_dir):
            raise ValueError("Index does not exist")

        parquet_file = os.path.join(index_dir, parquet_name) + ".parquet"
        if not os.path.exists(parquet_file):
            raise ValueError("Parquet file does not exist")
        
        return pd.read_parquet(parquet_file)
    
    def get_graph(self, index_name):
        index_dir = os.path.join(INDEX_DIR, index_name)
        if not os.path.exists(index_dir):
            raise ValueError("Index does not exist")
        graph_file = os.path.join(index_dir, INDEX_PREFIX + "_graph.bin")
        graph = load_graph_from_binary(graph_file)
        return graph
    
    def get_latest_experiment(self):
        exps = os.listdir(RESULT_PATH)
        exps = [os.path.join(RESULT_PATH, result) for result in exps]
        exps = [result for result in exps if os.path.exists(os.path.join(result, "query_info.json"))]
        exps = [json.load(open(os.path.join(result, "query_info.json"))) for result in exps]
        return sorted(exps, key=lambda x: x['time'])[-1]


    def load_vectors_bin(self, filename):
        filepath = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(filepath):
            raise RuntimeError("Cannot find file to load")
        return load_bin_to_numpy(filepath)

    def load_query_vectors(self, experiment_id):
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        if not os.path.exists(exp_folder):
            raise ValueError("Experiment does not exist")
        exp_info = json.load(open(os.path.join(exp_folder, "query_info.json")))
        file = exp_info['query_file']
        return self.load_vectors_bin(file)
        

    def get_used_edges(self, experiment_id):
        exp = self.get_experiment(experiment_id)
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        os.makedirs(exp_folder, exist_ok=True)

        used_edges_file = os.path.join(exp_folder, "used_edges.parquet")

        # Load if already computed
        if os.path.exists(used_edges_file):
            print("Loading precomputed used edges")
            return pd.read_parquet(used_edges_file)

        visited_df = self.load_query_metric(experiment_id, 'visited_node')
        graph = self.get_graph(exp['index_name'])

        all_edges = []

        for qid, group in tqdm(visited_df.groupby("qid", sort=True), desc="Computing used edges"):
            edges = extract_edges_simple(group['nodeid'].to_numpy(dtype=np.uint32), graph)
            for parent, node in edges:
                all_edges.append((parent, node, qid))

        df = pd.DataFrame(all_edges, columns=["parent", "node", "qid"])
        df.to_parquet(used_edges_file, index=False)
        print("Stored used edges to disk as parquet")

        return df
    
    def get_useful_edges(self, experiment_id):
        exp = self.get_experiment(experiment_id)
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        os.makedirs(exp_folder, exist_ok=True)

        useful_edges_file = os.path.join(exp_folder, "useful_edges.parquet")

        # Load if already computed
        if os.path.exists(useful_edges_file):
            print("Loading precomputed useful edges")
            return pd.read_parquet(useful_edges_file)

        # Load data once outside the loop
        visited_df = self.load_query_metric(experiment_id, 'visited_node')
        end_queries = self.load_query_metric(exp['id'], 'end_query')
        graph = self.get_graph(exp['index_name'])
        
        # Create a lookup dictionary for best_k values to avoid repeated lookups
        best_k_dict = dict(zip(end_queries["qid"], end_queries["best_k"]))
        
        useful_edges = []

        # Process all queries at once by grouping
        for qid, group in tqdm(visited_df.groupby("qid", sort=True), desc="Computing useful edges"):
            best_k = best_k_dict[qid]
            visited_order = group['nodeid'].to_numpy(dtype=np.uint32)
            
            # Optimized version of extract_useful_edges
            seen = set([visited_order[0]])
            parents = {}
            
            # Build parent map
            for node in visited_order:
                for neighbor in graph.get(node, []):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        parents[neighbor] = node
            
            # Process best_k nodes
            visited = set()
            edges_for_query = []
            
            for node in best_k:
                current = np.uint32(node)
                while current in parents and current not in visited:
                    visited.add(current)
                    parent = parents[current]
                    edges_for_query.append((parent, current, qid))
                    current = np.uint32(parent)
            
            useful_edges.extend(edges_for_query)

        # Convert to DataFrame once at the end
        df = pd.DataFrame(useful_edges, columns=["parent", "node", "qid"])
        df.to_parquet(useful_edges_file, index=False)
        print("Stored useful edges to disk as parquet")

        return df

    def load_index_vectors(self, index_name):
        index_dir = os.path.join(INDEX_DIR, index_name)
        if not os.path.exists(index_dir):
            raise ValueError("Index does not exist")
        index_info = json.load(open(os.path.join(index_dir, "index_info.json")))
        index_file = index_info['base_file']
        return self.load_vectors_bin(index_file)

dp = DataProvider()

def plot(filename, y, x=None, title="Plot"):

    meta = {
        "type": "line",
        "props" : {"title": title},
    }

    if x is None:
        x = np.arange(len(y))
    
    filename = filename.replace(".msgpack", "") + ".msgpack"
    

    graph_info = {"data": (x,y),  "meta": meta}
    # Recursively convert all NumPy data before writing
    data_serializable = convert_numpy_to_python(graph_info)

    file_path = os.path.join(SANDBOX_GRAPHS, filename)
    # Write using MessagePack
    with open(file_path, "wb") as f:  # Use "wb" since msgpack writes binary data
        f.write(msgpack.packb(data_serializable))
    SOCKETIO.emit("new_graph", {"filename": filename})

def hist(filename, counts, title="Histogram", ylog=False):

    meta = {
        "type": "hist",
        "props" : {"title": title, "ylog":ylog},
    }
    
    filename = filename.replace(".msgpack", "") + ".msgpack"
    

    graph_info = {"data": counts,  "meta": meta}
    # Recursively convert all NumPy data before writing
    data_serializable = convert_numpy_to_python(graph_info)

    file_path = os.path.join(SANDBOX_GRAPHS, filename)
    # Write using MessagePack
    with open(file_path, "wb") as f:  # Use "wb" since msgpack writes binary data
        f.write(msgpack.packb(data_serializable))
    SOCKETIO.emit("new_graph", {"filename": filename})



api = {
    "plot": plot,
    "hist": hist
}

@stream_func
def execute_user_code(code: str, data_provider):
    exec_globals = {
        "dpAPI": data_provider,
        "__builtins__": __builtins__,  # caution: restrict if needed
        **api
    }
    print(">>>Running python:")
    exec(code, exec_globals)
    
@code_bp.route("/graph/<path:filename>")
def get_sandbox_graph(filename):
    filename = filename.replace(".msgpack", "") + ".msgpack"
    json_path = os.path.join(SANDBOX_GRAPHS, filename)
    
    if not os.path.exists(json_path):
        return 404
    
    return send_file(json_path, mimetype="application/msgpack", as_attachment=False)

@code_bp.route("/list_graphs")
def list_sandbox_graphs():
    return os.listdir(SANDBOX_GRAPHS)

@code_bp.route('/exec', methods=['POST'])
def exec_route():
    code = request.json.get("code", "")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # Starts async threaded execution, output is streamed
    execute_user_code(code, dp)

    # Return immediately to frontend
    return jsonify({"status": "started"})

@code_bp.route("/code_file/create", methods=["POST"])
def create_code_file():
    filename = request.json.get("filename", "")
    if not filename.endswith(".py"):
        filename += ".py"

    file_path = os.path.join(SANDBOX_CODE, filename)
    
    if os.path.exists(file_path):
        return jsonify({"error": "File already exists"}), 409
    
    with open(file_path, "w") as f:
        f.write("# New Python file\n")

    return jsonify({"status": "created", "filename": filename})


@code_bp.route("/code_file/save", methods=["POST"])
def save_code_file():
    filename = request.json.get("filename", "")
    content = request.json.get("content", "")

    if not filename.endswith(".py"):
        filename += ".py"
    
    file_path = os.path.join(SANDBOX_CODE, filename)

    with open(file_path, "w") as f:
        f.write(content)

    return jsonify({"status": "saved", "filename": filename})


@code_bp.route("/code_file/delete", methods=["POST"])
def delete_code_file():
    filename = request.json.get("filename", "")

    if not filename.endswith(".py"):
        filename += ".py"

    file_path = os.path.join(SANDBOX_CODE, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File does not exist"}), 404

    os.remove(file_path)

    return jsonify({"status": "deleted", "filename": filename})

@code_bp.route("/code_file/list", methods=["GET"])
def list_code_files():
    files = [
        f for f in os.listdir(SANDBOX_CODE)
        if f.endswith(".py") and os.path.isfile(os.path.join(SANDBOX_CODE, f))
    ]
    return jsonify(files)

@code_bp.route("/code_file/get", methods=["POST"])
def get_code_file():
    filename = request.json.get("filename", "")
    
    if not filename.endswith(".py"):
        filename += ".py"

    file_path = os.path.join(SANDBOX_CODE, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File does not exist"}), 404

    with open(file_path, "r") as f:
        content = f.read()

    return jsonify({"filename": filename, "content": content})
