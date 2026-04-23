cmake_minimum_required(VERSION 3.20)
project(transport_c LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

add_library(transport_c_core STATIC
    src/transport_core.c
)

target_include_directories(transport_c_core PUBLIC include)

add_executable(transport_etude10_c
    src/etude10.c
)

target_include_directories(transport_etude10_c PRIVATE include)
target_link_libraries(transport_etude10_c PRIVATE transport_c_core)

if (MSVC)
    target_compile_options(transport_c_core PRIVATE $<$<CONFIG:Release>:/O2;/GL>)
    target_compile_options(transport_etude10_c PRIVATE $<$<CONFIG:Release>:/O2;/GL>)
    target_link_options(transport_etude10_c PRIVATE $<$<CONFIG:Release>:/LTCG>)
else ()
    target_compile_options(transport_c_core PRIVATE $<$<CONFIG:Release>:-O3;-DNDEBUG;-march=native;-flto>)
    target_compile_options(transport_etude10_c PRIVATE $<$<CONFIG:Release>:-O3;-DNDEBUG;-march=native;-flto>)
    target_link_options(transport_etude10_c PRIVATE $<$<CONFIG:Release>:-flto>)
endif ()
