"""
degerlendir.py - Olay tespiti degerlendirmesi (tezdeki tek olcum kaynagi)

Kural: yalnizca [--start, --end] saniye araligindaki etiket ve tahminler degerlendirilir.
Eslestirme: |dt| <= --tol, BIREBIR (bir etiket en fazla bir tahminle), TIP AYNI olmak zorunda;
en yakin cift once secilir.
Isaretli zaman farki = tahmin - gercek (pozitif: sistem etiketten GEC).

Kullanim:
  python degerlendir.py --events events.csv --labels gercek_olaylar.csv --start 60 --end 180 --tol 1.0
  ek: --diagnose  (ball_track/possession/teams/players.csv ile hata kategorilerini de sayar)
"""
import argparse
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0


def fmt(sec):
    return f"{int(sec // 60)}:{sec % 60:05.2f}"


def to_sec(v):
    v = str(v).strip()
    if ":" in v:
        m, s = v.split(":")
        return int(m) * 60 + float(s)
    return float(v)


def match(g, e, tol, typed=True):
    """Birebir eslestirme; (gt_index, ev_index) listesi dondurur."""
    pairs = sorted((abs(g.sec[i] - e.sec[j]), i, j) for i in g.index for j in e.index
                   if abs(g.sec[i] - e.sec[j]) <= tol and (not typed or g.tip[i] == e.tip[j]))
    ug, ue, out = set(), set(), []
    for _, i, j in pairs:
        if i in ug or j in ue:
            continue
        ug.add(i)
        ue.add(j)
        out.append((i, j))
    return out


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def run(events, labels, start, end, tol, diagnose=False, quiet=False, n_boot=1000):
    gt = pd.read_csv(labels, dtype=str)
    gt["sec"] = gt["zaman"].map(to_sec)
    gt["tip"] = gt["tip"].str.strip().str.upper()
    gt = gt[(gt.sec >= start) & (gt.sec <= end)].sort_values("sec").reset_index(drop=True)
    evall = pd.read_csv(events)
    ev = evall[(evall.sec >= start) & (evall.sec <= end)].sort_values("sec").reset_index(drop=True)
    ev["tip"] = ev["tip"].str.strip().str.upper()

    m = match(gt, ev, tol)
    mg = {i for i, _ in m}
    me = {j for _, j in m}
    fn = [i for i in gt.index if i not in mg]
    fp = [j for j in ev.index if j not in me]
    diffs = np.array([ev.sec[j] - gt.sec[i] for i, j in m])

    rows = []
    for name, sel in [("GENEL", None), ("PAS", "PAS"), ("TOP KAYBI", "TOP KAYBI")]:
        tp = sum(1 for i, _ in m if sel is None or gt.tip[i] == sel)
        nfp = sum(1 for j in fp if sel is None or ev.tip[j] == sel)
        nfn = sum(1 for i in fn if sel is None or gt.tip[i] == sel)
        p, r, f1 = prf(tp, nfp, nfn)
        rows.append(dict(grup=name, TP=tp, FP=nfp, FN=nfn, P=round(p, 3), R=round(r, 3), F1=round(f1, 3)))
    for r_ in rows:
        r_["F1_CI95_alt"], r_["F1_CI95_ust"] = (round(x, 3) for x in bootstrap_f1(r_["TP"], r_["FP"], r_["FN"], n_boot))
    res = dict(table=pd.DataFrame(rows), n_gt=len(gt), n_ev=len(ev), n_ev_disi=len(evall) - len(ev))
    if len(diffs):
        res["fark"] = dict(n=len(diffs), medyan=float(np.median(diffs)), ort=float(diffs.mean()),
                           std=float(diffs.std(ddof=1)) if len(diffs) > 1 else 0.0,
                           mutlak_ort=float(np.abs(diffs).mean()))
    # tip karisikligi: kalanlar arasinda zamani tutan ama tipi farkli olanlar
    cm = match(gt.loc[fn], ev.loc[fp], tol, typed=False)
    res["karisiklik"] = [(fmt(gt.sec[i]), gt.tip[i], ev.tip[j], fmt(ev.sec[j])) for i, j in cm]
    res["fn"], res["fp"], res["gt"], res["ev"], res["m"], res["cm"] = fn, fp, gt, ev, m, cm

    if diagnose:
        res["kategori"] = categorize(gt, ev, fn, fp, cm, tol)
    if not quiet:
        report(res, start, end, tol)
    return res


def bootstrap_f1(tp, fp, fn, n_boot=1000, seed=0):
    """F1 icin %95 yuzdelik bootstrap araligi. Birimler (TP / FP / FN ogeleri) yerine koyarak
    yeniden orneklenir; F1 = 2TP / (2TP + FP + FN). Sabit seed -> tekrarlanabilir."""
    units = np.array([0] * tp + [1] * fp + [2] * fn)       # 0=TP 1=FP 2=FN
    if len(units) == 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(units), size=(n_boot, len(units)))
    s = units[idx]
    t, f_p, f_n = (s == 0).sum(1), (s == 1).sum(1), (s == 2).sum(1)
    den = 2 * t + f_p + f_n
    f1 = np.where(den > 0, 2 * t / np.maximum(den, 1), 0.0)
    return float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5))


def paired_bootstrap(res_a, res_b, n_boot=1000, seed=0):
    """Etiket duzeyinde ESLESTIRILMIS bootstrap: A (taban) ve B (ayar) ayni etiket orneklerinden degerlendirilir.
    Birim = gercek etiket. Her etiketin her sistemdeki sonucu (TP/FN) ve o etikete (zamanca en yakin) atanan
    FP'ler birlikte yerine koyarak orneklenir; F1 = 2TP/(2TP+FP+FN). Cikti: grup basina F1 farki (B - A):
    gozlenen fark, %95 yuzdelik araligi, P(fark > 0). Ayni sabit seed ile her grup ayni orneklemeyi kullanir.
    Not: etiket setleri (gt) iki sonucta ayni olmali."""
    gt = res_a["gt"]
    n = len(gt)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    out = []
    for name, sel in (("GENEL", None), ("PAS", "PAS"), ("TOP KAYBI", "TOP KAYBI")):
        f1s = []
        obs = []
        for res in (res_a, res_b):
            tp = np.zeros(n); fn = np.zeros(n); fp = np.zeros(n)
            matched = {i for i, _ in res["m"]}
            for i in range(n):
                if sel is None or gt.tip[i] == sel:
                    (tp if i in matched else fn)[i] = 1
            for j in res["fp"]:
                if sel is None or res["ev"].tip[j] == sel:
                    fp[int(np.argmin(np.abs(gt.sec.to_numpy() - res["ev"].sec[j])))] += 1
            T, F, N = tp[idx].sum(1), fp[idx].sum(1), fn[idx].sum(1)
            den = 2 * T + F + N
            f1s.append(np.where(den > 0, 2 * T / np.maximum(den, 1), 0.0))
            t0, f0, n0 = tp.sum(), fp.sum(), fn.sum()
            obs.append(2 * t0 / (2 * t0 + f0 + n0) if (2 * t0 + f0 + n0) else 0.0)
        dlt = f1s[1] - f1s[0]
        out.append(dict(grup=name, F1_taban=round(obs[0], 3), F1_ayar=round(obs[1], 3), fark=round(obs[1] - obs[0], 3),
                        CI_alt=round(float(np.percentile(dlt, 2.5)), 3), CI_ust=round(float(np.percentile(dlt, 97.5)), 3),
                        P_fark_pozitif=round(float((dlt > 0).mean()), 3)))
    return pd.DataFrame(out)


def categorize(gt, ev, fn, fp, cm, tol):
    bt = pd.read_csv(os.path.join(HERE, "ball_track.csv")).set_index("frame")
    pos = pd.read_csv(os.path.join(HERE, "possession.csv"))
    teams = pd.read_csv(os.path.join(HERE, "teams.csv")).set_index("track_id").team.to_dict()
    p0 = pd.read_csv(os.path.join(HERE, "players.csv"), usecols=["frame", "track_id", "class_id"])
    cls0 = p0.groupby("track_id").class_id.agg(lambda s: s.mode().iloc[0]).to_dict()
    tm = match(gt.loc[fn], ev.loc[fp], 3.0)          # ayni tip, 1-3 sn kayma
    tmg = {i for i, _ in tm}
    tme = {j for _, j in tm}
    cmg = {i for i, _ in cm}
    cme = {j for _, j in cm}

    def seq(t):
        f0, f1 = int(round((t - 1.5) * FPS)), int(round((t + 1.5) * FPS))
        ps = pos[(pos.frame >= f0) & (pos.frame <= f1)]
        out = [(int(g.track_id.iloc[0]), len(g)) for _, g in ps.groupby((ps.track_id != ps.track_id.shift()).cumsum())]
        return out, float(bt.loc[f0:f1, "bx"].notna().mean())

    rows = []
    for i in fn:
        s, kn = seq(gt.sec[i])
        if any(cls0.get(a) == 2 for a, _ in s):
            c = "Hakem karisimi"
        elif i in tmg:
            c = "Zamanlama farki (1-3 sn)"
        elif gt.tip[i] == "TOP KAYBI" or i in cmg:
            c = "Yanlis takim atamasi"
        elif kn < 0.70:
            c = "Top kaybolmus"
        elif len({a for a, _ in s}) >= 2 and any(n < 5 for _, n in s[1:]):
            c = "Cok kisa sahiplik (filtre)"
        else:
            c = "Atlanan pas (alicida sahiplik yok)"
        rows.append(("FN", i, c))
    for j in fp:
        r = ev.loc[j]
        near = gt[((gt.sec - r.sec).abs() <= tol) & (gt.tip == r.tip)]
        if any(cls0.get(int(a)) == 2 for a in (r.kimden, r.kime)):
            c = "Hakem karisimi"
        elif j in cme:
            c = "Yanlis takim atamasi"
        elif j in tme:
            c = "Zamanlama farki (1-3 sn)"
        elif len(near):
            c = "Cift sayim"
        else:
            c = "Etiket yok / karsiliksiz tespit"
        rows.append(("FP", j, c))
    return pd.DataFrame(rows, columns=["tur", "idx", "kategori"])


def report(res, start, end, tol):
    print(f"Aralik {fmt(start)}-{fmt(end)} | tol +/-{tol} sn | etiket {res['n_gt']} | tahmin {res['n_ev']} "
          f"(aralik disi {res['n_ev_disi']} yok sayildi)")
    print(res["table"].to_string(index=False))
    print("(F1_CI95: TP/FP/FN birimleri yerine koyarak 1000x bootstrap, yuzdelik %95 araligi)")
    if "fark" in res:
        f = res["fark"]
        print(f"Isaretli zaman farki (tahmin-gercek, n={f['n']}): medyan {f['medyan']:+.2f} | ort {f['ort']:+.2f} | "
              f"std {f['std']:.2f} | mutlak ort {f['mutlak_ort']:.2f} sn")
    print(f"Tip karisikligi ({len(res['karisiklik'])}):", res["karisiklik"])
    gt, ev = res["gt"], res["ev"]
    kat = res.get("kategori")
    print("\nFN:")
    for i in res["fn"]:
        c = "" if kat is None else kat[(kat.tur == "FN") & (kat.idx == i)].kategori.iloc[0]
        print(f"  {fmt(gt.sec[i])}  {gt.tip[i]:<9}  {c}")
    print("FP:")
    for j in res["fp"]:
        c = "" if kat is None else kat[(kat.tur == "FP") & (kat.idx == j)].kategori.iloc[0]
        print(f"  {fmt(ev.sec[j])}  {ev.tip[j]:<9}  {int(ev.kimden[j])}->{int(ev.kime[j])}  {c}")
    if kat is not None:
        print("\nKategori sayilari:")
        print(pd.crosstab(kat.kategori, kat.tur, margins=True).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--events", default="events.csv")
    ap.add_argument("--labels", default="gercek_olaylar.csv")
    ap.add_argument("--start", type=float, default=60)
    ap.add_argument("--end", type=float, default=180)
    ap.add_argument("--tol", type=float, default=1.0)
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--compare", action="append", default=[], metavar="EVENTS_CSV",
                    help="--events'i taban alip bu ayar sonucuyla eslestirilmis bootstrap (1000x) karsilastirmasi; tekrarlanabilir")
    ap.add_argument("--bootstrap", type=int, default=1000, help="bootstrap ornekleme sayisi (F1 %%95 araligi)")
    a = ap.parse_args()
    base = run(a.events, a.labels, a.start, a.end, a.tol, a.diagnose, n_boot=a.bootstrap)
    for c in a.compare:
        var = run(c, a.labels, a.start, a.end, a.tol, quiet=True, n_boot=a.bootstrap)
        print(f"\nEslestirilmis bootstrap ({a.bootstrap}x): {c} - {a.events}")
        print(paired_bootstrap(base, var, a.bootstrap).to_string(index=False))
