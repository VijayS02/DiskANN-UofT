//
// Created by vijay on 3/7/25.
//
#include <iostream>
#include <fstream>
#include "tracking/construction_tracker.h"

#include <map>
#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/serialization/utility.hpp>
#include <boost/serialization/access.hpp>

#include <nlohmann/json.hpp>
#include <memory>

using namespace std;
using json = nlohmann::json;


ConstructionData loadFromFile(const string& filename) {
    ifstream ifs(filename, ios::binary);
    if (!ifs) {
        throw runtime_error("Failed to open file for reading.");
    }
    boost::archive::binary_iarchive ia(ifs);
    ConstructionData data;
    ia >> data;
    return data;
}

class DataExtractor {
public:
    virtual ~DataExtractor() = default;

    // Extracts the data but does NOT save it
    virtual json extractData(const ConstructionData& fullTrace) = 0;

    // graph metadata for the visualization
    json GraphProperties;

    // Calls extractData, appends graph properties, and saves the JSON
    void saveJson(const ConstructionData& fullTrace, const string& output_filename) {
        json output_json = {};
        output_json["data"] = extractData(fullTrace);
        output_json["graph_properties"] = GraphProperties;

        ofstream file(output_filename);
        file << output_json.dump(4);
        file.close();
        cout << "JSON written to " << output_filename << endl;
    }
};


class EdgeDistExtractor : public DataExtractor {
public:
    EdgeDistExtractor()
    {
        GraphProperties = json::parse(R"(
        {
            "title": "Edge Count Distribution",
            "x_label": "Number of Edges",
            "y_label": "Count",
            "type": "scatter",
            "x_log": false,
            "y_log": true,
            "sort_x": true,
            "marker": "o",
            "grouping": "single"
        }
        )");
    }

    json extractData(const ConstructionData& fullTrace) override {
        uint32_t max = *std::max_element(fullTrace.edge_counts.begin(), fullTrace.edge_counts.end());

        auto counts = vector<int> (max + 1, 0);

        for (uint32_t i : fullTrace.edge_counts)
        {
            counts[static_cast<int>(i)]++;
        }



        // Convert to a dictionary (JSON object)
        json counts_dict;
        for (size_t i = 0; i < counts.size(); i++) {
            if (counts[i] > 0) {  // Store only non-zero values
                counts_dict[std::to_string(i)] = counts[i];  // JSON requires string keys
            }
        }

        return counts_dict;

        // return output_json;
    }
};

class ConstructionStepExtractor : public DataExtractor {
public:
    ConstructionStepExtractor()
    {
        GraphProperties = json::parse(R"(
        {
            "title": "Number of Nodes Per Path CStep 1",
            "x_label": "Number of Nodes {Not incl itself}",
            "y_label": "Count",
            "type": "scatter",
            "x_log": false,
            "y_log": true,
            "sort_x": true,
            "marker": "o",
            "grouping": "single"
        }
        )");
    }

    json extractData(const ConstructionData& fullTrace) override {
        if (fullTrace.construction_path_counts.empty())
        {
            json empty;
            return empty;
        }


        vector<uint32_t> nodes_visited = fullTrace.construction_path_counts[0];

        uint32_t max = *std::max_element(nodes_visited.begin(), nodes_visited.end());

        auto counts = vector<int> (max + 1, 0);

        for (uint32_t i : nodes_visited)
        {
            counts[static_cast<int>(i)]++;
        }



        // Convert to a dictionary (JSON object)
        json counts_dict;
        for (size_t i = 0; i < counts.size(); i++) {
            if (counts[i] > 0) {  // Store only non-zero values
                counts_dict[std::to_string(i)] = counts[i];  // JSON requires string keys
            }
        }

        return counts_dict;

        // return output_json;
    }
};

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: ./construction_data_extractor tracking_output output_prefix [extractors...]\n");
        return 1;
    }


    // Load data once
    // Load data once
    string input_file = argv[1];
    string output_prefix = argv[2];
    ConstructionData data = loadFromFile(input_file);

    // Extractor mapping
    map<string, unique_ptr<DataExtractor>> extractors;
    extractors["edge_dist"] = make_unique<EdgeDistExtractor>();
    extractors["const_nodes_dist"] = make_unique<ConstructionStepExtractor>();

    for (int i = 3; i < argc; ++i) {
        string extractor_name = argv[i];
        if (extractors.find(extractor_name) != extractors.end()) {
            string output_filename = output_prefix + "_" + extractor_name + ".json";
            extractors[extractor_name]->saveJson(data, output_filename);
        } else {
            cout << "Unknown extractor: " << extractor_name << endl;
        }
    }

    return 0;
}
