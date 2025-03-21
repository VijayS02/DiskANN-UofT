import os
import subprocess
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
from lib.util import create_build
from dotenv import load_dotenv
import sys
import io

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow WebSockets

PROJECT_ROOT = os.getenv("DISK_ANN_ROOT")

BUILD_DIR = None
build_lock = threading.Lock() 

print(PROJECT_ROOT)

class StreamWrapper(io.TextIOBase):
    """Custom stream to capture stdout and forward to WebSocket."""
    def __init__(self, emit_event):
        self.emit_event = emit_event

    def write(self, message):
        if message.strip():  # Ignore empty messages
            socketio.emit("terminal_output", {"status": message.strip()})

    def flush(self):
        pass  # No buffering needed

def stream_func(func):
    def wrapper(*args, **kwargs):
        """Redirects stdout/stderr and runs `create_build()` directly."""
        # Save original stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            # Redirect stdout and stderr
            sys.stdout = StreamWrapper("terminal_output")
            sys.stderr = StreamWrapper("terminal_output")
            
            func(*args, **kwargs)


        finally:
            # Restore original stdout/stderr after build
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    return wrapper


@stream_func
def execute_build(*args, **kwargs):
    with build_lock:
        BUILD_DIR = create_build(*args, **kwargs)

@app.route("/")
def index():
    return render_template("index.html")  # HTML UI

@app.route("/create_build")
def run_build():
    """Start the build process in a separate thread."""
    thread = threading.Thread(target=execute_build, args=(PROJECT_ROOT,), kwargs={"tracking": True, "type": "Release"})
    thread.start()
    return "Build started! UI will update automatically."


if __name__ == "__main__":
    socketio.run(app, debug=True)
