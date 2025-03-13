#Copyright(c) Microsoft Corporation.All rights reserved.
#Licensed under the MIT                        license.

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_COMPILE_WARNING_AS_ERROR ON)

if(MSVC)
    add_subdirectory(dll)
else()
    #file(GLOB CPP_SOURCES *.cpp)
    set(CPP_SOURCES abstract_data_store.cpp ann_exception.cpp disk_utils.cpp 
        distance.cpp index.cpp in_mem_graph_store.cpp in_mem_data_store.cpp
        linux_aligned_file_reader.cpp math_utils.cpp natural_number_map.cpp
        in_mem_data_store.cpp in_mem_graph_store.cpp
        natural_number_set.cpp memory_mapper.cpp partition.cpp pq.cpp
        pq_flash_index.cpp scratch.cpp logger.cpp utils.cpp filter_utils.cpp index_factory.cpp abstract_index.cpp pq_l2_distance.cpp pq_data_store.cpp
        tracking/tracking.cpp)
    if (RESTAPI)
        list(APPEND CPP_SOURCES restapi/search_wrapper.cpp restapi/server.cpp)
    endif()


    add_library(${PROJECT_NAME} ${CPP_SOURCES})
    add_library(${PROJECT_NAME}_s STATIC ${CPP_SOURCES})

    if(TRACKING_ENABLED)
        ## load in pkg-config support
        find_package(PkgConfig)
        ## use pkg-config to get hints for 0mq locations
        pkg_check_modules(PC_ZeroMQ QUIET zmq)

        ## use the hint from above to find where 'zmq.hpp' is located
        find_path(ZeroMQ_INCLUDE_DIR
                NAMES zmq.hpp
                PATHS ${PC_ZeroMQ_INCLUDE_DIRS}
        )

        ## use the hint from above to find the location of libzmq
        find_library(ZeroMQ_LIBRARY
                NAMES zmq
                PATHS ${PC_ZeroMQ_LIBRARY_DIRS}
        )

        target_link_libraries(${PROJECT_NAME} PRIVATE ${ZeroMQ_LIBRARY})
        target_link_libraries(${PROJECT_NAME}_s PRIVATE ${ZeroMQ_LIBRARY})
    endif()
endif()

if (NOT MSVC)
    install(TARGETS ${PROJECT_NAME} LIBRARY)
endif()
