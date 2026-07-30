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
from kalman_tracker import KalmanBBoxTracker

class GimbalTrackerNode(Node):
    def __init__(self):
        super().__init__('gimbal_tracker_node')

        self.bridge = CvBridge()

        # ---- Parcalari TEK BIR KERE olustur ----
        self.detector = YoloDetector()
        self.gimbal = GimbalController(self)
        self.lock = TargetLock()
        
        self.kalman = KalmanBBoxTracker() 
        self.hedef_kayip_sayaci = 0

        self.mouse = MouseInputHandler(
            self.gimbal,
            on_manual_start=self.lock.release,   # sag tikla surukleme -> otomatik takip iptal
            logger=self.get_logger(),
        )
        
        self.image_sub = self.create_subscription(
            Image, config.TOPIC_KAMERA_GORUNTU, self.image_callback, 10)

        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(config.WINDOW_NAME, self.mouse.on_mouse_event)

        self.get_logger().info("YOLOv11 Gimbal Tracker basladi!")
        self.get_logger().info(
            "Bir hedefin uzerine SOL TIK ile kilitlenin, "
            "SAG TIK + SURUKLE ile manuel kontrol edin.")

    # ---------------- Ana kamera dongusu ----------------
    def image_callback(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        detections = self.detector.detect(frame)
        self._log_debug(detections)

        # Bekleyen bir sol tik varsa isle
        click = self.mouse.consume_click()
        if click is not None:
            # Eger gecerli bir hedefe tiklandiysa (kilit basariliysa)
            if self.lock.try_lock_from_click(detections, click[0], click[1], self.detector):
                self.gimbal.reset_pid()              # PID hafizasini temizle
                self.kalman.is_initialized = False   # Kalman hiz/tahmin hafizasini temizle

        self._takip_durumunu_isle_ve_ciz(frame, detections)

        hud.draw_zoom_info(frame, self.gimbal.zoom)
        cv2.imshow(config.WINDOW_NAME, frame)
        self._klavye_isle()

    def _takip_durumunu_isle_ve_ciz(self, frame, detections):
        if not self.lock.is_locked:
            hud.draw_waiting_state(frame, detections, self.detector.class_names)
            self.kalman.is_initialized = False 
            self.gimbal.reset_pid() # Bosta beklerken PID'nin sismemesi icin
            return

        best = self.lock.current_best(detections, self.detector)
        img_h, img_w = frame.shape[:2]

        if best is not None:
            obj_cx, obj_cy = best.center
            self.kalman.correct(obj_cx, obj_cy)
            self.hedef_kayip_sayaci = 0

            class_name = self.detector.class_names[self.lock.target_class_id].upper()
            hud.draw_tracking_state(frame, best, class_name)
        else:
            self.hedef_kayip_sayaci += 1
            if self.hedef_kayip_sayaci > 30: 
                hud.draw_lost_state(frame)
                self.kalman.is_initialized = False 
                self.gimbal.reset_pid()
                return
            else:
                cv2.putText(frame, "HEDEF BULUT ARKASINDA - TAHMIN EDILIYOR...", (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        if self.kalman.is_initialized:
            pred_cx, pred_cy = self.kalman.predict()
            cv2.circle(frame, (int(pred_cx), int(pred_cy)), 4, (0, 255, 0), -1)
            self.gimbal.track_target_center(pred_cx, pred_cy, img_w / 2.0, img_h / 2.0)

    def _log_debug(self, detections):
        if detections:
            pass # Istersen loglamayi acabilirsin, FPS'i dusurmemesi icin pass gecildi.
        else:
            pass

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