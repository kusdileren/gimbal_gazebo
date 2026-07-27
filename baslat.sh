#!/bin/bash

# 1. Sekme: Gazebo Simülasyonu
gnome-terminal --tab --title="Gazebo" -- bash -c "export GZ_SIM_SYSTEM_PLUGIN_PATH=/home/eren-ku-dil/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi/build:\$GZ_SIM_SYSTEM_PLUGIN_PATH && export GZ_SIM_RESOURCE_PATH=/home/eren-ku-dil/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi/models:\$GZ_SIM_RESOURCE_PATH && cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi && gz sim kasaba_binali.sdf; exec bash"

# 2. Sekme: ROS 2 Bridge (Gecikmeli başlatma)
gnome-terminal --tab --title="Bridge" -- bash -c "sleep 3 && source /opt/ros/lyrical/setup.bash && cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi && ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=kamera_bridge.yaml; exec bash"

# 3. Sekme: WASD Kontrol Scripti (Köprü açıldıktan hemen sonra başlasın)
gnome-terminal --tab --title="WASD Kontrol" -- bash -c "sleep 4 && source /opt/ros/lyrical/setup.bash && python3 /home/eren-ku-dil/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi/wasd_kontrol_ros2.py; exec bash"

# 4. Sekme: Python Tracker
gnome-terminal --tab --title="Tracker" -- bash -c "sleep 5 && source /opt/ros/lyrical/setup.bash && cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi && python3 gimbal_tracker.py; exec bash"