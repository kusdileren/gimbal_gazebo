import cv2
import numpy as np
import config

class KalmanBBoxTracker:
    def __init__(self):
        # Durum (State) Matrisi: [cx, cy, v_cx, v_cy] (Merkez x, Merkez y, x hızı, y hızı)
        # Ölçüm (Measurement) Matrisi: [cx, cy] (Sadece merkez koordinatları ölçebiliyoruz)
        self.kf = cv2.KalmanFilter(4, 2)
        
        # Durum Geçiş Matrisi (A) - Sabit Hız Modeli (x_yeni = x_eski + v * dt)
        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], np.float32)
        
        # Ölçüm Matrisi (H) - Durum matrisindeki hangi değerleri ölçtüğümüzü belirtir
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], np.float32)
        
        # Süreç Gürültüsü (Q) - Sistemin fiziksel modeline (sabit hız) ne kadar güvendiğimiz.
        # Bu değer küçüldükçe filtre "geçmişe ve hıza" daha çok güvenir, hareket pürüzsüzleşir.
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # Ölçüm Gürültüsü (R) - YOLO'nun tespitlerine ne kadar güvendiğimiz.
        # Titreme (jitter) fazlaysa bu değer artırılır.
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0
        
        # Başlangıç Hata Kovaryansı (P)
        self.kf.errorCovPost = np.eye(4, dtype=np.float32) * 1.0
        
        self.is_initialized = False

    def reset(self, cx: float, cy: float):
        """Filtreyi yeni bir hedefe kilitlendiğinde veya sıfırlandığında çağırılır."""
        self.kf.statePre = np.array([[cx], [cy], [0.0], [0.0]], dtype=np.float32)
        self.kf.statePost = np.array([[cx], [cy], [0.0], [0.0]], dtype=np.float32)
        self.is_initialized = True

    def predict(self) -> tuple[float, float]:
        """Hedefin bir sonraki konumunu tahmin eder (YOLO verisi olmasa bile çalışır)."""
        if not self.is_initialized:
            return 0.0, 0.0
            
        predicted = self.kf.predict()
        return float(predicted[0][0]), float(predicted[1][0])

    def correct(self, cx: float, cy: float):
        """YOLO'dan gelen yeni ham ölçüm ile filtreyi günceller."""
        if not self.is_initialized:
            self.reset(cx, cy)
            return
            
        measurement = np.array([[cx], [cy]], dtype=np.float32)
        self.kf.correct(measurement)

    def get_velocity(self) -> tuple[float, float]:
        """Kalman'in tahmin ettigi hedefin anlik pixel/kare hizini dondurur (v_cx, v_cy).

        Bu deger PID'e feedforward olarak eklenip donen/sabit hizla hareket eden
        hedeflerde (ornegin daire cizen ucak) integral teriminin surekli sisip
        overshoot yapmasini engellemek icin kullanilir. Kalman'in kendi hiz
        tahmini oldugu icin YOLO gurultusunden cok daha temizdir.
        """
        if not self.is_initialized:
            return 0.0, 0.0
        # statePost: [cx, cy, v_cx, v_cy]
        return float(self.kf.statePost[2][0]), float(self.kf.statePost[3][0])
