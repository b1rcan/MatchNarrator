"""
teshis_tk_fp.py - TOP KAYBI FP'leri icin annotasyonlu kare gorselleri (gelistirme/dogrulama; test seti YOK)

Her FP icin yan yana iki panel (top cevresi 3x yakin):
  SOL  = eski sahibin son sahiplik karesi (olaydan 'bosluk_sn' once)
  SAG  = olay karesi (yeni sahibin sahiplik serisinin ilk karesi)
Kutular: iz no, orijinal>duzeltilmis sinif, takim (A/B), topa uzaklik (m); kalin beyaz cerceve = possession.csv sahibi.
Kullanim: python teshis_tk_fp.py gelistirme:76.28 dogrulama:376.16 ...   (set:olay_saniyesi)
Cikti: teshis_tk_fp_<m-ss.ss>.png
"""
import os
import sys

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, ZOOM, CROP_W, CROP_H = 25.0, 3, 320, 180
CLS = {0: "player", 1: "goalkeeper", 2: "referee"}
SETS = {"gelistirme": dict(inp=HERE, out=os.path.join(HERE, "tarama", "baseline")),
        "dogrulama": dict(inp=os.path.join(HERE, "veri_360_540"), out=os.path.join(HERE, "veri_360_540"))}
COL = {"A": (255, 140, 0), "B": (0, 215, 255), "gk": (255, 255, 0), "-": (255, 0, 255), "?": (160, 160, 160)}
cap = cv2.VideoCapture(os.path.join(HERE, "barca_tactical.mp4"))


def fmt(sec):
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


class Data:
    def __init__(self, inp, out):
        p0 = pd.read_csv(os.path.join(inp, "players.csv"))
        pf = pd.read_csv(os.path.join(out, "players_fixed.csv"), usecols=["frame", "track_id", "class_id"]).rename(columns={"class_id": "cls_fixed"})
        self.players = p0.merge(pf, on=["frame", "track_id"], how="left")
        self.bt = pd.read_csv(os.path.join(out, "ball_track.csv")).set_index("frame")
        self.pos = pd.read_csv(os.path.join(out, "possession.csv")).drop_duplicates("frame").set_index("frame")["track_id"]
        self.teams = pd.read_csv(os.path.join(out, "teams.csv")).set_index("track_id")["team"].to_dict()
        hdf = pd.read_csv(os.path.join(inp, "homography.csv"))
        hdf = hdf[hdf["durum"] > 0]
        self.homo = dict(zip(hdf["frame"].astype(int), hdf[[f"h{i}" for i in range(9)]].to_numpy(np.float64).reshape(-1, 3, 3)))
        self.ev = pd.read_csv(os.path.join(out, "events.csv"))

    def team_str(self, tid, cf):
        if cf == 1:
            return "gk"
        if cf == 2:
            return "-"
        return "AB"[int(self.teams[tid])] if tid in self.teams else "?"

    def to_m(self, f, pts):
        H = self.homo.get(int(f))
        return None if H is None else cv2.perspectiveTransform(np.asarray(pts, np.float32).reshape(-1, 1, 2), H).reshape(-1, 2) / 100.0

    def ball(self, f):
        if f in self.bt.index and not np.isnan(self.bt.at[f, "bx"]):
            return self.bt.at[f, "bx"], self.bt.at[f, "by"], ("tespit" if self.bt.at[f, "detected"] else "interpole")
        return None, None, "yok"


def panel(D, f, title):
    d = D.players[D.players["frame"] == f].copy()
    bx, by, st = D.ball(f)
    d["fx"], d["fy"], d["h"] = (d.x1 + d.x2) / 2, d.y2, (d.y2 - d.y1).clip(lower=1)
    if bx is not None:
        pb, pp = D.to_m(f, [[bx, by]]), (D.to_m(f, np.column_stack((d.fx, d.fy))) if len(d) else None)
        d["dist_m"] = np.linalg.norm(pp - pb[0], axis=1) if (pb is not None and pp is not None) else np.nan
    else:
        d["dist_m"] = np.nan
    cx, cy, note = bx, by, st
    if bx is None:
        for k in range(1, 26):
            for g in (f - k, f + k):
                x, y, _ = D.ball(g)
                if x is not None:
                    cx, cy, note = x, y, f"yok (en yakin bilinen {g - f:+d} kare)"
                    break
            if cx is not None:
                break
        if cx is None:
            cx, cy = 640, 360
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ok, img = cap.read()
    x0 = int(np.clip(cx - CROP_W / 2, 0, img.shape[1] - CROP_W))
    y0 = int(np.clip(cy - CROP_H / 2, 0, img.shape[0] - CROP_H))
    view = cv2.resize(img[y0:y0 + CROP_H, x0:x0 + CROP_W], None, fx=ZOOM, fy=ZOOM, interpolation=cv2.INTER_CUBIC)
    owner = D.pos.get(f)
    for r in d.itertuples():
        a, b_, c, e = [(v - o) * ZOOM for v, o in ((r.x1, x0), (r.y1, y0), (r.x2, x0), (r.y2, y0))]
        if c < 0 or e < 0 or a > view.shape[1] or b_ > view.shape[0]:
            continue
        cf = int(r.cls_fixed) if not np.isnan(r.cls_fixed) else int(r.class_id)
        ts = D.team_str(r.track_id, cf)
        col = COL[ts]
        own = owner is not None and r.track_id == owner
        if own:
            cv2.rectangle(view, (int(a), int(b_)), (int(c), int(e)), (255, 255, 255), 7)
        cv2.rectangle(view, (int(a), int(b_)), (int(c), int(e)), col, 2)
        fix = "" if cf == int(r.class_id) else f">{CLS[cf][:3]}"
        cv2.putText(view, f"{int(r.track_id)} {CLS[int(r.class_id)][:3]}{fix} {ts}" + ("" if np.isnan(r.dist_m) else f" {r.dist_m:.1f}m"),
                    (int(a), max(int(b_) - 4, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)
    if bx is not None:
        cv2.circle(view, (int((bx - x0) * ZOOM), int((by - y0) * ZOOM)), 9, (0, 0, 255), 2)
        cv2.putText(view, "TOP" + ("" if st == "tespit" else " (interpole)"), (int((bx - x0) * ZOOM) + 10, int((by - y0) * ZOOM) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    cv2.rectangle(view, (0, 0), (view.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(view, f"{title} {fmt(f / FPS)} kare {f} | top: {note} | sahip: {owner if owner is not None else 'yok'}", (6, 17),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return view


if __name__ == "__main__":
    loaded = {}
    for arg in sys.argv[1:]:
        sname, sec = arg.split(":")
        D = loaded.setdefault(sname, Data(**SETS[sname]))
        e = D.ev[(D.ev.sec - float(sec)).abs() < 0.015]
        e = e[e.tip == "TOP KAYBI"].iloc[0]
        f_ev = int(e.frame)
        f_old = max(f_ev - int(round(e.sure_sn * FPS)), 0)
        left = panel(D, f_old, f"ESKI SAHIP {int(e.kimden)} son kare")
        right = panel(D, f_ev, f"OLAY {int(e.kimden)}>{int(e.kime)}")
        sep = np.full((left.shape[0], 8, 3), 255, np.uint8)
        name = f"teshis_tk_fp_{fmt(float(e.sec)).replace(':', '-')}.png"
        cv2.imwrite(os.path.join(HERE, name), np.hstack([left, sep, right]))
        print(name)
