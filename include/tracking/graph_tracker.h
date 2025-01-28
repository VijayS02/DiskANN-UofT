//
// Created by vijay on 1/27/25.
//

#ifndef GRAPH_TRACKER_H
#define GRAPH_TRACKER_H
#include <vector>
#include <stdint.h>
#include <unordered_map>
#include <string>

using namespace std;


struct PairHash {
  template <typename T1, typename T2>
  std::size_t operator()(const std::pair<T1, T2>& pair) const {
    std::size_t h1 = std::hash<T1>{}(pair.first);
    std::size_t h2 = std::hash<T2>{}(pair.second);
    return h1 ^ (h2 << 1); // Combine the two hash values
  }
};

class GraphTracker {
    public:
      static void TraceRoute(uint32_t id1, uint32_t id2);
      static void ClearTraces();
      static void EndQuery();
      static void SetTotalEdges(int totalEdges);
      static void InitializeTracker(const string& trace_file_name, const string& edge_file_name);
      static void EndTracker();

private:
  static int total_edges;
  static long unique_visits;
  static pair<long, pair<uint32_t,uint32_t>> max_visited_edge;
  static unordered_map<pair<uint32_t, uint32_t>, long, PairHash> edge_counts;
  static vector<vector<pair<uint32_t,uint32_t>>> graph_history;
  static vector<pair<uint32_t,uint32_t>> current_query;
  static vector<long> edge_distributions;

  static std::ofstream trace_file;
  static string trace_file_name;

  static std::ofstream distribution_file;
  static string distribution_file_name;

  static void write_query_stats();
};

#endif //GRAPH_TRACKER_H
