import numpy as np
from flask import Blueprint, request, jsonify, send_file
from services import stream_func
import os 
from config import RESULT_PATH, INDEX_DIR, INDEX_PREFIX, SOCKETIO, SANDBOX_GRAPHS
import json
import pandas as pd
import msgpack


from lib.read_utils import load_graph_from_binary
from lib.tracker import convert_numpy_to_python

code_bp = Blueprint("code", __name__, url_prefix='/code')


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
        exp_folder = os.path.join(RESULT_PATH, experiment_id)
        if not os.path.exists(exp_folder):
            raise ValueError("Experiment does not exist")

        parquet_file = os.path.join(exp_folder, parquet_name) + ".parquet"
        if not os.path.exists(parquet_file):
            raise ValueError("Parquet file does not exist")
        
        return pd.read_parquet(parquet_file)

    def load_construction_metric(self, index_name, parquet_name):
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



@stream_func
def execute_user_code(code: str, data_provider):
    exec_globals = {
        "dpAPI": data_provider,
        "__builtins__": __builtins__,  # caution: restrict if needed
        "plot": plot
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