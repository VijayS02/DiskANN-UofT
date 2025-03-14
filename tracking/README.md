# DiskANN Tracker

## Requirements

 - [Libmzq](https://github.com/zeromq/libzmq)
 - Linux


## Description

This branch of DiskANN contains tracking code that traces both `search_memory_index` and `build_memory_index`.

In order to trace events in the DiskANN code, a ZeroMQ server is hosted by DiskANN and then exposed for python scripts to
connect and pull information from.

There are 3 python files which run different things:
 - [`query_tests.py`](./query_tests.py) : This python file executes the search and build functions without executing tracking code. 
 - [`query_tracker.py`](./query_tracker.py) : Query tracker runs the build and search functions with tracking enabled, but only query functions are traced.
 - [`construction_tracker.py`](./construction_tracker.py) : Construction tracker traces the build phase of in-memory indexes. 

## Modifications

 - [`CMakeLists.txt`](../CMakeLists.txt) has been modified to include a new build option `-DTRACKING_ENABLED` which enables or disables the tracing code in DiskANN. 
 - [`include/tracking/*`](../include/tracking) has header files which include `json` + `zmq` header files. 
 - [`src/tracking/*`](../src/tracking) has the corresponding cpp files for the above header files.
 - [`src/index.cpp`](../src/index.cpp) has been modified to send various trace signals, see [Tracing](#Tracing) for more.
 - [`apps/build_memory_index.cpp`](../apps/build_memory_index.cpp) now includes CLI options to `saturate_graph` and set tracing server config.
 - [`apps/search_memory_index.cpp`](../apps/search_memory_index.cpp) now includes CLI options set tracing server config.

## Tracing
Tracing code should not need to be modified in order to work. There already exists some basic tracing in `index.cpp`. In order to add more signals, the following has to be done:

1) Modify [`include/tracking/metrics.h`](../include/tracking/metrics.h) to have a new inline function like the other ones existing. The 2nd argument to `MetricTracker::Track` accepts a json object.
2) Add the tracing code along the code path somewhere. (*Note:If the tracer is not initialized, tracing will not work. In order to initialize the tracer in new programs, follow `build_memory_index.cpp:97`*)
3) Create a corresponding `AbstractMetricTracker` (Either an `AbstractQueryTracker` for queries or `AbstractConstructionTracker` for construction). Read the documentation of the `AbstractMetricTracker` to understand how it operates better.
4) Initialize your new MetricTracker and provide it to the `QueryTrackerRunner` or `ConstructionTrackingRunner`. (*Note that I have created some basic generic trackers in [`basic_metric_types.py`](lib/basic_metric_types.py))
5) Modify the experiments to your needs, run and see results!