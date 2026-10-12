"""tarama_val.py - OLCUM_09: dogrulama seti (360-540 sn) POSS_DIST taramasi + uc set taban tablosu. Varsayilanlar degismez."""
import os, subprocess, sys
import numpy as np
import pandas as pd
import degerlendir as d
import tarama_filtre as tf
HERE = os.path.dirname(os.path.abspath(__file__))
VAL_LAB, VAL_S, VAL_E = "gercek_olaylar_val.csv", 360, 540
VALS = [0.45, 0.60, 0.65, 0.70]


def vdir(v):
    return os.path.join(HERE, "veri_360_540") if v == 0.45 else os.path.join(HERE, "veri_360_540", f"poss_{v}")


for v in VALS[1:]:
    if not os.path.exists(os.path.join(vdir(v), "events.csv")):
        subprocess.run([sys.executable, os.path.join(HERE, "events_v2.py"), "--in-dir", os.path.join(HERE, "veri_360_540"),
                        "--out-dir", vdir(v), "--set", f"POSS_DIST={v}"], check=True, capture_output=True, cwd=HERE)
res = {v: d.run(os.path.join(vdir(v), "events.csv"), VAL_LAB, VAL_S, VAL_E, 1.0, quiet=True) for v in VALS}
rb = res[0.45]; btp = tf.tpset(rb)[1]; bfp = tf.fpkeys(rb)
print("=== DOGRULAMA SETI (360-540 sn), etiket", rb["n_gt"], "===")
rows = []
for v in VALS:
    r = res[v]; g = r["table"].set_index("grup")
    row = dict(POSS_DIST=v, tahmin=r["n_ev"])
    for k, n in (("GENEL", "G"), ("PAS", "PAS"), ("TOP KAYBI", "TK")):
        row[f"{n}_TP/FP/FN"] = f"{g.at[k,'TP']}/{g.at[k,'FP']}/{g.at[k,'FN']}"
        row[f"{n}_P/R"] = f"{g.at[k,'P']:.2f}/{g.at[k,'R']:.2f}"
        row[f"{n}_F1(CI)"] = f"{g.at[k,'F1']:.3f} ({g.at[k,'F1_CI95_alt']:.2f}-{g.at[k,'F1_CI95_ust']:.2f})"
    if "fark" in r:
        row["zaman_medyan/std"] = f"{r['fark']['medyan']:+.2f}/{r['fark']['std']:.2f}"
    rows.append(row)
pd.set_option("display.width", 320)
print(pd.DataFrame(rows).T.to_string())
print("\n=== eslestirilmis fark (taban 0.45) ===")
for v in VALS[1:]:
    r = res[v]; pb = d.paired_bootstrap(rb, r, 1000).set_index("grup")
    tp = tf.tpset(r)[1]; fixed = sorted(tp - btp); broken = sorted(btp - tp); new = sorted(tf.fpkeys(r) - bfp); gone = sorted(bfp - tf.fpkeys(r))
    used = set(); shift = 0
    for f, k in new:
        c = [x for x in gone if x[1] == k and x not in used and abs(x[0] - f) <= 25]
        if c: used.add(c[0]); shift += 1
    print(f"\nPOSS_DIST={v}: F1 fark GENEL {pb.at['GENEL','fark']:+.3f} ({pb.at['GENEL','CI_alt']:+.3f}..{pb.at['GENEL','CI_ust']:+.3f}) P>0 {pb.at['GENEL','P_fark_pozitif']:.3f} | PAS {pb.at['PAS','fark']:+.3f} ({pb.at['PAS','CI_alt']:+.3f}..{pb.at['PAS','CI_ust']:+.3f}) P>0 {pb.at['PAS','P_fark_pozitif']:.3f} | TK {pb.at['TOP KAYBI','fark']:+.3f} ({pb.at['TOP KAYBI','CI_alt']:+.3f}..{pb.at['TOP KAYBI','CI_ust']:+.3f}) P>0 {pb.at['TOP KAYBI','P_fark_pozitif']:.3f}")
    print(f"  duzelen {len(fixed)}, TP->FN {len(broken)}, yeni FP {len(new)} (kayma {shift}), FARK SIKI {len(fixed)-len(broken)-len(new)}, kaymasiz {len(fixed)-len(broken)-(len(new)-shift)}")
    print("  DUZELEN", [(d.fmt(t), k[:3]) for t, k in fixed]); print("  TP->FN ", [(d.fmt(t), k[:3]) for t, k in broken])
    print("  YENI FP", [(d.fmt(f / 25), k[:3]) for f, k in new]); print("  GIDEN FP", [(d.fmt(f / 25), k[:3]) for f, k in gone])

# --- uc set taban tablosu (yalniz toplu sayilar) ---
sets = {"gelistirme 60-180": (os.path.join(HERE, "tarama", "baseline", "events.csv"), "gercek_olaylar.csv", 60, 180),
        "test 180-300": (os.path.join(HERE, "tarama", "baseline", "events.csv"), "gercek_olaylar_test.csv", 180, 300),
        "dogrulama 360-540": (os.path.join(vdir(0.45), "events.csv"), VAL_LAB, VAL_S, VAL_E)}
tot = dict(TP=0, FP=0, FN=0, n=0)
out = []
for name, (ev, lab, s, e) in sets.items():
    r = d.run(ev, lab, s, e, 1.0, quiet=True); g = r["table"].set_index("grup").loc["GENEL"]
    out.append(dict(set=name, etiket=r["n_gt"], tahmin=r["n_ev"], TP=g.TP, FP=g.FP, FN=g.FN, P=g.P, R=g.R, F1=g.F1, CI=f"{g.F1_CI95_alt:.2f}-{g.F1_CI95_ust:.2f}"))
    for k in ("TP", "FP", "FN"): tot[k] += int(g[k])
    tot["n"] += r["n_gt"]
tp, fp, fn = tot["TP"], tot["FP"], tot["FN"]
P, R = tp / (tp + fp), tp / (tp + fn); F = 2 * tp / (2 * tp + fp + fn)
lo, hi = d.bootstrap_f1(tp, fp, fn)
out.append(dict(set="BIRLESIK (3 set)", etiket=tot["n"], tahmin=tp + fp, TP=tp, FP=fp, FN=fn, P=round(P, 3), R=round(R, 3), F1=round(F, 3), CI=f"{lo:.2f}-{hi:.2f}"))
print("\n=== UC SET TABAN (POSS_DIST=0.45) ==="); print(pd.DataFrame(out).to_string(index=False))
