"""
etiketleme.py - Gercek olaylari (pas / top kaybi) klavyeyle hizlica etiketleme araci.

Videoyu oynatir; olay aninda tusa basarsin, zaman VIDEO saatinden otomatik alinir
(skorborddaki mac saatiyle karistirma riski yok) ve gercek_olaylar.csv'ye yazilir.
Her etiketten sonra dosya kaydedilir; yarida birakip tekrar acarsan kaldigin yerden devam eder.

TUSLAR
  bosluk : oynat / duraklat
  p      : PAS        (alici oyuncunun topa ILK temas ettigi an)
  k      : TOP KAYBI  (rakip oyuncunun topa ILK temas ettigi an)
  z      : son etiketi geri al
  a / d  : 2 sn geri / ileri
  s / f  : yavaslat / hizlandir (0.25x - 2x)
  q      : kaydet ve cik

KOMUT SATIRI (hepsi opsiyonel; verilmezse eski davranis: 60-180 sn, gercek_olaylar.csv)
  python etiketleme.py --start 180 --end 300 --out gercek_olaylar_test.csv
"""
import argparse
import os

import cv2
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.join(HERE, "barca_tactical.mp4")
_ap = argparse.ArgumentParser(description="Gercek olay etiketleme araci")
_ap.add_argument("--start", type=float, default=60, help="baslangic (video sn), varsayilan 60")
_ap.add_argument("--end", type=float, default=180, help="bitis (video sn), varsayilan 180")
_ap.add_argument("--out", default="gercek_olaylar.csv", help="cikti CSV, varsayilan gercek_olaylar.csv")
_args = _ap.parse_args()
if _args.end <= _args.start:
    _ap.error("--end, --start'tan buyuk olmali")
START_SEC = _args.start
END_SEC = _args.end
OUT = _args.out if os.path.isabs(_args.out) else os.path.join(HERE, _args.out)  # goreli yol proje klasorune gore
SPEEDS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]


def fmt(sec):
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


def to_sec(v):
    m, s = str(v).split(":")
    return int(m) * 60 + float(s)


def save(labels):
    df = pd.DataFrame(sorted(labels), columns=["sec", "tip"])
    df["zaman"] = df["sec"].map(fmt)
    df[["zaman", "tip"]].to_csv(OUT, index=False)


labels = []
if os.path.exists(OUT):                       # kaldigin yerden devam
    old = pd.read_csv(OUT, dtype=str)
    labels = [(to_sec(z), t) for z, t in zip(old["zaman"], old["tip"])]
    print(f"{len(labels)} mevcut etiket yuklendi ({OUT})")

cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    raise SystemExit(f"HATA: video acilamadi: {VIDEO}")
fps = cap.get(cv2.CAP_PROP_FPS)
start_f, end_f = int(START_SEC * fps), int(END_SEC * fps)
f = start_f
if labels:                                    # son etiketin biraz gerisinden basla
    f = max(start_f, int((max(s for s, _ in labels) - 2) * fps))
cap.set(cv2.CAP_PROP_POS_FRAMES, f)
speed_i, playing, flash, flash_left = 1, True, "", 0
frame = None

print(__doc__)
while True:
    if playing or frame is None:
        ok, frame = cap.read()
        if not ok or f >= end_f:
            playing = False
            if frame is None:
                break
        else:
            f += 1
    t = f / fps
    view = frame.copy()
    cv2.rectangle(view, (0, 0), (view.shape[1], 50), (0, 0, 0), -1)
    status = "OYNATILIYOR" if playing else "DURAKLATILDI"
    n_pas = sum(1 for _, x in labels if x == "PAS")
    n_kay = sum(1 for _, x in labels if x == "TOP KAYBI")
    cv2.putText(view, f"Video saati {fmt(t)}  |  {status} {SPEEDS[speed_i]}x  |  PAS {n_pas}  TOP KAYBI {n_kay}",
                (12, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(view, "bosluk:oynat  p:PAS  k:TOP KAYBI  z:geri al  a/d:-/+2sn  s/f:hiz  q:cik",
                (12, view.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if flash_left > 0:
        cv2.putText(view, flash, (12, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        flash_left -= 1
    cv2.imshow("Etiketleme", view)

    delay = max(1, int(1000 / (fps * SPEEDS[speed_i]))) if playing else 30
    key = cv2.waitKey(delay) & 0xFF
    if key == ord("q"):
        break
    elif key == ord(" "):
        playing = not playing
    elif key in (ord("p"), ord("k")):
        tip = "PAS" if key == ord("p") else "TOP KAYBI"
        labels.append((round(t, 2), tip))
        save(labels)
        flash, flash_left = f"+ {tip}  {fmt(t)}", 25
        print(f"  {fmt(t)}  {tip}")
    elif key == ord("z") and labels:
        last = max(labels)
        labels.remove(last)
        save(labels)
        flash, flash_left = f"geri alindi: {last[1]} {fmt(last[0])}", 25
        print(f"  geri alindi: {fmt(last[0])} {last[1]}")
    elif key in (ord("a"), ord("d")):
        f = min(max(start_f, f + (-2 if key == ord("a") else 2) * int(fps)), end_f - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, frame = cap.read()
    elif key == ord("s"):
        speed_i = max(0, speed_i - 1)
    elif key == ord("f"):
        speed_i = min(len(SPEEDS) - 1, speed_i + 1)

cap.release()
cv2.destroyAllWindows()
save(labels)
print(f"Kaydedildi: {OUT} ({len(labels)} etiket)")
