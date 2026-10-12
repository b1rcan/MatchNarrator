"""tk_fp_analiz.py - TOP KAYBI FP'lerinin ozellik tablosu (gelistirme + dogrulama; test seti YOK)."""
import os, sys
import numpy as np
import pandas as pd
import degerlendir as d
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0
SETS = {"gelistirme": dict(ev="tarama/baseline", inp=".", lab="gercek_olaylar.csv", s=60, e=180),
        "dogrulama": dict(ev="veri_360_540", inp="veri_360_540", lab="gercek_olaylar_val.csv", s=360, e=540)}


def speed(bt, f, a, b):
    """f+a .. f+b araligindaki top hizi (m/sn): saha koordinatinda ardisik kare farklari medyani"""
    w = bt.loc[f + a:f + b, ["saha_x_m", "saha_y_m"]].dropna()
    if len(w) < 2:
        return np.nan
    dd = np.hypot(np.diff(w.saha_x_m), np.diff(w.saha_y_m)) / np.maximum(np.diff(w.index.to_numpy()), 1) * FPS
    return float(np.median(dd))


rows = []
for name, c in SETS.items():
    evd, ind = os.path.join(HERE, c["ev"]), os.path.join(HERE, c["inp"])
    r = d.run(os.path.join(evd, "events.csv"), os.path.join(HERE, c["lab"]), c["s"], c["e"], 1.0, quiet=True)
    ev, gt = r["ev"], r["gt"]
    cand = pd.read_csv(os.path.join(evd, "events_adaylar.csv"))
    bt = pd.read_csv(os.path.join(evd, "ball_track.csv")).set_index("frame")
    pos = pd.read_csv(os.path.join(evd, "possession.csv"))
    teams = pd.read_csv(os.path.join(evd, "teams.csv")).set_index("track_id").team.to_dict()
    pl = pd.read_csv(os.path.join(ind, "players.csv"))
    cls0 = pl.groupby("track_id").class_id.agg(lambda s: s.mode().iloc[0]).to_dict()
    lab_mean = pl.groupby("track_id")[["L", "A", "B"]].median()
    tm = {t: lab_mean.loc[[k for k, v in teams.items() if v == t and k in lab_mean.index]].mean() for t in (0, 1)}
    first = pl.groupby("track_id").frame.min(); last = pl.groupby("track_id").frame.max()
    hh = (pl.y2 - pl.y1).groupby(pl.track_id).median()
    for j in r["fp"]:
        x = ev.loc[j]
        if x.tip != "TOP KAYBI":
            continue
        f = int(x.frame); a, b = int(x.kimden), int(x.kime)
        cj = cand[(cand.frame == f) & (cand.kimden == a) & (cand.kime == b) & (cand.karar == "kabul")]
        n_recv = int(cj.alici_kare.iloc[0]) if len(cj) else -1
        run = pos[pos.frame >= f]; k = 0                     # yeni sahibin possession.csv'deki kesintisiz kare sayisi
        fr = run[run.track_id == b].frame.to_numpy()
        # sonraki farkli sahip
        nxt = run[run.track_id != b]; nxt = nxt[nxt.frame > f]
        nxt_owner = int(nxt.track_id.iloc[0]) if len(nxt) else None
        t_nxt = (int(nxt.frame.iloc[0]) - f) / FPS if len(nxt) else np.nan
        # onceki sahip son kare / mesafe
        gap = float(x.sure_sn)
        # renk marji: iz medyan Lab'i kendi takim ortalamasina vs digerine
        def margin(t):
            if t not in lab_mean.index or t not in teams: return np.nan
            own, oth = tm[teams[t]], tm[1 - teams[t]]
            v = lab_mean.loc[t]; return float(np.linalg.norm(v - oth) - np.linalg.norm(v - own))   # + : kendi takimina yakin
        # iz kimligi: ayni anda var mi / birbirini izliyor mu
        coexist = max(0, min(last[a], last[b]) - max(first[a], first[b]))
        near_gt = gt[(gt.sec - x.sec).abs() <= 2.0]
        near_ev = ev[(ev.sec - x.sec).abs() <= 2.0]
        topdurum = "yok" if f not in bt.index or np.isnan(bt.at[f, "bx"]) else ("tespit" if bt.at[f, "detected"] else "interpole")
        rows.append(dict(set=name, zaman=d.fmt(x.sec), frame=f, kimden=f"{a}{'AB'[teams[a]] if a in teams else '?'}", kime=f"{b}{'AB'[teams[b]] if b in teams else '?'}",
                         top=topdurum, alici_kare=n_recv, poss_kesintisiz=int(len(fr)), gap_sn=gap, mesafe_m=x.mesafe_m, hiz_ms=x.hiz_ms,
                         top_hiz_once=round(speed(bt, f, -6, -1), 1), top_hiz_sonra=round(speed(bt, f, 0, 5), 1),
                         sonraki_sahip=("-" if nxt_owner is None else f"{nxt_owner}{'AB'[teams[nxt_owner]] if nxt_owner in teams else '?'}"), sonraki_sn=round(t_nxt, 2),
                         renk_marj_kimden=round(margin(a), 1), renk_marj_kime=round(margin(b), 1), iz_ortak_kare=coexist,
                         sinif_kimden=int(cls0.get(a, -1)), sinif_kime=int(cls0.get(b, -1)),
                         yakin_etiket=", ".join(f"{d.fmt(s)[2:]} {t[:3]}" for s, t in zip(near_gt.sec, near_gt.tip)) or "-",
                         yakin_olay=", ".join(f"{d.fmt(s)[2:]} {t[:3]}" for s, t in zip(near_ev.sec, near_ev.tip) if abs(s - x.sec) > 1e-6) or "-"))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "tarama", "tk_fp_ozellik.csv"), index=False)
pd.set_option("display.width", 400, "display.max_columns", 40, "display.max_colwidth", 60)
print(df.to_string(index=False))
