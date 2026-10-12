"""
ablasyon_v2.py - 3 kosul: K1 naif LLM, K2 korumali LLM, K3 yalniz sablon (ayni slotlar, gelistirme seti + dogrulama ilk dakika; TEST SETI YOK)
Metrikler (model basina): ihlal orani (a-e ve genisletilmis), yeniden deneme orani, sablona geri donus orani, ort. sure, type-token orani, ort. cumle uzunlugu.
Cikti: ablasyon_v2.csv, ablasyon_v2_md.md (OLCUM_14'e konur)
"""
import collections
import json
import os
import re

import pandas as pd

from spiker_llm_v2 import dogrula, SABLON, GIRDI, HERE

A_E = {"a_takim_adi", "b_yasak", "c_olgu", "d_uzunluk", "e_turkce_degil"}
girdi = {x["id"]: x for x in GIRDI}
naif = json.load(open(os.path.join(HERE, "spiker_llm_naif_v2.json"), encoding="utf-8"))
kor = json.load(open(os.path.join(HERE, "spiker_llm_korumali_v2.json"), encoding="utf-8"))
modeller = list(dict.fromkeys(x["model"] for x in naif))


def kelimeler(s):
    return re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", s.lower())


def ttr(metinler):
    k = [w for m in metinler for w in kelimeler(m)]
    return len(set(k)) / max(len(k), 1)


def ort_uzunluk(metinler):
    return sum(len(kelimeler(m)) for m in metinler) / max(len(metinler), 1)


rows = []
ex = []
sab_met = [SABLON[i]["metin"] for i in girdi]
v = [dogrula(m, m, girdi[i]["olgu"]) for i, m in zip(girdi, sab_met)]
rows.append(dict(kosul="K3 yalniz sablon", model="-", slot=len(sab_met), ihlal_ae=sum(any(x in A_E for x in vv) for vv in v) / len(v),
                 ihlal_genis=sum(bool(vv) for vv in v) / len(v), yeniden_deneme=0.0, sablona_donus=0.0, ort_sure_sn=0.0, ttr=ttr(sab_met), ort_kelime=ort_uzunluk(sab_met),
                 sablonla_ayni=1.0))
for m in modeller:
    N = [x for x in naif if x["model"] == m]
    K = [x for x in kor if x["model"] == m]
    vn = [x["ihlal_turleri"][0] for x in N]
    rows.append(dict(kosul="K1 naif LLM", model=m, slot=len(N), ihlal_ae=sum(any(t in A_E for t in vv) for vv in vn) / len(N),
                     ihlal_genis=sum(bool(vv) for vv in vn) / len(N), yeniden_deneme=float("nan"), sablona_donus=float("nan"),
                     ort_sure_sn=sum(x["sure_sn"] for x in N) / len(N), ttr=ttr([x["metin"] for x in N]), ort_kelime=ort_uzunluk([x["metin"] for x in N]),
                     sablonla_ayni=sum(x["metin"].strip() == x["sablon"].strip() for x in N) / len(N)))
    # K2 son cikti: dogrulayicidan gecen LLM cumlesi ya da sablon (geri donus)
    vf = [dogrula(x["metin"], x["sablon"], girdi[x["id"]]["olgu"]) for x in K]
    rows.append(dict(kosul="K2 korumali LLM (nihai cikti)", model=m, slot=len(K), ihlal_ae=sum(any(t in A_E for t in vv) for vv in vf) / len(K),
                     ihlal_genis=sum(bool(vv) for vv in vf) / len(K), yeniden_deneme=sum(x["deneme_sayisi"] > 1 for x in K) / len(K),
                     sablona_donus=sum(x["geri_donus"] for x in K) / len(K), ort_sure_sn=sum(x["sure_sn"] for x in K) / len(K),
                     ttr=ttr([x["metin"] for x in K]), ort_kelime=ort_uzunluk([x["metin"] for x in K]),
                     sablonla_ayni=sum(x["metin"].strip() == x["sablon"].strip() for x in K) / len(K)))
    # K2 ham (ilk deneme) ihlal turleri
    ilk = collections.Counter(t for x in K for t in x["ihlal_turleri"][0])
    tum = collections.Counter(t for x in K for tur in x["ihlal_turleri"] for t in tur)
    ex.append((m, sum(bool(x["ihlal_turleri"][0]) for x in K), len(K), dict(ilk), dict(tum), sum(x["deneme_sayisi"] for x in K) / len(K)))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "ablasyon_v2.csv"), index=False, encoding="utf-8-sig")
pd.set_option("display.width", 250)
print(df.round(3).to_string(index=False))
for m, n_bad, n, ilk, tum, ort_d in ex:
    print(f"{m}: ilk denemede ihlalli {n_bad}/{n}; ilk deneme ihlal turleri {ilk}; tum denemeler {tum}; ort deneme {ort_d:.2f}")


def pct(x):
    return "–" if pd.isna(x) else f"{100 * x:.0f}%"


md = ["| Koşul | Model | Slot | İhlal (a–e) | İhlal (genişletilmiş*) | Yeniden deneme | Şablona dönüş | Şablonla aynı cümle | Ort. süre (sn/slot) | TTR | Ort. cümle uzunluğu (kelime) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['kosul']} | {r['model']} | {r['slot']} | {pct(r['ihlal_ae'])} | {pct(r['ihlal_genis'])} | {pct(r['yeniden_deneme'])} | {pct(r['sablona_donus'])} | {pct(r['sablonla_ayni'])} | {r['ort_sure_sn']:.2f} | {r['ttr']:.2f} | {r['ort_kelime']:.1f} |")
open(os.path.join(HERE, "ablasyon_v2_md.md"), "w", encoding="utf-8").write("\n".join(md))
