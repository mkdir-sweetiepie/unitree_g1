cmake_minimum_required(VERSION 3.10)
project(g1_loco_wrapper)

set(CMAKE_CXX_STANDARD 17)

# Find unitree SDK
set(UNITREE_SDK_PATH "/home/tom2025orin006/dev/unitree_sdk2")
find_path(UNITREE_SDK_INCLUDE_DIR unitree/robot/g1/loco/g1_loco_client.hpp
    PATHS ${UNITREE_SDK_PATH}/include
    NO_DEFAULT_PATH)

if(NOT UNITREE_SDK_INCLUDE_DIR)
    message(FATAL_ERROR "Could not find unitree SDK headers")
endif()

# Find unitree SDK library
find_library(UNITREE_SDK_LIB unitree_sdk2
    PATHS ${UNITREE_SDK_PATH}/lib ${UNITREE_SDK_PATH}/build/lib ${UNITREE_SDK_PATH}/lib/aarch64
    NO_DEFAULT_PATH)

if(NOT UNITREE_SDK_LIB)
    message(FATAL_ERROR "Could not find unitree SDK library")
endif()

# Find DDS libraries
find_library(DDSC_LIB ddsc
    PATHS ${UNITREE_SDK_PATH}/thirdparty/lib/aarch64
    NO_DEFAULT_PATH)

find_library(DDSCXX_LIB ddscxx
    PATHS ${UNITREE_SDK_PATH}/thirdparty/lib/aarch64
    NO_DEFAULT_PATH)

if(NOT DDSC_LIB OR NOT DDSCXX_LIB)
    message(FATAL_ERROR "Could not find DDS libraries")
endif()

# Include directories
include_directories(${UNITREE_SDK_INCLUDE_DIR})
include_directories(${UNITREE_SDK_PATH}/thirdparty/include)
include_directories(${UNITREE_SDK_PATH}/thirdparty/include/ddscxx)

# Add shared libraries
add_library(g1_loco_wrapper SHARED g1_loco_wrapper.cpp)
add_library(g1_arm_wrapper SHARED g1_arm_wrapper.cpp)

# Link libraries
target_link_libraries(g1_loco_wrapper ${UNITREE_SDK_LIB} ${DDSC_LIB} ${DDSCXX_LIB})
target_link_libraries(g1_arm_wrapper ${UNITREE_SDK_LIB} ${DDSC_LIB} ${DDSCXX_LIB})

# Set output directory to parent directory
set_target_properties(g1_loco_wrapper PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/..
)
set_target_properties(g1_arm_wrapper PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/..
)

message(STATUS "UNITREE_SDK_INCLUDE_DIR: ${UNITREE_SDK_INCLUDE_DIR}")
message(STATUS "UNITREE_SDK_LIB: ${UNITREE_SDK_LIB}")
message(STATUS "DDSC_LIB: ${DDSC_LIB}")
message(STATUS "DDSCXX_LIB: ${DDSCXX_LIB}")