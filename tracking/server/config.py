import os
import threading
from dotenv import load_dotenv
from flask_socketio import SocketIO

SOCKETIO = SocketIO(cors_allowed_origins="*")
load_dotenv()

# Check if the environment variables are set
if not os.getenv("DISK_ANN_ROOT"):
    raise ValueError("DISK_ANN_ROOT is not set")

if not os.getenv("STORAGE_ROOT"):
    raise ValueError("STORAGE_ROOT is not set")

PROJECT_ROOT = os.getenv("DISK_ANN_ROOT")
STORAGE_ROOT = os.getenv("STORAGE_ROOT")

UPLOADS_DIR = os.path.join(STORAGE_ROOT, "uploads")
INDEX_DIR = os.path.join(STORAGE_ROOT, "indexes")
GT_FILES = os.path.join(STORAGE_ROOT, "gt_files")
RESULT_PATH = os.path.join(STORAGE_ROOT, "results")
SANDBOX_ROOT = os.path.join(STORAGE_ROOT, "sandbox")
INDEX_PREFIX = "index"

SANDBOX_GRAPHS = os.path.join(SANDBOX_ROOT, 'graphs')

os.makedirs(STORAGE_ROOT, exist_ok=True)
os.makedirs(SANDBOX_ROOT, exist_ok=True)
os.makedirs(SANDBOX_GRAPHS, exist_ok=True)

default_build = os.path.join(PROJECT_ROOT, "build", 'script_output')

BUILD_DIR = default_build
build_lock = threading.Lock() 

operation_lock = threading.Lock()