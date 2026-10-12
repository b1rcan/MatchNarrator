"""
extract_v2.py - Olay tespiti icin ham veri cikarma (v2)

Ne yapar:
  - Oyuncu / kaleci / hakem: YOLO + ByteTrack (tam kare, takip ID'li)
  - Top: goruntuyu parcalara bolerek (InferenceSlicer) kucuk nesne tespiti,
         her karedeki TUM top adaylari kaydedilir (secimi events_v2.py yapar)
  - Her oyuncu kutusu icin forma rengi (takim ayrimi icin)

Ciktilar: players.csv, ball_candidates.csv, meta.json
"""
import csv
import os
import json
import time

import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO

# ---------------- AYARLAR ----------------
import argparse
_ap = argparse.ArgumentParser(description="Ham veri cikarma (oyuncu/top)")
_ap.add_argument("--start-sec", type=float, default=None, help="baslangic (video sn); verilmezse betikteki/varsayilan deger")
_ap.add_argument("--duration-sec", type=float, default=None, help="sure (sn); verilmezse betikteki/varsayilan deger")
_ap.add_argument("--out-dir", default=None, help="cikti klasoru; verilmezse proje klasoru (eskisi gibi)")
_args = _ap.parse_args()
_OUT_DIR = os.path.abspath(_args.out_dir) if _args.out_dir else None   # chdir'den ONCE mutlak yola cevir
if _OUT_DIR:
    os.makedirs(_OUT_DIR, exist_ok=True)


def OUT(name):
    return os.path.join(_OUT_DIR, name) if _OUT_DIR else name


os.chdir(os.path.dirname(os.path.abspath(__file__)))  # goreli yollar betigin klasorune gore cozulur
VIDEO = "barca_tactical.mp4"
MODEL = "best.pt"
START_SEC = 60        # videonun hangi saniyesinden baslasin
DURATION_SEC = 300    # kac saniye islensin (5 dk). Tum video icin: None
if _args.start_sec is not None:
    START_SEC = _args.start_sec
if _args.duration_sec is not None:
    DURATION_SEC = _args.duration_sec
DEVICE = 0
PLAYER_CONF = 0.30
BALL_CONF = 0.10      # top icin bilerek dusuk: yanlislari events_v2 eleyecek
TRACKER = "botsort.yaml"  # BoT-SORT: kamera hareket telafili (eski: "bytetrack.yaml")
# ------------------------------------------

CLS_PLAYER, CLS_GK, CLS_REF, CLS_BALL = 0, 1, 2, 3

player_model = YOLO(MODEL)
ball_model = YOLO(MODEL)  # ayri nesne: takip durumu top tespitiyle karismasin


def ball_callback(image_slice):
    r = ball_model.predict(image_slice, classes=[CLS_BALL], conf=BALL_CONF,
                           imgsz=640, device=DEVICE, verbose=False)[0]
    return sv.Detections.from_ultralytics(r)


slicer = sv.InferenceSlicer(callback=ball_callback, slice_wh=(640, 640), overlap_wh=(128, 128))

# Saha maskesi icin sabitler
GREEN_LOW = np.array([30, 30, 30])
GREEN_HIGH = np.array([90, 255, 255])
FIELD_KERNEL = np.ones((25, 25), np.uint8)


def field_mask(frame):
    """O karenin sahasini (en buyuk yesil bolge) maske olarak dondurur.
    Kamera hareketli oldugu icin HER karede yeniden hesaplanir."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, FIELD_KERNEL)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    field = np.zeros_like(m)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        cv2.drawContours(field, [largest], -1, 255, cv2.FILLED)
    return field


def inside_field(field, x, y):
    h, w = field.shape
    xi, yi = int(x), int(y)
    if 0 <= yi < h and 0 <= xi < w:
        return field[yi, xi] > 0
    return False


def jersey_color(frame, x1, y1, x2, y2):
    """Kutunun govde bolgesinden (cim piksellerini atarak) ortalama Lab rengi."""
    w, h = x2 - x1, y2 - y1
    cx1, cx2 = int(x1 + 0.25 * w), int(x1 + 0.75 * w)
    cy1, cy2 = int(y1 + 0.15 * h), int(y1 + 0.50 * h)
    crop = frame[max(cy1, 0):max(cy2, 0), max(cx1, 0):max(cx2, 0)]
    if crop.size == 0:
        return (np.nan, np.nan, np.nan)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).reshape(-1, 3)
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).reshape(-1, 3)
    grass = (hsv[:, 0] > 30) & (hsv[:, 0] < 90) & (hsv[:, 1] > 40)
    pixels = lab[~grass] if (~grass).sum() >= 10 else lab
    return tuple(round(float(v), 1) for v in pixels.mean(axis=0))


cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
start_f = int(START_SEC * fps)
end_f = total if DURATION_SEC is None else min(total, start_f + int(DURATION_SEC * fps))
cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
n_total = end_f - start_f
print(f"Video: {VIDEO} | {fps:.1f} FPS | {width}x{height} | islenecek kare: {n_total}")

with open(OUT("players.csv"), "w", newline="") as fp, open(OUT("ball_candidates.csv"), "w", newline="") as fb:
    wp, wb = csv.writer(fp), csv.writer(fb)
    wp.writerow(["frame", "track_id", "class_id", "x1", "y1", "x2", "y2", "conf", "L", "A", "B"])
    wb.writerow(["frame", "x1", "y1", "x2", "y2", "conf"])

    t0 = time.time()
    for f in range(start_f, end_f):
        ok, frame = cap.read()
        if not ok:
            break

        # 0) Bu karenin saha maskesi (kamera hareketli -> her karede yeniden)
        field = field_mask(frame)

        # 1) Oyuncular (takipli) - sadece ayagi (alt-orta nokta) saha icindekiler
        r = player_model.track(frame, persist=True, classes=[CLS_PLAYER, CLS_GK, CLS_REF],
                               conf=PLAYER_CONF, imgsz=960, tracker=TRACKER,
                               device=DEVICE, verbose=False)[0]
        if r.boxes.id is not None:
            for tid, cls, conf, xyxy in zip(r.boxes.id.int().tolist(), r.boxes.cls.int().tolist(),
                                            r.boxes.conf.tolist(), r.boxes.xyxy.tolist()):
                x1, y1, x2, y2 = map(int, xyxy)
                foot_x, foot_y = (x1 + x2) / 2, y2      # ayak noktasi
                if not inside_field(field, foot_x, foot_y):
                    continue                             # saha disi (tribun/kulube) -> at
                color = jersey_color(frame, x1, y1, x2, y2)  # hakemler dahil: hakem/oyuncu karisikligini duzeltmek icin
                wp.writerow([f, tid, cls, x1, y1, x2, y2, round(conf, 3), *color])

        # 2) Top adaylari (parcali tespit) - sadece saha icindekiler
        balls = slicer(frame)
        if len(balls) > 0:
            for xyxy, conf in zip(balls.xyxy, balls.confidence):
                bx, by = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
                if not inside_field(field, bx, by):
                    continue                             # saha disi -> at
                wb.writerow([f, *[round(float(v), 1) for v in xyxy], round(float(conf), 3)])

        done = f - start_f + 1
        if done % 250 == 0:
            speed = done / (time.time() - t0)
            print(f"{done}/{n_total} kare | {speed:.1f} kare/sn | kalan ~{(n_total - done) / speed / 60:.1f} dk")

cap.release()
with open(OUT("meta.json"), "w") as f:
    json.dump({"video": VIDEO, "tracker": TRACKER, "fps": fps, "start_frame": start_f, "end_frame": end_f,
               "width": width, "height": height}, f, indent=2)
print(f"Bitti: {OUT('players.csv')}, {OUT('ball_candidates.csv')}, {OUT('meta.json')}")