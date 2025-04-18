from config import UPLOADS_DIR, INDEX_DIR, RESULT_PATH, GT_FILES, BUILD_DIR, INDEX_PREFIX, SOCKETIO, build_lock, operation_lock
import os
import io 
import sys 
import threading
import subprocess
import json
import hashlib
import time
from datetime import datetime
from query_tracker import initialize_query_tracker
from construction_tracker import initialize_construction_tracker
from lib.read_utils import get_bin_file_info, count_edges_from_binary, load_graph_from_binary
from lib.util import create_build


class StreamWrapper(io.TextIOBase):
    """Custom stream to capture stdout and forward to WebSocket."""
    def __init__(self):
        self.buffer = []
        
    def write(self, message):
        if message.strip():  # Ignore empty messages
            # Directly emit to socketio without using a queue
            SOCKETIO.emit("terminal_output", {"status": message.strip()})
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
                with operation_lock:
                    # Run the function and store result
                    result_container['value'] = func(*args, **kwargs)
            except Exception as e:
                # Capture any errors
                error_msg = f"ERROR: {str(e)}"
                # print stack trace
                import traceback
                traceback.print_exc()
                SOCKETIO.emit("terminal_output", {"status": error_msg})
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

    gt_file = os.path.join(GT_FILES, f"{hash_file(base_file)}_{hash_file(query_file)}_{gt_k}.gt")

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
def exec_build(*args, **kwargs):
    global BUILD_DIR
    with build_lock:
        BUILD_DIR = create_build(*args, **kwargs)


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

    parquets = tracker.generate_parquet(index_path)


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
            "parquets": parquets,
            "edges": count_edges_from_binary(os.path.join(index_path, INDEX_PREFIX + "_graph.bin")),
            "saturate_graph": saturate_graph,
            "metrics": metrics,
            "output_types": tracker.generate_output_dict()
        }))


    # tracker.generate_graphs(index_path)
    # print("Graph construction complete!")
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
    index_info = json.load(open(os.path.join(index_path, "index_info.json"))) if os.path.exists(os.path.join(index_path, "index_info.json")) else None

    nodes, _ = get_bin_file_info(query_file)

    tracker = initialize_query_tracker(metrics, result_path,index_info=index_info, graph=graph)
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

    parquets = tracker.generate_parquet(result_path)
    
    # tracker.generate_json_graphs(os.path.join(result_path, "graphs.msgpack"))

    # tracker.generate_graphs(result_path)

    # json_data = tracker.generate_json()

    # tracker.generate_text()

    
    # Create json file with data about query:
    with open(os.path.join(result_path, "query_info.json"), "w") as f:
        f.write(json.dumps({
            "id": current_time,
            "index_name": index_info["index_name"],
            "query_file": query_file_name,
            "l": l,
            "k": k,
            "n": nodes,
            "directory": result_path,
            "metrics": metrics,
            "parquets": parquets,
            "time": int(datetime.now().timestamp()),
            "output_types": tracker.generate_output_dict(),
            "individual_types": tracker.generate_output_dict(single_query=True),
            "individual_count": 10
        }))
    
    print("Query complete!")
    return "Query complete!"


