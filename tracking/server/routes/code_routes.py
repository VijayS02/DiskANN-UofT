from flask import Blueprint, request, jsonify, send_file
from services import stream_func
import os 
from config import RESULT_PATH, INDEX_DIR, INDEX_PREFIX
import json
import pandas as pd

from lib.read_utils import load_graph_from_binary

code_bp = Blueprint("code", __name__)


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

@stream_func
def execute_user_code(code: str, data_provider):
    exec_globals = {
        "dpAPI": data_provider,
        "__builtins__": __builtins__,  # caution: restrict if needed
    }
    print("------------------   PYTHON   ------------------")
    exec(code, exec_globals)
    print("------------------ END PYTHON ------------------")

    print("Execution done!")
    


@code_bp.route('/exec', methods=['POST'])
def exec_route():
    code = request.json.get("code", "")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # Starts async threaded execution, output is streamed
    execute_user_code(code, dp)

    # Return immediately to frontend
    return jsonify({"status": "started"})