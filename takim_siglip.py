"""
takim_siglip.py - SigLIP gomulumleri + UMAP(3) + KMeans ile takim atamasi (ayri secenek)

Mevcut teams.csv / events_v2.py varsayilan davranisina DOKUNMAZ.
Adimlar:
  1) players.csv'den her iz icin en fazla N_PER_TRACK rastgele (sabit seed) kare; kirpim = kutunun ust %60'i
     (yukseklik < MIN_H ele).  Tum siniflar (oyuncu / kaleci / hakem-sinifli) kirpilir.
  2) google/siglip-base-patch16-224 (GPU) -> ortalama last_hidden_state gomulumu.
  3) UMAP(3) + KMeans, KIRPIM duzeyinde; kaleci kirpimlari fit'e GIRMEZ (umap.transform + kmeans.predict ile
     sonradan en yakin merkeze atanir, rol='gk' olarak isaretli kalir).
  4) Iz karari = kirpim etiketlerinin cogunluk oyu; oy_orani ve kume_mesafesi (izin kirpimlarinin UMAP uzayinda
     atandigi merkeze ortalama uzakligi) kaydedilir.
Ciktilar: teams_siglip.csv (K=2, ana), teams_siglip_k3.csv (K=3, karsilastirma), kume_*.png / kume_k3_*.png (kontak sayfalari)
"""
import argparse
import os

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--n-per-track", type=int, default=12)
ap.add_argument("--min-h", type=int, default=25, help="kutu yuksekligi alt siniri (px)")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--in-dir", default=None, help="players.csv/meta.json/teams.csv klasoru (varsayilan: proje klasoru)")
ap.add_argument("--out-dir", default=None, help="cikti klasoru (varsayilan: proje klasoru; teams_siglip*.csv ve kume_*.png)")
a = ap.parse_args()
IN_DIR = os.path.abspath(a.in_dir) if a.in_dir else HERE
OUT_DIR = os.path.abspath(a.out_dir) if a.out_dir else HERE
os.makedirs(OUT_DIR, exist_ok=True)
N_PER_TRACK, MIN_H, SEED, TOP_FRAC = a.n_per_track, a.min_h, a.seed, 0.60

meta = pd.read_json(os.path.join(IN_DIR, "meta.json"), typ="series")
players = pd.read_csv(os.path.join(IN_DIR, "players.csv"))
players["h"] = players["y2"] - players["y1"]
trk_cls = players.groupby("track_id")["class_id"].agg(lambda s: s.mode().iloc[0])      # 0 oyuncu, 1 kaleci, 2 hakem
n_tracks_all = players["track_id"].nunique()

# ---------- 1) kirpim secimi ----------
rng = np.random.default_rng(SEED)
sel = []
for tid, g in players[players["h"] >= MIN_H].groupby("track_id"):
    idx = g.index.to_numpy()
    if len(idx) > N_PER_TRACK:
        idx = rng.choice(idx, N_PER_TRACK, replace=False)
    sel.append(players.loc[idx])
sel = pd.concat(sel).sort_values(["frame", "track_id"]).reset_index(drop=True)
print(f"Izler: {n_tracks_all} toplam, {sel['track_id'].nunique()} izde >= {MIN_H}px kirpim var; {len(sel)} kirpim")

need = {}
for r in sel.itertuples():
    need.setdefault(int(r.frame), []).append(r.Index)
cap = cv2.VideoCapture(os.path.join(HERE, str(meta["video"])))
if not cap.isOpened():
    raise SystemExit("HATA: video acilamadi")
f0, f1 = min(need), max(need)
cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
crops = [None] * len(sel)
for f in range(f0, f1 + 1):
    if f not in need:
        cap.grab()
        continue
    ok, img = cap.read()
    if not ok:
        break
    for i in need[f]:
        r = sel.loc[i]
        x1, x2 = max(int(r.x1), 0), min(int(r.x2), img.shape[1])
        y1, y2 = max(int(r.y1), 0), min(int(r.y1 + (r.y2 - r.y1) * TOP_FRAC), img.shape[0])
        if x2 - x1 >= 4 and y2 - y1 >= 4:
            crops[i] = cv2.cvtColor(img[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)
cap.release()
keep = [i for i, c in enumerate(crops) if c is not None]
sel = sel.loc[keep].reset_index(drop=True)
crops = [crops[i] for i in keep]
sel["cls"] = sel["track_id"].map(trk_cls)
print(f"Okunan kirpim: {len(crops)}  (sinif: {sel['cls'].value_counts().sort_index().to_dict()})")

# ---------- 2) SigLIP gomulumleri ----------
import torch
from transformers import AutoImageProcessor, SiglipVisionModel

dev = "cuda" if torch.cuda.is_available() else "cpu"
proc = AutoImageProcessor.from_pretrained("google/siglip-base-patch16-224")
model = SiglipVisionModel.from_pretrained("google/siglip-base-patch16-224").to(dev).eval()
if dev == "cuda":
    model = model.half()
embs = []
with torch.no_grad():
    for b in range(0, len(crops), 128):
        inp = proc(images=crops[b:b + 128], return_tensors="pt")
        px = inp["pixel_values"].to(dev)
        if dev == "cuda":
            px = px.half()
        embs.append(model(pixel_values=px).last_hidden_state.mean(dim=1).float().cpu().numpy())
embs = np.concatenate(embs)
print(f"Gomulum: {embs.shape} ({dev})")

# ---------- 3) UMAP(3) + KMeans ----------
import umap
from sklearn.cluster import KMeans

fit_mask = (sel["cls"] != 1).to_numpy()             # kaleci fit'e girmez
reducer = umap.UMAP(n_components=3, random_state=SEED)
z = np.zeros((len(sel), 3), np.float32)
z[fit_mask] = reducer.fit_transform(embs[fit_mask])
if (~fit_mask).any():
    z[~fit_mask] = reducer.transform(embs[~fit_mask])


def agreement_perm(labels_by_track, ref):
    """Kume numaralarini eski teams.csv ile hizala (en cok ortusen permutasyon)."""
    from itertools import permutations
    common = [t for t in labels_by_track.index if t in ref.index]
    k = int(labels_by_track.max()) + 1
    best, bp = -1, tuple(range(k))
    for perm in permutations(range(k)):
        sc = sum(perm[labels_by_track[t]] == ref[t] for t in common if ref[t] < k)
        if sc > best:
            best, bp = sc, perm
    return bp


old = pd.read_csv(os.path.join(IN_DIR, "teams.csv")).set_index("track_id")["team"]
summary = {}
for K, suffix in ((2, ""), (3, "_k3")):
    km = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit(z[fit_mask])
    lab = km.predict(z)
    d = np.linalg.norm(z - km.cluster_centers_[lab], axis=1)
    df = sel[["track_id", "cls"]].copy()
    df["lab"], df["d"] = lab, d
    rows = []
    for tid, g in df.groupby("track_id"):
        vc = g["lab"].value_counts()
        win = int(vc.index[0])
        rows.append(dict(track_id=tid, team=win, oy_orani=round(float(vc.iloc[0] / len(g)), 3),
                         kume_mesafesi=round(float(g.loc[g["lab"] == win, "d"].mean()), 3),
                         rol={0: "oyuncu", 1: "gk", 2: "hakem_sinifli"}[int(g["cls"].iloc[0])], n_kirpim=len(g)))
    out = pd.DataFrame(rows)
    # eski teams.csv ile hizala (yalniz oyuncu sinifli izlerde)
    pl = out[out["rol"] == "oyuncu"].set_index("track_id")["team"]
    perm = agreement_perm(pl, old)
    pm = {i: perm[i] for i in range(K)}
    out["team"] = out["team"].map(pm)
    sel[f"lab{K}"] = pd.Series(lab).map(pm).to_numpy()
    out.to_csv(os.path.join(OUT_DIR, f"teams_siglip{suffix}.csv"), index=False)
    # kume ozeti
    print(f"\n=== K={K}: kume x rol (iz sayisi) ===")
    print(pd.crosstab(out["team"], out["rol"]).to_string())
    print(f"kirpim sayisi / kume: {pd.Series(sel[f'lab{K}']).value_counts().sort_index().to_dict()}")
    print(f"oy_orani medyan {out['oy_orani'].median():.2f}; oy_orani<0.7: {(out['oy_orani'] < 0.7).sum()} iz")
    summary[K] = out

    # kontak sayfalari (kume basina 40 rastgele kirpim)
    r2 = np.random.default_rng(SEED + 1)
    for c in range(K):
        idx = np.where(sel[f"lab{K}"].to_numpy() == c)[0]
        pick = r2.choice(idx, min(40, len(idx)), replace=False) if len(idx) else []
        tiles = []
        for i in pick:
            t = cv2.resize(crops[i], (110, 110), interpolation=cv2.INTER_CUBIC)
            t = cv2.cvtColor(t, cv2.COLOR_RGB2BGR)
            tag = "PGR"[int(sel["cls"][i])] + str(int(sel["track_id"][i]))
            cv2.putText(t, tag, (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            tiles.append(t)
        while len(tiles) % 8:
            tiles.append(np.zeros((110, 110, 3), np.uint8))
        rows_ = [np.hstack(tiles[k:k + 8]) for k in range(0, len(tiles), 8)]
        name = f"kume_{c}.png" if K == 2 else f"kume_k3_{c}.png"
        if rows_:
            cv2.imwrite(os.path.join(OUT_DIR, name), np.vstack(rows_))
        print(f"  kontak sayfasi: {name} ({len(pick)} kirpim)")

# ---------- 4) eski K-means ile fark ----------
new = summary[2].set_index("track_id")
common = [t for t in old.index if t in new.index]
diff = [t for t in common if new.loc[t, "team"] != old[t]]
print(f"\nEski teams.csv: {len(old)} iz; SigLIP K=2 kapsami ile ortak: {len(common)}; farkli atanan: {len(diff)}")
