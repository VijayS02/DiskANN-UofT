//
// Created by vijay on 3/12/25.
//

#ifndef METRICS_H
#define METRICS_H
#include "tracking.h"


inline void TestTrack(int number)
{
    MetricTracker::Track("test", number);
    std::cout << "Testing number " << number << std::endl;
}


#endif //METRICS_H
