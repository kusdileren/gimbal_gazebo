# gimbal_gazebo
tracking vehicles with gimbal camera in additon zoom etc.

TERMİNAL KODLARI:

Terminal 1 :

# 1. Proje dizinine git
cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi

# 2. C++ eklentisinin (.so dosyası) bulunduğu klasörü (build) Gazebo'ya tanıt
export GZ_SIM_SYSTEM_PLUGIN_PATH=/home/eren-ku-dil/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi/build:$GZ_SIM_SYSTEM_PLUGIN_PATH

# 3. Kendi özel modellerinin bulunduğu klasörü Gazebo'ya tanıt
export GZ_SIM_RESOURCE_PATH=/home/eren-ku-dil/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi/models:$GZ_SIM_RESOURCE_PATH

# 4. Simülasyonu çalıştır
gz sim kasaba_binali.sdf -v 4
Terminal 2:

# 1. ROS 2 Lyrical ortamını aktif et
source /opt/ros/lyrical/setup.bash

# 2. Proje dizinine git
cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi

# 3. Köprüyü yapılandırma dosyası (YAML) ile başlat
ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=kamera_bridge.yaml


Terminal 3 :

# 1. ROS 2 Lyrical ortamını aktif et
source /opt/ros/lyrical/setup.bash

# 2. Proje dizinine git
cd ~/Belgeler/c++_zoom_deneme/moduler_gimbal_projesi

# 3. Tracker scriptini çalıştır
python3 gimbal_tracker.py
