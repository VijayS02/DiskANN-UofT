//
// Created by vijay on 3/12/25.
//

#ifndef TRACKING_H
#define TRACKING_H
#include "tracking/tracking.h"

// Define static members
zmq::context_t MetricTracker::context(1);
zmq::socket_t MetricTracker::socket(context, ZMQ_PUSH);
bool MetricTracker::is_initialized = false;

void MetricTracker::initialize(const std::string& connection_str)
{
    if (!is_initialized)
    {
        try {
            // Set the linger option to ensure messages are delivered
            socket.set(zmq::sockopt::linger, 1000);  // 1 second linger period

            // Set reconnect options - will try to connect until successful
            socket.set(zmq::sockopt::reconnect_ivl, -1);  // -1 means block until connected

            std::cout << "Connecting to " << connection_str << "..." << std::endl;
            socket.connect(connection_str);
            is_initialized = true;
            std::cout << "Successfully connected to " << connection_str << std::endl;
        } catch (const zmq::error_t& e) {
            std::cerr << "Failed to initialize tracking: " << e.what() << std::endl;
        }
    }
}

void MetricTracker::Track(const std::string& metric_name, nlohmann::json value)
{
    if (!is_initialized)
    {
        std::cerr << "Tracking not initialized" << std::endl;
        return;
    }

    try {
        nlohmann::json payload;
        payload["metric_name"] = metric_name;
        payload["value"] = value;
        payload["type"] = value.type_name();

        std::string message = payload.dump();
        zmq::message_t zmq_msg(message.begin(), message.end());
        socket.send(zmq_msg, zmq::send_flags::none);
    } catch (const std::exception& e) {
        std::cout << e.what() << std::endl;
    }
}


#endif //TRACKING_H
