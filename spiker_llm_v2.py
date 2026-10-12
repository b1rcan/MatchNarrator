"""
spiker_llm_v2.py - KORUMALI LLM uretimi: sablon cumlesini LLM'e yeniden ifade ettir -> dogrula -> (en fazla 2 yeniden deneme) -> sablona don.
Ayni slotlar (spiker_ortak_v2 takvimi, gelistirme seti 60-180 sn + dogrulama setinin ilk dakikasi; TEST SETI YOK) icin iki kosul:
  naif     : K1 - spiker_llm.py ile ayni sistem istemi, ham olgu JSON'dan cumle (sablon yok)
  korumali : K2 - sablon cumlesi + 5 few-shot ornek + kati kurallar + dogrulama + yeniden deneme + sablona geri donus
Modeller sirayla calisir, her model sonrasi bosaltilir (ollama stop). Cikti: spiker_llm_naif_v2.json, spiker_llm_korumali_v2.json, spiker_llm_v2_meta.json
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

import olgu_kontrol as ok
from spiker_llm import SISTEM as SISTEM_NAIF, URL, temizle, vram, ps
from spiker_ortak_v2 import HERE

SABLON = {x["id"]: x for x in json.load(open(os.path.join(HERE, "spiker_sablon_v2.json"), encoding="utf-8"))}
GIRDI = json.load(open(os.path.join(HERE, "spiker_girdi_v2.json"), encoding="utf-8"))
TEMPS = [0.3, 0.2, 0.1]          # deneme 1, 2, 3 (en fazla 2 yeniden deneme; sicaklik biraz dusurulur)

SISTEM_KORUMALI = (
    "Sen bir Türkçe spor spikerisin. Sana verilen TEK cümleyi anlamını değiştirmeden doğal bir şekilde yeniden ifade edeceksin.\n"
    "Kesin kurallar:\n"
    "1) Yeni sayı, skor, dakika, oyuncu adı, forma numarası, gol, hız EKLEME. Cümledeki sayıları aynen koru.\n"
    "2) 'gibi görünüyor', 'gibi duruyor', 'gibi' gibi temkinli (hedge) ifadeleri SİLME; cümlede varsa yeniden ifadede de kalsın.\n"
    "3) Takım adlarını (Barcelona, Espanyol) aynen koru; başka takım adı ekleme; takımların rollerini değiştirme.\n"
    "4) Yön söyleme (sağ, sol, ileri, geri deme); konum ifadelerini olduğu gibi koru.\n"
    "5) En fazla 15 kelime, tek cümle.\n"
    "6) Yalnızca yeniden ifade edilmiş cümleyi yaz; tırnak, başlık, açıklama, emoji ekleme."
)
FEWSHOT = [
    ("Barcelona topu arkadaşına aktarmış gibi görünüyor.", "Barcelona topu takım arkadaşına ulaştırmış gibi görünüyor."),
    ("Espanyol topu kaybetmiş gibi görünüyor, Barcelona topu aldı.", "Espanyol topu kaybetmiş, Barcelona topu almış gibi görünüyor."),
    ("Barcelona art arda 5 pas yapmış gibi görünüyor.", "Barcelona arka arkaya 5 pasla oyunu sürdürmüş gibi görünüyor."),
    ("Son on saniyede topa daha çok Espanyol sahip olmuş gibi görünüyor.", "Bu on saniyede top çoğunlukla Espanyol'da kalmış gibi görünüyor."),
    ("Barcelona sahanın ortasında topu yaklaşık 9 metre taşımış gibi duruyor.", "Barcelona sahanın ortasında topu yaklaşık 9 metre götürmüş gibi duruyor."),
]
TAKIMLAR = list(ok.IZINLI)
HEDGE = ok.HEDGE


def sor(model, messages, temp):
    body = {"model": model, "stream": False, "think": False,
            "options": {"temperature": temp, "seed": 42, "num_predict": 100, "num_ctx": 2048}, "messages": messages}
    for think in (False, None):
        b = dict(body)
        if think is None:
            b.pop("think")
        try:
            req = urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError:
            if think is None:
                raise


def sayilar(s):
    return set(ok.sayilar(s))


def dogrula(metin, sablon, olgu):
    """Ihlal turleri listesi (bos = gecti). a-e: olgu_kontrol; ek: sayi_yeni, hedge_kayip, takim_degisti, bos."""
    v = []
    if not metin or not metin.strip():
        return ["bos"]
    olgu_k = dict(olgu)
    if olgu["tur"] == "olay_grup":                      # kontrol 'olay' bicimini bekler; pas sayisi mesafe alanindan izinli sayi olur
        olgu_k["tur"], olgu_k["mesafe_m"] = "olay", olgu["pas_sayisi"]
    r = ok.kontrol(metin, olgu_k)
    for k in ("a_takim_adi", "b_yasak", "c_olgu", "d_uzunluk", "e_turkce_degil"):
        if r[k]:
            v.append(k)
    izinli = sayilar(sablon) | set(ok.izinli_sayilar(olgu_k))
    if not sayilar(metin) <= izinli:
        v.append("sayi_yeni")
    if olgu["tur"] in ("olay", "olay_grup") and re.search(HEDGE, sablon.lower()) and not re.search(HEDGE, metin.lower()):
        v.append("hedge_kayip")
    if {t for t in TAKIMLAR if t in metin} != {t for t in TAKIMLAR if t in sablon}:
        v.append("takim_degisti")
    return v


def uret_korumali(model, it):
    sablon = SABLON[it["id"]]["metin"]
    msgs = [{"role": "system", "content": SISTEM_KORUMALI}]
    for a, b in FEWSHOT:
        msgs += [{"role": "user", "content": f"Cümle: {a}"}, {"role": "assistant", "content": b}]
    msgs.append({"role": "user", "content": f"Cümle: {sablon}"})
    t0 = time.time()
    denemeler, ihlaller = [], []
    for n, temp in enumerate(TEMPS, 1):
        r = sor(model, msgs, temp)
        m = temizle(r["message"]["content"])
        v = dogrula(m, sablon, it["olgu"])
        denemeler.append(m)
        ihlaller.append(v)
        if not v:
            return dict(id=it["id"], zaman=it["zaman"], tur=it["tur"], model=model, sablon=sablon, metin=m, deneme_sayisi=n, geri_donus=False,
                        ihlal_turleri=ihlaller, denemeler=denemeler, sure_sn=round(time.time() - t0, 2), kaynak_olay_ids=it["kaynak_olay_ids"])
    return dict(id=it["id"], zaman=it["zaman"], tur=it["tur"], model=model, sablon=sablon, metin=sablon, deneme_sayisi=len(TEMPS), geri_donus=True,
                ihlal_turleri=ihlaller, denemeler=denemeler, sure_sn=round(time.time() - t0, 2), kaynak_olay_ids=it["kaynak_olay_ids"])


def uret_naif(model, it):
    sablon = SABLON[it["id"]]["metin"]
    msgs = [{"role": "system", "content": SISTEM_NAIF}, {"role": "user", "content": json.dumps(it["olgu"], ensure_ascii=False) + "\n\nCümle:"}]
    t0 = time.time()
    r = sor(model, msgs, 0.3)
    m = temizle(r["message"]["content"])
    return dict(id=it["id"], zaman=it["zaman"], tur=it["tur"], model=model, sablon=sablon, metin=m, deneme_sayisi=1, geri_donus=False,
                ihlal_turleri=[dogrula(m, sablon, it["olgu"])], denemeler=[m], sure_sn=round(time.time() - t0, 2), kaynak_olay_ids=it["kaynak_olay_ids"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["gemma3:4b", "qwen3.5:4b", "llama3.1:8b"])
    ap.add_argument("--modlar", nargs="+", default=["naif", "korumali"])
    a = ap.parse_args()
    cikti = {m: [] for m in a.modlar}
    meta = {}
    for model in a.models:
        t = time.time()                                   # ilk cagri modeli yukler (yukleme suresi ayri olculur)
        sor(model, [{"role": "user", "content": "Merhaba"}], 0.3)
        meta[model] = {"yukleme_sn": round(time.time() - t, 2)}
        for mod in a.modlar:
            fn = uret_naif if mod == "naif" else uret_korumali
            t0, peak = time.time(), 0
            for it in GIRDI:
                cikti[mod].append(fn(model, it))
                peak = max(peak, vram() or 0)
            meta[model][mod] = dict(toplam_sn=round(time.time() - t0, 1), slot=len(GIRDI), vram_tepe_mib=peak)
            print(model, mod, meta[model][mod], flush=True)
        meta[model]["ollama_ps"] = ps().strip()
        subprocess.run(["ollama", "stop", model], capture_output=True)       # sonraki model icin bosalt
        time.sleep(3)
    for mod, v in cikti.items():
        json.dump(v, open(os.path.join(HERE, f"spiker_llm_{mod}_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(HERE, "spiker_llm_v2_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("BITTI")
