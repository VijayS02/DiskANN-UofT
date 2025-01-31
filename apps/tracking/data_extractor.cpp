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
                for (const auto& query_data : query_trace.edges_visited) {
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
            string title = "L: " + to_string(fullTrace.tests[test_idx].L);
            output_json[title] = test_json;
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
                for (const auto& query_data : query_trace.edges_visited) {
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
                visit_distribution[query.edges_visited.size()]++;
            }

            distributions.push_back(visit_distribution);
        }

        json output_json;
        for (size_t test_idx = 0; test_idx < distributions.size(); ++test_idx) {
            json test_json;
            for (const auto& [query_idx, count] : distributions[test_idx]) {
                test_json[to_string(query_idx)] = count;
            }
            string title = "L: " + to_string(fullTrace.tests[test_idx].L);
            output_json[title] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};


class DistanceDistributionExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        json output_json;

        for (size_t test_idx = 0; test_idx < fullTrace.tests.size(); ++test_idx) {
            map<int, pair<double, int>> dist_dist;
            const auto& test = fullTrace.tests[test_idx];

            const auto &quries = test.query_traces;
            for (const auto &[edges_visited, node_visited, _] : quries)
            {
                const auto &visited = node_visited;
                for (size_t step = 0; step < visited.size(); ++step)
                {
                    const auto &node = visited[step];
                    if (dist_dist.find(step) == dist_dist.end())
                    {
                        dist_dist[step] = make_pair(node.distance, 1);
                    }else
                    {
                        dist_dist[step].first += node.distance;
                        dist_dist[step].second++;
                    }
                }
            }
            json test_json;
            for (const auto& [step, dist_comp] : dist_dist)
            {
                double avg_dist = dist_comp.first / dist_comp.second;
                test_json[to_string(step)] = avg_dist;
            }

            string title = "L: " + to_string(test.L);
            output_json[title] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};

#define GRANULARITY 0.05

class LatestPositionDistributionExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        json output_json;

        for (size_t test_idx = 0; test_idx < fullTrace.tests.size(); ++test_idx) {
            const auto& test = fullTrace.tests[test_idx];
            vector<double> step_prop; // Map step index -> (sum of distances, count)

            for (const QueryTrace& query_trace : test.query_traces) {
                float min_dist = INT_MAX;
                int index = -1;
                auto &visited = query_trace.node_visited;
                for (size_t step = 0; step < visited.size(); ++step) {
                    if (visited[step].distance <= min_dist)
                    {
                        min_dist = visited[step].distance;
                        index = static_cast<int>(step);
                    }
                }

                double prop = static_cast<double>(index)/ static_cast<double>(visited.size());
                step_prop.push_back(prop);
            }


            // Convert vector into frequencies (bucketed by 0.05)

            map<double, int> distribution;

            for (double item : step_prop)
            {
                // round item to nearest 0.05
                double rounded_v = std::round(item / GRANULARITY) * GRANULARITY;
                distribution[rounded_v]++;
            }

            json test_json;
            for (const auto& [prop, count] : distribution) {
                test_json[to_string(prop)] = count;
            }

            string title = "L: " + to_string(test.L);
            output_json[title] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};


class ConvergenceStepExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        json output_json;

        for (size_t test_idx = 0; test_idx < fullTrace.tests.size(); ++test_idx) {
            const auto& test = fullTrace.tests[test_idx];
            map<int, int> step_counts; // Maps step count -> number of queries that took this many steps

            for (const QueryTrace& query_trace : test.query_traces) {
                int steps = query_trace.node_visited.size();
                step_counts[steps]++;
            }

            json test_json;
            for (const auto& [steps, count] : step_counts) {
                test_json[to_string(steps)] = count;
            }

            string title = "L: " + to_string(test.L);
            output_json[title] = test_json;
        }

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};

class ExactConvergenceStepExtractor : public DataExtractor {
public:
    void extractAndSave(const FullTrace& fullTrace, const string& output_filename) override {
        json output_json;

        for (size_t test_idx = 0; test_idx < fullTrace.tests.size(); ++test_idx) {
            const auto& test = fullTrace.tests[test_idx];
            vector<double> step_prop;

            for (const QueryTrace& query_trace : test.query_traces) {
                double prop = static_cast<double>(query_trace.converge_step)/ static_cast<double>(query_trace.node_visited.size());
                step_prop.push_back(prop);
            }


            // Convert vector into frequencies (bucketed by 0.05)
            map<double, int> distribution;

            for (double item : step_prop)
            {
                // round item to nearest 0.05
                double rounded_v = std::round(item / GRANULARITY) * GRANULARITY;
                distribution[rounded_v]++;
            }

            json test_json;
            for (const auto& [prop, count] : distribution) {
                test_json[to_string(prop)] = count;
            }

            string title = "L: " + to_string(test.L);
            output_json[title] = test_json;
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
        printf("  edge_util\n  edge_visits\n  hop_dist\n distance_dist\n steps_dist\n latest_dist\n exact_conv");
        return 1;
    }

    // Load data once
    string input_file = argv[1];
    string output_prefix = argv[2];
    FullTrace data = loadFromFile(input_file);
    cout << data.total_edges << " Total Edges in Graph" << endl;

    // Extractor mapping
    map<string, unique_ptr<DataExtractor>> extractors;
    extractors["edge_util"] = make_unique<EdgeUtilizationExtractor>();
    extractors["edge_visits"] = make_unique<EdgeVisitDistributionExtractor>();
    extractors["hop_dist"] = make_unique<HopDistributionExtractor>();
    extractors["distance_dist"] = make_unique<DistanceDistributionExtractor>();
    extractors["steps_dist"] = make_unique<ConvergenceStepExtractor>();
    extractors["latest_dist"] = make_unique<LatestPositionDistributionExtractor>();
    extractors["exact_conv"] = make_unique<ExactConvergenceStepExtractor>();

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
