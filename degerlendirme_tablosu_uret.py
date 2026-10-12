"""degerlendirme_tablosu_uret.py - degerlendirme_tablosu.csv (UTF-8 BOM, Excel). Satir = takvimdeki oge (olay/pencere).
Sutunlar: zaman, tur, kaynak_ozet (insan okunur), sablon cumlesi, model cumleleri, ve her cumle icin bos 'dogru_mu (e/h)' + 'akicilik (1-5)'."""
import csv
import json
import os

from spiker_ortak import HERE, REC, WIN, cfg

girdi = json.load(open(os.path.join(HERE, "spiker_girdi.json"), encoding="utf-8"))
sablon = {x["id"]: x["metin"] for x in json.load(open(os.path.join(HERE, "spiker_sablon.json"), encoding="utf-8"))}
llm = json.load(open(os.path.join(HERE, "spiker_llm.json"), encoding="utf-8"))
modeller = list(dict.fromkeys(x["model"] for x in llm))
by = {(x["model"], x["id"]): x["metin"] for x in llm}
rec = {r["id"]: r for r in REC}


def ozet(it):
    if it["tur"] == "olay":
        r = rec[it["kaynak_olay_ids"][0]]
        ad = lambda k: cfg[k] if k else "?"
        if r["tip"] == "PAS":
            return f"{ad(r['kimden']['takim'])} pas (iz {r['kimden']['iz']}→{r['kime']['iz']}), {r['mesafe_m']} m, bölge: {r['bolge_bitis']['x_ucte_bir']}/{r['bolge_bitis']['enine']}, top: {r['guven']['top_durumu_olay_kare']}"
        return f"{ad(r['kimden']['takim'])} top kaybı → {ad(r['kime']['takim'])} (iz {r['kimden']['iz']}→{r['kime']['iz']}), bölge: {r['bolge_bitis']['x_ucte_bir']}/{r['bolge_bitis']['enine']}, top: {r['guven']['top_durumu_olay_kare']}"
    o = it["olgu"]
    return f"10 sn özeti: pas {o['pas']}, top kaybı {o['top_kaybi']}, sahiplik % {o.get('sahiplik_yuzde')}, en çok tutan: {o['en_cok_topu_tutan']}"


bas = ["zaman", "tur", "kaynak_olay_ozeti", "sablon_cumlesi", "sablon_dogru_mu (e/h)", "sablon_akicilik (1-5)"]
for m in modeller:
    bas += [f"{m}_cumlesi", f"{m}_dogru_mu (e/h)", f"{m}_akicilik (1-5)"]
with open(os.path.join(HERE, "degerlendirme_tablosu.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(bas)
    for it in girdi:
        row = [it["zaman"], it["tur"], ozet(it), sablon[it["id"]], "", ""]
        for m in modeller:
            row += [by[(m, it["id"])], "", ""]
        w.writerow(row)
print(len(girdi), "satir;", modeller)
