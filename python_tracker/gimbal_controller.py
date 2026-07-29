"""
Gimbal'in kendisiyle ilgili her sey burada: acilarin tutulmasi,
ROS'a yayinlanmasi ve otomatik takip icin PID hesaplamasi.

Bu modul YOLO'dan, faredan vs. haberdar DEGIL - sadece "su aciya git",
"hedefi merkeze al", "zoom'u su yap" gibi komutlar alir.
"""

from std_msgs.msg import Float64

import config


class GimbalController:
    def __init__(self, node):
        self.node = node

        self.yaw_pub = node.create_publisher(Float64, config.TOPIC_YAW_CMD, 10)
        self.tilt_pub = node.create_publisher(Float64, config.TOPIC_TILT_CMD, 10)
        self.zoom_pub = node.create_publisher(Float64, config.TOPIC_ZOOM_CMD, 10)

        self.yaw = config.BASLANGIC_YAW
        self.tilt = config.BASLANGIC_TILT
        self.zoom = config.ZOOM_MIN

    # ---------------- Aci kontrolu ----------------
    def set_yaw_tilt(self, yaw: float, tilt: float):
        """Aciyi dogrudan ayarlar ve yayinlar. Tilt sinirlanir, yaw sinirlanmaz
        (yaw_joint continuous/limitsiz)."""
        self.yaw = yaw
        self.tilt = max(min(tilt, config.TILT_MAX), config.TILT_MIN)
        self._publish_pose()

    def nudge(self, d_yaw: float, d_tilt: float):
        """Goreli aci degisimi - manuel fare suruklemesi icin kullanilir."""
        self.set_yaw_tilt(self.yaw + d_yaw, self.tilt + d_tilt)

    def track_target_center(self, obj_cx: float, obj_cy: float,
                             img_cx: float, img_cy: float):
        """Hedefi goruntu merkezine dogru getiren bir PID adimi atar.
        Zoom arttikca hareket yavaslar (dynamic gain)."""
        err_x = img_cx - obj_cx
        err_y = img_cy - obj_cy

        dynamic_kp_yaw = config.KP_YAW / max(1.0, self.zoom)
        dynamic_kp_tilt = config.KP_TILT / max(1.0, self.zoom)

        new_yaw = self.yaw + dynamic_kp_yaw * err_x
        new_tilt = self.tilt - dynamic_kp_tilt * err_y
        self.set_yaw_tilt(new_yaw, new_tilt)

    def _publish_pose(self):
        yaw_msg = Float64()
        yaw_msg.data = self.yaw
        self.yaw_pub.publish(yaw_msg)

        tilt_msg = Float64()
        tilt_msg.data = self.tilt
        self.tilt_pub.publish(tilt_msg)

    # ---------------- Zoom kontrolu ----------------
    def set_zoom(self, value: float):
        value = max(value, config.ZOOM_MIN)
        if value == self.zoom:
            return
        self.zoom = value
        msg = Float64()
        msg.data = self.zoom
        self.zoom_pub.publish(msg)
        self.node.get_logger().info(f"Zoom -> {self.zoom}x")

    def zoom_in(self):
        self.set_zoom(self.zoom + config.ZOOM_ADIMI)

    def zoom_out(self):
        self.set_zoom(self.zoom - config.ZOOM_ADIMI)
