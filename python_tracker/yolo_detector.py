"""
YOLO tabanli nesne tespiti.

Bu modul sadece "kameradan gelen bir karede hangi nesneler var" sorusuna
cevap verir. Takip mantigi, kilitlenme mantigi burada YOK - sadece tespit.
"""

from dataclasses import dataclass

from ultralytics import YOLO

import config



@dataclass
class Detection:
    """Tek bir YOLO tespiti: kutu koordinatlari + guven skoru + sinif id'si."""
    x1: int
    y1: int
    x2: int
    y2: int
    conf: float
    cls_id: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.width / 2.0, self.y1 + self.height / 2.0)

    def contains_point(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class YoloDetector:
    """Ultralytics YOLO modelini sarmalar; kareden Detection listesi uretir."""

    def __init__(self, model_path: str = config.YOLO_MODEL_PATH):
        self.model = YOLO(model_path) # video aktarılır.
        print(self.model.names)


    @property
    def class_names(self) -> dict:
        """COCO sinif id -> isim eslemesi (orn. {2: 'car', 4: 'airplane'})."""
        return self.model.names
    

    def detect(self, frame) -> list[Detection]:
        """Bir kare uzerinde YOLO calistirip Detection listesi dondurur."""
        results = self.model(
            frame,
            verbose=False, #loglarla yormaz.
            conf=config.YOLO_CONF_THRESHOLD,
            imgsz=config.YOLO_IMG_SIZE,
            classes=config.HEDEF_SINIF_ID,
        )

        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                detections.append(Detection(x1, y1, x2, y2, conf, cls_id))
        return detections

    @staticmethod
    def find_at_point(detections: list[Detection], x: int, y: int) -> Detection | None: #tıklanan noktadaki nesneyi bulur.
        for det in detections:
            if det.contains_point(x, y):
                return det
        return None

    @staticmethod
    def best_of_class(detections: list[Detection], cls_id: int) -> Detection | None: # max güven skoruna sahip nesneyi seçer.
        candidates = [d for d in detections if d.cls_id == cls_id]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d.conf)
