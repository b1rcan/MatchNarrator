"""
events_v2.py - Sahiplik (possession) tabanli olay tespiti

Mantik: "Top hizli mi?" degil, "Top KIMDE ve kimden kime GECTI?"
  1) Top izi: her karede tek top secilir (onceki konuma en yakin aday),
     kisa bosluklar doldurulur.
  2) Takim ayrimi: forma renkleri 2 kumeye ayrilir (K-means).
  3) Sahiplik: topa en yakin oyuncu, mesafe / oyuncu boyu < esik ise topun sahibi.
     Olcek olarak oyuncunun kendi boyu kullanildigi icin kamera zoom/pan'dan etkilenmez.
  4) Olay: sahiplik A'dan B'ye gecti ->
        ayni takim  -> PAS
        farkli takim -> TOP KAYBI

Girdiler : players.csv, ball_candidates.csv, meta.json  (extract_v2.py uretir)
Opsiyonel: gercek_olaylar.csv  (elle isaretlenmis dogru olaylar -> precision/recall)
Ciktilar : events.csv, ball_track.csv, possession.csv, teams.csv
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
import pandas as pd

# ---------------- AYARLAR (deneyerek ayarlanacak) ----------------
MAX_BALL_JUMP = 45       # px/kare: onceki top konumundan izin verilen en buyuk sicrama
MAX_INTERP_GAP = 10      # kare: bu uzunluga kadar olan bosluklar dogrusal doldurulur
POSS_DIST = 0.45         # (top-ayak mesafesi) / (oyuncu boyu) bunun altindaysa top o oyuncuda
DRIBBLE_GAP = 12         # kare: ayni oyuncunun sahipligi bu kadar kesintiyle devam sayilir
MIN_POSS_FRAMES = 2      # sahiplik sayilmasi icin en az kare
MAX_PASS_GAP_SEC = 3.0   # iki sahiplik arasi en fazla sure (fazlasi: top kayip/oyun disi)
SAME_PLAYER_DIST = 0.5   # takip ID'si degisse de ayni kisi mi? (boy orani)
MATCH_TOL_SEC = 1.0      # dogrulama toleransi (saniye)
EVENT_TIME_ANCHOR = "receiver_start"  # olay zamani: "receiver_start" = alicinin (PAS) / rakibin (TOP KAYBI)
                                      # sahiplik serisinin ILK karesi; "passer_end" = eski davranis (pasorun son karesi)
ID_MERGE_REQUIRE_SAME_TEAM = 0  # 1: "ayni kisi, ID degismis" birlestirmesi, iki izin takimi (ikisi de biliniyorsa) farkliysa yapilmaz; 0: eski davranis
MIN_PASS_DIST_M = 3.0    # pas: atildigi ve alindigi yer arasi en az bu kadar metre
MAX_BALL_SPEED_MS = 35.0 # en sert sutlar ~35-40 m/sn; ustu top izinin sicramasidir
MIN_RECEIVE_FRAMES = 4   # pas alicisi topu en az bu kadar kare tutmali (titreme filtresi)
MIN_RECEIVE_FRAMES_LOSS = 5  # top kaybi: karsi takim topu en az bu kadar kare tutmali
BALL_MARGIN_M = 1.0
PENCERE_TABAN_M = 2.0      # top izi: son konum etrafindaki arama penceresinin taban yaricapi
TOP_KAYIP_SN = 0.5         # bu sureden uzun kayipsa yeniden yakalama dogrulamasi gerekir
DOGRULAMA_KARE = 3         # yeniden yakalamada aday art arda en az bu kadar karede tutarli olmali
ANINDA_KABUL_GUVEN = 0.70  # bu guvenin ustundeki aday dogrulamasiz kabul edilir
SPOT_RADIUS_M = 0.7        # penalti/orta noktasina bu kadar yakin aday "beyaz nokta" sayilir
SPOT_TAKIP_M = 1.5         # beyaz noktadaki aday, top bu mesafeden takip edilerek geldiyse kabul      # top, cizgilerin bu kadar disina kadar kabul edilir (homografi hatasi payi)
REF_KEEP_RATIO = 0.90
MAX_REF_CONCURRENT = 1.5  # bir takim renginde ayni anda bundan fazla 'hakem' = sistematik karisiklik    # karelerinin %90'indan fazlasinda "hakem" denen iz gercek hakem sayilir
# ------------------------------------------------------------------

# ---- komut satiri: --set PARAM=DEGER (tekrarlanabilir) ve --out-dir KLASOR ----
# Ornek: python events_v2.py --set MIN_RECEIVE_FRAMES=3 --out-dir tarama/mrf3
_ap = argparse.ArgumentParser(description="Sahiplik tabanli olay tespiti")
_ap.add_argument("--set", action="append", default=[], metavar="PARAM=DEGER",
                 help="yukaridaki AYARLAR sabitlerinden birini ez (orn. MIN_RECEIVE_FRAMES=3)")
_ap.add_argument("--out-dir", default=None,
                 help="cikti klasoru (verilmezse eskisi gibi proje klasoru); ana ciktilarin ustune yazmamak icin")
_ap.add_argument("--in-dir", default=None,
                 help="girdi klasoru (players.csv, ball_candidates.csv, meta.json, homography.csv); verilmezse proje klasoru")
_ap.add_argument("--teams", default=None, metavar="CSV",
                 help="takim atamasini bu CSV'den al (takim_siglip.py ciktisi). Verilmezse eski K-means (varsayilan)")
_args = _ap.parse_args()
for _kv in _args.set:
    _k, _, _v = _kv.partition("=")
    if _k not in globals() or not _k.isupper() or _k.startswith("_"):
        sys.exit(f"HATA: bilinmeyen parametre: {_k}")
    globals()[_k] = type(globals()[_k])(_v)
    print(f"[--set] {_k} = {globals()[_k]!r}")
_IN_DIR = os.path.abspath(_args.in_dir) if _args.in_dir else None
_TEAMS_CSV = os.path.abspath(_args.teams) if _args.teams else None
_OUT_DIR = os.path.abspath(_args.out_dir) if _args.out_dir else None
if _OUT_DIR:
    os.makedirs(_OUT_DIR, exist_ok=True)


def IN(name):
    """Girdi dosya yolu: --in-dir varsa orada, yoksa proje klasorunde (eskisi gibi)."""
    return os.path.join(_IN_DIR, name) if _IN_DIR else name


def OUT(name):
    """Cikti dosya yolu: --out-dir varsa orada, yoksa (eskisi gibi) proje klasorunde."""
    return os.path.join(_OUT_DIR, name) if _OUT_DIR else name


os.chdir(os.path.dirname(os.path.abspath(__file__)))  # goreli yollar betigin klasorune gore cozulur
meta = json.load(open(IN("meta.json")))
fps = meta["fps"]
frames = np.arange(meta["start_frame"], meta["end_frame"])
players = pd.read_csv(IN("players.csv"))
cands = pd.read_csv(IN("ball_candidates.csv"))


def fmt(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


# ================= 0) SAHA DISI TOP ADAYLARINI ELEME =================
# Asil yontem (homography.csv varsa): her top adayi o karenin homografisiyle gercek saha
# koordinatina cevrilir; tac/kale cizgilerinin BALL_MARGIN_M disindaysa elenir.
# Kamera hareketinden ve stadyumdan bagimsizdir (logo, top toplayicilar, tribun vb.).
HOMO = {}
if os.path.exists(IN("homography.csv")):
    from saha_geometri import L as PITCH_L, W as PITCH_W
    hdf = pd.read_csv(IN("homography.csv"))
    hdf = hdf[hdf["durum"] > 0]
    hcols = [f"h{i}" for i in range(9)]
    HOMO = dict(zip(hdf["frame"].astype(int), hdf[hcols].to_numpy(np.float64).reshape(-1, 3, 3)))

    cx_all = ((cands["x1"] + cands["x2"]) / 2).to_numpy(np.float32)
    cy_all = ((cands["y1"] + cands["y2"]) / 2).to_numpy(np.float32)
    pxm = np.full(len(cands), np.nan)
    pym = np.full(len(cands), np.nan)
    for f, idx in cands.groupby("frame").indices.items():
        H = HOMO.get(int(f))
        if H is None:
            continue
        pts = np.column_stack((cx_all[idx], cy_all[idx])).reshape(-1, 1, 2)
        pp = cv2.perspectiveTransform(pts, H).reshape(-1, 2) / 100.0
        pxm[idx], pym[idx] = pp[:, 0], pp[:, 1]
    known = ~np.isnan(pxm)
    inside = ((pxm >= -BALL_MARGIN_M) & (pxm <= PITCH_L / 100 + BALL_MARGIN_M)
              & (pym >= -BALL_MARGIN_M) & (pym <= PITCH_W / 100 + BALL_MARGIN_M))
    outside = known & ~inside
    n_before = len(cands)
    cands = cands[~outside].reset_index(drop=True)
    print(f"Saha disi top eleme (homografi): {int(outside.sum())} aday elendi "
          f"(%{100 * outside.sum() / max(n_before, 1):.1f}); homografisi olmayan karedeki "
          f"{int((~known).sum())} aday filtrelenemedi")
else:
    # Yedek yontem (homografi yoksa): sabit nokta temizleme
    cx_all = (cands["x1"] + cands["x2"]) / 2
    cy_all = (cands["y1"] + cands["y2"]) / 2

    # Adaylari 8 px yuvarlayarak grupla; ayni "nokta"da kac kez, kac farkli karede belirmis?
    qx = (cx_all / 8).round() * 8
    qy = (cy_all / 8).round() * 8
    pt = pd.DataFrame({"qx": qx, "qy": qy, "frame": cands["frame"]})
    grp = pt.groupby(["qx", "qy"])
    hits = grp["frame"].size()
    span = grp["frame"].apply(lambda s: s.max() - s.min())   # ilk-son gorulme araligi

    # Sabit nokta: cok kez belirmis (>=40) VE genis bir zaman araligina yayilmis
    # (yani anlik degil, video boyunca hep orada) -> logo
    STATIC_MIN_HITS = 40
    STATIC_MIN_SPAN = 1500   # kare: ~1 dk'dan uzun sure ayni noktada goruluyorsa logo
    static_pts = set(hits[(hits >= STATIC_MIN_HITS) & (span >= STATIC_MIN_SPAN)].index)

    if static_pts:
        is_static = np.array([(x, y) in static_pts for x, y in zip(qx, qy)])
        removed = int(is_static.sum())
        cands = cands[~is_static].reset_index(drop=True)
        print(f"Sabit grafik/logo temizleme: {len(static_pts)} sabit nokta, "
              f"{removed} top adayi elendi")
    else:
        print("Sabit grafik/logo temizleme: sabit nokta bulunamadi")


# ================= 1) TOP IZI =================
# Homografi varsa top saha koordinatinda (metre) izlenir:
#  - Top biliniyorken: yalnizca son konumun etrafindaki fiziksel pencerede aranir
#    (pencere = PENCERE_TABAN_M + MAX_BALL_SPEED_MS * gecen sure). Disindaki adaylar yok sayilir.
#  - Penalti noktalari ve orta nokta (beyaz, yuvarlak): buradaki aday ancak top oraya TAKIP
#    EDILEREK geldiyse kabul edilir (penaltida top oyuncu tarafindan noktaya getirilir).
#  - Top TOP_KAYIP_SN'den uzun sure kaybolursa yeni bir aday ancak art arda DOGRULAMA_KARE
#    karede tutarli gorunurse (veya guveni cok yuksekse) yeniden "top" kabul edilir.
chosen = {}
ball_stats = {"pencere_disi": 0, "beyaz_nokta": 0, "yeniden_yakalama": 0, "dogrulanmayan_aday": 0}

if HOMO:
    from saha_geometri import PS as _PS
    SPOTS_M = np.array([[_PS / 100, PITCH_W / 200], [PITCH_L / 200, PITCH_W / 200],
                        [(PITCH_L - _PS) / 100, PITCH_W / 200]])
by_frame = {}
for f, g in cands.groupby("frame"):
    c = g[["x1", "y1", "x2", "y2", "conf"]].to_numpy()
    img = np.column_stack(((c[:, 0] + c[:, 2]) / 2, (c[:, 1] + c[:, 3]) / 2))
    H = HOMO.get(int(f))
    if H is not None:
        pm = cv2.perspectiveTransform(img.reshape(-1, 1, 2).astype(np.float32), H).reshape(-1, 2) / 100.0
        spot = np.linalg.norm(pm[:, None, :] - SPOTS_M[None, :, :], axis=2).min(axis=1) < SPOT_RADIUS_M
    else:
        pm, spot = None, np.zeros(len(c), bool)
    by_frame[int(f)] = (img, pm, c[:, 4], spot)

trk_pm, trk_img, trk_f = None, None, None      # metrik iz
tentative = []                                 # top kayipken aday izler
last_xy, last_f = None, None                   # homografisiz yedek yontem
for f in frames:
    item = by_frame.get(int(f))
    if item is None:
        continue
    img, pm, conf, spot = item

    if pm is None:                             # --- yedek: piksel tabanli eski yontem ---
        if last_xy is not None and f - last_f <= fps:
            d = np.linalg.norm(img - last_xy, axis=1)
            i = int(np.argmin(d))
            if d[i] > MAX_BALL_JUMP * (f - last_f):
                continue
        else:
            i = int(np.argmax(conf))
        chosen[f] = img[i]
        last_xy, last_f = img[i], f
        continue

    lost = trk_f is None or (f - trk_f) > TOP_KAYIP_SN * fps
    if not lost:                               # --- top biliniyor: pencere icinde en yakin aday ---
        dt = (f - trk_f) / fps
        d = np.linalg.norm(pm - trk_pm, axis=1)
        in_win = d <= PENCERE_TABAN_M + MAX_BALL_SPEED_MS * dt
        normal = in_win & ~spot
        if normal.any():                       # once beyaz nokta OLMAYAN adaylar
            i = np.where(normal)[0][np.argmin(d[normal])]
            chosen[f] = img[i]
            trk_pm, trk_img, trk_f = pm[i], img[i], f
            ball_stats["beyaz_nokta"] += int((in_win & spot).sum())
            continue
        spot_ok = in_win & spot & (d <= SPOT_TAKIP_M)
        if spot_ok.any():
            # Beyaz noktadaki aday: top oraya takip edilerek geldiyse gosterilir, ama izin
            # "son gercek gorulme" bilgisi YENILENMEZ. Boylece iz noktaya yapisip kalamaz:
            # TOP_KAYIP_SN sonra iz kayip sayilir ve yeniden yakalamada noktalar haric tutulur.
            i = np.where(spot_ok)[0][np.argmin(d[spot_ok])]
            chosen[f] = img[i]
        else:
            ball_stats["beyaz_nokta"] += int((in_win & spot).sum())
            ball_stats["pencere_disi"] += 1
        continue

    # --- top kayip: yeniden yakalama icin dogrulama ---
    ball_stats["beyaz_nokta"] += int(spot.sum())
    updated = set()
    for i in np.where(~spot)[0]:
        match = None
        for k, t in enumerate(tentative):
            dt = (f - t["f"]) / fps
            if k not in updated and 0 < dt <= 0.4 and \
                    np.linalg.norm(pm[i] - t["pm"]) <= PENCERE_TABAN_M + MAX_BALL_SPEED_MS * dt:
                match = k
                break
        if match is None:
            tentative.append(dict(pm=pm[i], f=f, hits=1, hist=[(f, img[i])], maxconf=conf[i]))
            updated.add(len(tentative) - 1)
        else:
            t = tentative[match]
            t.update(pm=pm[i], f=f, hits=t["hits"] + 1, maxconf=max(t["maxconf"], conf[i]))
            t["hist"].append((f, img[i]))
            updated.add(match)
    tentative = [t for t in tentative if (f - t["f"]) <= 0.4 * fps]
    ready = [t for t in tentative if t["hits"] >= DOGRULAMA_KARE or t["maxconf"] >= ANINDA_KABUL_GUVEN]
    if ready:
        t = max(ready, key=lambda t: (t["hits"], t["maxconf"]))
        for ff, ii in t["hist"]:               # dogrulanan izin onceki karelerini de geri doldur
            chosen[ff] = ii
        trk_pm, trk_img, trk_f = t["pm"], t["hist"][-1][1], f
        ball_stats["yeniden_yakalama"] += 1
        ball_stats["dogrulanmayan_aday"] += sum(1 for x in tentative if x is not t)
        tentative = []

ball = pd.DataFrame(index=pd.Index(frames, name="frame"), columns=["bx", "by"], dtype=float)
for f, (x, y) in chosen.items():
    ball.loc[f] = (x, y)
ball["detected"] = ball["bx"].notna()

isna = ball["bx"].isna()
gap_len = isna.groupby((~isna).cumsum()).transform("sum")
interp = ball[["bx", "by"]].interpolate(limit_area="inside")
fill = isna & (gap_len <= MAX_INTERP_GAP) & interp["bx"].notna()
ball.loc[fill, ["bx", "by"]] = interp.loc[fill]

n = len(frames)
print("=" * 60)
print(f"Islenen aralik: {fmt(frames[0] / fps)} - {fmt(frames[-1] / fps)}  ({n} kare)")
print(f"Topun tespit edildigi kare   : %{100 * ball['detected'].mean():.1f}")
if HOMO:
    print(f"Top izi: {ball_stats['pencere_disi']} karede adaylar fiziksel pencere disinda kaldi (yok sayildi), "
          f"{ball_stats['beyaz_nokta']} beyaz nokta (penalti/orta) adayi reddedildi, "
          f"{ball_stats['yeniden_yakalama']} kez top kaybindan sonra dogrulanarak yeniden yakalandi")
print(f"Doldurma sonrasi top bilinen : %{100 * ball['bx'].notna().mean():.1f}")

# ================= 2) TAKIM AYRIMI + HAKEM DUZELTMESI =================
# Her iz (track) icin: en sik gorulen sinif + medyan forma rengi
players = players.dropna(subset=["L", "A", "B"]).copy()
trk = players.groupby("track_id").agg(
    cls=("class_id", lambda s: s.mode().iloc[0]),
    ref_ratio=("class_id", lambda s: float((s == 2).mean())),
    n=("frame", "size"), L=("L", "median"), A=("A", "median"), B=("B", "median"))

team_of = {}
fixed_refs = 0
fit = trk[(trk["cls"] == 0) & (trk["n"] >= 25)]
if len(fit) < 4:
    fit = trk[trk["cls"] == 0]
if len(fit) >= 2:
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.1)
    _, labels, centers = cv2.kmeans(fit[["L", "A", "B"]].to_numpy(np.float32), 2, None,
                                    criteria, 10, cv2.KMEANS_PP_CENTERS)
    dist = np.linalg.norm(trk[["L", "A", "B"]].to_numpy()[:, None, :] - centers[None, :, :], axis=2)
    trk["team"] = dist.argmin(axis=1)
    trk["team_dist"] = dist.min(axis=1)

    # Takim icindeki "normal" renk sapmasi: oyuncularin kendi merkezine uzakliginin %90'i
    own = np.linalg.norm(fit[["L", "A", "B"]].to_numpy() - centers[labels.ravel()], axis=1)
    thr = float(np.percentile(own, 90))

    # Hakem sanilan ama formasi bir takimla eslesen izler -> aslinda oyuncu.
    # Gercek hakem neredeyse her karede "hakem" olarak tespit edilir (ref_ratio yuksek);
    # yanlis etiketlenen oyuncular ise oyuncu/hakem arasinda gidip gelir.
    ref_like_player = ((trk["cls"] == 2) & (trk["team_dist"] <= thr)
                       & (trk["ref_ratio"] < REF_KEEP_RATIO))

    # Sistematik karisiklik kontrolu: sahada ayni anda en fazla 1 orta hakem olur.
    # Bir takimin renginde AYNI ANDA ortalama MAX_REF_CONCURRENT'ten fazla "hakem" goruluyorsa
    # (or. sari formali takim, egitim verisindeki sari hakemlere benzedigi icin), o renkteki
    # tum "hakem" izleri aslinda oyuncudur. Gercek hakemin renginde ise ayni anda ~1 kisi gorulur.
    cand = trk[(trk["cls"] == 2) & (trk["team_dist"] <= thr)]
    ref_rows = players[players["track_id"].isin(cand.index)].copy()
    ref_rows["cand_team"] = ref_rows["track_id"].map(cand["team"])
    for t in (0, 1):
        per_frame = ref_rows[ref_rows["cand_team"] == t].groupby("frame")["track_id"].nunique()
        concurrent = float(per_frame.mean()) if len(per_frame) else 0.0
        if concurrent > MAX_REF_CONCURRENT:
            ref_like_player |= (trk["cls"] == 2) & (trk["team_dist"] <= thr) & (trk["team"] == t)
        print(f"  Takim {'AB'[t]} renginde ayni anda ortalama {concurrent:.1f} 'hakem' -> "
              f"{'sistematik karisiklik, oyuncuya cevriliyor' if concurrent > MAX_REF_CONCURRENT else 'normal (gercek hakem olabilir)'}")
    fixed_refs = int(ref_like_player.sum())
    trk.loc[ref_like_player, "cls"] = 0

    for tid, row in trk.iterrows():
        if row["cls"] == 0:                     # kaleci (1) ve hakem (2) takimsiz kalir
            team_of[tid] = int(row["team"])

# --teams: takim etiketini disaridan al (hakem duzeltmesi ve sinif kararlari YUKARIDA oldugu gibi kalir;
# yalniz zaten oyuncu sayilan izlerin takimi degisir). Kaleci (rol=gk) eskisi gibi takimsiz kalir.
if _TEAMS_CSV:
    _sig = pd.read_csv(_TEAMS_CSV).set_index("track_id")
    _chg = _miss = 0
    for _tid in list(team_of):
        if _tid in _sig.index and _sig.at[_tid, "rol"] != "gk":
            _new = int(_sig.at[_tid, "team"])
            _chg += int(_new != team_of[_tid])
            team_of[_tid] = _new
        else:
            _miss += 1                                      # CSV'de yok -> eski K-means takimi korunur
    print(f"[--teams] {os.path.basename(_TEAMS_CSV)}: {len(team_of)} oyuncu izinden {_chg} tanesinin takimi degisti, "
          f"{_miss} izde CSV'de yok (eski takim korundu)")

# Her izin tum satirlarina tek, tutarli sinif ver (iz icinde sinif titremesini de onler)
players["class_id"] = players["track_id"].map(trk["cls"]).astype(int)
players.to_csv(OUT("players_fixed.csv"), index=False)

n_a = sum(v == 0 for v in team_of.values())
n_b = sum(v == 1 for v in team_of.values())
print(f"Takim ayrimi: {n_a} iz -> Takim A, {n_b} iz -> Takim B")
print(f"Hakem duzeltmesi: hakem sanilan {fixed_refs} iz, formasi takimla eslestigi icin oyuncuya cevrildi "
      f"(kalan hakem izi: {int((trk['cls'] == 2).sum())})")

# Takip kalitesi olcutu (BoT-SORT vs ByteTrack karsilastirmasi icin)
pl_tracks = trk[trk["cls"].isin([0, 1])]
print(f"Takip kalitesi: {len(pl_tracks)} benzersiz oyuncu izi, "
      f"ortalama iz suresi {pl_tracks['n'].mean() / fps:.1f} sn, "
      f"medyan {pl_tracks['n'].median() / fps:.1f} sn  (az iz + uzun sure = daha az ID kaymasi)")
pd.Series(team_of, name="team").rename_axis("track_id").to_csv(OUT("teams.csv"))

# ================= 3) SAHIPLIK =================
pl = players[players["class_id"].isin([0, 1])].copy()
pl["fx"] = (pl["x1"] + pl["x2"]) / 2
pl["fy"] = pl["y2"]
pl["h"] = (pl["y2"] - pl["y1"]).clip(lower=1)
pl = pl.merge(ball[["bx", "by"]], left_on="frame", right_index=True).dropna(subset=["bx"])
pl["nd"] = np.hypot(pl["fx"] - pl["bx"], pl["fy"] - pl["by"]) / pl["h"]

nearest = pl.loc[pl.groupby("frame")["nd"].idxmin()]
poss = nearest[nearest["nd"] < POSS_DIST].sort_values("frame")
poss[["frame", "track_id"]].to_csv(OUT("possession.csv"), index=False)
print(f"Topun bir oyuncuda oldugu kare: %{100 * len(poss) / n:.1f}")

# Sahiplik parcalari (segment)
segs = []
for row in poss.itertuples():
    s = segs[-1] if segs else None
    if s and s["id"] == row.track_id and row.frame - s["end"] <= DRIBBLE_GAP:
        s.update(end=row.frame, ex=row.fx, ey=row.fy, n=s["n"] + 1)
    else:
        segs.append(dict(id=row.track_id, cls=row.class_id, start=row.frame, end=row.frame,
                         sx=row.fx, sy=row.fy, ex=row.fx, ey=row.fy, h=row.h, n=1))
segs = [s for s in segs if s["n"] >= MIN_POSS_FRAMES]

# ================= 4) OLAYLAR =================
def to_pitch_m(f, x, y):
    """Goruntu noktasini (ayak) saha koordinatina (metre) cevirir; homografi yoksa None."""
    H = HOMO.get(int(f))
    if H is None:
        return None
    p = cv2.perspectiveTransform(np.array([[[x, y]]], np.float32), H)[0, 0]
    return p / 100.0


events = []
cand_log = []   # her sahiplik degisimi adayi icin karar kaydi (davranisi etkilemez)


def _log(cur, nxt, typ, karar, neden, gap, dist_m=np.nan, speed_ms=np.nan):
    ef = int(nxt["start"] if EVENT_TIME_ANCHOR == "receiver_start" else cur["end"])
    cand_log.append(dict(frame=ef, sec=round(ef / fps, 2), zaman=fmt(ef / fps), tip=typ,
                         kimden=int(cur["id"]), kime=int(nxt["id"]), alici_kare=int(nxt["n"]),
                         bosluk_sn=round(gap, 2),
                         mesafe_m=None if np.isnan(dist_m) else round(dist_m, 1),
                         hiz_ms=None if np.isnan(speed_ms) else round(speed_ms, 1),
                         karar=karar, neden=neden))


skipped = {"titreme": 0, "kisa_pas": 0, "imkansiz_hiz": 0}
if segs:
    cur = segs[0]
    for nxt in segs[1:]:
        gap = (nxt["start"] - cur["end"]) / fps
        if gap > MAX_PASS_GAP_SEC:                         # arada top kayboldu / oyun durdu
            _log(cur, nxt, "", "red", "bosluk_buyuk", gap)
            cur = nxt
            continue
        if cur["id"] == nxt["id"]:                         # ayni oyuncu -> pas degil, top surme
            _log(cur, nxt, "", "red", "ayni_oyuncu", gap)
            cur.update(end=nxt["end"], ex=nxt["ex"], ey=nxt["ey"])
            continue
        moved = np.hypot(nxt["sx"] - cur["ex"], nxt["sy"] - cur["ey"]) / cur["h"]
        _ta, _tb = team_of.get(cur["id"]), team_of.get(nxt["id"])
        _teams_differ = _ta is not None and _tb is not None and _ta != _tb
        if moved < SAME_PLAYER_DIST and gap < 0.5 and not (ID_MERGE_REQUIRE_SAME_TEAM and _teams_differ):   # ayni kisi, sadece ID degismis
            _log(cur, nxt, "", "red", "ayni_kisi_id_degisimi", gap)
            cur.update(end=nxt["end"], ex=nxt["ex"], ey=nxt["ey"])
            continue
        ta, tb = team_of.get(cur["id"]), team_of.get(nxt["id"])
        if ta is None or tb is None:
            typ = "DEGISIM (takim belirsiz)"               # kaleci veya kisa iz
        elif ta == tb:
            typ = "PAS"
        else:
            typ = "TOP KAYBI"

        # --- Titreme / ikili mucadele filtresi ---
        need = MIN_RECEIVE_FRAMES_LOSS if typ == "TOP KAYBI" else MIN_RECEIVE_FRAMES
        if nxt["n"] < need:                                # alici topu yeterince tutmadi -> yok say
            skipped["titreme"] += 1
            _log(cur, nxt, typ, "red", "kisa_kayip" if typ == "TOP KAYBI" else "kisa_alim", gap)
            continue                                       # cur ayni kalir
        dist_m = np.nan
        a = to_pitch_m(cur["end"], cur["ex"], cur["ey"])
        b = to_pitch_m(nxt["start"], nxt["sx"], nxt["sy"])
        if a is not None and b is not None:
            dist_m = float(np.linalg.norm(b - a))
        # Fiziksel olabilirlik: top bu mesafeyi bu surede alabilir mi?
        # (sahiplik yaricapi kadar mesafe zaten ayakta kabul edildigi icin ~1.5 m dusulur)
        speed_ms = np.nan
        if not np.isnan(dist_m):
            speed_ms = max(dist_m - 1.5, 0) / max(gap, 1 / fps)
            if speed_ms > MAX_BALL_SPEED_MS:
                skipped["imkansiz_hiz"] += 1               # top izi baska bir tespite sicramis
                _log(cur, nxt, typ, "red", "imkansiz_hiz", gap, dist_m, speed_ms)
                continue                                   # cur ayni kalir
        if typ == "PAS" and not np.isnan(dist_m) and dist_m < MIN_PASS_DIST_M:
            skipped["kisa_pas"] += 1                       # yan yana iki oyuncu arasinda gidip gelme
            _log(cur, nxt, typ, "red", "min_mesafe", gap, dist_m, speed_ms)
            cur = nxt
            continue

        _log(cur, nxt, typ, "kabul", "", gap, dist_m, speed_ms)
        ev_frame = int(nxt["start"] if EVENT_TIME_ANCHOR == "receiver_start" else cur["end"])
        events.append(dict(frame=ev_frame, sec=round(ev_frame / fps, 2),
                           zaman=fmt(ev_frame / fps), tip=typ,
                           kimden=int(cur["id"]), kime=int(nxt["id"]), sure_sn=round(gap, 2),
                           mesafe_m=None if np.isnan(dist_m) else round(dist_m, 1),
                           hiz_ms=None if np.isnan(speed_ms) else round(speed_ms, 1)))
        cur = nxt
print(f"Filtrelenen sahiplik degisimi: {skipped['titreme']} titreme (alici topu kisa sure tuttu), "
      f"{skipped['kisa_pas']} kisa mesafe (< {MIN_PASS_DIST_M:.0f} m) pas adayi, "
      f"{skipped['imkansiz_hiz']} fiziksel olarak imkansiz hiz (> {MAX_BALL_SPEED_MS:.0f} m/sn)")

ev = pd.DataFrame(events, columns=["frame", "sec", "zaman", "tip", "kimden", "kime", "sure_sn", "mesafe_m", "hiz_ms"])
ev.to_csv(OUT("events.csv"), index=False)
pd.DataFrame(cand_log, columns=["frame", "sec", "zaman", "tip", "kimden", "kime", "alici_kare", "bosluk_sn",
                                "mesafe_m", "hiz_ms", "karar", "neden"]).to_csv(OUT("events_adaylar.csv"), index=False)
ball["saha_x_m"] = np.nan
ball["saha_y_m"] = np.nan
if HOMO:
    for f in ball.index[ball["bx"].notna()]:
        H = HOMO.get(int(f))
        if H is not None:
            p = cv2.perspectiveTransform(np.array([[[ball.at[f, "bx"], ball.at[f, "by"]]]], np.float32), H)[0, 0]
            ball.at[f, "saha_x_m"], ball.at[f, "saha_y_m"] = p[0] / 100, p[1] / 100
ball.to_csv(OUT("ball_track.csv"))

minutes = n / fps / 60
print("-" * 60)
print(f"Toplam olay: {len(ev)}  ({len(ev) / minutes:.1f} / dakika)")
if len(ev):
    print(ev["tip"].value_counts().to_string())
    n_pass = (ev["tip"] == "PAS").sum()
    print(f"\n45 dk'ya oranlanmis PAS tahmini: ~{int(n_pass / minutes * 45)}  "
          f"(gercek maclarda bir devrede tipik olarak ~400-550 pas)")
    print("\nIlk 15 olay:")
    print(ev.head(15)[["zaman", "tip", "kimden", "kime", "sure_sn", "mesafe_m", "hiz_ms"]].to_string(index=False))

# ================= 5) DOGRULAMA (opsiyonel) =================
if os.path.exists("gercek_olaylar.csv") and not _args.in_dir:   # --in-dir (baska video araligi): etiketler eslesmez, atla
    gt = pd.read_csv("gercek_olaylar.csv", dtype=str)

    def to_sec(v):
        v = str(v).strip()
        if ":" in v:
            m, s = v.split(":")
            return int(m) * 60 + float(s)
        return float(v)

    gt["sec"] = gt["zaman"].map(to_sec)
    gt = gt[(gt["sec"] >= frames[0] / fps) & (gt["sec"] <= frames[-1] / fps)]
    # Yalnizca elle etiketlenen zaman araligi degerlendirilir (ornegin sadece 2 dakika etiketlendiyse)
    lo, hi = gt["sec"].min() - MATCH_TOL_SEC, gt["sec"].max() + MATCH_TOL_SEC
    evw = ev[(ev["sec"] >= lo) & (ev["sec"] <= hi)]

    def score(pred_t, gt_t):
        used, tp = set(), 0
        for t in gt_t:
            cand = [i for i in np.argsort(np.abs(pred_t - t)) if i not in used and abs(pred_t[i] - t) <= MATCH_TOL_SEC]
            if cand:
                used.add(cand[0])
                tp += 1
        p = tp / len(pred_t) if len(pred_t) else 0
        r = tp / len(gt_t) if len(gt_t) else 0
        return tp, p, r, (2 * p * r / (p + r) if p + r else 0)

    print("=" * 60)
    print(f"DOGRULAMA: {fmt(lo + MATCH_TOL_SEC)} - {fmt(hi - MATCH_TOL_SEC)} arasi, tolerans +/-{MATCH_TOL_SEC} sn")
    tp, p, r, f1 = score(evw["sec"].to_numpy(), gt["sec"].to_numpy())
    print(f"  Tum olaylar : {len(gt)} gercek, {len(evw)} tahmin | dogru {tp} | Precision {p:.2f} | Recall {r:.2f} | F1 {f1:.2f}")
    if "tip" in gt.columns:
        gp = gt[gt["tip"].str.upper().str.strip() == "PAS"]
        ep = evw[evw["tip"] == "PAS"]
        if len(gp):
            tp, p, r, f1 = score(ep["sec"].to_numpy(), gp["sec"].to_numpy())
            print(f"  Sadece PAS  : {len(gp)} gercek, {len(ep)} tahmin | dogru {tp} | Precision {p:.2f} | Recall {r:.2f} | F1 {f1:.2f}")
print("=" * 60)