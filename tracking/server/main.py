import os
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import matplotlib
import psutil

from config import SOCKETIO, PROJECT_ROOT, build_lock, BUILD_DIR

from routes.file_routes import file_bp
from routes.index_routes import index_bp
from routes.query_routes import query_bp

from services import exec_build


matplotlib.use('Agg')

app = Flask(__name__)
SOCKETIO.init_app(app, cors_allowed_origins="*")

print(PROJECT_ROOT)


@app.route("/")
def index():
    return render_template("index.html")  # HTML UI


        
@app.route("/create_build", methods=["POST"])
def run_build():    
    exec_build(PROJECT_ROOT, tracking=True, type="Release")
    return "Build started! UI will update automatically."


@app.route("/status")
def status():
    stats = {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory": psutil.virtual_memory()._asdict(),
    }

    # You can still include your build_dir info if you like
    if build_lock.acquire(blocking=False):
        try:
            if BUILD_DIR and os.path.exists(BUILD_DIR):
                stats["build_dir"] = BUILD_DIR
            else:
                stats["build_dir"] = "NONE"
        finally:
            build_lock.release()
    else:
        stats["build_dir"] = "LOCKED"
        
app.register_blueprint(file_bp)
app.register_blueprint(index_bp)
app.register_blueprint(query_bp)


if __name__ == "__main__":
    SOCKETIO.run(app, debug=True)
