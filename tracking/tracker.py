import zmq
import json

# Set up ZeroMQ receiver
context = zmq.Context()
socket = context.socket(zmq.PULL)

# Allow reusing the address
socket.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout after 5 seconds
socket.setsockopt(zmq.LINGER, 0)       # Avoid hanging on close

try:
    socket.bind("tcp://*:5555")  # Allow external connections too
except zmq.error.ZMQError as e:
    print(f"Error binding to port: {e}")
    exit(1)

print("Listening for messages on port 5555...")

while True:
    try:
        msg = socket.recv_string()
        data = json.loads(msg)  # Parse JSON
        print("Received:", data)
    except zmq.Again:
        print("No message received, retrying...")
    except json.JSONDecodeError:
        print("Invalid JSON format received, skipping...")
