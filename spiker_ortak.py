"""spiker_ortak.py - sablon, LLM ve olgu kontrolu icin ORTAK girdi takvimi (ayni olaylar/pencereler, ayni zamanlar).

Takvim: sabit pencere 1:00-2:30 (60-150 sn, ana_60_360 kaynagi, gelistirme seti icinde).
Yerlestirme sirasi: (1) TOP KAYBI olaylari, (2) 10 sn'lik pencere ozetleri (pencere bitince <= 3 sn icinde ilk uygun an), (3) PAS olaylari zaman sirasiyla;
iki cumle arasi >= MIN_ARA sn; sigmayan olay/ozet atlanir. Cumle zamani = olay zamani + 0.5 sn.
Olgu (olgu): LLM'e verilen ve kontrolun karsilastirdigi YASAL alanlar (iz no, hiz, ham konum YOK).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
T0, T1, MIN_ARA, GECIKME = 60.0, 150.0, 4.0, 0.5
cfg = json.load(open(os.path.join(HERE, "config_takimlar.json"), encoding="utf-8"))
REC = json.load(open(os.path.join(HERE, "olaylar_zengin.json"), encoding="utf-8"))
WIN = json.load(open(os.path.join(HERE, "pencere_ozet.json"), encoding="utf-8"))


def bolge_metni(b):
    """Yon bilinmedigi icin sag/sol YOK; yalnizca notr ifadeler."""
    if not b:
        return None
    x, y = b["x_ucte_bir"], b["enine"]
    kanat = y.startswith("kanat")
    if x == "orta":
        return "orta alanda, kanat tarafında" if kanat else "sahanın ortasında"
    return "sahanın uç bölgelerinden birinde, kanat tarafında" if kanat else "sahanın uç bölgelerinden birinde"


def olgu_olay(r):
    d = {"tur": "olay", "tip": r["tip"]}
    if r["tip"] == "PAS":
        d["takim"] = cfg[r["kimden"]["takim"]] if r["kimden"]["takim"] else None
    else:
        d["topu_kaybeden_takim"] = cfg[r["kimden"]["takim"]] if r["kimden"]["takim"] else None
        d["topu_alan_takim"] = cfg[r["kime"]["takim"]] if r["kime"]["takim"] else None
    if r["mesafe_m"] is not None:
        d["mesafe_m"] = int(round(r["mesafe_m"]))
    d["bolge"] = bolge_metni(r["bolge_bitis"])
    return d


def olgu_pencere(w):
    A, B = w["takimlar"]["A"], w["takimlar"]["B"]
    d = {"tur": "pencere", "sure_sn": 10,
         "pas": {A["ad"]: A["pas"], B["ad"]: B["pas"]},
         "top_kaybi": {A["ad"]: A["top_kaybi"], B["ad"]: B["top_kaybi"]},
         "en_cok_topu_tutan": w["en_cok_topu_tutan"]}
    if A["sahiplik_orani"] is not None:
        d["sahiplik_yuzde"] = {A["ad"]: int(round(A["sahiplik_orani"] * 100)), B["ad"]: int(round(B["sahiplik_orani"] * 100))}
    return d


def takvim():
    ev = [r for r in REC if r["kaynak"] == "ana_60_360" and T0 <= r["zaman_sn"] <= T1 and r["kimden"]["takim"] and r["kime"]["takim"]]
    placed = []                                  # (zaman, tur, kaynak, olgu)
    atlanan = []

    def yerlestir(r):
        t = r["zaman_sn"] + GECIKME
        if all(abs(t - p[0]) >= MIN_ARA for p in placed):
            placed.append((t, "olay", [r["id"]], olgu_olay(r), r))
        else:
            atlanan.append(r["id"])

    for r in sorted([r for r in ev if r["tip"] == "TOP KAYBI"], key=lambda r: r["zaman_sn"]):   # 1) TOP KAYBI
        yerlestir(r)
    for w in [w for w in WIN if w["kaynak"] == "ana_60_360" and T0 <= w["baslangic_sn"] and w["bitis_sn"] <= T1]:   # 2) 10 sn ozetleri
        t = w["bitis_sn"] + GECIKME
        while t <= w["bitis_sn"] + 3.0:
            if all(abs(t - p[0]) >= MIN_ARA for p in placed):
                placed.append((t, "pencere", list(w["olay_idleri"]), olgu_pencere(w), w))
                break
            t += 0.5
    for r in sorted([r for r in ev if r["tip"] == "PAS"], key=lambda r: r["zaman_sn"]):        # 3) PAS (kalan bosluklara)
        yerlestir(r)
    placed.sort(key=lambda p: p[0])
    items = []
    for i, (t, tur, ids, olgu, kaynak) in enumerate(placed, 1):
        items.append(dict(id=f"s{i:02d}", zaman_sn=round(t, 2), zaman=f"{int(t // 60)}:{t % 60:05.2f}", tur=tur, kaynak_olay_ids=ids, olgu=olgu, _kaynak=kaynak))
    return items, atlanan


def public(items):
    return [{k: v for k, v in it.items() if k != "_kaynak"} for it in items]


if __name__ == "__main__":
    items, atl = takvim()
    json.dump(public(items), open(os.path.join(HERE, "spiker_girdi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(items), "ogeler:", sum(i["tur"] == "olay" for i in items), "olay,", sum(i["tur"] == "pencere" for i in items), "pencere; aralik nedeniyle atlanan olay:", len(atl))
