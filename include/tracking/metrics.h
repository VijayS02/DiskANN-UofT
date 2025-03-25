//
// Created by vijay on 3/12/25.
//

#ifndef METRICS_H
#define METRICS_H
#include "tracking.h"

inline std::vector<uint32_t> best_k = {};
inline int best_k_counter = 0;
inline uint32_t *ground_truth_ids = nullptr;
inline float *ground_truth_dists = nullptr;
inline uint32_t ground_truth_dim = 0;
inline uint32_t recall_at = 0;


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

inline void EndQuery(uint32_t i, float query_time)
{
    uint32_t *gt_vec = ground_truth_ids + ground_truth_dim * i;
    size_t tie_breaker = recall_at;
    if (ground_truth_dists != nullptr)
    {
        tie_breaker = recall_at - 1;
        float *gt_dist_vec = ground_truth_dists + ground_truth_dim * i;
        while (tie_breaker < ground_truth_dim && gt_dist_vec[tie_breaker] == gt_dist_vec[recall_at - 1])
            tie_breaker++;
    }

    std::set<uint32_t> gt(gt_vec, gt_vec + tie_breaker);

    const nlohmann::json jsonData = {
        {"querytime", query_time},
        {"best_k", best_k},
        {"ground_truth", gt}
    };
    MetricTracker::Track("end_query", jsonData);
    best_k.clear();
    best_k_counter++;
}

inline void VisitedNode(uint32_t nodeId, float distance)
{
    const nlohmann::json jsonData = {
        {"nodeid", nodeId},
        {"distance", distance}
    };

    MetricTracker::Track("visited_node", jsonData);
}

inline void ConfigureExperimentQuery(size_t queries, uint32_t *gt_ids, float *gt_dists, uint32_t dim, uint32_t recall)
{
    const nlohmann::json jsonData = {
        {"queries", queries}
    };

    ground_truth_dists = gt_dists;
    ground_truth_ids = gt_ids;
    ground_truth_dim = dim;
    recall_at = recall;

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

inline void AddBestK(uint32_t id)
{
    if (best_k_counter < MetricTracker::max_queries_details)
    {
        best_k.push_back(id);
    }
}


#endif //METRICS_H
