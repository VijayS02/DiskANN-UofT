#include "tracking/graph_tracker.h"
#include <iostream>
#include <fstream>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/serialization/utility.hpp>
#include <boost/serialization/access.hpp>
#include <nlohmann/json.hpp>
#include <unordered_set>

using namespace std;
using json = nlohmann::json;

// Custom hash function for std::pair<uint32_t, uint32_t>
struct pair_hash {
    template <class T1, class T2>
    size_t operator()(const pair<T1, T2>& p) const {
        return hash<T1>()(p.first) ^ (hash<T2>()(p.second) << 1);
    }
};

// Load FullTrace from file
FullTrace loadFromFile(const string& filename) {
    ifstream ifs(filename, ios::binary);
    if (!ifs) {
        throw runtime_error("Failed to open file for reading.");
    }
    boost::archive::binary_iarchive ia(ifs);
    FullTrace data;
    ia >> data;
    return data;
}

// Compute Edge Utilization Over Time for Each Test
vector<vector<double>> computeEdgeUtilization(const FullTrace& fullTrace) {
    vector<vector<double>> utilizations;

    for (const auto& test : fullTrace.tests) {
        unordered_set<pair<uint32_t, uint32_t>, pair_hash> unique_edges;
        vector<double> utilization;
        int total_edges = fullTrace.total_edges;

        int unique_edge_count = 0;
        int time_step = 1;

        // Iterate over each query trace (time step)
        for (const auto& query_trace : test.query_traces) {
            for (const auto& query_data : query_trace) {
                if (unique_edges.insert(query_data.edge_explored).second) {
                    unique_edge_count++; // New unique edge found
                }
            }
            double utilization_value = (total_edges > 0) ? (double)unique_edge_count / total_edges : 0.0;
            utilization.push_back(utilization_value);
        }

        utilizations.push_back(utilization);
    }

    return utilizations;
}

// Function to write edge utilization to JSON
void writeUtilizationToJSON(const vector<vector<double>>& utilizations, const string& filename) {
    json output_json;

    for (size_t test_idx = 0; test_idx < utilizations.size(); ++test_idx) {
        json test_json;
        for (size_t time_step = 0; time_step < utilizations[test_idx].size(); ++time_step) {
            test_json[to_string(time_step + 1)] = utilizations[test_idx][time_step];
        }
        output_json["Test " + to_string(test_idx)] = test_json;
    }

    ofstream file(filename);
    file << output_json.dump(4);
    file.close();
    cout << "JSON written to " << filename << endl;
}

// Main function
int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: ./extract_edge_utilization raw_edges_file output_file\n");
        return 1;
    }

    FullTrace data = loadFromFile(argv[1]);
    cout << data.total_edges << " Total Edges in Graph" << endl;

    vector<vector<double>> utilizations = computeEdgeUtilization(data);
    writeUtilizationToJSON(utilizations, argv[2]);

    return 0;
}
