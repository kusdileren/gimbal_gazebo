"""
Gimbal'in kendisiyle ilgili her sey burada: acilarin tutulmasi,
ROS'a yayinlanmasi ve otomatik takip icin tam PID hesaplamasi.

Bu modul YOLO'dan, faredan vs. haberdar DEGIL - sadece "su aciya git",
"hedefi merkeze al", "zoom'u su yap" gibi komutlar alir.
"""

from std_msgs.msg import Float64
import time
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

        # --- PID Durum (State) Değişkenleri ---
        self.prev_err_x = 0.0
        self.integral_x = 0.0
        self.prev_err_y = 0.0
        self.integral_y = 0.0
        
        # Zaman takibi (Gerçekçi türev ve integral hesabı için dt)
        self.last_time = time.time()

    def reset_pid(self):
        """Yeni hedefe kilitlenildiğinde veya kilit açıldığında eski hataları sıfırlar."""
        self.prev_err_x = 0.0
        self.integral_x = 0.0
        self.prev_err_y = 0.0
        self.integral_y = 0.0
        self.last_time = time.time()

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
        
        # Zaman farkini hesapla (dt)
        current_time = time.time()
        dt = current_time - self.last_time
        dt = min(max(dt, 0.02), 0.15)     # <-- eskiden sadece dt<=0 kontrolü vardı, artık minimum taban var
        self.last_time = current_time

        # 1. Hata (Error) Hesaplama: P Bileşeni
        err_x = img_cx - obj_cx
        err_y = img_cy - obj_cy

        # 2. İntegral (Birikmiş Hata) Hesaplama: I Bileşeni
        # Sürekli aynı tarafta hata varsa, zamanla artarak sistemi zorlar.
        self.integral_x += err_x * dt
        self.integral_y += err_y * dt
        
        # Windup (İntegral Yığılması) Koruması
        # Hata çok büyüdüğünde integralin sonsuza gitmesini ve sistemin çıldırmasını önler.
        self.integral_x = max(min(self.integral_x, config.PID_INTEGRAL_MAX), -config.PID_INTEGRAL_MAX)
        self.integral_y = max(min(self.integral_y, config.PID_INTEGRAL_MAX), -config.PID_INTEGRAL_MAX)

        # 3. Türev (Hatanın Değişim Hızı) Hesaplama: D Bileşeni
        # Hedef merkeze yaklaştıkça sistemi frenler, overshoot'u (hedefi geçmeyi) engeller.
        derivative_x = (err_x - self.prev_err_x) / dt
        derivative_y = (err_y - self.prev_err_y) / dt

        # Zoom arttikca kazançları dinamik olarak düşür[cite: 2]
        zoom_factor = max(1.0, self.zoom)

        # Ekseni için Toplam PID Çıkışı
        delta_yaw = (
            (config.KP_YAW * err_x) + 
            (config.KI_YAW * self.integral_x) + 
            (config.KD_YAW * derivative_x)
        ) / zoom_factor

        delta_tilt = (
            (config.KP_TILT * err_y) + 
            (config.KI_TILT * self.integral_y) + 
            (config.KD_TILT * derivative_y)
        ) / zoom_factor

        # Yeni açıları uygula ve sınırla (tilt için)
        MAX_DELTA_PER_STEP = 2.0  # derece, config'e taşınabilir
        
        new_yaw = self.yaw + max(min(delta_yaw, MAX_DELTA_PER_STEP), -MAX_DELTA_PER_STEP)
        new_tilt = self.tilt - max(min(delta_tilt, MAX_DELTA_PER_STEP), -MAX_DELTA_PER_STEP)
        self.set_yaw_tilt(new_yaw, new_tilt)

        # Gelecek döngü için mevcut hatayı kaydet
        self.prev_err_x = err_x
        self.prev_err_y = err_y

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