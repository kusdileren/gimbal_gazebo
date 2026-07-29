"""
Ekran uzerine yazi/kutu cizen fonksiyonlar.

Bu modulde HICBIR karar mantigi yok - sadece "verilen bilgiyi ekrana ciz".
Boylece gorsellestirme, takip/tespit mantigindan tamamen ayri kaliyor.
"""

import cv2

import config


def draw_zoom_info(frame, zoom: float):
    cv2.putText(frame, f"Zoom: {zoom:.0f}x", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)


def draw_waiting_state(frame, detections, class_names):
    """Henuz bir hedefe kilitlenilmemisken: tum tespitleri soluk renkte goster."""
    cv2.putText(frame, "HEDEF SECMEK ICIN UZERINE TIKLAYIN", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    for det in detections:
        name = class_names[det.cls_id]
        cv2.rectangle(frame, (det.x1, det.y1), (det.x2, det.y2), (200, 200, 200), 1)
        cv2.putText(frame, name, (det.x1, max(15, det.y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)


def draw_lost_state(frame):
    """Kilitliydik ama bu karede hedef bulunamadi."""
    cv2.putText(frame, "HEDEF KAYBEDILDI - ARANIYOR...", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


def draw_tracking_state(frame, det, class_name: str):
    """Aktif takip: hedef kutusu + etiket + gerekirse 'cok yakin' uyarisi."""
    label = f"{class_name} %{det.conf * 100:.1f}"

    img_h, img_w = frame.shape[:2]
    if det.width > img_w * config.COK_YAKIN_ESIK or det.height > img_h * config.COK_YAKIN_ESIK:
        cv2.putText(frame, "HEDEF COK YAKIN! ZOOM DUSURUN", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.rectangle(frame, (det.x1, det.y1), (det.x2, det.y2), (0, 0, 0), 2)
    cv2.putText(frame, label, (det.x1, max(20, det.y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    cv2.putText(frame, "Takip Durumu: AKTIF", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
