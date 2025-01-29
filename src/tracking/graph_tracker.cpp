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
    QueryData data = {make_pair(id1, id2)};
    current_query.emplace_back(std::move(data));
}

void GraphTracker::StartTest(const int l)
{
    current_l = l;
}



void GraphTracker::EndQuery()
{
    test_history.push_back(std::move(current_query));
}

void GraphTracker::EndTest(){
    TestData test = {
    std::move(test_history), current_l};
    total_history.push_back(std::move(test));
}

void GraphTracker::SetTotalEdges(int totalEdges){
    total_edges = totalEdges;
}





