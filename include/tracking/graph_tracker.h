//
// Created by vijay on 1/27/25.
//

#ifndef GRAPH_TRACKER_H
#define GRAPH_TRACKER_H
#include <vector>
#include <cstdint>
#include <neighbor.h>
#include <string>

using namespace std;

struct NodeVisited
{
  uint32_t id;
  float distance;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & id;
    ar & distance;
  }
};
struct EdgeData
{
  pair<uint32_t, uint32_t> edge_explored;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & edge_explored;
  }
};

struct QueryTrace
{
  std::vector<EdgeData> edges_visited;
  std::vector<NodeVisited> node_visited;
  int converge_step;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & edges_visited;
    ar & node_visited;
    ar & converge_step;
  }
};

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
      static void VisitedNode(uint32_t id, float distance);
      static void SaveBestLNodes(diskann::NeighborPriorityQueue& best_l);
      static void SetK(int k);
private:
  static int total_edges;
  static vector<QueryTrace> test_history;
  static vector<TestData> total_history;
  static QueryTrace current_query;
  static string file_path;
  static int current_l;
  static vector<uint32_t> best_k_nodes;
  static int step_num;
  static int k;
  static int converge_step;
};

#endif //GRAPH_TRACKER_H
