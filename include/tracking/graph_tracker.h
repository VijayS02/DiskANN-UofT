//
// Created by vijay on 1/27/25.
//

#ifndef GRAPH_TRACKER_H
#define GRAPH_TRACKER_H
#include <vector>
#include <cstdint>
#include <string>

using namespace std;

struct QueryData
{
  pair<uint32_t, uint32_t> edge_explored;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & edge_explored;
  }
};

using QueryTrace = std::vector<QueryData>;

struct TestData
{
  vector<QueryTrace> query_traces;
  int L;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & query_traces;
    ar & L;
  }
};

struct FullTrace
{
  vector<TestData> tests;
  int total_edges;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & tests;
    ar & total_edges;
  }
};

class GraphTracker {
    public:
      static void TraceRoute(uint32_t id1, uint32_t id2);
      static void EndTest();
      static void EndQuery();
      static void StartTest(int l);
      static void SetTotalEdges(int totalEdges);
      static void InitializeTracker(const string& filePath, int num_threads);
      static void EndTracker();

private:
  static int total_edges;
  static vector<QueryTrace> test_history;
  static vector<TestData> total_history;
  static QueryTrace current_query;
  static string file_path;
  static int current_l;

};

#endif //GRAPH_TRACKER_H
