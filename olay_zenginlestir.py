"""
olay_zenginlestir.py - events.csv olaylarini ek bilgilerle (konum, mesafe, yon, bolge, guven) JSON'a donusturur.

Girdiler (iki kaynak, ayri iz numarasi uzaylari):
  ana_60_360   : events.csv, players.csv, homography.csv, ball_track.csv, teams.csv, events_adaylar.csv, players_fixed.csv (proje klasoru)
  veri_360_540 : ayni dosyalar veri_360_540/ icinde
Cikti: olaylar_zengin.json (liste). Eksik bilgi (homografi/oyuncu/top) -> alan null; deger UYDURULMAZ.

Konum: eski sahibin SON sahiplik karesindeki ve yeni sahibin ILK sahiplik karesindeki AYAK noktasi
(kutu alt-orta), kareye ozgu homografiyle saha koordinatina (metre, 105 x 68; x = boy, y = en) cevrilir.
Hucum yonu bilinmedigi icin yon x ekseninde isaretle (+x / -x) verilir; 'savunma/hucum' ayrimi yapilmaz, x ucte biri
dusuk_x / orta / yuksek_x olarak adlandirilir.
Top hizi: events.csv'deki hiz_ms = max(mesafe - 1.5, 0) / bosluk_sn (yaklasik; ayak-top ofseti ~1.5 m dusulmus).
"""
import argparse
import json
import os

import cv2
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 25.0
PITCH_L, PITCH_W = 105.0, 68.0
_ap = argparse.ArgumentParser()
_ap.add_argument("--config", default=os.path.join(HERE, "config_takimlar.json"),
                 help="takim adlari {\"A\": ..., \"B\": ...}; dosya yoksa takim adi alani EKLENMEZ (cikti eskisi gibi)")
_ap.add_argument("--out", default=os.path.join(HERE, "olaylar_zengin.json"))
_args = _ap.parse_args()
TEAM_NAMES = json.load(open(_args.config, encoding="utf-8")) if os.path.exists(_args.config) else {}
SOURCES = {"ana_60_360": HERE, "veri_360_540": os.path.join(HERE, "veri_360_540")}


def mss(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def color_name(bgr):
    """Kaba renk adi (yaklasik, HSV tabanli)."""
    h, s, v = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
    h, s, v = int(h) * 2, int(s) / 255, int(v) / 255
    if v < 0.25:
        return "siyah/cok koyu"
    if s < 0.18:
        return "beyaz" if v > 0.75 else "gri"
    if s < 0.30:
        return "karisik/soluk (ad guvenilmez)"
    for lo, hi, name in ((0, 15, "kirmizi"), (15, 40, "turuncu"), (40, 70, "sari"), (70, 170, "yesil"), (170, 255, "mavi"),
                         (255, 290, "mor/lacivert"), (290, 345, "pembe/bordo"), (345, 361, "kirmizi")):
        if lo <= h < hi:
            return name + (" (koyu)" if v < 0.5 else "")
    return "belirsiz"


def team_colors(players, fixed, teams):
    """Takim basina baskin forma rengi: o takimin oyuncu-sinifli izlerinin (>=25 kare) medyan Lab degeri (kare agirlikli medyan)."""
    p = players.merge(fixed, on=["frame", "track_id"], how="left", suffixes=("", "_f"))
    p = p[p["class_id_f"] == 0].dropna(subset=["L", "A", "B"])
    out = {}
    for t, name in ((0, "A"), (1, "B")):
        ids = [k for k, v in teams.items() if v == t]
        q = p[p.track_id.isin(ids)]
        cnt = q.groupby("track_id").size()
        q = q[q.track_id.isin(cnt[cnt >= 25].index)]
        if q.empty:
            out[name] = dict(forma_rengi_hex=None, ad_yaklasik=None, iz_sayisi=0)
            continue
        lab = np.uint8([[[np.median(q.L), np.median(q.A), np.median(q.B)]]])           # OpenCV 8-bit Lab
        bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)[0, 0]
        out[name] = dict(forma_rengi_hex="#%02x%02x%02x" % (int(bgr[2]), int(bgr[1]), int(bgr[0])),
                         ad_yaklasik=color_name(bgr), iz_sayisi=int(q.track_id.nunique()))
    return out


def region(x, y):
    if x is None or y is None:
        return None
    xt = "dusuk_x" if x < PITCH_L / 3 else ("orta" if x < 2 * PITCH_L / 3 else "yuksek_x")
    yt = "kanat_y_dusuk" if y < PITCH_W / 3 else ("merkez" if y < 2 * PITCH_W / 3 else "kanat_y_yuksek")
    return dict(x_ucte_bir=xt, enine=yt)


def r2(v, n=2):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), n)


records = []
for src, d in SOURCES.items():
    ev = pd.read_csv(os.path.join(d, "events.csv"))
    players = pd.read_csv(os.path.join(d, "players.csv"))
    fixed = pd.read_csv(os.path.join(d, "players_fixed.csv"), usecols=["frame", "track_id", "class_id"]).rename(columns={"class_id": "class_id_f"})
    bt = pd.read_csv(os.path.join(d, "ball_track.csv")).set_index("frame")
    teams = pd.read_csv(os.path.join(d, "teams.csv")).set_index("track_id")["team"].to_dict()
    cand = pd.read_csv(os.path.join(d, "events_adaylar.csv"))
    cand = cand[cand.karar == "kabul"]
    hdf = pd.read_csv(os.path.join(d, "homography.csv"))
    hdur = dict(zip(hdf.frame.astype(int), hdf.durum.astype(int)))
    hdf = hdf[hdf.durum > 0]
    HOMO = dict(zip(hdf.frame.astype(int), hdf[[f"h{i}" for i in range(9)]].to_numpy(np.float64).reshape(-1, 3, 3)))
    pidx = players.set_index(["frame", "track_id"]).sort_index()
    colors = team_colors(players, fixed, teams)
    if TEAM_NAMES:                                   # config varsa takim adi eklenir (renk bilgisi ayri kalir)
        colors = {k: ({"ad": TEAM_NAMES[k]} | v if k in TEAM_NAMES else v) for k, v in colors.items()}

    def foot(f, tid):
        """(x_px, y_px, kutu_yuksekligi_px) veya None"""
        try:
            r = pidx.loc[(int(f), int(tid))]
        except KeyError:
            return None
        if isinstance(r, pd.DataFrame):
            r = r.iloc[0]
        return (r.x1 + r.x2) / 2, r.y2, float(r.y2 - r.y1)

    def to_m(f, p):
        H = HOMO.get(int(f))
        if p is None or H is None:
            return None
        q = cv2.perspectiveTransform(np.array([[[p[0], p[1]]]], np.float32), H)[0, 0] / 100.0
        return float(q[0]), float(q[1])

    def ball_state(f):
        if f in bt.index and not np.isnan(bt.at[f, "bx"]):
            return "tespit" if bool(bt.at[f, "detected"]) else "interpole"
        return "yok"

    for e in ev.itertuples():
        f_ev = int(e.frame)
        f_old = f_ev - int(round(float(e.sure_sn) * FPS))
        fo, fn = foot(f_old, e.kimden), foot(f_ev, e.kime)
        a, b = to_m(f_old, fo), to_m(f_ev, fn)
        dist = None if a is None or b is None else float(np.hypot(b[0] - a[0], b[1] - a[1]))
        dx = None if a is None or b is None else b[0] - a[0]
        cj = cand[(cand.frame == f_ev) & (cand.kimden == e.kimden) & (cand.kime == e.kime)]
        ok_in = lambda p: None if p is None else bool(-1 <= p[0] <= PITCH_L + 1 and -1 <= p[1] <= PITCH_W + 1)
        records.append(dict(
            id=f"{src}_{f_ev}", kaynak=src, kare=f_ev,
            zaman_sn=r2(e.sec), zaman=mss(e.sec), tip=e.tip,
            takimlar=colors,
            kimden=dict(iz=int(e.kimden), takim=("AB"[teams[e.kimden]] if e.kimden in teams else None)),
            kime=dict(iz=int(e.kime), takim=("AB"[teams[e.kime]] if e.kime in teams else None)),
            konum_baslangic_m=None if a is None else dict(x=r2(a[0]), y=r2(a[1])),
            konum_bitis_m=None if b is None else dict(x=r2(b[0]), y=r2(b[1])),
            konum_saha_icinde=dict(baslangic=ok_in(a), bitis=ok_in(b)),
            mesafe_m=r2(dist, 1),
            yon_x=None if dx is None else ("+x" if dx > 1.0 else ("-x" if dx < -1.0 else "~0")),
            dx_m=r2(dx, 1), dy_m=None if a is None or b is None else r2(b[1] - a[1], 1),
            top_hizi_ms=r2(e.hiz_ms, 1) if not pd.isna(e.hiz_ms) else None,
            top_hizi_yontem="(mesafe_m - 1.5) / bosluk_sn (yaklasik)",
            bosluk_sn=r2(e.sure_sn),
            bolge_baslangic=region(None if a is None else a[0], None if a is None else a[1]),
            bolge_bitis=region(None if b is None else b[0], None if b is None else b[1]),
            guven=dict(top_durumu_olay_kare=ball_state(f_ev), top_durumu_eski_sahip_son_kare=ball_state(f_old),
                       kutu_yuksekligi_px=dict(kimden=r2(fo[2], 0) if fo else None, kime=r2(fn[2], 0) if fn else None),
                       yeni_sahip_seri_kare=int(cj.alici_kare.iloc[0]) if len(cj) else None,
                       homografi_durum_olay_kare={1: "bu karede hesaplandi", 2: "onceki gecerli homografi", 0: "yok"}.get(hdur.get(f_ev), None))))

if TEAM_NAMES:                                       # kimden/kime icin takim_adi (yalniz config varsa)
    for r in records:
        for k in ("kimden", "kime"):
            t = r[k]["takim"]
            if t in TEAM_NAMES:
                r[k]["takim_adi"] = TEAM_NAMES[t]
with open(_args.out, "w", encoding="utf-8") as fh:
    json.dump(records, fh, ensure_ascii=False, indent=1)
print(f"{len(records)} olay yazildi -> {_args.out}")
miss = sum(r["konum_baslangic_m"] is None or r["konum_bitis_m"] is None for r in records)
print(f"konum eksik (null) olay: {miss}; saha disi konum isaretli: {sum(any(v is False for v in r['konum_saha_icinde'].values()) for r in records)}")
