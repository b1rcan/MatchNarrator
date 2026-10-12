"""
teshis_takip.py - Takip (tracking) kalitesini olcer.
Kullanim:  python teshis_takip.py <klasor>
   ornek:  python teshis_takip.py .                  (guncel veri)
           python teshis_takip.py sonuc_bytetrack    (yedeklenmis eski veri)
"""
import json
import os
import sys

import pandas as pd

folder = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(folder, "meta.json")))
fps = meta["fps"]
n_frames = meta["end_frame"] - meta["start_frame"]
p = pd.read_csv(os.path.join(folder, "players.csv"))

print("=" * 60)
print(f"Klasor: {folder} | Tracker: {meta.get('tracker', 'bytetrack.yaml (eski kod)')}")
print(f"Kare basina ortalama kisi tespiti: {len(p) / n_frames:.1f}  (sahada ~22-25 kisi var)")
names = {0: "oyuncu", 1: "kaleci", 2: "hakem"}
print("Tespitlerin sinif dagilimi:", {names.get(k, k): int(v) for k, v in p["class_id"].value_counts().items()})

lengths = p.groupby("track_id").size()
print(f"\nToplam iz: {len(lengths)}")
for th_sec in [0.2, 1, 5, 10]:
    th = th_sec * fps
    short = lengths[lengths < th]
    print(f"  {th_sec:>4} sn'den kisa iz: {len(short):>5} iz  -> tum tespitlerin %{100 * short.sum() / lengths.sum():5.1f}'i")

s = lengths.sort_values()
cum = s.cumsum() / s.sum()
w_med = s[cum >= 0.5].iloc[0]
print(f"Tespit agirlikli medyan iz suresi: {w_med / fps:.1f} sn  (bir tespitin ait oldugu tipik iz uzunlugu)")

mixed = p.groupby("track_id")["class_id"].nunique()
print(f"\nIz icinde sinif degisimi (oyuncu<->hakem titremesi): {(mixed > 1).sum()} iz (%{100 * (mixed > 1).mean():.1f})")

print(f"\nTespit guveni: medyan {p['conf'].median():.2f} | %10'luk dilim {p['conf'].quantile(0.10):.2f} | "
      f"0.40 altindaki tespit orani %{100 * (p['conf'] < 0.40).mean():.1f}")
print("=" * 60)
