import json
import os
import threading
from flask import Flask, jsonify, render_template, request, send_file
from flask_socketio import SocketIO
from lib.util import create_build
from dotenv import load_dotenv
import sys
import io
import subprocess
from construction_tracker import get_available_construction_metrics, initialize_construction_tracker
from query_tracker import get_available_query_metrics, initialize_query_tracker 
import time
import hashlib
from datetime import datetime
import matplotlib

from lib.read_utils import get_bin_file_info, load_graph_from_binary
matplotlib.use('Agg')



load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow WebSockets

PROJECT_ROOT = os.getenv("DISK_ANN_ROOT")
STORAGE_ROOT = os.getenv("STORAGE_ROOT")

UPLOADS_DIR = os.path.join(STORAGE_ROOT, "uploads")
INDEX_DIR = os.path.join(STORAGE_ROOT, "indexes")
GT_FILES = os.path.join(STORAGE_ROOT, "gt_files")
RESULT_PATH = os.path.join(STORAGE_ROOT, "results")
INDEX_PREFIX = "index"

os.makedirs(STORAGE_ROOT, exist_ok=True)

default_build = os.path.join(PROJECT_ROOT, "build", 'script_output')

BUILD_DIR = default_build if os.path.exists(default_build) else None
build_lock = threading.Lock() 

print(PROJECT_ROOT)

class StreamWrapper(io.TextIOBase):
    """Custom stream to capture stdout and forward to WebSocket."""
    def __init__(self):
        self.buffer = []
        
    def write(self, message):
        if message.strip():  # Ignore empty messages
            # Directly emit to socketio without using a queue
            socketio.emit("terminal_output", {"status": message.strip()})
            self.buffer.append(message.strip())
            
    def flush(self):
        pass  # No buffering needed
        
    def get_output(self):
        return "\n".join(self.buffer)

def stream_func(func):
    """Decorator to run `func` in a thread and stream output to WebSockets."""
    def wrapper(*args, **kwargs):
        # Create a result container that will be set from the thread
        result_container = {'value': None, 'error': None}
        
        # Save original stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        # Create stream wrapper
        stream = StreamWrapper()
        
        # Function to run in thread
        def run_func():
            # Redirect stdout/stderr
            sys.stdout = stream
            sys.stderr = stream
            
            try:
                # Run the function and store result
                result_container['value'] = func(*args, **kwargs)
            except Exception as e:
                # Capture any errors
                error_msg = f"ERROR: {str(e)}"
                # print stack trace
                import traceback
                traceback.print_exc()
                socketio.emit("terminal_output", {"status": error_msg})
                result_container['error'] = e
            finally:
                # Restore original stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        
        # Create and start the thread
        thread = threading.Thread(target=run_func)
        thread.start()

        # Return the result
        return result_container['value']
        
    return wrapper


def hash_file(file_path):
    BUF_SIZE = 65536
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()


def generate_gt_file(base_file, query_file, query_k):
    gt_k = max(query_k + 20, 100)
    os.makedirs(GT_FILES, exist_ok=True)

    gt_file = os.path.join(GT_FILES, f"{hash_file(query_file)}_{gt_k}.gt")

    if not os.path.exists(gt_file):
        compute_groundtruth = os.path.join(BUILD_DIR, "apps", 'utils', "compute_groundtruth")
        command = [
            compute_groundtruth,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--base_file", base_file,
            "--query_file", query_file,
            "--gt_file", gt_file,
            "--K", str(gt_k)
        ]
        process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
            )

        for line in process.stdout:
            sys.stdout.write(line)  # Write to WebSocket (via stdout redirection)
            sys.stdout.flush()

        for line in process.stderr:
            sys.stderr.write(line)  # Write stderr to WebSocket
            sys.stderr.flush()

        # Wait for completion
        process.wait()

        time.sleep(1)

        if process.returncode != 0:
            raise Exception("Error computing ground truth")

    else:
        print("Ground truth file already exists, skipping gt calculation.")

    return gt_file



@stream_func
def construct_graph(index_name, base_file_name, r=32, l_build=50, alpha=1.2, saturate_graph=True, metrics=[]):
    print(f"BUILD DIR: {BUILD_DIR}")
    
    os.makedirs(INDEX_DIR, exist_ok=True)
    index_path = os.path.join(INDEX_DIR, index_name)
    base_file = os.path.join(UPLOADS_DIR, base_file_name)

    if not os.path.exists(base_file):
        print("Base File does not exist")
        return "Base File does not exist", 400

    os.makedirs(index_path, exist_ok=True)
    index_prefix = os.path.join(index_path, INDEX_PREFIX)
    build_memory_index = os.path.join(BUILD_DIR, "apps", "build_memory_index")
    tracker = initialize_construction_tracker(metrics)
    tracking_port = 5555
    nodes, ndims = get_bin_file_info(base_file)

    command = [
            build_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--data_path", base_file,
            "--index_path_prefix", index_prefix,
            "-R", str(r),
            "-L", str(l_build),
            "--alpha", str(alpha),
            "--num_threads", "1",
            "--tracking_addr", f"tcp://localhost:{tracking_port}",
            "--saturate_graph" if saturate_graph else "",
            "--output_graph"
        ]
    
    print(command)

    def trace_function():
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
        )

        for line in process.stdout:
            sys.stdout.write(line)  # Write to WebSocket (via stdout redirection)
            sys.stdout.flush()

        for line in process.stderr:
            sys.stderr.write(line)  # Write stderr to WebSocket
            sys.stderr.flush()

        # Wait for completion
        process.wait()

        # Give time for any final messages to be received
        time.sleep(1)

        return {
            "exit_code": process.returncode,
        }

    tracker.trace_program(index_name, trace_function, tracking_port=tracking_port)

    # Create json file with data about index:
    with open(os.path.join(index_path, "index_info.json"), "w") as f:
        f.write(json.dumps({
            "index_name": index_name,
            "base_file": base_file_name,
            "r": r,
            "l_build": l_build,
            "alpha": alpha,
            "n": nodes,
            "dimensions": ndims,
            "saturate_graph": saturate_graph,
            "metrics": metrics,
            "output_types": tracker.generate_output_dict()
        }))

    tracker.generate_graphs(index_path)
    print("Graph construction complete!")
    return "Graph construction complete!"

@stream_func
def trace_query(index_path, query_file_name, l=50, k=10, metrics=[]):
    if not os.path.exists(index_path):
        return "Index does not exist", 400
    
    query_file = os.path.join(UPLOADS_DIR, query_file_name)
    
    if not os.path.exists(query_file):
        return "Query file does not exist", 400

    os.makedirs(RESULT_PATH, exist_ok=True)
    
    current_time = datetime.now().strftime("%d%m%y_%H%M%S")
    result_path = os.path.join(RESULT_PATH, f"{current_time}")

    os.makedirs(result_path, exist_ok=True)

    # Load index info 
    with open(os.path.join(index_path, "index_info.json"), "r") as f:
        index_info = json.load(f)

    # TODO: Base file may change since index creation. Need to handle this
    # Maybe copy the base file to the index directory?
    base_file = os.path.join(UPLOADS_DIR, index_info["base_file"])
    gt_file = generate_gt_file(base_file, query_file, k)
    
    search_memory_index = os.path.join(BUILD_DIR, "apps", "search_memory_index")
    # Send results to /dev/null to avoid cluttering the output

    graph_file = os.path.join(index_path, INDEX_PREFIX + "_graph.bin")
    graph = load_graph_from_binary(graph_file)

    tracker = initialize_query_tracker(metrics, result_path, graph=graph)
    tracking_port = 5555
    command = [
        search_memory_index,
        "--data_type", "float",
        "--dist_fn", "l2",
        "--index_path_prefix", os.path.join(index_path, INDEX_PREFIX),
        "--query_file", query_file,
        "--gt_file", gt_file,
        "-K", str(k),
        "-L", str(l),
        "--result_path", RESULT_PATH,
        "--num_threads", "1",
        "--tracking_addr", f"tcp://localhost:{tracking_port}", 
        "--collect_queries_data", "100",
    ]
    
    def exec_func():
            # Search command with all the arguments
            print(f"Executing: {' '.join(command)}")

            # Run the build command
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
            )

            for line in process.stdout:
                sys.stdout.write(line)  # Write to WebSocket (via stdout redirection)
                sys.stdout.flush()

            for line in process.stderr:
                sys.stderr.write(line)  # Write stderr to WebSocket
                sys.stderr.flush()

            # Wait for completion
            process.wait()

            # Give time for any final messages to be received
            time.sleep(1)

            return {
                "exit_code": process.returncode,
            }


    ret = tracker.trace_program('query_run', exec_func, tracking_port=tracking_port)
    print(ret)
    tracker.generate_graphs(result_path)

    json_data = tracker.generate_json()

    tracker.generate_text()
    # Create json file with data about query:
    with open(os.path.join(result_path, "query_info.json"), "w") as f:
        f.write(json.dumps({
            "id": current_time,
            "index_name": index_info["index_name"],
            "query_file": query_file_name,
            "l": l,
            "k": k,
            "directory": result_path,
            "data": json_data,
            "metrics": metrics,
            "time": int(datetime.now().timestamp()),
            "output_types": tracker.generate_output_dict(),
            "individual_types": tracker.generate_output_dict(single_query=True),
            "individual_count": 10
        }))
    
    print("Query complete!")
    return "Query complete!"




@app.route("/")
def index():
    return render_template("index.html")  # HTML UI

@stream_func
def exec_build(*args, **kwargs):
    global BUILD_DIR
    with build_lock:
        BUILD_DIR = create_build(*args, **kwargs)
        
@app.route("/create_build", methods=["POST"])
def run_build():    
    exec_build(PROJECT_ROOT, tracking=True, type="Release")
    return "Build started! UI will update automatically."

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:  # 🔹 Check if the file key exists
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':  # 🔹 Check if a file was actually selected
        return jsonify({"error": "No selected file"}), 400

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    file.save(file_path)
    
    return jsonify({"message": "File uploaded successfully", "path": file_path})

@app.route('/uploads')
def list_files():
    files = os.listdir(UPLOADS_DIR)
    return jsonify({"files": files})

@app.route("/create_graph", methods=["POST"])
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

@app.route("/list_indexes")
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


@app.route("/status")
def status():
    if build_lock.acquire(blocking=False):
        try:
            if BUILD_DIR and os.path.exists(BUILD_DIR):
                return jsonify({"build_dir": BUILD_DIR}), 200
            return jsonify({"build_dir": "NONE"}), 200
        finally:
            # Always release the lock
            build_lock.release()
    else:
        # Lock couldn't be acquired immediately
        return jsonify({"error": "Build operation in progress"}), 423 
        


@app.route("/query_index", methods=["POST"])
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
        if BUILD_DIR is None:
            build_lock.release()
            return "Build not started. Please start the build first.", 400
        build_lock.release()
        trace_query(index_path, query_file, l=l, k=k, metrics=metrics)
        return jsonify({"message": "Query started! UI will update automatically."}), 200
        
    else:
        return jsonify({"error": "Build operation in progress"}), 423
        
@app.route("/download")
def download_file():
    return send_file("/home/vijay/Documents/DiskANN-UofT/tracking/server/storage/indexes/csv_test/index.txt", as_attachment=True)


@app.route("/results_list")
def get_results():
    if not os.path.exists(RESULT_PATH):
        return jsonify({"results": []})
    results = os.listdir(RESULT_PATH)
    results = [os.path.join(RESULT_PATH, result) for result in results]
    results = [result for result in results if os.path.exists(os.path.join(result, "query_info.json"))]
    results = [json.load(open(os.path.join(result, "query_info.json"))) for result in results]
    return jsonify({"results": results})


@app.route("/query_image/<path:id>/<path:metric>")
def get_image(id, metric):
    image_path = os.path.join(RESULT_PATH, id, f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")

@app.route("/query_json/<path:id>")
def get_json(id):
    json_path = os.path.join(RESULT_PATH, id, "query_info.json")
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))

@app.route("/indv_query_json/<path:id>/<path:query_id>")
def get_query_ind_json(id, query_id):
    json_path = os.path.join(RESULT_PATH, id, f"query_{query_id}", f"metrics.json")
    print(json_path)
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))

@app.route("/indv_query_image/<path:id>/<path:query_id>/<path:metric>")
def get_query_ind_image(id, query_id, metric):
    image_path = os.path.join(RESULT_PATH, id, f"query_{query_id}", f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")

@app.route("/index_json/<path:id>")
def get_index_json(id):
    json_path = os.path.join(INDEX_DIR, id, "index_info.json")
    
    if not os.path.exists(json_path):
        return 404
    
    return jsonify(json.load(open(json_path)))


@app.route("/index_image/<path:id>/<path:metric>")
def get_index_image(id, metric):
    image_path = os.path.join(INDEX_DIR, id, f"{metric}.png")
    
    if not os.path.exists(image_path):
        return 404  # Return 404 if the image doesn't exist
    
    return send_file(image_path, mimetype="image/png")

@app.route("/construction_metrics")
def get_construction_metrics():
    return jsonify(get_available_construction_metrics())



@app.route("/query_metrics")
def get_query_metrics():
    return jsonify(get_available_query_metrics())


if __name__ == "__main__":
    socketio.run(app, debug=True)
