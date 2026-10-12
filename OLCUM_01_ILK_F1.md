# OLCUM_01 — İlk F1 ölçümü (pas / top kaybı)

Tarih: 2026-10-12 · Kod değiştirilmedi · `events_v2.py` olduğu gibi çalıştırıldı (çıktılar yedeğiyle bayt bayt aynı çıktı → ara CSV'ler güncel).

## 1. Etiket dosyası (gercek_olaylar.csv)
| Kontrol | Sonuç |
|---|---|
| Satır | 41 (PAS 36, TOP KAYBI 5) |
| Aralık | 1:03.60 – 2:57.20 (video saati) |
| Format | Hata yok (m:ss.ss, boş/NaN yok, tipler yalnız PAS / TOP KAYBI, sıralı) |
| Yinelenen satır | 0 |
| <1 sn aralıklı satırlar | 10 çift (satır farkı <1 sn; en kısa 0.20 sn: 1:22.20 PAS → 1:22.40 TOP KAYBI; diğerleri 1:09.48→1:09.96, 1:23.08→1:23.44, 1:56.48 sonrası 1:57.12 / 1:58.76 / 1:59.60 / 2:00.32 zinciri, 2:03.04, 2:35.48 vb.). Düzeltme yapılmadı; hızlı ardışık pas/top kaybı olabilir, karar sana ait. Yinelenen yok, hepsi ≥0.20 sn. |

## 2. Ara CSV güncelliği
- `meta.json`: kare 1500–9000, 25 fps (= 1:00–6:00). players/ball_candidates/homography/ball_track: kare 1500–8999, hepsi 7500 kare (homography eksiksiz).
- Zaman damgaları: players, ball_candidates, meta 1.10 11:05 → homography 12:26 → players_fixed/teams/possession/events/ball_track 12:45 (zincir tutarlı). Betikler 12.10 10:51 tarihli (geri kurulum kopyası) — o günkü kodla birebir olup olmadığı dosya tarihinden doğrulanamaz; ancak `events_v2.py` yeniden çalıştırınca 5 çıktı (events, ball_track, possession, teams, players_fixed) eskisiyle **hash olarak aynı** çıktı → kod ve ara veri uyumlu.
- Tam hat çalıştırılmadı; yalnız `events_v2.py`. (Önce yedek alındı.)
- Not: `events_v2.py` kendi içindeki doğrulaması 14 TP / 26 tahmin / F1 0.42 diyor (eşleştirme yöntemi farklı: tip gözetmiyor, GT sırasına göre ilk uygun tahmini alıyor, değerlendirme penceresi 1:02.6–2:58.2). Aşağıdaki sayılar sizin kuralınıza göre.

## 3. Değerlendirme
Kural: yalnız 1:00–3:00 arası tahminler (27 tahmin; aralık dışı 29 tahmin yok sayıldı), ±1 sn, birebir (en yakın çift önce), **eşleşme için tip de aynı olmalı**. Tahmin zamanı = `events.csv` `sec` (pasör sahipliğinin son karesi).

| Grup | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| **Genel** | 12 | 15 | 29 | 0.444 | 0.293 | **0.353** |
| PAS | 11 | 13 | 25 | 0.458 | 0.306 | 0.367 |
| TOP KAYBI | 1 | 2 | 4 | 0.333 | 0.200 | 0.250 |

- Eşleşenlerde ortalama |zaman sapması| = **0.53 sn** (işaretli ortalama −0.04, medyan +0.08).
- Tip karışıklığı (zamanı ±1 sn tutan, tipi yanlış; TP sayılmadı, FP+FN'de duruyor): **3** — 2:55.40 gerçek TOP KAYBI→PAS tahmin; 1:58.76 TOP KAYBI→PAS; 1:18.76 PAS→TOP KAYBI.
- Duyarlılık (yalnız bilgi, kural değil): tolerans 1.5 sn → TP 19, P 0.70, R 0.46, F1 0.56; 2.0 sn → TP 22, P 0.81, R 0.54, F1 0.65.

### Hata listesi (44 hata: 29 FN + 15 FP)
Bakılan veri: `ball_track.csv` (top tespit/bilinen oranı, olay çevresi ±1.5 sn), `possession.csv` (sahip iz ID'si; A/B = `teams.csv`; kare sayısı `x…`), `players.csv` (hakem sınıfı), `homography.csv` (tüm hata anlarında %100 geçerli → homografi hiçbirinde neden değil).

**FN (kaçırılan gerçek olay)**

| Zaman | Tip | Kategori | O anda ne vardı |
|---|---|---|---|
| 1:07.00 | PAS | Zamanlama | top %88; 6A x12; sistem 1:08.04 PAS 6→8 üretmiş (+1.04) |
| 1:09.48 | PAS | Çok kısa sahiplik | top %100; 6A x2 > 8A x7 > 16B x2 > 21B x1 |
| 1:09.96 | PAS | Çok kısa sahiplik | top %87; 8A x7 > 16B x2 > 21B x1 |
| 1:11.64 | TOP KAYBI | Zamanlama | top %56; sistem 1:13.60 TOP KAYBI (+1.96) |
| 1:12.56 | PAS | Top kaybolmuş | top %55; 421B x1 > 392A x7 > 450B x16 |
| 1:18.76 | PAS | Hakem karışması | top %78; tüm pencere 476 "B" ama 476 hakem-sınıflı iz (x22) |
| 1:23.08 | PAS | Çok kısa sahiplik | top %100; 843B x7 > 822A x1 > 597A x1 |
| 1:23.44 | PAS | Çok kısa sahiplik | aynı dizi |
| 1:30.84 | PAS | Zamanlama | top %81; 6A x30; sistem 1:28.04 PAS (−2.80) |
| 1:39.56 | PAS | Zamanlama | top %87; sistem 1:38.00 (−1.56) |
| 1:45.16 | PAS | Zamanlama | top %80; sistem 1:46.40 (+1.24) |
| 1:48.00 | PAS | Zamanlama | top %82; sistem 1:49.04 (+1.04) |
| 1:52.44 | PAS | Top kaybolmuş | top %64; 6A x8 > 1047A x2 > 12A x22 |
| 1:56.48 | TOP KAYBI | Yanlış takım | top %100; 1304A x1 > 12A x5 (ikisi de A → TOP KAYBI üretilemez) |
| 1:57.12 | PAS | Zamanlama | top %100; sistem 1:58.52/1:59.08 PAS (+1.4/+1.96) |
| 1:58.76 | TOP KAYBI | Yanlış takım | top %100; 601A/12A karşılıklı, hepsi A; sistem 1:58.52 PAS |
| 2:00.32 | PAS | Zamanlama | top %69; sistem −1.24 |
| 2:05.84 | PAS | Top kaybolmuş | top %62; 1511A x19 tek sahip |
| 2:10.24 | PAS | Zamanlama | top %61; sistem 2:08.88 PAS (−1.36) |
| 2:17.76 | PAS | Atlanan pas | top %84; 7A x19 tek sahip, alıcıda sahiplik yok |
| 2:30.36 | PAS | Top kaybolmuş | top %67; possession'da hiç sahip yok |
| 2:34.72 | PAS | Çok kısa sahiplik | top %100; 1018A x21 > 1313A x1 > 3180B x2 > 1018A x5 |
| 2:37.08 | PAS | Atlanan pas | top %100; 1511A x19 tek sahip |
| 2:44.16 | PAS | Top kaybolmuş | top %48; 1511A x11 > 3325A x1 |
| 2:49.20 | PAS | Atlanan pas | top %86; 6A x29 tek sahip |
| 2:51.52 | PAS | Çok kısa sahiplik | top %84; 6A x9 > 2694B x3 > 12A x2 > 2798A x1 |
| 2:53.24 | PAS | Zamanlama | top %84; sistem 2:55.24 PAS (+2.0) |
| 2:55.40 | TOP KAYBI | Yanlış takım | top %100; 3839B x2 (3839→3894 ikisi B → PAS üretilmiş) |
| 2:57.20 | PAS | Zamanlama | top %81; sistem 2:58.64 PAS (+1.44) |

**FP (fazla tahmin)**

| Zaman | Tip | Kategori | Ayrıntı |
|---|---|---|---|
| 1:04.76 | PAS | Etiketsiz/karşılıksız | 1→6, 1.92 sn, 13.9 m; ±1 sn içinde etiket yok (top %58) |
| 1:08.04 | PAS | Zamanlama | 6→8; en yakın gerçek 1:07.00 (+1.04) |
| 1:13.60 | TOP KAYBI | Zamanlama | 392→505; gerçek 1:11.64 TOP KAYBI (+1.96) |
| 1:16.64 | PAS | Hakem karışması | 505→476 (476 hakem-sınıflı iz, B'ye çevrilmiş) |
| 1:19.60 | TOP KAYBI | Hakem karışması | 476→597, 36.9 m / 25 m/sn; gerçek 1:18.76 PAS (tip karışıklığı) |
| 1:28.04 | PAS | Zamanlama | 597→6; gerçek 1:30.84 (−2.80), top %51 |
| 1:38.00 | PAS | Zamanlama | 6→597; gerçek 1:39.56 (−1.56) |
| 1:41.24 | PAS | Etiketsiz/karşılıksız | 597→1047; en yakın PAS etiketi 1:42.28, 1.04 sn uzakta (eşik dışı, başka olayla eşleşmiş) |
| 1:46.40 | PAS | Zamanlama | 6→601; gerçek 1:45.16 (+1.24) |
| 1:49.04 | PAS | Zamanlama | 601→6; gerçek 1:48.00 (+1.04) |
| 1:58.52 | PAS | Yanlış takım | 12→601 (0.2 sn); gerçek 1:58.76 TOP KAYBI (tip karışıklığı) |
| 1:59.08 | PAS | Zamanlama | 601→12; 1:57.12 ile eşleşiyor (+1.96) |
| 2:08.88 | PAS | Zamanlama | 1511→1342; gerçek 2:10.24 (−1.36), top %44 |
| 2:55.24 | PAS | Yanlış takım | 3839→3894 (ikisi B); gerçek 2:55.40 TOP KAYBI (tip karışıklığı) |
| 2:58.64 | PAS | Zamanlama | 3894→2694; gerçek 2:57.20 (+1.44) |

## 4. Hata kategorileri
Kural-tabanlı atama (öncelik: hakem izi → tip karışıklığı/yanlış takım → aynı tipte 1–3 sn kayma → top bilinen <%70 → kısa sahiplik → diğer). Her hata tek kategoride. "Zamanlama" ve "yanlış takım" atamaları video izlenmeden yapıldı; etiketlerin doğru olduğu varsayıldı.

| Kategori | FN | FP | Toplam |
|---|---|---|---|
| **Zamanlama farkı** (aynı tip olay 1–3 sn kaymış; etiket anı ↔ sistem anı) | 11 | 9 | **20** |
| **Çok kısa sahiplik** (alıcı <4–5 kare tuttu, filtre atıyor) | 6 | 0 | **6** |
| Top kaybolmuş (olay çevresi top bilinen <%70) | 5 | 0 | 5 |
| Yanlış takım ataması (tip karışıklığı / aynı takım görünen rakip) | 3 | 2 | 5 |
| Hakem karışması (hakem-sınıflı iz oyuncuya çevrilmiş) | 1 | 2 | 3 |
| Atlanan pas (alıcıda sahiplik hiç kurulmadı, top görünüyor) | 3 | 0 | 3 |
| Etiketsiz/karşılıksız tespit | 0 | 2 | 2 |
| Çift sayım | 0 | 0 | 0 |
| Toplam | 29 | 15 | 44 |

Not: takım/hakem birlikte (yanlış takım + hakem) 8 hata → üçüncü sıra olarak birlikte ele alındı. Takım ayrımında dengesiz sonuç var: 510 iz A, 1992 iz B (log).

### En çok hata yaratan 3 kategori ve öneri (uygulanmadı)
1. **Zamanlama farkı (20 hata, 12 çift; kayma yönü karışık, 12 eşleşen çiftte işaretli ort. +0.09, medyan +1.04, mutlak ort. 1.60 sn)** — sistem olay zamanını `cur["end"]` (pasörün son sahiplik karesi, `DRIBBLE_GAP=12` ile 0.48 sn uzamış olabilir) alıyor; senin etiketin büyük ihtimalle vuruş/alım anı. Kayma tek yönlü olmadığı için sabit ofset çözmez. Önce: etiketlerin vuruş anı mı alım anı mı olduğunu netleştir; sonra olay zamanını `cur["end"]` yerine `(cur["end"] + nxt["start"]) / 2` veya `nxt["start"]` dene, `DRIBBLE_GAP` 12→6. Ayrıca `MATCH_TOL_SEC` 1.0→1.5 hem etiket gürültüsünü hem sistemi adil ölçer (F1 0.35→0.56).
2. **Çok kısa sahiplik (6 FN)** — `MIN_RECEIVE_FRAMES` 4→2–3, `MIN_RECEIVE_FRAMES_LOSS` 5→3. Risk: titreme FP'leri artar (log: 53 sahiplik değişimi filtrelendi); `POSS_DIST` 0.45→0.55 ile birlikte dene, F1'e bak.
3. **Takım/hakem (8 hata) + top kaybı (5)** — takım: 476 gibi hakem-sınıflı izleri B'ye çeviren kural (`REF_KEEP_RATIO`, `MAX_REF_CONCURRENT` 1.5; log: B renginde ort. 2.4 "hakem") fazla agresif; hakem düzeltmesini yalnızca `n` yüksek ve `ref_ratio` düşük izlere sınırlamak veya K-means'e 3. küme (hakem) eklemek. Top kaybı: `DOGRULAMA_KARE` 3→2, `MAX_INTERP_GAP` 10→15 (şu an top %70.2 bilinen, %53.1 tespit).
