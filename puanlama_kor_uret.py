"""
puanlama_kor_uret.py - KOR puanlama tablosu: 20 slot x (sablon + 3 model korumali cikti), karisik sirada, model adi GIZLI.
Cikti: puanlama_kor.csv (id, slot_bilgisi, cumle, dogruluk, akicilik; UTF-8 BOM) ve puanlama_kor_anahtar.csv (id -> uretici(ler), slot).
Ayni slottaki birebir ayni cumleler TEK satirda birlestirilir (anahtarda tum ureticiler listelenir; sablona geri donen modeller sablon satirina baglanir).
Slot secimi: 24 slottan 20'si sabit tohumla (seed=7) rastgele. Satir sirasi sabit tohumla (seed=11) tamamen karistirilir.
"""
import csv
import json
import os
import random

from spiker_llm_v2 import GIRDI, SABLON, HERE

kor = json.load(open(os.path.join(HERE, "spiker_llm_korumali_v2.json"), encoding="utf-8"))
modeller = list(dict.fromkeys(x["model"] for x in kor))
girdi = {x["id"]: x for x in GIRDI}


def slot_bilgisi(it):
    o = it["olgu"]
    z = it["zaman"].split(".")[0]
    if o["tur"] == "olay":
        if o["tip"] == "PAS":
            return f"{z} | Tek pas | takım: {o['takim']} | mesafe ≈ {o.get('mesafe_m', '?')} m | bölge: {o['bolge']}"
        return f"{z} | Top kaybı | topu kaybeden: {o['topu_kaybeden_takim']}, alan: {o['topu_alan_takim']} | bölge: {o['bolge']}"
    if o["tur"] == "olay_grup":
        return f"{z} | Art arda pas | takım: {o['takim']} | pas sayısı: {o['pas_sayisi']} | bölge: {o['bolge']}"
    names = list(o["pas"])
    return (f"{z} | 10 sn özeti | pas: {names[0]} {o['pas'][names[0]]}, {names[1]} {o['pas'][names[1]]}; top kaybı: {names[0]} {o['top_kaybi'][names[0]]}, "
            f"{names[1]} {o['top_kaybi'][names[1]]}; sahiplik %: {', '.join(f'{k} {v}' for k, v in (o.get('sahiplik_yuzde') or {}).items())}; en çok topu tutan: {o['en_cok_topu_tutan']}")


rng = random.Random(7)
secilen = sorted(rng.sample(list(girdi), 20))
satirlar, anahtar = [], []
for sid in secilen:
    adaylar = {"sablon": SABLON[sid]["metin"]}
    for m in modeller:
        x = [y for y in kor if y["model"] == m and y["id"] == sid][0]
        adaylar[m] = x["metin"]
    gruplar = {}
    for uretici, metin in adaylar.items():
        gruplar.setdefault(metin.strip(), []).append(uretici)
    for metin, ur in gruplar.items():
        satirlar.append((sid, slot_bilgisi(girdi[sid]), metin))
        anahtar.append((sid, "+".join(ur)))
idx = list(range(len(satirlar)))
random.Random(11).shuffle(idx)
with open(os.path.join(HERE, "puanlama_kor.csv"), "w", newline="", encoding="utf-8-sig") as f1, \
        open(os.path.join(HERE, "puanlama_kor_anahtar.csv"), "w", newline="", encoding="utf-8-sig") as f2:
    w1, w2 = csv.writer(f1), csv.writer(f2)
    w1.writerow(["id", "slot_bilgisi", "cumle", "dogruluk (e/h)", "akicilik (1-5)"])
    w2.writerow(["id", "slot_id", "uretici"])
    for n, i in enumerate(idx, 1):
        pid = f"p{n:03d}"
        sid, bilgi, metin = satirlar[i]
        w1.writerow([pid, bilgi, metin, "", ""])
        w2.writerow([pid, sid, anahtar[i][1]])
print(f"slot {len(secilen)}, satir {len(satirlar)} (birlestirilen: {20 * 4 - len(satirlar)})")
tur = {}
for sid in secilen:
    tur[girdi[sid]["tur"]] = tur.get(girdi[sid]["tur"], 0) + 1
print("slot bileşimi:", tur)
