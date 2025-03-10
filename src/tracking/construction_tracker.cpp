//
// Created by vijay on 3/7/25.
//
#ifdef DISKANN_TRACKING_ENABLED
#include "tracking/construction_tracker.h"
#include "vector"

#include <fstream>
#include <boost/serialization/vector.hpp>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/utility.hpp>

#include <iostream>
#include <ostream>

vector<uint32_t> edge_counts = {};
string output_filename;
uint32_t r_v;
float alpha_v;
vector<vector<uint32_t>> construction_path_counts = {};
vector<uint32_t> current_construction_paths = {};
int current_construction_step = 0;

void saveToFile(ConstructionData construction_data, const string& filename) {
    cout << "Writing to file " << filename << endl;

    // Open file for binary output
    ofstream ofs(filename, ios::binary);
    if (!ofs) {
        throw runtime_error("Failed to open file for writing.");
    }

    // Create Boost binary archive
    boost::archive::binary_oarchive oa(ofs);

    // Serialize data
    oa << construction_data;

    ofs.close();

    cout << "Finished saving to " << filename << endl;
}


void ConstructionTracker::AddConstructionPathLength(uint32_t construction_path_length)
{
    current_construction_paths.push_back(construction_path_length);
}


void ConstructionTracker::SetConstructionStep(int i)
{
    if (current_construction_step != i)
    {
        current_construction_step = i;
        construction_path_counts.push_back(std::move(current_construction_paths));
    }
}


void ConstructionTracker::StartConstruction(uint32_t R, float alpha, string output) {
    edge_counts.clear();
    r_v = R;
    alpha_v = alpha;
    output_filename = output;
}

void ConstructionTracker::AddEdgeCount(uint32_t edge_count)
{
    edge_counts.push_back(edge_count);
}

void ConstructionTracker::EndConstruction()
{
    construction_path_counts.push_back(std::move(current_construction_paths));
    std::cout << edge_counts.size() << " " << r_v << " " << alpha_v << " " << output_filename << std::endl;
    ConstructionData construction_data = {edge_counts, r_v, alpha_v, construction_path_counts};
    saveToFile(construction_data, output_filename);
}

#endif

