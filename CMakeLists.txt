cmake_minimum_required(VERSION 3.10.2 FATAL_ERROR)
project(zoom_controller_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(gz_cmake_vendor REQUIRED)
find_package(gz-cmake REQUIRED)

gz_find_package(gz-plugin REQUIRED COMPONENTS register)
gz_find_package(gz-sim REQUIRED)
gz_find_package(gz-rendering REQUIRED)
gz_find_package(gz-transport REQUIRED)
gz_find_package(gz-msgs REQUIRED)
gz_find_package(gz-math REQUIRED)
gz_find_package(gz-common REQUIRED)

add_library(ZoomControllerCpp SHARED src/ZoomController.cc)

target_include_directories(ZoomControllerCpp
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(ZoomControllerCpp
  PRIVATE
    gz-plugin::register
    gz-sim::gz-sim
    gz-rendering::gz-rendering
    gz-transport::gz-transport
    gz-msgs::gz-msgs
    gz-math::gz-math
    gz-common::gz-common
)

# Kalici, taşınabilir bir konuma kur. SDF dosyasindaki plugin filename'i
# artik build/ klasorune degil, bu klasore bagli olacak (GZ_SIM_SYSTEM_PLUGIN_PATH
# ile birlikte kullanilir, README.md'ye bakin).
install(TARGETS ZoomControllerCpp
  LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/lib
)