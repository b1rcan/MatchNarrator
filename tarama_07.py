"""tarama_07.py - OLCUM_07 taramalari (yalniz gelistirme seti 60-180 sn). Kabul: duzelen - bozulan >= 2."""
import os, sys
import pandas as pd
import degerlendir as d
import tarama_filtre as tf
HERE = os.path.dirname(os.path.abspath(__file__))
GRIDS = {"ID_MERGE_REQUIRE_SAME_TEAM": ([0, 1], 0),
         "POSS_DIST": ([0.40, 0.45, 0.50, 0.55, 0.60], 0.45),
         "MIN_POSS_FRAMES": ([1, 2, 3], 2)}
rb = tf.summarize(os.path.join(HERE, "tarama", "baseline")); base_tp = tf.tpset(rb)[1]; base_fp = tf.fpkeys(rb)
rows = []
for p, (vals, base) in GRIDS.items():
    for v in vals:
        name = f"{p}_{v}"
        out = os.path.join(HERE, "tarama", name)
        if v != base and not os.path.exists(os.path.join(out, "events.csv")):
            tf.run_variant(name, {p: v})
        r = rb if v == base else tf.summarize(out)
        tp = tf.tpset(r)[1]
        fixed = sorted(tp - base_tp); broken = sorted(base_tp - tp); newfp = sorted(tf.fpkeys(r) - base_fp); gone = sorted(base_fp - tf.fpkeys(r))
        g = r["table"].iloc[0]; gp = r["table"].iloc[1]; gk = r["table"].iloc[2]
        rows.append(dict(parametre=p, deger=v, TP=g.TP, FP=g.FP, FN=g.FN, F1=g.F1, CI=f"{g.F1_CI95_alt:.2f}-{g.F1_CI95_ust:.2f}",
                         F1_PAS=gp.F1, F1_TK=gk.F1, TK_TP=gk.TP, duzelen=len(fixed), bozulan=len(broken) + len(newfp),
                         fark=len(fixed) - len(broken) - len(newfp), giden_FP=len(gone),
                         duzelen_z=", ".join(f"{d.fmt(t)} {k[:3]}" for t, k in fixed),
                         bozulan_z=", ".join([f"{d.fmt(t)} {k[:3]} (TP->FN)" for t, k in broken] + [f"{d.fmt(f / 25)} {k[:3]} (yeni FP)" for f, k in newfp]),
                         giden_z=", ".join(f"{d.fmt(f / 25)} {k[:3]}" for f, k in gone)))
df = pd.DataFrame(rows)
df["oneri"] = ["(mevcut)" if v == GRIDS[p][1] else ("ONERILIR" if f >= 2 else "onerilmez") for p, v, f in zip(df.parametre, df.deger, df.fark)]
df.to_csv(os.path.join(HERE, "tarama", "ozet_07.csv"), index=False)
pd.set_option("display.width", 250)
print(df.drop(columns=["duzelen_z", "bozulan_z", "giden_z"]).to_string(index=False))
for r in df.itertuples():
    if r.oneri != "(mevcut)":
        print(f"\n{r.parametre}={r.deger}: DUZELEN [{r.duzelen_z}]\n   BOZULAN [{r.bozulan_z}]\n   GIDEN FP [{r.giden_z}]")
