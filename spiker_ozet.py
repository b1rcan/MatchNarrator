"""
spiker_ozet.py - olaylar_zengin.json'dan 10 sn'lik pencere ozetleri (pencere_ozet.json)

Her pencere: takim basina pas sayisi, top kaybi sayisi (topu KAYBEDEN takima yazilir = TOP KAYBI olayinda 'kimden' takimi),
sahiplik orani (possession.csv'de topun sahibi olan oyuncunun takimina gore KARE orani; kaleci/takimsiz izler hesaba katilmaz;
possession.csv kaydi yoksa pas sayisi orani), pencerede en cok topu tutan takim (fark < 10 puan ise 'dengeli' sayilir).
Takim adlari config_takimlar.json'dan. Konum null olan olaylar da sayilir (sayim konuma bagli degil).
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0
WIN = 10
SRC = {"ana_60_360": (HERE, 60, 360), "veri_360_540": (os.path.join(HERE, "veri_360_540"), 360, 540)}
cfg = json.load(open(os.path.join(HERE, "config_takimlar.json"), encoding="utf-8"))
rec = json.load(open(os.path.join(HERE, "olaylar_zengin.json"), encoding="utf-8"))


def main():
    out = []
    for src, (d, t0, t1) in SRC.items():
        pos = pd.read_csv(os.path.join(d, "possession.csv"))
        teams = pd.read_csv(os.path.join(d, "teams.csv")).set_index("track_id")["team"].to_dict()
        pos["team"] = pos.track_id.map(teams)
        pos = pos.dropna(subset=["team"])
        for s in range(t0, t1, WIN):
            e = s + WIN
            ev = [r for r in rec if r["kaynak"] == src and s <= r["zaman_sn"] < e]
            w = {"kaynak": src, "baslangic_sn": s, "bitis_sn": e, "zaman": f"{s // 60}:{s % 60:02d}-{e // 60}:{e % 60:02d}",
                 "olay_idleri": [r["id"] for r in ev], "takimlar": {}}
            p = pos[(pos.frame >= s * FPS) & (pos.frame < e * FPS)]
            frames = {k: int((p.team == (0 if k == "A" else 1)).sum()) for k in "AB"}
            tot = sum(frames.values())
            pas = {k: sum(1 for r in ev if r["tip"] == "PAS" and r["kimden"]["takim"] == k) for k in "AB"}
            tk = {k: sum(1 for r in ev if r["tip"] == "TOP KAYBI" and r["kimden"]["takim"] == k) for k in "AB"}
            if tot > 0:
                ratio, kaynak = {k: frames[k] / tot for k in "AB"}, "possession.csv kare orani"
            elif sum(pas.values()) > 0:
                ratio, kaynak = {k: pas[k] / sum(pas.values()) for k in "AB"}, "pas sayisi orani (possession kaydi yok)"
            else:
                ratio, kaynak = {k: None for k in "AB"}, None
            for k in "AB":
                w["takimlar"][k] = dict(ad=cfg[k], pas=pas[k], top_kaybi=tk[k], sahiplik_kare=frames[k],
                                       sahiplik_orani=None if ratio[k] is None else round(ratio[k], 3))
            w["sahiplik_kaynagi"] = kaynak
            if ratio["A"] is None:
                w["en_cok_topu_tutan"], w["fark_puan"] = None, None
            else:
                fark = abs(ratio["A"] - ratio["B"]) * 100
                w["fark_puan"] = round(fark, 1)
                w["en_cok_topu_tutan"] = "dengeli" if fark < 10 else (cfg["A"] if ratio["A"] > ratio["B"] else cfg["B"])
            out.append(w)
    json.dump(out, open(os.path.join(HERE, "pencere_ozet.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(out)} pencere -> pencere_ozet.json")
    return out


if __name__ == "__main__":
    out = main()
    for w in out[:3] + out[3:4]:
        print(json.dumps(w, ensure_ascii=False))
