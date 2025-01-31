#include "tracking/graph_tracker.h"

#include <cassert>
#include <iostream>
#include <fstream>

//
// Created by vijay on 1/27/25.
//

#include <boost/serialization/vector.hpp>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/utility.hpp>

vector<QueryTrace> GraphTracker::test_history = {};
QueryTrace GraphTracker::current_query = {};
int GraphTracker::total_edges = 0;
string GraphTracker::file_path;
vector<TestData> GraphTracker::total_history = {};
int GraphTracker::current_l = 0;
vector<uint32_t> GraphTracker::best_k_nodes = {};
int GraphTracker::step_num = 0;
int GraphTracker::k = 0;
int GraphTracker::converge_step = 0;

void saveToFile(const vector<TestData>& data, int total_edges, const string& filename) {
    cout << "Writing to file " << filename << endl;
    FullTrace trace = {
    data, total_edges };
    // Open file for binary output
    ofstream ofs(filename, ios::binary);
    if (!ofs) {
        throw runtime_error("Failed to open file for writing.");
    }

    // Create Boost binary archive
    boost::archive::binary_oarchive oa(ofs);

    // Serialize data
    oa << trace;

    ofs.close();

    cout << "Finished saving to " << filename << endl;
}

void GraphTracker::InitializeTracker(const string& filePath, int num_threads){
    if (num_threads != 1)
    {
        std::cerr << "ERROR: Number of threads must be 1" << std::endl;
        exit(1);
    }
    file_path = filePath;
}


void GraphTracker::EndTracker(){
    saveToFile(total_history, total_edges, file_path + "_raw_edges.bin");
}


void GraphTracker::TraceRoute(uint32_t const id1, uint32_t const id2) {
    EdgeData data = {make_pair(id1, id2)};
    current_query.edges_visited.emplace_back(std::move(data));
}

void GraphTracker::StartTest(const int l)
{
    current_l = l;
}



void GraphTracker::EndQuery()
{
    current_query.converge_step = converge_step;
    test_history.push_back(std::move(current_query));
    step_num = 0;
}

void GraphTracker::EndTest(){
    TestData test = {
    std::move(test_history), current_l};
    total_history.push_back(std::move(test));
}

void GraphTracker::SetTotalEdges(int totalEdges){
    total_edges = totalEdges;
}

void GraphTracker::VisitedNode(uint32_t id, float distance)
{
    NodeVisited node = {id, distance};
    current_query.node_visited.push_back(node);
}

void GraphTracker::SaveBestLNodes(diskann::NeighborPriorityQueue &best_l)
{
    step_num++;

    if (best_k_nodes.size() < k)
    {
        for (int i = 0; i < best_l.size(); i++)
        {
            if (best_k_nodes.size() <= i)
            {
                best_k_nodes.push_back(best_l[i].id);
            }else
            {
                best_k_nodes[i] = best_l[i].id;
            }
            if (i == k - 1)
            {
                break;
            }
        }
    }else
    {
        bool updated = false;
        for (int i = 0; i < best_l.size(); i++)
        {
            if (i == k)
            {
                break;
            }
            if (best_k_nodes[i] != best_l[i].id)
            {
                best_k_nodes[i] = best_l[i].id;
                updated = true;
            }
        }
        if (updated)
        {
            converge_step = step_num;
        }
    }



}

void GraphTracker::SetK(int in_k)
{
    k = in_k;
}








