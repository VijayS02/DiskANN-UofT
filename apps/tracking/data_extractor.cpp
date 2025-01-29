//
// Created by vijay on 1/29/25.
//
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
#include <map>
#include <memory>

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

// **Abstract Base Class for Data Extractors**
class DataExtractor {
public:
    virtual ~DataExtractor() = default;
    virtual void extractAndSave(const FullTrace& fullTrace, const string& output_filename) = 0;
};

// **Extractor 1: Edge Utilization**
class EdgeUtilizationExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        vector<vector<double>> utilizations;

        for (const auto& test : fullTrace.tests) {
            unordered_set<pair<uint32_t, uint32_t>, pair_hash> unique_edges;
            vector<double> utilization;
            int total_edges = fullTrace.total_edges;

            int unique_edge_count = 0;

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

        // Write to JSON
        json output_json;
        for (size_t test_idx = 0; test_idx < utilizations.size(); ++test_idx) {
            json test_json;
            for (size_t time_step = 0; time_step < utilizations[test_idx].size(); ++time_step) {
                test_json[to_string(time_step + 1)] = utilizations[test_idx][time_step];
            }
            output_json["Test " + to_string(test_idx)] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};

// **Extractor 2: Edge Visit Distribution**
class EdgeVisitDistributionExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
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

        json output_json;
        for (size_t test_idx = 0; test_idx < distributions.size(); ++test_idx) {
            json test_json;
            for (const auto& [query_idx, count] : distributions[test_idx]) {
                test_json[to_string(query_idx)] = count;
            }
            string name = "L value: " + to_string(fullTrace.tests[test_idx].L);
            output_json[name] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};

// **Extractor 3: Hop Distribution**
class HopDistributionExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        vector<map<int, int>> distributions; // One per TestData

        for (const auto& test : fullTrace.tests) {
            map<int, int> visit_distribution; // Map query index -> number of edges visited

            // Iterate over each query trace
            for (const auto& query: test.query_traces) {
                visit_distribution[query.size()]++;
            }

            distributions.push_back(visit_distribution);
        }

        json output_json;
        for (size_t test_idx = 0; test_idx < distributions.size(); ++test_idx) {
            json test_json;
            for (const auto& [query_idx, count] : distributions[test_idx]) {
                test_json[to_string(query_idx)] = count;
            }
            output_json["Test " + to_string(test_idx)] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};

// **Main function**
int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: ./data_extractor raw_edges_file output_prefix [extractors...]\n");
        printf("Available extractors:\n");
        printf("  edge_utilization\n  edge_visits\n  hop_distribution\n");
        return 1;
    }

    // Load data once
    string input_file = argv[1];
    string output_prefix = argv[2];
    FullTrace data = loadFromFile(input_file);
    cout << data.total_edges << " Total Edges in Graph" << endl;

    // Extractor mapping
    map<string, unique_ptr<DataExtractor>> extractors;
    extractors["edge_utilization"] = make_unique<EdgeUtilizationExtractor>();
    extractors["edge_visits"] = make_unique<EdgeVisitDistributionExtractor>();
    extractors["hop_distribution"] = make_unique<HopDistributionExtractor>();

    // Process selected extractors
    for (int i = 3; i < argc; ++i) {
        string extractor_name = argv[i];
        if (extractors.find(extractor_name) != extractors.end()) {
            string output_filename = output_prefix + "_" + extractor_name + ".json";
            extractors[extractor_name]->extractAndSave(data, output_filename);
        } else {
            cout << "Unknown extractor: " << extractor_name << endl;
        }
    }

    return 0;
}
