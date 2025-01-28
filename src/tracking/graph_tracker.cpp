#include "tracking/graph_tracker.h"
#include <iostream>
#include <fstream>


//
// Created by vijay on 1/27/25.
//

vector<vector<pair<uint32_t,uint32_t>>> GraphTracker::graph_history = {};
vector<pair<uint32_t,uint32_t>> GraphTracker::current_query = {};
int GraphTracker::total_edges = 0;
unordered_map<pair<uint32_t, uint32_t>, long, PairHash> GraphTracker::edge_counts = {};
long GraphTracker::unique_visits = 0;
pair<long, pair<uint32_t,uint32_t>> GraphTracker::max_visited_edge = make_pair(0, make_pair(0, 0));
string GraphTracker::trace_file_name;
std::ofstream GraphTracker::trace_file;

vector<long> GraphTracker::edge_distributions = {};


string GraphTracker::distribution_file_name;
std::ofstream GraphTracker::distribution_file;


void GraphTracker::InitializeTracker(const string& traceFileName, const string& rawEdgeFileName){
    trace_file_name = traceFileName;
    trace_file.open(traceFileName);

    if (!trace_file.is_open()) {
        std::cerr << "Failed to open the trace (EU) file." << std::endl;
    }

    distribution_file_name = rawEdgeFileName;
    distribution_file.open(distribution_file_name);

    if (!distribution_file.is_open()) {
        std::cerr << "Failed to open the distribution file." << std::endl;
    }

}


void GraphTracker::EndTracker(){
    trace_file.close();
    distribution_file.close();
}


void GraphTracker::TraceRoute(uint32_t const id1, uint32_t const id2) {
    current_query.emplace_back(make_pair(id1, id2));
}

void GraphTracker::write_query_stats()
{
    if (!trace_file.is_open())
    {
        return;
    }

    trace_file << (static_cast<float>(unique_visits) / static_cast<float>(total_edges)) << endl;
}

void GraphTracker::EndQuery()
{
    for (auto pair : current_query)
    {
        edge_counts[pair]++;
        if (edge_counts[pair] == 1)
        {
            unique_visits++;
        }
        if (edge_counts[pair] > max_visited_edge.first)
        {
            max_visited_edge.first = edge_counts[pair];
            max_visited_edge.second = pair;
        }
    }
    graph_history.push_back(std::move(current_query));
    write_query_stats();
}

void GraphTracker::ClearTraces(){
    cout << "Unique Edges used: " << unique_visits << ", Max Edge Util: " << max_visited_edge.first << endl;
    cout << "Edge Utilization: " << (float(unique_visits) / float(total_edges)) * 100 << "%" << endl;


    edge_distributions.reserve(max_visited_edge.first + 1);

    for (int i =0; i < max_visited_edge.first + 1; i++)
    {
        edge_distributions.push_back(0);

    }

    for (auto edge: edge_counts)
    {
        edge_distributions[edge.second]++;
    }

    edge_distributions[0] = total_edges - unique_visits;

    unique_visits = 0;
    max_visited_edge.first = 0;
    edge_counts.clear();
    graph_history.clear();

    if (!trace_file.is_open()) {
        return;
    }

    trace_file << "!END_TRACE!" << endl;

    if (!distribution_file.is_open())
    {
        return;
    }

    for (auto item: edge_distributions)
    {
        distribution_file << item << endl;
    }

    distribution_file << "!END_TRACKER!" << endl;
}

void GraphTracker::SetTotalEdges(int totalEdges){
    total_edges = totalEdges;
    if (distribution_file.is_open())
    {
        distribution_file << total_edges << endl;
    }
}





