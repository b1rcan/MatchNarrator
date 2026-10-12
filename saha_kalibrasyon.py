"""
saha_kalibrasyon.py - Her kare icin goruntu -> saha homografisi hesaplar.

extract_v2.py ile ayni video araligini isler (meta.json'dan okur), bu yuzden
agir oyuncu/top tespitini TEKRAR calistirmaya gerek yoktur.

Kalite kapisi:
  - en az MIN_POINTS guvenilir nokta
  - noktalar neredeyse tek bir dogru uzerindeyse (orta saha gorunumlerinde olur) reddet
  - ortalama izdusum hatasi MAX_ERR_M'den buyukse reddet
  Reddedilen karede, en fazla MAX_AGE kare onceki son gecerli homografi kullanilir.

Cizgi inceltmesi (saha_cizgi.py): Modelden gelen kaba homografi, goruntudeki gercek beyaz
cizgilere hizalanir. Baslangic adayi olarak hem modelin homografisi hem de bir onceki karenin
inceltilmis homografisi denenir; cizgilerle daha iyi ortuseni secilip inceltilir.

Cikti: homography.csv  (frame, durum, nokta_sayisi, hata_m, kapsama_once, kapsama_sonra, h0..h8)
  kapsama: gorunen sablon cizgilerinin yuzde kaci gercek beyaz cizgi uzerinde (0-1)
  durum: 1 = bu karede hesaplandi, 2 = onceki gecerli homografi kullanildi, 0 = yok
"""
import csv
import json
import os
import time

import cv2
import numpy as np
from ultralytics import YOLO

from saha_geometri import VERTICES
from saha_cizgi import line_mask, coverage, refine

import argparse
_ap = argparse.ArgumentParser(description="Kare basina saha homografisi")
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
PITCH_MODEL = "football-pitch-detection.pt"
DEVICE = 0
KP_CONF = 0.5
MIN_POINTS = 4
MAX_ERR_M = 2.0
MIN_SPREAD = 0.08     # noktalarin "tek dogru" olmama olcusu (kucuk tekil deger / buyuk tekil deger)
MAX_AGE = 25          # kare: gecerli homografi en fazla bu kadar sure yeniden kullanilir (1 sn)
REFINE = True        # cizgi inceltmesi acik/kapali (karsilastirma icin)
MIN_COVERAGE = 0.25  # inceltilmis homografinin kabul edilmesi icin en az cizgi kapsamasi

meta = json.load(open(OUT("meta.json")))        # --out-dir verilirse extract_v2'nin orada yazdigi meta okunur
if _args.start_sec is not None:                  # aralik elle verilirse meta'daki aralik ezilir
    meta["start_frame"] = int(_args.start_sec * meta["fps"])
    if _args.duration_sec is not None:
        meta["end_frame"] = meta["start_frame"] + int(_args.duration_sec * meta["fps"])
model = YOLO(PITCH_MODEL)
cap = cv2.VideoCapture(meta["video"])
cap.set(cv2.CAP_PROP_POS_FRAMES, meta["start_frame"])
n_total = meta["end_frame"] - meta["start_frame"]

last_H, last_f = None, None
covs0, covs1 = [], []
n_refined, n_from_prev, n_used = 0, 0, 0
stats = {0: 0, 1: 0, 2: 0}
errs = []
reasons = {"az_nokta": 0, "dogrusal": 0, "yuksek_hata": 0, "hesaplanamadi": 0}

with open(OUT("homography.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["frame", "durum", "nokta_sayisi", "hata_m", "kapsama_once", "kapsama_sonra"]
               + [f"h{i}" for i in range(9)])
    t0 = time.time()
    for f in range(meta["start_frame"], meta["end_frame"]):
        ok, frame = cap.read()
        if not ok:
            break
        H, n, err = None, 0, np.nan
        r = model(frame, verbose=False, device=DEVICE)[0]
        if r.keypoints is not None and r.keypoints.conf is not None and len(r.keypoints.xy):
            xy = r.keypoints.xy[0].cpu().numpy()
            conf = r.keypoints.conf[0].cpu().numpy()
            good = (conf > KP_CONF) & (xy[:, 0] > 1) & (xy[:, 1] > 1)
            n = int(good.sum())
            if n < MIN_POINTS:
                reasons["az_nokta"] += 1
            else:
                tgt = VERTICES[good]
                sv = np.linalg.svd(tgt - tgt.mean(axis=0), compute_uv=False)
                if sv[1] / max(sv[0], 1e-6) < MIN_SPREAD:
                    reasons["dogrusal"] += 1
                else:
                    Hc, _ = cv2.findHomography(xy[good], tgt, cv2.RANSAC, 100.0)
                    if Hc is None:
                        reasons["hesaplanamadi"] += 1
                    else:
                        proj = cv2.perspectiveTransform(xy[good].reshape(-1, 1, 2), Hc).reshape(-1, 2)
                        err = float(np.mean(np.linalg.norm(proj - tgt, axis=1))) / 100
                        if err <= MAX_ERR_M:
                            H = Hc / Hc[2, 2]
                        else:
                            reasons["yuksek_hata"] += 1

        if H is not None:
            errs.append(err)

        # --- Cizgi inceltmesi ---
        c0 = c1 = np.nan
        if REFINE:
            inits = [h for h in (H, last_H if (last_H is not None and f - last_f <= MAX_AGE) else None)
                     if h is not None]
            if inits:
                lines = line_mask(frame)
                covs = [coverage(*lines, h) for h in inits]
                init = inits[int(np.argmax(covs))]
                Hr, c0, c1, _ = refine(frame, init, lines=lines)
                if c1 >= MIN_COVERAGE:
                    if H is None:
                        n_from_prev += 1          # model basarisiz, onceki kareden cizgilerle kurtarildi
                    n_refined += int(c1 > c0)
                    n_used += 1
                    H = Hr
                    covs0.append(c0); covs1.append(c1)

        if H is not None:
            durum, last_H, last_f = 1, H, f
        elif last_H is not None and f - last_f <= MAX_AGE:
            durum, H = 2, last_H
        else:
            durum = 0
        stats[durum] += 1
        hv = H.ravel().tolist() if H is not None else [""] * 9
        w.writerow([f, durum, n, "" if np.isnan(err) else round(err, 3),
                    "" if np.isnan(c0) else round(c0, 3), "" if np.isnan(c1) else round(c1, 3)] + hv)

        done = f - meta["start_frame"] + 1
        if done % 500 == 0:
            speed = done / (time.time() - t0)
            print(f"{done}/{n_total} kare | {speed:.1f} kare/sn | kalan ~{(n_total - done) / speed / 60:.1f} dk")

cap.release()
tot = sum(stats.values())
print("=" * 60)
print(f"Homografi bu karede hesaplandi : %{100 * stats[1] / tot:.1f}")
print(f"Onceki gecerli homografi       : %{100 * stats[2] / tot:.1f}")
print(f"Homografi yok                  : %{100 * stats[0] / tot:.1f}")
if errs:
    print(f"Ortalama izdusum hatasi        : {np.mean(errs):.2f} m (medyan {np.median(errs):.2f} m)")
print("Reddedilme nedenleri:", reasons)
if REFINE and covs0:
    print(f"Cizgi inceltmesi: karelerin %{100 * n_used / tot:.1f}'inde cizgilere hizali homografi kullanildi | "
          f"ortalama cizgi kapsamasi %{100 * np.mean(covs0):.0f} -> %{100 * np.mean(covs1):.0f} | "
          f"model basarisizken onceki kareden kurtarilan: {n_from_prev}")
print(f"Bitti: {OUT('homography.csv')}")