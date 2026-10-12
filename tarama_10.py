"""tarama_10.py - MIN_RECEIVE_FRAMES_LOSS {5,6,8,10,12}: gelistirme (60-180) ve dogrulama (360-540) AYRI. Test seti YOK.
Kabul: genel F1 farki > 0 her iki sette VE PAS F1 hicbir sette 0.02'den fazla dusmemeli."""
import os, subprocess, sys
import pandas as pd
import degerlendir as d
import tarama_filtre as tf
HERE = os.path.dirname(os.path.abspath(__file__))
VALS = [5, 6, 8, 10, 12]
SETS = {"gelistirme": dict(base="tarama/baseline", pre="tarama/MRFL_", inp=None, lab="gercek_olaylar.csv", s=60, e=180),
        "dogrulama": dict(base="veri_360_540", pre="veri_360_540/mrfl_", inp="veri_360_540", lab="gercek_olaylar_val.csv", s=360, e=540)}
res = {}
for sn, c in SETS.items():
    for v in VALS:
        out = os.path.join(HERE, c["base"] if v == 5 else f"{c['pre']}{v}")
        if v != 5 and not os.path.exists(os.path.join(out, "events.csv")):
            cmd = [sys.executable, os.path.join(HERE, "events_v2.py"), "--out-dir", out, "--set", f"MIN_RECEIVE_FRAMES_LOSS={v}"]
            if c["inp"]: cmd += ["--in-dir", os.path.join(HERE, c["inp"])]
            subprocess.run(cmd, check=True, capture_output=True, cwd=HERE)
        res[(sn, v)] = d.run(os.path.join(out, "events.csv"), os.path.join(HERE, c["lab"]), c["s"], c["e"], 1.0, quiet=True)
rows = []
for v in VALS:
    row = dict(MRFL=v)
    for sn in SETS:
        r = res[(sn, v)]; b = res[(sn, 5)]; g = r["table"].set_index("grup"); gb = b["table"].set_index("grup")
        pb = d.paired_bootstrap(b, r, 1000).set_index("grup") if v != 5 else None
        tp = tf.tpset(r)[1]; btp = tf.tpset(b)[1]
        pre = sn[:3]
        row[f"{pre}_TK_TP/FP/FN"] = f"{g.at['TOP KAYBI','TP']}/{g.at['TOP KAYBI','FP']}/{g.at['TOP KAYBI','FN']}"
        row[f"{pre}_TK_F1"] = g.at["TOP KAYBI", "F1"]
        row[f"{pre}_genel_TP/FP/FN"] = f"{g.at['GENEL','TP']}/{g.at['GENEL','FP']}/{g.at['GENEL','FN']}"
        row[f"{pre}_genel_F1(CI)"] = f"{g.at['GENEL','F1']:.3f} ({g.at['GENEL','F1_CI95_alt']:.2f}-{g.at['GENEL','F1_CI95_ust']:.2f})"
        row[f"{pre}_PAS_F1"] = g.at["PAS", "F1"]
        row[f"{pre}_genel_fark"] = round(g.at["GENEL", "F1"] - gb.at["GENEL", "F1"], 3)
        row[f"{pre}_PAS_fark"] = round(g.at["PAS", "F1"] - gb.at["PAS", "F1"], 3)
        row[f"{pre}_boot_fark(CI)P"] = "-" if pb is None else f"{pb.at['GENEL','fark']:+.3f} ({pb.at['GENEL','CI_alt']:+.3f}..{pb.at['GENEL','CI_ust']:+.3f}) P={pb.at['GENEL','P_fark_pozitif']:.2f}"
        row[f"{pre}_TK_boot"] = "-" if pb is None else f"{pb.at['TOP KAYBI','fark']:+.3f} ({pb.at['TOP KAYBI','CI_alt']:+.3f}..{pb.at['TOP KAYBI','CI_ust']:+.3f})"
        row[f"{pre}_duzelen/TP->FN/yeniFP"] = "-" if v == 5 else f"{len(tp-btp)}/{len(btp-tp)}/{len(tf.fpkeys(r)-tf.fpkeys(b))}"
    gok = row["gel_genel_fark"] > 0 and row["dog_genel_fark"] > 0
    pok = row["gel_PAS_fark"] >= -0.02 and row["dog_PAS_fark"] >= -0.02
    row["karar"] = "(mevcut)" if v == 5 else ("ONERILIR" if gok and pok else "onerilmez")
    row["_neden"] = "" if v == 5 else f"genel>0 iki sette: {gok}; PAS>=-0.02: {pok}"
    rows.append(row)
df = pd.DataFrame(rows)
pd.set_option("display.width", 400, "display.max_columns", 60, "display.max_colwidth", 70)
print(df.T.to_string())
df.to_csv(os.path.join(HERE, "tarama", "ozet_10.csv"), index=False)
for sn in SETS:
    for v in VALS[1:]:
        r, b = res[(sn, v)], res[(sn, 5)]; tp, btp = tf.tpset(r)[1], tf.tpset(b)[1]
        print(f"{sn} MRFL={v}: DUZELEN {[(d.fmt(t), k[:3]) for t, k in sorted(tp-btp)]} TP->FN {[(d.fmt(t), k[:3]) for t, k in sorted(btp-tp)]} YENI FP {[(d.fmt(f/25), k[:3]) for f, k in sorted(tf.fpkeys(r)-tf.fpkeys(b))]} GIDEN FP {[(d.fmt(f/25), k[:3]) for f, k in sorted(tf.fpkeys(b)-tf.fpkeys(r))]}")
