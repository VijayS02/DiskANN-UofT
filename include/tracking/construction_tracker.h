//
// Created by vijay on 3/7/25.
//

#ifndef CONSTRUCTION_TRACKER_H
#define CONSTRUCTION_TRACKER_H
#include <vector>
#include <cstdint>
#include "string"

#ifdef DISKANN_TRACKING_ENABLED
# pragma message("TRACKING IS ENABLED!")



using namespace std;

struct ConstructionData
{
  vector<uint32_t> edge_counts;
  uint32_t r_v;
  float alpha_v;
  vector<vector<uint32_t>> construction_path_counts;

  template<class Archive>
  void serialize(Archive& ar, const unsigned int version) {
    ar & edge_counts;
    ar & r_v;
    ar & alpha_v;
    ar & construction_path_counts;
  }
};



class ConstructionTracker {
    public:
        static void StartConstruction(uint32_t R, float alpha, string output_filename);
        static void TraceRoute(uint32_t id1, uint32_t id2);
        static void EndConstruction();
        static void AddEdgeCount(uint32_t edge_count);
        static void SetConstructionStep(int i);
        static void AddConstructionPathLength(uint32_t construction_path_length);
};

#else

class ConstructionTrakcer {
public:
  static inline void StartConstruction() {}
  static inline void TraceRoute(uint32_t id1, uint32_t id2){}
  static inline void EndConstruction(){}
  static inline void AddEdgeCount(uint32_t edge_count){}
  static void SetConstructionStep(int i) {}
  static void AddConstructionPathLength(uint32_t construction_path_length) {}
};


#endif // DISKANN_TRACKING_ENABLED


#endif //CONSTRUCTION_TRACKER_H
