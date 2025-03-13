import time
from abc import abstractmethod
from typing import List, Dict

import zmq
import json
from tracking.abstract_trackers import AbstractConstructionTracker
import threading


class AbstractTrackingRunner:

    def __init__(self, port=5555, metric_handlers: List[AbstractConstructionTracker] = None):
        self.tracking_thread = None
        self.port = port
        self.metric_handlers : Dict[str, AbstractConstructionTracker] = dict()
        self.stop_tracking = False
        for metric_handler in metric_handlers:
            self.metric_handlers[metric_handler.get_metric_name()] = metric_handler


    @abstractmethod
    def handle_metric_event(self, data):
        pass

    def start_tracking_server(self, port=5556):
        """Start a ZMQ server in a separate thread to collect metrics"""
        self.stop_tracking = False

        def tracker_thread():
            context = zmq.Context()
            socket = context.socket(zmq.PULL)
            socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout for clean shutdown
            socket.setsockopt(zmq.LINGER, 0)

            try:
                socket.bind(f"tcp://*:{port}")
                print(f"Listening for metrics on port {port}...")

                while not self.stop_tracking:
                    try:
                        msg = socket.recv_string()
                        data = json.loads(msg)
                        self.handle_metric_event(data)
                    except zmq.Again:
                        # Timeout occurred, just continue
                        pass
                    except json.JSONDecodeError:
                        print("Invalid JSON format received, skipping...")

            except zmq.error.ZMQError as e:
                print(f"Error in ZMQ server: {e}")
            finally:
                socket.close()
                context.term()
                print("Tracking server stopped")

        self.tracking_thread = threading.Thread(target=tracker_thread)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()

    def stop_tracking_server(self):
        """Stop the ZMQ tracking server thread"""
        if self.tracking_thread:
            self.stop_tracking = True
            self.tracking_thread.join(timeout=5)
            self.tracking_thread = None


