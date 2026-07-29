"""
Fare olaylarini yonetir:
  - SOL TIK -> bir hedef secme tiklamasi (islenmesi image_callback'e birakilir)
  - SAG TIK + SURUKLE -> manuel kamera kontrolu (otomatik takibi iptal eder)
"""

import cv2

import config


class MouseInputHandler:
    def __init__(self, gimbal, on_manual_start=None, logger=None):
        self.gimbal = gimbal
        self.on_manual_start = on_manual_start  # sag tikla surukleme baslayinca cagrilir
        self.logger = logger

        self.click_point = None   # bekleyen sol tik konumu, consume_click() ile okunur
        self.is_dragging = False
        self._last_x = 0
        self._last_y = 0

    def on_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.click_point = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._suruklemeyi_baslat(x, y)
        elif event == cv2.EVENT_RBUTTONUP:
            self.is_dragging = False
        elif event == cv2.EVENT_MOUSEMOVE and self.is_dragging:
            self._surukle(x, y)

    def consume_click(self):
        """Bekleyen tiklama noktasini dondurur ve sifirlar (bir kez islenir)."""
        point = self.click_point
        self.click_point = None
        return point

    # ---------------- Manuel kontrol (sag tik) ----------------
    def _suruklemeyi_baslat(self, x, y):
        self.is_dragging = True
        self._last_x, self._last_y = x, y

        if self.on_manual_start is not None:
            self.on_manual_start()
        if self.logger is not None:
            self.logger.info("Manuel Kamera Kontrolu (Sag Tik)")

    def _surukle(self, x, y):
        dx = x - self._last_x
        dy = y - self._last_y

        self.gimbal.nudge(
            d_yaw=-dx * config.MANUEL_HASSASIYET,
            d_tilt=dy * config.MANUEL_HASSASIYET,
        )

        self._last_x, self._last_y = x, y
