"""
olgu_kontrol.py - spiker cumleleri icin otomatik olgu kontrolu (sablon + LLM modelleri).
Kontroller (ihlal = 1):
  a) takim adi: config disinda takim adi/lakabi, ya da 'A takimi/B takimi'
  b) yasak oge: gol/skor/forma-numara/dakika/hiz/hakem/seyirci vb. kelimeler, skor kalibi, yon (sag/sol/ileri/geri), bilinmeyen ozel isim
  c) olgu uyumu: cumledeki sayilar (rakam veya yaziyla) JSON olgulariyla +-1 eslesmiyor; PAS cumlesinde olgudaki takimdan baska takim adi
  d) uzunluk > 15 kelime ya da birden fazla cumle
  e) Turkce degil: langdetect (seed 0) 'tr' vermiyor ya da Latin disi alfabe
  (bilgi) temkinli ifade yok: tekil olay cumlesinde gibi/sanki/gorunuyor/duruyor/olabilir yok
Girdi: spiker_girdi.json (olgular), spiker_sablon.json, spiker_llm.json. Cikti: olgu_kontrol_detay.csv, ihlal_tablosu.md/csv
"""
import json
import os
import re

import pandas as pd
from langdetect import DetectorFactory, detect_langs

DetectorFactory.seed = 0
HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "config_takimlar.json"), encoding="utf-8"))
IZINLI = set(cfg.values())
BASKA_TAKIM = r"real madrid|madrid|atl[eé]tico|sevilla|valencia|villarreal|getafe|betis|athletic|bilbao|girona|celta|osasuna|barça|barca|blaugrana|cul[eé]|katalan\w*|perikolar|periko\w*|galatasaray|fenerbah[cç]e|be[sş]ikta[sş]|trabzonspor|[aA] tak[ıi]m[ıi]?|[bB] tak[ıi]m[ıi]?|ev sahibi|deplasman\w*|konuk takım\w*"
YASAK = r"\bgol\w*|\bskor\w*|\bberabere\w*|\bfark[ıi]\b|numaral[ıi]|\bnumara\w*|\bforma\w*|\bdakika\w*|\bhız\w*|\bsürat\w*|\bkm\b|\bm/s\w*|saat başına|\bpenalt[ıi]\w*|\bkart\w*|\bofsayt\w*|\bkorner\w*|\bhakem\w*|\btaraftar\w*|\bseyirci\w*|\bkaleci\w*|\bteknik direktör\w*|\bforvet\w*|\bdefans\w*|\bortasaha\w*"
YON = r"\bsağ\w*|\bsol\w*|\bileri\b|\bgeri\b|\bileriye\b|\bgeriye\b|\bsağdan\b|\bsoldan\b"
SAYI_KELIME = {"sıfır": 0, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10, "onbir": 11, "oniki": 12,
               "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90, "yüz": 100}
HEDGE = r"gibi|sanki|görünüyor|duruyor|olabilir|galiba|muhtemelen|herhalde"


def kelimeler(s):
    return re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", s)


def izinli_sayilar(olgu):
    v = set()
    if olgu["tur"] == "olay":
        if "mesafe_m" in olgu:
            v.add(olgu["mesafe_m"])
    else:
        v.add(olgu["sure_sn"])
        for k in ("pas", "top_kaybi", "sahiplik_yuzde"):
            for x in olgu.get(k, {}).values():
                v.add(x)
    return v


def sayilar(s):
    out = [int(x) for x in re.findall(r"\d+", s)]
    for w in kelimeler(s.lower()):
        if w in SAYI_KELIME:
            out.append(SAYI_KELIME[w])
    return out


def kontrol(metin, olgu):
    res = dict(a_takim_adi=0, b_yasak=0, c_olgu=0, d_uzunluk=0, e_turkce_degil=0, temkin_yok=0)
    ml = metin.lower()
    if re.search(BASKA_TAKIM, metin if "A takım" in metin or "B takım" in metin else ml, re.I):
        res["a_takim_adi"] = 1
    # b) yasak
    govde = metin
    if re.search(YASAK, ml) or re.search(r"\d+\s*[-–:]\s*\d+", metin) or re.search(YON, ml):
        res["b_yasak"] = 1
    for w in re.findall(r"(?<=[a-zçğıöşü,;] )[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ]*", metin):      # cumle ici buyuk harfli kelime
        if w not in IZINLI:
            res["b_yasak"] = 1
    if re.search(r"\d+\s*numara|numara\s*\d+", ml):
        res["b_yasak"] = 1
    # c) olgu uyumu
    ok = izinli_sayilar(olgu)
    for n in sayilar(metin):
        if not any(abs(n - x) <= 1 for x in ok):
            res["c_olgu"] = 1
    if olgu["tur"] == "olay" and olgu["tip"] == "PAS":
        for t in IZINLI - {olgu.get("takim")}:
            if t in metin:
                res["c_olgu"] = 1
    # c2) TOP KAYBI rol tutarliligi (yaklasik sezgisel): cumlenin ilk anilan takimi 'kaybet' ile topu kaybeden, 'kazan/aldi' ile topu alan olmali
    if olgu["tur"] == "olay" and olgu["tip"] == "TOP KAYBI":
        pos_ = sorted((metin.find(t), t) for t in IZINLI if t in metin)
        if pos_:
            ilk = pos_[0][1]
            if re.search(r"kaybet|kaptır", ml) and not re.search(r"kazan|aldı|alan|ele geçir", ml) and ilk != olgu.get("topu_kaybeden_takim"):
                res["c_olgu"] = 1
            if re.search(r"kazan|ele geçir", ml) and not re.search(r"kaybet|kaptır", ml) and ilk != olgu.get("topu_alan_takim"):
                res["c_olgu"] = 1
    # d) uzunluk
    if len(kelimeler(metin)) > 15 or len(re.findall(r"(?<!\d)[.!?](\s|$)", metin)) > 1:     # '10. dakikada' gibi sira sayilari cumle sonu sayilmaz
        res["d_uzunluk"] = 1
    # e) Turkce
    if re.search(r"[Ѐ-ӿ؀-ۿ一-鿿぀-ヿ]", metin):
        res["e_turkce_degil"] = 1
    else:
        try:
            top = detect_langs(metin)[0]
            if top.lang != "tr" and top.prob >= 0.8:          # kisa cumlelerde belirsiz tahminler (<0.8) ihlal sayilmaz
                res["e_turkce_degil"] = 1
        except Exception:
            res["e_turkce_degil"] = 1
    if olgu["tur"] == "olay" and not re.search(HEDGE, ml):
        res["temkin_yok"] = 1
    return res


if __name__ == "__main__":
    girdi = {x["id"]: x for x in json.load(open(os.path.join(HERE, "spiker_girdi.json"), encoding="utf-8"))}
    src = [("sablon", x) for x in json.load(open(os.path.join(HERE, "spiker_sablon.json"), encoding="utf-8"))]
    pth = os.path.join(HERE, "spiker_llm.json")
    if os.path.exists(pth):
        src += [(x["model"], x) for x in json.load(open(pth, encoding="utf-8"))]
    rows = []
    for gen, x in src:
        r = kontrol(x["metin"], girdi[x["id"]]["olgu"])
        rows.append(dict(uretici=gen, id=x["id"], tur=girdi[x["id"]]["tur"], metin=x["metin"], kelime=len(kelimeler(x["metin"])), **r))
    df = pd.DataFrame(rows)
    df["ihlal_var"] = df[["a_takim_adi", "b_yasak", "c_olgu", "d_uzunluk", "e_turkce_degil"]].max(axis=1)
    df.to_csv(os.path.join(HERE, "olgu_kontrol_detay.csv"), index=False, encoding="utf-8-sig")
    t = df.groupby("uretici").agg(cumle=("id", "size"), a_takim_adi=("a_takim_adi", "mean"), b_yasak=("b_yasak", "mean"), c_olgu=("c_olgu", "mean"),
                                  d_uzunluk=("d_uzunluk", "mean"), e_turkce_degil=("e_turkce_degil", "mean"), herhangi_ihlal=("ihlal_var", "mean"),
                                  temkin_yok_tekil_olay=("temkin_yok", "sum"), ort_kelime=("kelime", "mean"))
    t.to_csv(os.path.join(HERE, "ihlal_tablosu.csv"), encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print((t.drop(columns=["cumle", "temkin_yok_tekil_olay", "ort_kelime"]) * 100).round(1).assign(cumle=t.cumle, temkin_yok=t.temkin_yok_tekil_olay, ort_kelime=t.ort_kelime.round(1)).to_string())
    print(df[df.ihlal_var == 1][["uretici", "id", "metin", "a_takim_adi", "b_yasak", "c_olgu", "d_uzunluk", "e_turkce_degil"]].to_string(index=False))
