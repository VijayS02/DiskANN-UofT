#include "tracking/graph_tracker.h"
#include <cassert>
#include <iostream>
#include <fstream>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/serialization/utility.hpp>
#include <boost/serialization/access.hpp>
#include <nlohmann/json.hpp>


#include <unordered_map>
#include <map>


using namespace std;

using json = nlohmann::json;

struct pair_hash {
    template <class T1, class T2>
    size_t operator()(const pair<T1, T2>& p) const {
        return hash<T1>()(p.first) ^ (hash<T2>()(p.second) << 1);
    }
};

FullTrace loadFromFile(const string& filename) {
    // Open file for binary input
    ifstream ifs(filename, ios::binary);
    if (!ifs) {
        throw runtime_error("Failed to open file for reading.");
    }

    // Create Boost binary archive
    boost::archive::binary_iarchive ia(ifs);

    // Deserialize data
    FullTrace data;
    ia >> data;

    ifs.close();
    return data;
}

void writeDistributionToJSON(const vector<map<int, int>>& distributions, const string& filename) {
    json output_json;
    int test_idx = 0;

    for (const auto& dist : distributions) {
        json test_json;
        for (const auto& [times_explored, count] : dist) {
            test_json[to_string(times_explored)] = count;
        }
        output_json["Test " + to_string(test_idx++)] = test_json;
    }

    ofstream file(filename);
    file << output_json.dump(4); // Pretty-print with indentation
    file.close();
    cout << "JSON written to " << filename << endl;
}

// Function to compute the edge exploration frequency distribution
vector<map<int, int>> computeEdgeExplorationDistribution(const FullTrace& fullTrace) {
    vector<map<int, int>> distributions; // One per TestData

    for (const auto& test : fullTrace.tests) {
        unordered_map<pair<uint32_t, uint32_t>, int, pair_hash> edge_counts;

        // Count occurrences of each edge
        for (const auto& query_trace : test.query_traces) {
            for (const auto& query_data : query_trace) {
                edge_counts[query_data.edge_explored]++;
            }
        }

        // Create a histogram of edge frequencies
        map<int, int> frequency_distribution;
        for (const auto& [edge, count] : edge_counts) {
            frequency_distribution[count]++;
        }

        distributions.push_back(frequency_distribution);
    }

    return distributions;
}





int main(int argc, char **argv) {
    if (argc != 3){
        printf("Usage: ./extract_edge_distribution raw_edges_file output_file\n");
    }

    FullTrace data = loadFromFile(argv[1]);

    cout << data.total_edges << " Total Edges" << endl;

    vector<map<int, int>> distributions = computeEdgeExplorationDistribution(data);

    writeDistributionToJSON(distributions, argv[2]);

    return 0;

}