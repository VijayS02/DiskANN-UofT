import os
import threading
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
from lib.util import create_build
from dotenv import load_dotenv
import sys
import io
import subprocess
from construction_tracker import initialize_tracking_runner
import time 

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow WebSockets

PROJECT_ROOT = os.getenv("DISK_ANN_ROOT")
STORAGE_ROOT = os.getenv("STORAGE_ROOT")

UPLOADS_DIR = os.path.join(STORAGE_ROOT, "uploads")
INDEX_DIR = os.path.join(STORAGE_ROOT, "indexes")

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
                socketio.emit("terminal_output", {"status": error_msg})
                result_container['error'] = e
            finally:
                # Restore original stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        
        # Create and start the thread
        thread = threading.Thread(target=run_func)
        thread.start()
        thread.join()  # Wait for thread to complete
        
        # If there was an error, raise it
        if result_container['error']:
            raise result_container['error']
            
        # Return the result
        return result_container['value']
        
    return wrapper

@stream_func
def construct_graph(index_name, base_file, r=32, l_build=50, alpha=1.2, saturate_graph=True):
    print(f"BUILD DIR: {BUILD_DIR}")
    if not os.path.exists(base_file):
        print("Base File does not exist")
        return "Base File does not exist", 400
    os.makedirs(INDEX_DIR, exist_ok=True)
    index_path = os.path.join(INDEX_DIR, index_name)
    os.makedirs(index_path, exist_ok=True)
    index_path = os.path.join(index_path, "index")
    build_memory_index = os.path.join(BUILD_DIR, "apps", "build_memory_index")
    tracker = initialize_tracking_runner()
    tracking_port = 5555
    command = [
            build_memory_index,
            "--data_type", "float",
            "--dist_fn", "l2",
            "--data_path", base_file,
            "--index_path_prefix", index_path,
            "-R", str(r),
            "-L", str(l_build),
            "--alpha", str(alpha),
            "--num_threads", "1",
            "--tracking_addr", f"tcp://localhost:{tracking_port}",
            "--saturate_graph" if saturate_graph else "",
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

    return "Graph construction complete!", 200

@app.route("/")
def index():
    return render_template("index.html")  # HTML UI

@app.route("/create_build")
def run_build():
    global BUILD_DIR
    
    with build_lock:
        BUILD_DIR = stream_func(create_build)(PROJECT_ROOT, tracking=True, type="Release")
    return "Build started! UI will update automatically."

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    os.makedirs(UPLOADS_DIR,
                exist_ok=True)
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

    with build_lock:
        if BUILD_DIR is None:
            return "Build not started. Please start the build first.", 400

    return construct_graph(index_name, base_file, r=r, l_build=l_build, alpha=alpha, saturate_graph=saturate_graph)

@app.route("/list_indexes")
def list_indexes():
    indexes = os.listdir(INDEX_DIR)
    return jsonify({"indexes": indexes})


if __name__ == "__main__":
    socketio.run(app, debug=True)
