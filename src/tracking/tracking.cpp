//
// Created by vijay on 3/12/25.
//

#ifndef TRACKING_H
#define TRACKING_H
#ifdef DISKANN_TRACKING_ENABLED

#include "tracking/tracking.h"

#include <utility>

// Define static members
zmq::context_t MetricTracker::context(1);
zmq::socket_t MetricTracker::socket(context, ZMQ_PUSH);
bool MetricTracker::is_initialized = false;

void MetricTracker::initialize(const std::string& connection_str, int max_qs)
{
    if (!is_initialized)
    {
        max_queries_details = max_qs;
        if (connection_str == "NONE")
        {
            std::cout << "TRACKING DISABLED." << std::endl;
            return;
        }
        std::cout << "Initializing Metric Tracker with connection: " << connection_str << std::endl;
        try {
            socket.set(zmq::sockopt::sndhwm, 1000000);

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
        // std::cerr << "Tracking not initialized" << std::endl;
        return;
    }

    try {
        nlohmann::json payload;
        payload["metric_name"] = metric_name;
        payload["value"] = std::move(value);

        std::string message = payload.dump();
        zmq::message_t zmq_msg(message.begin(), message.end());
        socket.send(zmq_msg, zmq::send_flags::none);
    } catch (const std::exception& e) {
        std::cout << e.what() << std::endl;
    }
}

#endif

#endif //TRACKING_H
