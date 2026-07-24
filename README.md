# gimbal_gazebo
tracking vehicles with gimbal camera in additon zoom etc.

TERMİNAL KODLARI:

1)

export PYTHONPATH=$PYTHONPATH:/home/eren/Belgeler/moduler_gimbal_projesi
export GZ_SIM_RESOURCE_PATH=/home/eren-ku-dil/Belgeler/moduler_gimbal_projesi/models:$GZ_SIM_RESOURCE_PATH
gz sim kasaba_binali.sdf

2)

ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=kamera_bridge.yaml

3)

python3 /home/eren-ku-dil/Belgeler/moduler_gimbal_projesi/gimbal_tracker.py
