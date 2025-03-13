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


inline void StartConstruction()
{
    MetricTracker::Track("construction_start", true);
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

inline void EndQuery()
{
    MetricTracker::Track("end_query", true);
}

inline void VisitedNode(uint32_t nodeId, float distance)
{
    const nlohmann::json jsonData = {
        {"nodeid", nodeId},
        {"distance", distance}
    };

    MetricTracker::Track("visited_node", jsonData);
}




#endif //METRICS_H
