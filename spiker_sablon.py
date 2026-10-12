"""
spiker_sablon.py - LLM'siz taban cizgisi: ortak takvimdeki her ogeye Turkce sablon cumlesi.
Kurallar: tekil olaylarda temkinli ifade ('...gibi gorunuyor'); oyuncu ismi / forma no / hiz / skor YOK; konum yalnizca bolge adindan (notr);
cumleler arasi >= 4 sn (takvim); 10 sn ozetleri; cumle <= 15 kelime; olay tipi basina >= 4 sablon (sirayla donulur).
Cikti: spiker_sablon.json [{id, zaman, metin, kaynak_olay_ids}]
"""
import json
import os

from spiker_ortak import HERE, takvim, public

PAS = [
    "{t} topu arkadaşına aktarmış gibi görünüyor.",
    "{t} {b} pas yapmış gibi görünüyor.",
    "{t} topu yaklaşık {m} metre taşımış gibi duruyor.",
    "{t} oyunu {b} sürdürüyor gibi görünüyor.",
    "Pasla top {t} oyuncusunun ayağına gitmiş gibi.",
]
PAS_YOK_M = [PAS[0], PAS[1], PAS[3], PAS[4]]
TK = [
    "{k} topu kaybetmiş gibi görünüyor, {a} topu aldı.",
    "Top {a} oyuncusuna geçmiş gibi duruyor.",
    "{a} {b} topu kazanmış gibi görünüyor.",
    "{k} burada topu rakibe kaptırmış gibi görünüyor.",
    "Topun sahibi değişmiş gibi, şimdi {a} elinde.",
]
PEN = {
    "sahiplik": ["Son on saniyede topa daha çok {s} sahip olmuş gibi görünüyor.",
                 "Bu bölümde top ağırlıklı olarak {s} tarafında gibi."],
    "dengeli": ["Son on saniyede top iki takım arasında paylaşılmış gibi görünüyor.",
                "Bu bölümde oyun dengeli gibi, top iki takımda da dolaşıyor."],
    "sayi": ["Son on saniyede {a} {na} pas, {b} {nb} pas yaptı.",
             "{a} bu bölümde {na} pas yaptı, top kaybı sayısı {ka}.",
             "On saniyelik bölümde {a} {na}, {b} {nb} pas gördük."],
}


def cumle(it, k):
    o = it["olgu"]
    if o["tur"] == "olay":
        b = o["bolge"] or "sahada"
        if o["tip"] == "PAS":
            havuz = PAS if "mesafe_m" in o else PAS_YOK_M
            return havuz[k % len(havuz)].format(t=o["takim"], b=b, m=o.get("mesafe_m"))
        return TK[k % len(TK)].format(k=o["topu_kaybeden_takim"], a=o["topu_alan_takim"], b=b)
    names = list(o["pas"])
    A, B = names
    tutan = o["en_cok_topu_tutan"]
    if k % 3 == 2 or tutan is None:
        h = PEN["sayi"]
        return h[(k // 3) % len(h)].format(a=A, b=B, na=o["pas"][A], nb=o["pas"][B], ka=o["top_kaybi"][A])
    if tutan == "dengeli":
        return PEN["dengeli"][k % 2]
    return PEN["sahiplik"][k % 2].format(s=tutan)


def main():
    items, _ = takvim()
    out, ky, kp = [], 0, 0
    for it in items:
        if it["tur"] == "olay":
            m = cumle(it, ky); ky += 1
        else:
            m = cumle(it, kp); kp += 1
        out.append(dict(id=it["id"], zaman=it["zaman"], metin=m, kaynak_olay_ids=it["kaynak_olay_ids"]))
    json.dump(out, open(os.path.join(HERE, "spiker_sablon.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return items, out


if __name__ == "__main__":
    items, out = main()
    json.dump(public(items), open(os.path.join(HERE, "spiker_girdi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for o in out:
        print(o["id"], o["zaman"], "|", o["metin"], f"({len(o['metin'].split())} kelime)")
