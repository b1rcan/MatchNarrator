"""
teshis_top_kaybi.py - Secilen olay aninda top cevresi teshis gorselleri + tablo (kod/parametre DEGISTIRMEZ)

Her olay icin etiket anindaki (ve istenirse +-0.5 sn) kare: top cevresi 3x yakin, tum oyuncu/hakem kutulari
(iz no, sinif, takim, topa uzaklik m), possession.csv sahibi kalin cerceve.
Girdiler: barca_tactical.mp4, players.csv, players_fixed.csv, ball_track.csv, possession.csv, homography.csv, teams.csv
          (tarama/baseline = eski K-means takim, varsayilan ayarlar)
Cikti: teshis_<zaman>_<offset>.png ve konsola tablo.
"""
import os

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0
POSS_DIST, MIN_POSS_FRAMES, MIN_RECEIVE_FRAMES_LOSS = 0.45, 2, 5      # events_v2.py ile ayni
ZOOM, CROP_W, CROP_H = 3, 320, 180
B = os.path.join(HERE, "tarama", "baseline")                          # varsayilan ayarlarin ciktilari
CLS = {0: "player", 1: "goalkeeper", 2: "referee"}

# (etiket zamani sn, etiket, ofsetler)
EVENTS = [(71.64, "TOP KAYBI FN", (-0.5, 0, 0.5)), (116.48, "TOP KAYBI FN", (-0.5, 0, 0.5)),
          (118.76, "TOP KAYBI FN", (-0.5, 0, 0.5)), (175.40, "TOP KAYBI FN", (-0.5, 0, 0.5)),
          (81.00, "TOP KAYBI FP", (0,)), (76.28, "TOP KAYBI FP", (0,))]

p0 = pd.read_csv(os.path.join(HERE, "players.csv"))
pf = pd.read_csv(os.path.join(B, "players_fixed.csv"), usecols=["frame", "track_id", "class_id"]).rename(columns={"class_id": "cls_fixed"})
players = p0.merge(pf, on=["frame", "track_id"], how="left")
bt = pd.read_csv(os.path.join(B, "ball_track.csv")).set_index("frame")
pos = pd.read_csv(os.path.join(B, "possession.csv")).drop_duplicates("frame").set_index("frame")["track_id"]
teams = pd.read_csv(os.path.join(B, "teams.csv")).set_index("track_id")["team"].to_dict()
hdf = pd.read_csv(os.path.join(HERE, "homography.csv"))
hdf = hdf[hdf["durum"] > 0]
HOMO = dict(zip(hdf["frame"].astype(int), hdf[[f"h{i}" for i in range(9)]].to_numpy(np.float64).reshape(-1, 3, 3)))
ref_ratio = p0.groupby("track_id")["class_id"].agg(lambda s: float((s == 2).mean()))
n_frames = p0.groupby("track_id").size()
cap = cv2.VideoCapture(os.path.join(HERE, "barca_tactical.mp4"))


def fmt(sec):
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


def team_str(tid, cls_fixed):
    if cls_fixed == 1:
        return "gk"
    if cls_fixed == 2:
        return "-"
    return "AB"[int(teams[tid])] if tid in teams else "?"


def to_m(f, pts):
    H = HOMO.get(int(f))
    if H is None:
        return None
    return cv2.perspectiveTransform(np.asarray(pts, np.float32).reshape(-1, 1, 2), H).reshape(-1, 2) / 100.0


def ball_at(f):
    """(x, y, durum) durum: 'tespit' | 'interpole' | 'yok'"""
    if f in bt.index and not np.isnan(bt.at[f, "bx"]):
        return bt.at[f, "bx"], bt.at[f, "by"], ("tespit" if bt.at[f, "detected"] else "interpole")
    return None, None, "yok"


def detections(f):
    """O karedeki tum kutular + topa uzaklik (m) ve normalize uzaklik."""
    d = players[players["frame"] == f].copy()
    bx, by, st = ball_at(f)
    d["fx"], d["fy"], d["h"] = (d.x1 + d.x2) / 2, d.y2, (d.y2 - d.y1).clip(lower=1)
    if bx is None:
        d["dist_m"], d["nd"] = np.nan, np.nan
        return d, (bx, by, st)
    d["nd"] = np.hypot(d.fx - bx, d.fy - by) / d.h
    pb = to_m(f, [[bx, by]])
    pp = to_m(f, np.column_stack((d.fx, d.fy))) if len(d) else None
    d["dist_m"] = np.linalg.norm(pp - pb[0], axis=1) if (pb is not None and pp is not None) else np.nan
    return d, (bx, by, st)


def render(f, tag, label, off):
    d, (bx, by, st) = detections(f)
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read()
    if not ok:
        return
    cx, cy, ball_note = bx, by, st
    if bx is None:                                           # top yok: en yakin bilinen konuma ortala
        for k in range(1, 26):
            for g in (f - k, f + k):
                x, y, s2 = ball_at(g)
                if x is not None:
                    cx, cy, ball_note = x, y, f"yok (en yakin bilinen: {g - f:+d} kare)"
                    break
            if cx is not None:
                break
        if cx is None:
            cx, cy = 640, 360
    x0 = int(np.clip(cx - CROP_W / 2, 0, img.shape[1] - CROP_W))
    y0 = int(np.clip(cy - CROP_H / 2, 0, img.shape[0] - CROP_H))
    owner = pos.get(f)
    view = cv2.resize(img[y0:y0 + CROP_H, x0:x0 + CROP_W], None, fx=ZOOM, fy=ZOOM, interpolation=cv2.INTER_CUBIC)
    colors = {"A": (255, 140, 0), "B": (0, 215, 255), "gk": (255, 255, 0), "-": (255, 0, 255), "?": (160, 160, 160)}
    for r in d.itertuples():
        a, b_, c, e = [(v - o) * ZOOM for v, o in ((r.x1, x0), (r.y1, y0), (r.x2, x0), (r.y2, y0))]
        if c < 0 or e < 0 or a > view.shape[1] or b_ > view.shape[0]:
            continue
        ts = team_str(r.track_id, r.cls_fixed if not np.isnan(r.cls_fixed) else r.class_id)
        col = colors[ts]
        thick = 5 if (owner is not None and r.track_id == owner) else 1
        cv2.rectangle(view, (int(a), int(b_)), (int(c), int(e)), (255, 255, 255) if thick > 1 else col, thick + (2 if thick > 1 else 0))
        if thick > 1:
            cv2.rectangle(view, (int(a), int(b_)), (int(c), int(e)), col, 2)
        dm = "" if np.isnan(r.dist_m) else f" {r.dist_m:.1f}m"
        orig = CLS[int(r.class_id)][:3]
        fix = "" if int(r.cls_fixed) == int(r.class_id) else f">{CLS[int(r.cls_fixed)][:3]}"
        cv2.putText(view, f"{int(r.track_id)} {orig}{fix} {ts}{dm}", (int(a), max(int(b_) - 4, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
    if bx is not None:
        cv2.circle(view, (int((bx - x0) * ZOOM), int((by - y0) * ZOOM)), 9, (0, 0, 255), 2)
        cv2.putText(view, "TOP" + ("" if st == "tespit" else " (interpole)"), (int((bx - x0) * ZOOM) + 10, int((by - y0) * ZOOM) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    head = f"{label} {fmt(f / FPS)} (ofset {off:+.1f}s, kare {f}) | top: {ball_note if bx is None else st} | sahip(possession): {owner if owner is not None else 'yok'}"
    cv2.rectangle(view, (0, 0), (view.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(view, head, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(view, "kutu: A mavi/turuncu, B sari, gk camgobegi, hakem mor; beyaz kalin = possession sahibi; sinif: orijinal>duzeltilmis",
                (6, view.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    name = f"teshis_{fmt(f / FPS).replace(':', '-')}_{('m' if off < 0 else 'p' if off > 0 else '')}{abs(off):g}.png"
    cv2.imwrite(os.path.join(HERE, name), view)
    return name


if __name__ == "__main__":
    for t, label, offs in EVENTS:
        f0 = int(round(t * FPS))
        print(f"\n################ {label} {fmt(t)} (kare {f0})")
        for off in offs:
            f = f0 + int(round(off * FPS))
            print("  gorsel:", render(f, label, label, off))
        # --- tablo: etiket anindaki 3 m icindeki tespitler ---
        d, (bx, by, st) = detections(f0)
        print(f"  top (etiket kare): {st}" + ("" if bx is None else f" ({bx:.0f},{by:.0f})") + f" | possession sahibi: {pos.get(f0, 'yok')}")
        near = d[d["dist_m"] <= 3.0].sort_values("dist_m")
        rows = []
        for r in near.itertuples():
            tid = int(r.track_id)
            cf = int(r.cls_fixed)
            cand = (r.nd < POSS_DIST) and cf in (0, 1)
            if r.class_id == 2:
                why = ("hakem-sinifli, oyuncuya CEVRILDI" if cf == 0 else "hakem-sinifli, HAKEM KALDI (disladi)") + \
                      f" [ref_orani {ref_ratio[tid]:.2f}, {int(n_frames[tid])} kare]"
            else:
                why = ""
            rows.append((tid, CLS[int(r.class_id)], CLS[cf], team_str(tid, cf), round(r.dist_m, 2), round(r.nd, 2), "EVET" if cand else "hayir", why))
        print(pd.DataFrame(rows, columns=["iz", "sinif", "sinif_duz", "takim", "mesafe_m", "nd(POSS<0.45)", "sahiplik_adayi", "hakem_notu"]).to_string(index=False)
              if rows else "  3 m icinde tespit YOK")
        # --- +-0.5 sn pencere ozeti (iz bazinda) ---
        agg = {}
        for f in range(f0 - 12, f0 + 13):
            dd, (b2, _, s2) = detections(f)
            if b2 is None:
                continue
            for r in dd[dd["dist_m"] <= 3.0].itertuples():
                a = agg.setdefault(int(r.track_id), dict(sinif=CLS[int(r.class_id)], duz=CLS[int(r.cls_fixed)], takim=team_str(int(r.track_id), int(r.cls_fixed)),
                                                       kare=0, min_m=9e9, min_nd=9e9, aday=0))
                a["kare"] += 1
                a["min_m"] = min(a["min_m"], r.dist_m)
                a["min_nd"] = min(a["min_nd"], r.nd)
                a["aday"] += int(r.nd < POSS_DIST and int(r.cls_fixed) in (0, 1))
        print(f"  +-0.5 sn penceresi (25 kare; top bilinen: {sum(ball_at(f)[2] != 'yok' for f in range(f0 - 12, f0 + 13))}/25): topa <=3 m izler")
        print(pd.DataFrame(agg).T.sort_values("min_m").to_string() if agg else "  yok")
        seq = [(int(pos[f]), int(f)) for f in range(f0 - 38, f0 + 39) if f in pos.index]
        runs = []
        for tid, f in seq:
            if runs and runs[-1][0] == tid:
                runs[-1][2] = f; runs[-1][3] += 1
            else:
                runs.append([tid, f, f, 1])
        print("  possession (+-1.5 sn):", " > ".join(f"{tid}{team_str(tid, 0)}[{fmt(a / FPS)[2:]}..{fmt(b / FPS)[2:]},{n}k]" for tid, a, b, n in runs) or "yok")
