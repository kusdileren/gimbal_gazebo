"""
"Hangi nesne sinifina kilitliyiz" durumunu tutar.

Kullanici bir tespite tikladiginda o tespitin SINIFINA kilitlenilir
(orn. 'car'). Sonraki her karede ayni siniftan en yuksek guvenli kutu
takip edilir - boylece ayni araba kareler arasinda farkli bir YOLO
kutusuyla eslese bile takip kopmaz.
"""


class TargetLock:
    def __init__(self):
        self.target_class_id = None

    @property
    def is_locked(self) -> bool:
        return self.target_class_id is not None

    def lock_to(self, cls_id: int):
        self.target_class_id = cls_id

    def release(self):
        self.target_class_id = None

    def try_lock_from_click(self, detections, click_x, click_y, detector) -> bool:
        """Tiklanan noktadaki tespiti bulup varsa o sinifa kilitlenir.
        Tiklama bos bir alana denk gelirse kilit acilir (release)."""
        det = detector.find_at_point(detections, click_x, click_y)
        if det is not None:
            self.lock_to(det.cls_id)
            return True
        self.release()
        return False

    def current_best(self, detections, detector):
        """Kilitli sinifa ait, bu karedeki en yuksek guvenli tespiti dondurur."""
        if not self.is_locked:
            return None
        return detector.best_of_class(detections, self.target_class_id)
