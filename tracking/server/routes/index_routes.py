from flask import Blueprint, request, jsonify, send_file
import os
from config import UPLOADS_DIR, build_lock, BUILD_DIR, RESULT_PATH, INDEX_DIR
import json
from services import construct_graph
from construction_tracker import get_available_construction_metrics

index_bp = Blueprint("index", __name__)


@index_bp.route("/create_graph", methods=["POST"])
def create_graph():
    """Start the build process in a separate thread."""
    data = request.get_json()

    # Validate required parameters
    required_params = ["index_name", "base_file"]
    missing_params = [param for param in required_params if param not in data]

    if missing_params:
        return jsonify({"error": f"Missing required parameters: {', '.join(missing_params)}"}), 400

    # Extract parameters
    index_name = data["index_name"]
    base_file = data["base_file"]
    r = data.get("r", 32)  # Default 32
    l_build = data.get("l_build", 50)  # Default 50
    alpha = data.get("alpha", 1.2)  # Default 1.2
    saturate_graph = data.get("saturate_graph", True)  # Default True
    metrics = data.get("metrics", [])

    if build_lock.acquire(blocking=False):
        if BUILD_DIR is None:
            build_lock.release()
            return "Build not started. Please start the build first.", 400
        build_lock.release()
    else:
        return jsonify({"error": "Build operation in progress"}), 423
     
    construct_graph(index_name, base_file, r=r, l_build=l_build, alpha=alpha, saturate_graph=saturate_graph, metrics=metrics)

    return jsonify({"message": "Graph construction started! UI will update automatically."}), 200

@index_bp.route("/list_indexes")
def list_indexes():
    if not os.path.exists(INDEX_DIR):
        return jsonify({"indexes": []
        })
    indexes = os.listdir(INDEX_DIR)
    # Load json files with data about indexes
    indexes = [os.path.join(INDEX_DIR, index) for index in indexes]
    indexes = [index for index in indexes if os.path.exists(os.path.join(index, "index_info.json"))]
    indexes = [json.load(open(os.path.join(index, "index_info.json"))) for index in indexes]
    return jsonify({"indexes": indexes})

@index_bp.route("/index_json/<path:id>")
def get_index_json(id):
    json_path = os.path.join(INDEX_DIR, id, "index_info.json")
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))


@index_bp.route("/index_image/<path:id>/<path:metric>")
def get_index_image(id, metric):
    image_path = os.path.join(INDEX_DIR, id, f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")

@index_bp.route("/construction_metrics")
def get_construction_metrics():
    return jsonify(get_available_construction_metrics())