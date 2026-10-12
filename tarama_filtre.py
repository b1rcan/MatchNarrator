"""
tarama_filtre.py - Tek-parametre taramasi (YALNIZCA gelistirme seti, 60-180 sn)

Her calistirmada tek parametre degisir; digerleri events_v2.py'deki mevcut deger.
Ciktilar tarama/<param>_<deger>/ klasorune yazilir (ana ciktilar korunur).
Kullanim: python tarama_filtre.py
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

import degerlendir as d

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS, START, END, TOL = "gercek_olaylar.csv", 60, 180, 1.0     # test seti burada KULLANILMAZ
GRID = {"MIN_RECEIVE_FRAMES": [2, 3, 4], "MIN_RECEIVE_FRAMES_LOSS": [3, 4, 5],
        "DRIBBLE_GAP": [6, 9, 12], "MAX_INTERP_GAP": [10, 15, 20], "DOGRULAMA_KARE": [2, 3]}
BASE = {"MIN_RECEIVE_FRAMES": 4, "MIN_RECEIVE_FRAMES_LOSS": 5, "DRIBBLE_GAP": 12,
        "MAX_INTERP_GAP": 10, "DOGRULAMA_KARE": 3}


def run_variant(name, sets):
    out = os.path.join(HERE, "tarama", name)
    cmd = [sys.executable, os.path.join(HERE, "events_v2.py"), "--out-dir", out]
    for k, v in sets.items():
        cmd += ["--set", f"{k}={v}"]
    subprocess.run(cmd, check=True, capture_output=True, cwd=HERE)
    return out


def summarize(outdir):
    return d.run(os.path.join(outdir, "events.csv"), LABELS, START, END, TOL, quiet=True)


def tpset(r):
    return {r["gt"].sec[i] for i, _ in r["m"]}, {(r["gt"].sec[i], r["gt"].tip[i]) for i, _ in r["m"]}


def fpkeys(r):
    return {(int(r["ev"].frame[j]), r["ev"].tip[j]) for j in r["fp"]}


if __name__ == "__main__":
    base_out = run_variant("baseline", {})
    rb = summarize(base_out)
    base_tp = tpset(rb)[1]
    base_fp = fpkeys(rb)
    rows = []
    for p, vals in GRID.items():
        for v in vals:
            if v == BASE[p]:
                r, name = rb, "baseline"
            else:
                r = summarize(run_variant(f"{p}_{v}", {p: v}))
            tp = tpset(r)[1]
            fixed = sorted(tp - base_tp, key=lambda x: x[0])
            broken = sorted(base_tp - tp, key=lambda x: x[0])
            newfp = sorted(fpkeys(r) - base_fp)
            g = r["table"].iloc[0]
            rows.append(dict(parametre=p, deger=v, TP=g.TP, FP=g.FP, FN=g.FN, F1=g.F1,
                             CI=f"{g.F1_CI95_alt:.2f}-{g.F1_CI95_ust:.2f}",
                             duzelen=len(fixed), bozulan_TPFN=len(broken), yeni_FP=len(newfp),
                             bozulan=len(broken) + len(newfp),
                             duzelen_zaman=", ".join(d.fmt(t) + " " + k[:3] for t, k in fixed),
                             bozulan_zaman=", ".join([d.fmt(t) + " " + k[:3] + " (TP->FN)" for t, k in broken]
                                                     + [d.fmt(f / 25) + " " + k[:3] + " (yeni FP)" for f, k in newfp])))
    df = pd.DataFrame(rows)
    df["oneri"] = np.where(df.deger.astype(int) == df.parametre.map(BASE), "(mevcut)",
                           np.where(df.duzelen - df.bozulan >= 2, "ONERILIR", "onerilmez"))
    df.to_csv(os.path.join(HERE, "tarama", "ozet.csv"), index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 120)
    print(df.drop(columns=["duzelen_zaman", "bozulan_zaman"]).to_string(index=False))
    print()
    for r in df.itertuples():
        if r.oneri != "(mevcut)":
            print(f"{r.parametre}={r.deger}: DUZELEN [{r.duzelen_zaman}] | BOZULAN [{r.bozulan_zaman}]")
