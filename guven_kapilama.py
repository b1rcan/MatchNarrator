"""
guven_kapilama.py - olaylar_zengin.json guven isaretleriyle olay alt kumeleri; gelistirme (60-180) ve dogrulama (360-540) AYRI.
TEST SETI (180-300) KULLANILMAZ. Kurallar onceden sabit (esikler ayarlanmadi); hedefe gore secim YAPILMAZ.
Degerlendirme: alt kumedeki olaylar tahmin kabul edilir; etiketlerin TUMU gercek olarak kalir (recall dusebilir).
Eslestirme degerlendir.py ile ayni: +-1 sn, birebir, tip ayni, en yakin cift once.
"""
import json
import os
import numpy as np
import pandas as pd
import degerlendir as d
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0
SETS = {"gelistirme": dict(src="ana_60_360", dir=HERE, lab="gercek_olaylar.csv", s=60, e=180),
        "dogrulama": dict(src="veri_360_540", dir=os.path.join(HERE, "veri_360_540"), lab="gercek_olaylar_val.csv", s=360, e=540)}
rec = json.load(open(os.path.join(HERE, "olaylar_zengin.json"), encoding="utf-8"))


def ball_window(dirn, f, half=12):
    bt = ball_cache.setdefault(dirn, pd.read_csv(os.path.join(dirn, "ball_track.csv")).set_index("frame"))
    w = bt.loc[f - half:f + half]
    return float(w.bx.notna().mean()), float(w.detected.mean())


ball_cache = {}
RULES = {  # ad: (aciklama, fonksiyon)
    "K0 tum olaylar (taban)": lambda r, k: True,
    "K1 olay karesinde top tespit": lambda r, k: r["guven"]["top_durumu_olay_kare"] == "tespit",
    "K2 top tespit: olay + eski sahip son kare": lambda r, k: r["guven"]["top_durumu_olay_kare"] == "tespit" and r["guven"]["top_durumu_eski_sahip_son_kare"] == "tespit",
    "K3 K1 + konum var (baslangic+bitis) + saha ici": lambda r, k: r["guven"]["top_durumu_olay_kare"] == "tespit" and r["konum_baslangic_m"] is not None and r["konum_bitis_m"] is not None and all(v is True for v in r["konum_saha_icinde"].values()),
    "K4 yeni sahip serisi >= 6 kare": lambda r, k: (r["guven"]["yeni_sahip_seri_kare"] or 0) >= 6,
    "K5 K1 + seri >= 6 kare": lambda r, k: r["guven"]["top_durumu_olay_kare"] == "tespit" and (r["guven"]["yeni_sahip_seri_kare"] or 0) >= 6,
    "K6 kutu yuksekligi >= 30 px (kimden ve kime)": lambda r, k: all((r["guven"]["kutu_yuksekligi_px"][x] or 0) >= 30 for x in ("kimden", "kime")),
    "K7 olay +-0,5 sn top bilinen >= %80": lambda r, k: k["bilinen"] >= 0.8,
    "K8 K1 + seri>=6 + kutu>=30 px + K7 (en siki)": lambda r, k: r["guven"]["top_durumu_olay_kare"] == "tespit" and (r["guven"]["yeni_sahip_seri_kare"] or 0) >= 6 and all((r["guven"]["kutu_yuksekligi_px"][x] or 0) >= 30 for x in ("kimden", "kime")) and k["bilinen"] >= 0.8,
    "K9 makul geometri: mesafe <= 30 m ve hiz <= 20 m/sn": lambda r, k: r["mesafe_m"] is not None and r["mesafe_m"] <= 30 and (r["top_hizi_ms"] is None or r["top_hizi_ms"] <= 20),
}
rows = []
for sn, c in SETS.items():
    gt = pd.read_csv(os.path.join(HERE, c["lab"]), dtype=str)
    gt["sec"] = gt["zaman"].map(d.to_sec); gt["tip"] = gt["tip"].str.strip().str.upper()
    gt = gt[(gt.sec >= c["s"]) & (gt.sec <= c["e"])].reset_index(drop=True)
    R = [r for r in rec if r["kaynak"] == c["src"] and c["s"] <= r["zaman_sn"] <= c["e"]]
    ext = []
    for r in R:
        kn, dt = ball_window(c["dir"], r["kare"])
        ext.append(dict(bilinen=kn, tespit=dt))
    for name, fn in RULES.items():
        keep = [(r, k) for r, k in zip(R, ext) if fn(r, k)]
        ev = pd.DataFrame([dict(sec=r["zaman_sn"], tip=r["tip"]) for r, _ in keep], columns=["sec", "tip"]).reset_index(drop=True)
        m = d.match(gt, ev, 1.0)
        for grp, sel in (("GENEL", None), ("PAS", "PAS"), ("TOP KAYBI", "TOP KAYBI")):
            ng = int((gt.tip == sel).sum()) if sel else len(gt)
            ne = int((ev.tip == sel).sum()) if sel else len(ev)
            tp = sum(1 for i, j in m if sel is None or gt.tip[i] == sel)
            fp, fn_ = ne - tp, ng - tp
            P = tp / ne if ne else np.nan; Rr = tp / ng if ng else np.nan
            F = 2 * tp / (2 * tp + fp + fn_) if (2 * tp + fp + fn_) else np.nan
            rows.append(dict(set=sn, kural=name, grup=grp, olay_toplam=len(R) if sel is None else sum(r["tip"] == sel for r in R), olay_kalan=ne, TP=tp, FP=fp, FN=fn_, P=P, R=Rr, F1=F))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "tarama", "guven_kapilama.csv"), index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 60)
for grp in ("GENEL", "PAS", "TOP KAYBI"):
    print(f"\n===== {grp} =====")
    t = df[df.grup == grp].pivot(index="kural", columns="set", values=["olay_kalan", "TP", "FP", "FN", "P", "R", "F1"])
    t = t.reindex(list(RULES))
    print(t.round(3).to_string())
