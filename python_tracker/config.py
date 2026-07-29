"""
Tum sabitler ve ayarlar burada.
Bir parametreyi degistirmek istedigin zaman once buraya bak.
"""

# ---- ROS topic isimleri ----
TOPIC_KAMERA_GORUNTU = '/kamera/goruntu'
TOPIC_ZOOM_CMD = '/kamera/zoom_cmd'
TOPIC_YAW_CMD = '/kule_yaw_cmd'
TOPIC_TILT_CMD = '/kule_tilt_cmd'

# ---- YOLO ayarlari ----
YOLO_MODEL_PATH = 'yolo11s.pt'
YOLO_CONF_THRESHOLD = 0.15
YOLO_IMG_SIZE = 1280
# COCO sinif id'leri: 2=car, 4=airplane, 5=bus, 7=truck
HEDEF_SINIF_ID = [2, 4, 5, 7]

# ---- Gimbal baslangic acilari (radyan) ----
BASLANGIC_YAW = 1.60
BASLANGIC_TILT = 2.5

# ---- Otomatik takip PID kazanclari ----
KP_YAW = 0.0003
KP_TILT = 0.0003

# ---- Tilt fiziksel sinirlari ----
# Not: yaw_joint artik surekli/limitsiz (continuous) oldugu icin yaw'a
# herhangi bir sinir uygulanmiyor - sadece tilt sinirlaniyor.
TILT_MIN = -0.1
TILT_MAX = 3.1415

# ---- Manuel kamera kontrolu (sag tik + suruklemeyle) ----
MANUEL_HASSASIYET = 0.002

# ---- Zoom ayarlari ----
ZOOM_ADIMI = 0.5
ZOOM_MIN = 1.0

# ---- Hedef "cok yakin" uyarisi esigi ----
# Kutu genisligi/yuksekligi, ekranin bu orandan fazlasini kapladiginda uyar
COK_YAKIN_ESIK = 0.9

WINDOW_NAME = "Gimbal Kamera Takip Arayuzu"
