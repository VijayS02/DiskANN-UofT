//
// Created by vijay on 3/12/25.
//

#ifndef METRICS_H
#define METRICS_H
#include "tracking.h"


inline void TestTrack(int number)
{
    MetricTracker::Track("test", number);
    std::cout << "Testing number " << number << std::endl;
}


inline void StartConstruction(uint32_t range, uint32_t n_nodes )
{
    const nlohmann::json jsonData = {
        {"range", range},
        {"n_nodes", n_nodes}
    };

    MetricTracker::Track("construction_start", jsonData);
}

inline void EndConstruction()
{
    MetricTracker::Track("construction_end", true);
}

inline void AddEdgeCount(uint32_t number)
{
    MetricTracker::Track("add_edge_count", number);
}

inline void AddConstructionPathLength(uint32_t number)
{
    MetricTracker::Track("add_construction_path_length", number);
}

inline void EndQuery(float query_time)
{
    const nlohmann::json jsonData = {
        {"querytime", query_time},
    };
    MetricTracker::Track("end_query", jsonData);
}

inline void VisitedNode(uint32_t nodeId, float distance)
{
    const nlohmann::json jsonData = {
        {"nodeid", nodeId},
        {"distance", distance}
    };

    MetricTracker::Track("visited_node", jsonData);
}

inline void ConfigureExperimentQuery(size_t queries)
{
    const nlohmann::json jsonData = {
        {"queries", queries}
    };

    MetricTracker::Track("configure_experiment", jsonData);
}


inline void NodeInfo(uint32_t node, std::vector<float> neighbor_distances)
{
    const nlohmann::json jsonData = {
            {"neighbor_distances", neighbor_distances},
            {"nodeid", node},
        };

    MetricTracker::Track("node_info", jsonData);

}


#endif //METRICS_H
