#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

import config
from yolo_detector import YoloDetector
from gimbal_controller import GimbalController
from mouse_input import MouseInputHandler
from target_lock import TargetLock
import hud






class GimbalTrackerNode(Node):
    def __init__(self):
        super().__init__('gimbal_tracker_node')

        self.bridge = CvBridge()

        # ---- Parcalari olustur ----
        self.detector = YoloDetector()
        self.gimbal = GimbalController(self)
        self.lock = TargetLock()
        self.mouse = MouseInputHandler(
            self.gimbal,
            on_manual_start=self.lock.release,   # sag tikla surukleme -> otomatik takip iptal
            logger=self.get_logger(),
        )

        self.image_sub = self.create_subscription(
            Image, config.TOPIC_KAMERA_GORUNTU, self.image_callback, 10)

        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(config.WINDOW_NAME, self.mouse.on_mouse_event)

        # NOT: baslangic pozunu periyodik yayinlayan bir timer BILEREK YOK.
        # Yuksek frekansli bir timer, klavye/fare olaylarinin (cv2.waitKey)
        # zamaninda islenmesini engelleyip tuslarin "takilmasina" sebep oluyordu.

        self.get_logger().info("YOLOv11 Gimbal Tracker basladi!")
        self.get_logger().info(
            "Bir hedefin uzerine SOL TIK ile kilitlenin, "
            "SAG TIK + SURUKLE ile manuel kontrol edin.")

    # ---------------- Ana kamera dongusu ----------------
    def image_callback(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        detections = self.detector.detect(frame)
        self._log_debug(detections)

        # Bekleyen bir sol tik varsa isle (hedefe kilitlenmeyi dener)
        click = self.mouse.consume_click()
        if click is not None:
            self.lock.try_lock_from_click(detections, click[0], click[1], self.detector)

        self._takip_durumunu_isle_ve_ciz(frame, detections)

        hud.draw_zoom_info(frame, self.gimbal.zoom)
        cv2.imshow(config.WINDOW_NAME, frame)
        self._klavye_isle()

    def _takip_durumunu_isle_ve_ciz(self, frame, detections):
        """Kilit durumuna gore ya bekleme ekranini, ya kaybedildi ekranini,
        ya da aktif takip ekranini cizer + gimbal'i hedefe dogru yonlendirir."""
        if not self.lock.is_locked:
            hud.draw_waiting_state(frame, detections, self.detector.class_names)
            return

        best = self.lock.current_best(detections, self.detector) #kilitli ise.
        if best is None:
            hud.draw_lost_state(frame)
            return

        class_name = self.detector.class_names[self.lock.target_class_id].upper()
        hud.draw_tracking_state(frame, best, class_name)

        img_h, img_w = frame.shape[:2]
        obj_cx, obj_cy = best.center
        self.gimbal.track_target_center(obj_cx, obj_cy, img_w / 2.0, img_h / 2.0)

    def _log_debug(self, detections):
        if detections:
            ozet = [f"{self.detector.class_names[d.cls_id]}(%{d.conf * 100:.0f})"
                    for d in detections]
            self.get_logger().info(f"[DEBUG] Bu karede tespit edilenler: {ozet}")
        else:
            self.get_logger().info("[DEBUG] Bu karede hicbir sey tespit edilmedi.")

    # ---------------- Klavye kontrolleri (zoom) ----------------
    def _klavye_isle(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            rclpy.shutdown()
        elif key == ord('1'):
            self.gimbal.set_zoom(1.0)
        elif key == ord('2'):
            self.gimbal.set_zoom(2.0)
        elif key == ord('3'):
            self.gimbal.set_zoom(4.0)
        elif key in (ord('+'), ord('=')):
            self.gimbal.zoom_in()
        elif key == ord('-'):
            self.gimbal.zoom_out()


def main(args=None):
    rclpy.init(args=args)
    node = GimbalTrackerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
