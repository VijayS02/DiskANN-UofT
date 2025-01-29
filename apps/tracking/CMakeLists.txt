find_package(Boost REQUIRED COMPONENTS program_options serialization)
find_package(nlohmann_json 3.11.3 REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_COMPILE_WARNING_AS_ERROR ON)

add_executable(extract_edge_distribution extract_edge_distribution.cpp)
target_link_libraries(extract_edge_distribution ${PROJECT_NAME} ${DISKANN_ASYNC_LIB} Boost::serialization nlohmann_json::nlohmann_json)

add_executable(extract_edge_usage extract_edge_usage.cpp)
target_link_libraries(extract_edge_usage ${PROJECT_NAME} ${DISKANN_ASYNC_LIB} Boost::serialization nlohmann_json::nlohmann_json)