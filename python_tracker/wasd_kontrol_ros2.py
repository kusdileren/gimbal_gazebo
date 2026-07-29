#!/usr/bin/env python3
"""
wasd_kontrol_ros2.py
----------------------
- W/A/S/D  -> kule govdesini yatayda hareket ettirir (VelocityControl / cmd_vel)
- N/M      -> kule govdesini dikeyde (yukari/asagi) hareket ettirir (ayni cmd_vel, linear.z)
- J/L      -> yaw_joint (kamera saga/sola doner)
- I/K      -> tilt_joint (kamera yukari/asagi bakar)"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Float64
from geometry_msgs.msg import Twist

# ---------------- SABITLER ----------------
HIZ = 2.0             # WASD hareket hizi (m/s)
DURMA_SURESI = 0.25   # WASD icin: son tus basimindan sonra otomatik dur (sn)

ACI_ADIMI = 0.05      # ok tuslari: her basimda kac radyan degisecek (~2.9 derece)
YAW_LIMIT = (-3.1415, 3.1415)
TILT_LIMIT = (-0.1, 3.1415)

# WASD eksen eslemesi (kule 90 derece donuk oldugu icin duzeltilmis)
# Degerler: (vx, vy, vz)
WASD_HARITASI = {
    87: (0.0,  HIZ, 0.0),   # W -> ileri
    83: (0.0, -HIZ, 0.0),   # S -> geri
    65: (-HIZ, 0.0, 0.0),   # A -> sol
    68: (HIZ,  0.0, 0.0),   # D -> sag
    78: (0.0,  0.0,  HIZ),  # N -> yukari
    77: (0.0,  0.0, -HIZ),  # M -> asagi
}

# Yaw/tilt icin tus kodlari (ok tuslari Gazebo'nun kendi kamera navigasyonu
# tarafindan yakalanip KeyPublisher'a hic ulasmiyor, bu yuzden harflere gectik)
TUS_SOL = 74     # J -> yaw sola
TUS_YUKARI = 73  # I -> tilt yukari
TUS_SAG = 76     # L -> yaw saga
TUS_ASAGI = 75   # K -> tilt asagi
# -------------------------------------------


def clamp(deger, sinirlar):
    alt, ust = sinirlar
    return max(alt, min(ust, deger))


class WasdKontrol(Node):
    def __init__(self):
        super().__init__('wasd_kontrol')

        self.cmd_vel_pub = self.create_publisher(Twist, '/kule_cmd_vel', 10)
        self.yaw_pub = self.create_publisher(Float64, '/kule_yaw_cmd', 10)
        self.tilt_pub = self.create_publisher(Float64, '/kule_tilt_cmd', 10)

        self.create_subscription(Int32, '/keyboard/keypress', self.keypress_callback, 10)

        self.durma_timer = None
        self.yaw_hedef = 1.60
        self.tilt_hedef = 2.5

        self.get_logger().info(
            'Kontrol basladi: W/A/S/D hareket, N/M yukari/asagi, J/L=yaw, I/K=tilt. '
            'Gazebo penceresine tiklayip odagi 3D gorunume verin.')

    # ---------------- WASD (hareket) ----------------
    def _dur(self):
        self.cmd_vel_pub.publish(Twist())
        if self.durma_timer is not None:
            self.durma_timer.cancel()
            self.durma_timer = None

    def _wasd_isle(self, tus_kodu):
        vx, vy, vz = WASD_HARITASI[tus_kodu]
        hareket = Twist()
        hareket.linear.x = vx
        hareket.linear.y = vy
        hareket.linear.z = vz
        self.cmd_vel_pub.publish(hareket)

        if self.durma_timer is not None:
            self.durma_timer.cancel()
        self.durma_timer = self.create_timer(DURMA_SURESI, self._dur)

    # ---------------- Ok tuslari (yaw/tilt) ----------------
    def _yaw_ayarla(self, delta):
        # yaw_joint artik siniz (continuous) oldugu icin burada clamp yok.
        # Onceden YAW_LIMIT ile (-3.1415, 3.1415) sinirlaniyordu, bu da
        # baslangic acisi (1.60) +pi'ye yakin oldugundan bir yonde cok
        # cabuk duvara carpip "donemiyor" hissi veriyordu.
        self.yaw_hedef += delta
        msg = Float64()
        msg.data = self.yaw_hedef
        self.yaw_pub.publish(msg)

    def _tilt_ayarla(self, delta):
        self.tilt_hedef = clamp(self.tilt_hedef + delta, TILT_LIMIT)
        msg = Float64()
        msg.data = self.tilt_hedef
        self.tilt_pub.publish(msg)

    # ---------------- Ana callback ----------------
    def keypress_callback(self, msg: Int32):
        kod = msg.data

        if kod in WASD_HARITASI:
            self._wasd_isle(kod)
        elif kod == TUS_SAG:
            self._yaw_ayarla(-ACI_ADIMI)
        elif kod == TUS_SOL:
            self._yaw_ayarla(ACI_ADIMI)
        elif kod == TUS_YUKARI:
            self._tilt_ayarla(-ACI_ADIMI)
        elif kod == TUS_ASAGI:
            self._tilt_ayarla(ACI_ADIMI)


def main():
    rclpy.init()
    node = WasdKontrol()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()