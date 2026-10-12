"""spiker_ortak_v2.py - takvim v2: yakin olaylari tek cumlede BIRLESTIRME ve oncelik kurali (eski spiker_ortak.py degismedi).

Sorun: 4 sn kurali + soldan saga acgozlu yerlestirme yuzunden 1:00-2:30'daki 23 olayin 17'si cumle almadi (kapsama %26).
Kural (v2):
  1) Olaylar 4 sn'lik KOVALARA ayrilir (kova ilk olayda baslar, [s, s+4) icindekileri toplar). Kova basina TEK cumle slotu.
  2) Kovada TOP KAYBI varsa slot = en guvenilir TOP KAYBI (top 'tespit', sonra yeni sahip serisi uzun); digerleri o cumlede anilmaz.
  3) Kova yalniz PAS ise: ayni takimdan >= 2 pas -> BIRLESIK slot ('olay_grup', 'N pas', zaman = son olay + 0.5);
     tek pas -> tekil; farkli takimlardan PAS'lar -> en guvenilir tek PAS.
  4) Cumle zamani = olay + 0.5 sn; bir onceki cumleye < MIN_ARA kalirsa cumle MIN_ARA'ya kadar GECIKTIRILIR (gecikme raporlanir).
     10 sn ozet cumleleri bos kalan en erken uygun ana (pencere sonu .. +3 sn) konur; uygun an yoksa uretilmez.
Kapsama = bir cumle slotunun (tekil ya da birlesik) temsil ettigi olay sayisi / toplam olay.
Pencere sabit: T0..T1 (varsayilan 60-180 sn = gelistirme seti; test seti 180+ KULLANILMAZ).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
T0, T1, MIN_ARA, GECIKME = 60.0, 180.0, 4.0, 0.5
cfg = json.load(open(os.path.join(HERE, "config_takimlar.json"), encoding="utf-8"))
REC = json.load(open(os.path.join(HERE, "olaylar_zengin.json"), encoding="utf-8"))
WIN = json.load(open(os.path.join(HERE, "pencere_ozet.json"), encoding="utf-8"))
from spiker_ortak import bolge_metni, olgu_olay, olgu_pencere  # v1 yardimcilari (degismedi)


def guven(r):
    g = r["guven"]
    return (g["top_durumu_olay_kare"] == "tespit", g["yeni_sahip_seri_kare"] or 0)


SEGMENTLER = [("ana_60_360", 60.0, 180.0), ("veri_360_540", 360.0, 420.0)]   # gelistirme seti + dogrulama setinin ilk dakikasi (test seti YOK)


def _segment(kaynak, t0, t1, idx0):
    ev = sorted([r for r in REC if r["kaynak"] == kaynak and t0 <= r["zaman_sn"] <= t1 and r["kimden"]["takim"] and r["kime"]["takim"]],
                key=lambda r: r["zaman_sn"])
    # 1) 4 sn'lik KOVALAR: kova ilk olayda baslar, [s, s+4) icindeki olaylari toplar; sonraki kova ilk >= s+4 olayda baslar
    kumeler, cur = [], []
    for r in ev:
        if cur and r["zaman_sn"] < cur[0]["zaman_sn"] + MIN_ARA:
            cur.append(r)
        else:
            if cur:
                kumeler.append(cur)
            cur = [r]
    if cur:
        kumeler.append(cur)
    placed, onceki_t = [], -1e9
    for k in kumeler:
        tk = [r for r in k if r["tip"] == "TOP KAYBI"]
        ids = [r["id"] for r in k]
        if tk:
            r = max(tk, key=guven)
            t, tur, olgu, kaynak_, temsil = r["zaman_sn"] + GECIKME, "olay", olgu_olay(r), r, [r["id"]]
        else:
            takimlar = {r["kimden"]["takim"] for r in k}
            if len(k) >= 2 and len(takimlar) == 1:
                last = k[-1]
                t, tur, kaynak_, temsil = last["zaman_sn"] + GECIKME, "olay_grup", k, ids
                olgu = {"tur": "olay_grup", "tip": "PAS", "takim": cfg[last["kimden"]["takim"]], "pas_sayisi": len(k), "bolge": bolge_metni(last["bolge_bitis"])}
            else:
                r = max(k, key=guven)
                t, tur, olgu, kaynak_, temsil = r["zaman_sn"] + GECIKME, "olay", olgu_olay(r), r, [r["id"]]
        t = max(t, onceki_t + MIN_ARA)                      # cumleler arasi >= MIN_ARA; gerekirse cumle biraz GECIKTIRILIR
        placed.append((t, tur, temsil, olgu, kaynak_, ids))
        onceki_t = t
    # 2) 10 sn ozetleri: bos kalan en erken uygun ana; cumle zamani segment sonunu (t1) asmaz
    for w in [w for w in WIN if w["kaynak"] == kaynak and t0 <= w["baslangic_sn"] and w["bitis_sn"] <= t1]:
        t = w["bitis_sn"] + GECIKME
        while t <= min(w["bitis_sn"] + 3.0, t1):
            if all(abs(t - p[0]) >= MIN_ARA for p in placed):
                placed.append((t, "pencere", list(w["olay_idleri"]), olgu_pencere(w), w, list(w["olay_idleri"])))
                break
            t += 0.5
    placed.sort(key=lambda p: p[0])
    return placed, ev, kumeler


def takvim_v2(segmentler=None):
    segmentler = segmentler or SEGMENTLER
    items, tum_ev, tum_k = [], [], []
    for kaynak, t0, t1 in segmentler:
        placed, ev, kumeler = _segment(kaynak, t0, t1, len(items))
        for (t, tur, temsil, olgu, kaynak_, ids) in placed:
            items.append(dict(id=f"v{len(items) + 1:02d}", kaynak=kaynak, zaman_sn=round(t, 2), zaman=f"{int(t // 60)}:{t % 60:05.2f}", tur=tur,
                              kaynak_olay_ids=temsil, kume_olay_ids=ids, olgu=olgu, _kaynak=kaynak_))
        tum_ev += ev
        tum_k += kumeler
    return items, tum_ev, tum_k


def gecikme_istatistigi(items):
    g = []
    for i in items:
        if i["tur"] in ("olay", "olay_grup"):
            son = max(r["zaman_sn"] for r in REC if r["id"] in i["kaynak_olay_ids"])
            g.append(i["zaman_sn"] - son)
    return dict(ort=sum(g) / len(g), maks=max(g)) if g else {}


def kapsama(items, ev):
    olay_slot = [i for i in items if i["tur"] in ("olay", "olay_grup")]
    temsil = set()
    for i in olay_slot:
        temsil.update(i["kaynak_olay_ids"])
    return dict(olay=len(ev), olay_slot=len(olay_slot), pencere_slot=sum(i["tur"] == "pencere" for i in items),
                temsil_edilen_olay=len(temsil & {r["id"] for r in ev}), kapsama=len(temsil & {r["id"] for r in ev}) / max(len(ev), 1),
                dogrudan_ayrik_cumle=sum(i["tur"] == "olay" for i in items))


def public(items):
    return [{k: v for k, v in i.items() if k != "_kaynak"} for i in items]


if __name__ == "__main__":
    from spiker_ortak import takvim as eski
    e_items, e_atl = eski()
    ev_eski = [r for r in REC if r["kaynak"] == "ana_60_360" and 60 <= r["zaman_sn"] <= 150 and r["kimden"]["takim"] and r["kime"]["takim"]]
    print("ESKI (60-150 sn):", {"olay": len(ev_eski), "olay_cumlesi": sum(i["tur"] == "olay" for i in e_items), "pencere": sum(i["tur"] == "pencere" for i in e_items),
                                "kapsama": round(sum(i["tur"] == "olay" for i in e_items) / len(ev_eski), 3)})
    for seg in ([("ana_60_360", 60.0, 150.0)], [("ana_60_360", 60.0, 180.0)], SEGMENTLER):
        it, ev, k = takvim_v2(seg)
        print("YENI", seg, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in kapsama(it, ev).items()}, "toplam slot", len(it),
              {a: round(b, 2) for a, b in gecikme_istatistigi(it).items()})
