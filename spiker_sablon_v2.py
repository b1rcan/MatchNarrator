"""spiker_sablon_v2.py - takvim v2 (spiker_ortak_v2) icin sablon cumleleri. Eski spiker_sablon.py/json DEGISMEDI; olay/pencere sablonlari ondan alinir.
Birlesik pas slotu ('olay_grup') icin ek 4 sablon. Cikti: spiker_sablon_v2.json, spiker_girdi_v2.json."""
import json
import os

from spiker_ortak_v2 import HERE, takvim_v2, public
import spiker_sablon as v1

GRUP = [
    "{t} art arda {n} pas yapmış gibi görünüyor.",
    "{t} topu {n} pasla dolaştırıyor gibi görünüyor.",
    "Kısa sürede {n} pas görüldü, top {t} oyuncularında gibi.",
    "{t} {b} {n} pas yapmış gibi duruyor.",
]


def cumle(it, k):
    o = it["olgu"]
    if o["tur"] == "olay_grup":
        return GRUP[k % len(GRUP)].format(t=o["takim"], n=o["pas_sayisi"], b=o["bolge"] or "sahada")
    return v1.cumle(it, k)


def main():
    items, ev, kumeler = takvim_v2()
    sayac = {"olay": 0, "olay_grup": 0, "pencere": 0}
    out = []
    for it in items:
        k = sayac[it["tur"]]
        sayac[it["tur"]] += 1
        out.append(dict(id=it["id"], zaman=it["zaman"], metin=cumle(it, k), kaynak_olay_ids=it["kaynak_olay_ids"]))
    json.dump(out, open(os.path.join(HERE, "spiker_sablon_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(public(items), open(os.path.join(HERE, "spiker_girdi_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return items, out


if __name__ == "__main__":
    items, out = main()
    for it, o in zip(items, out):
        print(o["id"], o["zaman"], it["tur"], "|", o["metin"], f"({len(o['metin'].split())})")
