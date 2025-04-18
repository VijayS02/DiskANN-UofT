from flask import Blueprint, request, jsonify, send_file
from services import stream_func
code_bp = Blueprint("code", __name__)


class DataProvider():
    def list_experiments(self):
        print("Hello")

    def list_indexes(self):
        pass

    def get_experiment(self,experiment_id):
        pass

    def load_query_metric(self, experiment_id, metric_id):
        pass

    def load_construction_metric(self, index_name, metric_id):
        pass

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