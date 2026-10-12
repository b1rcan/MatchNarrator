# OLCUM_06 — TOP KAYBI kaçırmaları ve iki FP için teşhis

Tarih: 2026-10-12 · Kod/parametre değişmedi (yalnız yeni betik `teshis_top_kaybi.py`). Yalnız geliştirme seti (60–180 sn); varsayılan ayarlar (eski K-means takım, `tarama/baseline`). Not: SigLIP seçeneği kodda duruyor, varsayılan değil; OLCUM_05 sonucu "önerilmez".

Okuma notları: sınıf = `orijinal>düzeltilmiş` (örn. `ref>pla` = YOLO hakem dedi, hakem düzeltmesi oyuncuya çevirdi). Takım A = Barça (lacivert-bordo), B = sarı. Mesafe = homografiyle zemin düzleminde topa uzaklık (m). `nd` = `events_v2.py`'nin kullandığı ayak-top piksel mesafesi / oyuncu boyu (sahiplik için `< POSS_DIST = 0.45`). **Uyarı:** top havadayken zemin homografisi ve piksel mesafesi yanıltıcıdır (2:55.40 +0.5 sn'de top kafa hizasında).

## Görseller (hepsi `C:\Users\gorur\Desktop\futbol-ai-tez\` altında, 14 dosya)
İstenen "6 olay × 3 kare" = 18 dosya sınırı aştığı için 4 kaçırma için 3'er kare (12), iki FP için yalnız olay anı (2). Üst bant kare/zaman/top durumu/possession sahibi; kalın beyaz çerçeve = possession.csv sahibi.

| Olay | −0,5 sn | etiket anı | +0,5 sn |
|---|---|---|---|
| 1:11.64 FN | `teshis_1-11.16_m0.5.png` | `teshis_1-11.64_0.png` | `teshis_1-12.12_p0.5.png` |
| 1:56.48 FN | `teshis_1-56.00_m0.5.png` | `teshis_1-56.48_0.png` | `teshis_1-56.96_p0.5.png` |
| 1:58.76 FN | `teshis_1-58.28_m0.5.png` | `teshis_1-58.76_0.png` | `teshis_1-59.24_p0.5.png` |
| 2:55.40 FN | `teshis_2-54.92_m0.5.png` | `teshis_2-55.40_0.png` | `teshis_2-55.88_p0.5.png` |
| 1:21.00 FP | – | `teshis_1-21.00_0.png` | – |
| 1:16.28 FP | – | `teshis_1-16.28_0.png` | – |

## Kaçırılan TOP KAYBI'lar

### 1:11.64 (kare 1791)
- Top: ±0,5 sn içinde **0/25 karede bilinen** (en yakın bilinen 14 kare önce); possession yok; 3 m içinde tespit tablosu **boş** (top konumu yok).
- possession (±1,5 sn): 21B x1 > 421B x1 > 392A x7 > 450B x5.
- Aday logu (`events_adaylar.csv`): 72.48 `8→392` red `bosluk_buyuk` (3,08 sn > 3,0); **73.00 `392A→450B` red `ayni_kisi_id_degisimi`** (alıcı 16 kare, boşluk 0,28 sn); 75.00 `392→540` red `kisa_kayip` (4 kare); 75.80 `392→562` red `kisa_kayip` (3 kare); 76.28 `392→505` kabul.
- **Hipotez: (e) başka — top izi yok.** Etiket anında top hiç görünmediği için sahiplik kurulamıyor. Ek bulgu: 73.00'daki A→B geçişi (392A→450B) "aynı kişi, ID değişmiş" kuralıyla elenmiş; oysa takımları farklı. Etiket zamanına 1,36 sn uzak olduğu için tek başına ±1 sn eşleşme sağlamazdı.

### 1:56.48 (kare 2912)
Etiket anında topa ≤3 m:

| iz | sınıf | takım | mesafe (m) | nd | sahiplik adayı | hakem notu |
|---|---|---|---|---|---|---|
| 12 | player | A | 2,83 | 1,81 | hayır | – |

±0,5 sn penceresi (top 25/25 bilinen): 12A 13 kare (min 0,43 m, 5 kare aday); **2033B 4 kare (min 1,52 m, min nd 0,497)**; 1806 (ref>pla, B) 6 kare (min 1,87 m, nd 0,80); 977B 5 kare (2,11 m, nd 0,96). possession: 1304A x1 > 12A x5 (56.68–56.84).
Görsel: etiket anında top açık alanda, hiçbir oyuncuya yakın değil; +0,5 sn'de sarı 2033 (YOLO'da hakem sınıflı, düzeltmeyle oyuncu B) topa 1,6 m (top interpole).
- **Hipotez: (c) rakip tespit edilmiş ama topa uzaklık sahiplik eşiği dışında.** Rakip (2033B) pencerede topa en çok nd = 0,497 yaklaşıyor (eşik 0,45'in hemen dışında) ve yalnız 4/25 karede görülüyor; top interpole karelerde. (a)'ya yakın: etiket anında rakip tespiti yok. (b) elendi: 2033 hakem-sınıflıydı ama oyuncuya çevrilmiş, dışlanmamış.

### 1:58.76 (kare 2969)
| iz | sınıf | takım | mesafe (m) | nd | sahiplik adayı | hakem notu |
|---|---|---|---|---|---|---|
| 601 | player | A | 0,84 | 0,36 | EVET (possession sahibi) | – |
| 2123 | referee→player | B | 2,40 | 1,17 | hayır | hakem-sınıflı, oyuncuya ÇEVRİLDİ (ref_oranı 0,90, 10 kare) |

±0,5 sn: 12A (10 kare), 601A (17 kare), 2116 (ref>pla, A, 2 kare, 1,70 m), 2123 (ref>pla, B, 10 kare, min 2,38 m, nd 1,17), 2137 (B, 3 kare, 2,47 m), 1342A. possession: 601A > 12A > 601A > 12A > 1342A (hepsi A, alternan).
Görsel: etiket anında top 601'in ayağında; sarı rakip (2123) hemen yanında ama topla temas yok; +0,5 sn'de top 601'den ayrılmış, sarı 2137 3,5 m uzakta.
- **Hipotez: (c) rakip tespit edilmiş (YOLO'da hakem sınıflı, düzeltmeyle oyuncu B), ama topa uzaklık sahiplik eşiği dışında** (nd 1,17–1,3). Pencerede hiçbir B oyuncusu topa nd < 0,45 yaklaşmıyor; sahiplik kurulamıyor. (b) kısmen: iz `ref_oranı = 0,90`, `REF_KEEP_RATIO` sınırında ama çevrilmiş, dışlanmamış.

### 2:55.40 (kare 4385)
Etiket anında topa ≤3 m: **tespit yok**. ±0,5 sn: 3839B 10 kare (min 1,17 m, nd 0,39; **2 karede aday**), 3911 (ref>pla, B) 1 kare (1,36 m, nd 0,72). possession: 3839B[55.20..55.24] x2 kare.
Görsel: top bir oyuncu kümesinin üstünde, +0,5 sn'de kafa hizasında (havada); 3839'un kutusu iki oyuncuyu (sarı + önündeki Barça oyuncusu) birlikte kapsıyor.
- Aday logu: **175.20 `6A→3839B` red `bosluk_buyuk`** (boşluk 4,88 sn) ve alıcı yalnız 2 kare (`kisa_kayip` eşiği 5 de elerdi); 177.12–177.76 `3839→3894` red `kisa_alim`; 178.00 `3839→3894` kabul (PAS).
- **Hipotez: (d) rakip (3839B) tespit edilmiş ve topa yakın, ama sahiplik süresi çok kısa** (2 kare < `MIN_RECEIVE_FRAMES_LOSS = 5`). Ek: öncesindeki sahiplikle boşluk 4,88 sn (`MAX_PASS_GAP_SEC = 3,0`'ı aşıyor; uzun/yüksek top), birleşik kutu ve havadaki top.

## FP'ler
### 1:21.00 (kare 2025) — TOP KAYBI 476B→597A, 36,9 m / 25,3 m/sn
Topa ≤3 m: 597 (ref>pla, **A**, 1,58 m, nd 0,30, possession sahibi; ref_oranı 0,11, 620 kare). Top **interpole** (pencerede 14/25 bilinen). possession: 476B x4 > 597A x7 > 768A x4.
Görsel: top ve zeminde yatan **sarı formalı** oyuncu 597'nin kutusunda, ama iz A (Barça) olarak etiketli. 597'nin SigLIP `oy_orani` değeri 0,58 (OLCUM_05, 12 kırpımın ~7'si bir takım, ~5'i diğeri) → iz içinde iki takım karışıyor olabilir.
- **FP nedeni: iz içi takım karışması** (597 hem Barça hem sarı oyuncu) + interpole top; 36,9 m geçiş 35 m/sn hız sınırına çok yakın (25,3).

### 1:16.28 (kare 1907) — TOP KAYBI 392A→505B
Topa ≤3 m: 505B (0,70 m, nd 0,12, possession sahibi). Pencerede 476B, 591B(ref>pla), 562B, 507A (1,13 m, nd 0,26), 492A.
Aday zinciri: 392A'dan sonra B oyuncuları 450B (73.00, `ayni_kisi_id_degisimi`), 540B (75.00, 4 kare, `kisa_kayip`), 562B (75.80, 3 kare, `kisa_kayip`) sırayla **reddedilmiş**; cur 392A'da kalmış ve 76.28'deki 505B (10 kare) ile "TOP KAYBI" oluşmuş.
- **FP nedeni: etiketli 1:11.64 TOP KAYBI'sının (5 sn önce) gecikmeli tespiti olabilir** (B sahipliğinin ilk kabul edilen karesi 505B). Bu bir hipotez; 1:16.28 çevresinde başka etiket yok (en yakın etiket 1:18.76 PAS). 505B gerçekten topu alıyor (görselde ayak teması).

## Özet (4 kaçırma)
| Kategori | Sayı | Olaylar |
|---|---|---|
| (a) rakip hiç tespit edilmemiş | 0 | – |
| (b) hakem sınıfıyla tespit edilmiş ve dışlanmış | 0 | (2033, 2123, 2137 YOLO'da hakemdi ama oyuncuya çevrildi; dışlanmadı) |
| (c) tespit edilmiş, topa uzaklık POSS_DIST dışında | 2 | 1:56.48, 1:58.76 |
| (d) tespit edilmiş ve yakın, sahiplik çok kısa | 1 | 2:55.40 |
| (e) başka | 1 | 1:11.64 (top izi yok) |

## Bulgular
- TOP KAYBI kaçırmalarının nedeni **takım etiketi değil**, topa temasın sahiplik kuralıyla yakalanamaması: 2 olayda rakip var ama eşik dışında (nd 0,50–1,2), biri çok kısa, biri top izi boşluğu. OLCUM_05'teki "yanlış takım" ön yorumu bu dört olay için **doğrulanmadı**.
- Eşik dışı iki olayda rakip oyuncular **YOLO'da hakem sınıflıydı** (2033, 2123, 2137); çevirme sayesinde dışlanmamışlar. Hakem düzeltmesi bu olaylarda zarar vermiyor.
- Aday logundan çıkan ek hata modları (düzeltme önerisi değil, gözlem): `ayni_kisi_id_degisimi` kuralı takımı farklı iki oyuncuyu (392A→450B) birleştirebiliyor; `bosluk_buyuk` (>3 sn) uzun/yüksek toplarda TOP KAYBI adayını eliyor (2:55.40, 4,88 sn); iz içi takım karışması (597) FP üretiyor.
- Sınırlar: gözle yorumlanan görseller (kutular 25–40 px, top küçük), top havadayken mesafe ölçüleri güvenilmez; etiketlere güveniliyor.
