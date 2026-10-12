"""tarama_08.py - POSS_DIST genisletme (60-180 sn): metrikler, belirsiz sahiplik, eslestirilmis bootstrap. Test seti kullanilmaz."""
import os
import numpy as np
import pandas as pd
import degerlendir as d
import tarama_filtre as tf
HERE = os.path.dirname(os.path.abspath(__file__))
FPS, F0, F1_ = 25.0, 1500, 4500
BASE = 0.45
VALS = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 1.00]


def name(v):
    return "baseline" if v == BASE else f"POSS_DIST_{v}"


for v in VALS:
    if v != BASE and not os.path.exists(os.path.join(HERE, "tarama", name(v), "events.csv")):
        tf.run_variant(name(v), {"POSS_DIST": v})
res = {v: tf.summarize(os.path.join(HERE, "tarama", name(v))) for v in VALS}
rb = res[BASE]; btp = tf.tpset(rb)[1]; bfp = tf.fpkeys(rb)

# --- belirsiz sahiplik: kare basina R icindeki aday sayisi (players_fixed sinif 0/1, top bilinen kareler, 60-180 sn)
pf = pd.read_csv(os.path.join(HERE, "tarama", "baseline", "players_fixed.csv"))
pf = pf[(pf.frame >= F0) & (pf.frame < F1_) & pf.class_id.isin([0, 1])]
bt = pd.read_csv(os.path.join(HERE, "tarama", "baseline", "ball_track.csv")).set_index("frame")
pf = pf.merge(bt[["bx", "by"]], left_on="frame", right_index=True).dropna(subset=["bx"])
pf["nd"] = np.hypot((pf.x1 + pf.x2) / 2 - pf.bx, pf.y2 - pf.by) / (pf.y2 - pf.y1).clip(lower=1)
n_known = int(bt.loc[F0:F1_ - 1, "bx"].notna().sum())


def segs(poss, gap=12, minf=2):
    out = []
    for r in poss.sort_values("frame").itertuples():
        if out and out[-1][0] == r.track_id and r.frame - out[-1][2] <= gap:
            out[-1][2] = r.frame; out[-1][3] += 1
        else:
            out.append([r.track_id, r.frame, r.frame, 1])
    return [s for s in out if s[3] >= minf]


rows = []
for v in VALS:
    r = res[v]; g = r["table"].set_index("grup")
    cnt = pf[pf.nd < v].groupby("frame").size()
    poss = pd.read_csv(os.path.join(HERE, "tarama", name(v), "possession.csv")); poss = poss[(poss.frame >= F0) & (poss.frame < F1_)]
    sg = segs(poss); dur = np.array([(s[2] - s[1] + 1) / FPS for s in sg])
    tp = tf.tpset(r)[1]
    rows.append(dict(POSS_DIST=v, TP=g.at["GENEL", "TP"], FP=g.at["GENEL", "FP"], FN=g.at["GENEL", "FN"], F1=g.at["GENEL", "F1"],
                     CI=f"{g.at['GENEL','F1_CI95_alt']:.2f}-{g.at['GENEL','F1_CI95_ust']:.2f}",
                     PAS=f"{g.at['PAS','TP']}/{g.at['PAS','FP']}/{g.at['PAS','FN']} F1 {g.at['PAS','F1']:.3f} ({g.at['PAS','F1_CI95_alt']:.2f}-{g.at['PAS','F1_CI95_ust']:.2f})",
                     TK=f"{g.at['TOP KAYBI','TP']}/{g.at['TOP KAYBI','FP']}/{g.at['TOP KAYBI','FN']} F1 {g.at['TOP KAYBI','F1']:.3f} ({g.at['TOP KAYBI','F1_CI95_alt']:.2f}-{g.at['TOP KAYBI','F1_CI95_ust']:.2f})",
                     sahiplik_kare_pct=round(100 * len(cnt) / n_known, 1), belirsiz_pct_tum=round(100 * (cnt >= 2).sum() / n_known, 1),
                     belirsiz_pct_sahipli=round(100 * (cnt >= 2).sum() / max(len(cnt), 1), 1),
                     ort_sahiplik_sn=round(float(dur.mean()), 2), med_sahiplik_sn=round(float(np.median(dur)), 2), n_seri=len(sg),
                     olay=len(r["ev"])))
df = pd.DataFrame(rows)
pd.set_option("display.width", 300, "display.max_colwidth", 80)
print(df.to_string(index=False))
df.to_csv(os.path.join(HERE, "tarama", "ozet_08_a.csv"), index=False)

print("\n=== eslestirilmis fark (taban 0.45) + duzelen/bozulan ===")
pr = []
for v in [0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 1.00]:
    r = res[v]; pb = d.paired_bootstrap(rb, r, 1000).set_index("grup")
    tp = tf.tpset(r)[1]; fixed = tp - btp; broken = btp - tp; new = sorted(tf.fpkeys(r) - bfp); gone = sorted(bfp - tf.fpkeys(r))
    used = set(); shift = 0
    for f, k in new:
        c = [x for x in gone if x[1] == k and x not in used and abs(x[0] - f) <= 25]
        if c: used.add(c[0]); shift += 1
    pr.append(dict(POSS_DIST=v, F1_fark=pb.at["GENEL", "fark"], CI=f"{pb.at['GENEL','CI_alt']:+.3f}..{pb.at['GENEL','CI_ust']:+.3f}", P_pozitif=pb.at["GENEL", "P_fark_pozitif"],
                   PAS_fark=pb.at["PAS", "fark"], PAS_CI=f"{pb.at['PAS','CI_alt']:+.3f}..{pb.at['PAS','CI_ust']:+.3f}", PAS_P=pb.at["PAS", "P_fark_pozitif"],
                   TK_fark=pb.at["TOP KAYBI", "fark"], TK_CI=f"{pb.at['TOP KAYBI','CI_alt']:+.3f}..{pb.at['TOP KAYBI','CI_ust']:+.3f}", TK_P=pb.at["TOP KAYBI", "P_fark_pozitif"],
                   duzelen=len(fixed), TP_FN=len(broken), yeni_FP=len(new), kayma=shift, fark_siki=len(fixed) - len(broken) - len(new),
                   fark_kaymasiz=len(fixed) - len(broken) - (len(new) - shift)))
    if v in (0.65, 0.70, 0.80, 1.00):
        print(f"\nPOSS_DIST={v}: DUZELEN {[(d.fmt(t), k[:3]) for t, k in sorted(fixed)]}\n  TP->FN {[(d.fmt(t), k[:3]) for t, k in sorted(broken)]}\n  YENI FP {[(d.fmt(f/25), k[:3]) for f, k in new]}\n  GIDEN FP {[(d.fmt(f/25), k[:3]) for f, k in gone]}")
pdf = pd.DataFrame(pr)
print(pdf.to_string(index=False))
pdf.to_csv(os.path.join(HERE, "tarama", "ozet_08_b.csv"), index=False)
