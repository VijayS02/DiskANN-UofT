

from flask import Blueprint, request, jsonify, send_file
import os
from config import UPLOADS_DIR, build_lock, BUILD_DIR, RESULT_PATH, INDEX_DIR
import json
from services import trace_query
from query_tracker import get_available_query_metrics

query_bp = Blueprint("query", __name__)

@query_bp.route("/query_index", methods=["POST"])
def query_graph():
    """Start the query process in a separate thread."""
    data = request.get_json()

    # Validate required parameters
    required_params = ["index_name", "query_file"]
    missing_params = [param for param in required_params if param not in data]

    if missing_params:
        return jsonify({"error": f"Missing required parameters: {', '.join(missing_params)}"}), 400

    # Extract parameters
    index_name = data["index_name"]
    query_file = data["query_file"]
    l = data.get("l", 50)
    k = data.get("k", 10)
    metrics = data.get("metrics", [])

    index_path = os.path.join(INDEX_DIR, index_name)

    if build_lock.acquire(blocking=False):
        if not os.path.exists(BUILD_DIR):
            build_lock.release()
            return "Build not started. Please start the build first.", 400
        build_lock.release()
        trace_query(index_path, query_file, l=l, k=k, metrics=metrics)
        return jsonify({"message": "Query started! UI will update automatically."}), 200
        
    else:
        return jsonify({"error": "Build operation in progress"}), 423

@query_bp.route("/results_list")
def get_results():
    if not os.path.exists(RESULT_PATH):
        return jsonify({"results": []})
    results = os.listdir(RESULT_PATH)
    results = [os.path.join(RESULT_PATH, result) for result in results]
    results = [result for result in results if os.path.exists(os.path.join(result, "query_info.json"))]
    results = [json.load(open(os.path.join(result, "query_info.json"))) for result in results]
    return jsonify({"results": results})


@query_bp.route("/query_image/<path:id>/<path:metric>")
def get_image(id, metric):
    image_path = os.path.join(RESULT_PATH, id, f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")

@query_bp.route("/query_json/<path:id>")
def get_json(id):
    json_path = os.path.join(RESULT_PATH, id, "query_info.json")
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))

@query_bp.route("/query_msgpack_graphs/<path:id>")
def get_msg_pack_query(id):
    json_path = os.path.join(RESULT_PATH, id, "graphs.msgpack")
    
    if not os.path.exists(json_path):
        return 404
    
    return send_file(json_path, mimetype="application/msgpack", as_attachment=False)

@query_bp.route("/indv_query_json/<path:id>/<path:query_id>")
def get_query_ind_json(id, query_id):
    json_path = os.path.join(RESULT_PATH, id, f"query_{query_id}", f"metrics.json")
    print(json_path)
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))

@query_bp.route("/indv_query_image/<path:id>/<path:query_id>/<path:metric>")
def get_query_ind_image(id, query_id, metric):
    image_path = os.path.join(RESULT_PATH, id, f"query_{query_id}", f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")


@query_bp.route("/query_metrics")
def get_query_metrics():
    return jsonify(get_available_query_metrics())