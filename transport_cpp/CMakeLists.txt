cmake_minimum_required(VERSION 3.20)
project(transport_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(transport_lib
    src/transport_problem.cpp
    src/generator.cpp
)

target_include_directories(transport_lib PUBLIC include)

add_executable(transport_cli src/main.cpp)
target_link_libraries(transport_cli PRIVATE transport_lib)

add_executable(transport_benchmark src/benchmark_main.cpp)
target_link_libraries(transport_benchmark PRIVATE transport_lib)

add_executable(transport_etude10 src/etude10_main.cpp)
target_link_libraries(transport_etude10 PRIVATE transport_lib)

add_executable(transport_traces src/traces_main.cpp)
target_link_libraries(transport_traces PRIVATE transport_lib)
