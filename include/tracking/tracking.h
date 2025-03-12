#ifndef TRACKING_HPP
#define TRACKING_HPP
#include "json.hpp"

#ifdef DISKANN_TRACKING_ENABLED
#include "zmq.hpp"
#include <string>
#include <iostream>

class MetricTracker
{
private:
  static zmq::socket_t socket;
  static zmq::context_t context;
  static bool is_initialized;

  MetricTracker() {}; // Private constructor to prevent instantiation

public:
  static void initialize(const std::string& connection_str);
  static void Track(const std::string& metric_name, nlohmann::json value);
};
#else
class MetricTracker
{
private:

  MetricTracker() {};

public:
  static void initialize(const std::string& connection_str) {};
  static void Track(const std::string& metric_name, nlohmann::json value) {}
};
#endif


#endif //TRACKING_HPP
