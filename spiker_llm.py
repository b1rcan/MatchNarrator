"""
spiker_llm.py - ayni takvim/olgularla (spiker_ortak) yerel Ollama modelleriyle Turkce spiker cumlesi uretimi.
Sabit pencere 1:00-2:30 (gelistirme seti). Sicaklik 0.3, sabit seed 42. Cikti: spiker_llm.json (model alani + sure/VRAM olcumu).
Kullanim: python spiker_llm.py --models gemma3:4b qwen3.5:4b llama3.1:8b
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.request

from spiker_ortak import HERE, takvim

URL = "http://localhost:11434/api/chat"
SISTEM = ("Sen bir Türkçe spor spikerisin. Sana verilen JSON olgularından TEK bir kısa cümle yazacaksın (en fazla 15 kelime).\n"
          "Kurallar:\n"
          "1) Yalnızca JSON'da verilen alanları kullan. JSON'da olmayan hiçbir şeyi söyleme: oyuncu ismi, forma numarası, hız, skor, gol, dakika, hakem, seyirci, başka rakam ya da bilmediğin herhangi bir bilgi yok.\n"
          "2) Tekil olaylarda (tur=olay) kesin konuşma; 'gibi görünüyor', 'sanki' gibi temkinli ifadeler kullan.\n"
          "3) Takım adlarını JSON'daki gibi yaz, başka takım adı kullanma.\n"
          "4) Yön belirtme (sağ, sol, ileri, geri deme); konumu yalnızca 'bolge' alanındaki ifadeyle anlat.\n"
          "5) Rakamları yalnızca JSON'da geçen sayılarla yaz.\n"
          "6) Yalnızca cümleyi yaz; tırnak, başlık, emoji, açıklama ekleme.")


def sor(model, olgu, think_false=True):
    body = {"model": model, "stream": False,
            "options": {"temperature": 0.3, "seed": 42, "num_predict": 100, "num_ctx": 2048},
            "messages": [{"role": "system", "content": SISTEM},
                         {"role": "user", "content": json.dumps(olgu, ensure_ascii=False) + "\n\nCümle:"}]}
    if think_false:
        body["think"] = False
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def temizle(s):
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip()
    s = s.splitlines()[0].strip() if s else ""
    return s.strip(' "“”«»*')


def vram():
    try:
        o = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
        return int(o.strip().splitlines()[0])
    except Exception:
        return None


def ps():
    try:
        return subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    except Exception:
        return ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "spiker_llm.json"))
    a = ap.parse_args()
    items, _ = takvim()
    out, meta = [], {}
    for m in a.models:
        v0 = vram()
        # ilk cagri model yukleme icerir: ayri olc
        t = time.time()
        try:
            sor(m, items[0]["olgu"])
        except Exception:
            sor(m, items[0]["olgu"], think_false=False)
        yukleme = time.time() - t
        peaks, sureler, toks = [], [], []
        for it in items:
            t = time.time()
            try:
                r = sor(m, it["olgu"])
            except urllib.error.HTTPError:
                r = sor(m, it["olgu"], think_false=False)
            dt = time.time() - t
            peaks.append(vram())
            sureler.append(dt)
            toks.append(r.get("eval_count"))
            out.append(dict(id=it["id"], zaman=it["zaman"], metin=temizle(r["message"]["content"]), kaynak_olay_ids=it["kaynak_olay_ids"],
                            model=m, sure_sn=round(dt, 2), uretilen_token=r.get("eval_count")))
        pst = ps()
        meta[m] = dict(ilk_cagri_yukleme_dahil_sn=round(yukleme, 2), ort_sure_sn=round(sum(sureler) / len(sureler), 2), maks_sure_sn=round(max(sureler), 2),
                       ort_token=round(sum(t for t in toks if t) / max(1, sum(1 for t in toks if t)), 1),
                       vram_once_mib=v0, vram_tepe_mib=max(p for p in peaks if p), ollama_ps=pst.strip())
        print(m, json.dumps(meta[m], ensure_ascii=False))
        subprocess.run(["ollama", "stop", m], capture_output=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(HERE, "spiker_llm_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
