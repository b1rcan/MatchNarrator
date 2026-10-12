"""karsilastir_takim.py - eski (K-means) vs --teams takim atamasi, YALNIZCA gelistirme seti (60-180 sn)."""
import os, sys
import pandas as pd
import degerlendir as d
import tarama_filtre as tf
HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else "tarama/baseline"
B = sys.argv[2] if len(sys.argv) > 2 else "tarama/siglip_k2"
ra = tf.summarize(os.path.join(HERE, A)); rb = tf.summarize(os.path.join(HERE, B))
print(ra["table"].to_string(index=False)); print(rb["table"].to_string(index=False))
tpa, tpb = tf.tpset(ra)[1], tf.tpset(rb)[1]
fixed = sorted(tpb - tpa); broken = sorted(tpa - tpb); newfp = sorted(tf.fpkeys(rb) - tf.fpkeys(ra)); gonefp = sorted(tf.fpkeys(ra) - tf.fpkeys(rb))
print("DUZELEN (FN->TP):", [(d.fmt(t), k) for t, k in fixed])
print("BOZULAN TP->FN :", [(d.fmt(t), k) for t, k in broken])
print("YENI FP        :", [(d.fmt(f / 25), k) for f, k in newfp])
print("GIDEN FP       :", [(d.fmt(f / 25), k) for f, k in gonefp])
print("duzelen - bozulan =", len(fixed) - len(broken) - len(newfp))
print("fark A:", ra["fark"]); print("fark B:", rb["fark"])
# TOP KAYBI etiketleri ve takim-kategorisi
gt = ra["gt"]
for name, r in (("eski", ra), ("siglip", rb)):
    tp = {r["gt"].sec[i] for i, _ in r["m"]}
    print(f"\n[{name}] TOP KAYBI etiketleri:", {d.fmt(s): ("TP" if s in tp else "FN") for s in gt[gt.tip == "TOP KAYBI"].sec})
    print(f"[{name}] TOP KAYBI tahminleri (aralikta):", [(d.fmt(x.sec), int(x.kimden), int(x.kime)) for x in r["ev"][r["ev"].tip == "TOP KAYBI"].itertuples()])
