"""red_analizi.py - events_adaylar.csv'deki reddedilen adaylarin gercek etiketlerle (60-180 sn, +/-1 sn) eslesmesi."""
import os, sys
import pandas as pd
import degerlendir as d
HERE = os.path.dirname(os.path.abspath(__file__))
adir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "tarama", "baseline")
r = d.run(os.path.join(adir, "events.csv"), "gercek_olaylar.csv", 60, 180, 1.0, quiet=True)
gt = r["gt"]; fn_idx = set(r["fn"])
a = pd.read_csv(os.path.join(adir, "events_adaylar.csv"))
a = a[(a.sec >= 60) & (a.sec <= 180)]
rows = []
for neden, g in a[a.karar == "red"].groupby("neden"):
    nm, lab, rec = 0, set(), set()
    for c in g.itertuples():
        near = gt[(gt.sec - c.sec).abs() <= 1.0]
        if isinstance(c.tip, str) and c.tip:                 # tipi belli aday: tip de ayni olmali
            near = near[near.tip == c.tip]
        if len(near):
            nm += 1; lab |= set(near.index); rec |= set(i for i in near.index if i in fn_idx)
    rows.append(dict(neden=neden, aday=len(g), etikete_denk=nm, tekil_etiket=len(lab), bunlardan_FN=len(rec),
                     tip="belirsiz (tip-bagimsiz)" if neden in ("ayni_oyuncu", "ayni_kisi_id_degisimi", "bosluk_buyuk") else "tip ayni"))
print(f"aralikta aday: {len(a)} (kabul {int((a.karar=='kabul').sum())}, red {int((a.karar=='red').sum())})")
print(pd.DataFrame(rows).to_string(index=False))
