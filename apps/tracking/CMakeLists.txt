find_package(Boost REQUIRED COMPONENTS program_options serialization)
find_package(nlohmann_json 3.11.3 REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_COMPILE_WARNING_AS_ERROR ON)

add_executable(data_extractor data_extractor.cpp)
target_link_libraries(data_extractor ${PROJECT_NAME} ${DISKANN_ASYNC_LIB} Boost::serialization nlohmann_json::nlohmann_json)