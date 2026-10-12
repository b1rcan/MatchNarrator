# OLCUM_10 — TOP KAYBI FP'leri ve MIN_RECEIVE_FRAMES_LOSS yukarı yön taraması

Tarih: 2026-10-12 · Geliştirme (60–180) + doğrulama (360–540) birlikte = geliştirme havuzu (82 etiket). **Test seti (180–300) kullanılmadı.** POSS_DIST 0,45 ve diğer tüm parametreler değişmedi; hiçbir şey kalıcı uygulanmadı. Yeni/değişen araçlar: `tk_fp_analiz.py`, `teshis_tk_fp.py`, `tarama_10.py`, `takim_siglip.py` (yeni `--in-dir/--out-dir`, varsayılan aynı; yedek `.bak_20261012`). Doğrulama seti için SigLIP takımı da üretildi (`veri_360_540/siglip/teams_siglip.csv`; 1 578 ortak izde 79 fark) — yalnız (b) kategorisi kanıtı için.

## 1. TOP KAYBI FP'leri (13: geliştirme 2, doğrulama 11)
Ölçüler: `ball_track.csv`, `possession.csv`, `events.csv`, `events_adaylar.csv`. "Yeni sahip serisi" = adayın alıcı kare sayısı (≥5, filtre eşiği); "eski sahip serisi" = eski sahibin olay öncesi kesintisiz sahiplik kare sayısı; "sonraki sahip" = olaydan sonraki ilk farklı sahip ve gecikmesi; top hızı olay öncesi (−6…−1 kare) / sonrası (0…+5 kare), m/sn, saha koordinatında; boşluk = eski sahibin son karesi ile olay arası (sn); mesafe = o iki nokta arası (m).

| Set | Zaman | Kimden → kime (iz, takım) | Top (olay karesi) | Yeni seri (kare) | Eski seri (kare) | Sonraki sahip (gecikme) | Boşluk (sn) | Mesafe (m) | Top hızı önce/sonra | SigLIP oy (kimden / kime) | Yakın etiket (±2 sn) | **Kategori** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gel | 1:16.28 | 392A → 505B | tespit | 10 | 7 | 507A (0,52 s) | 2,68 | 12,6 | 36,9 / 2,6 | 0,75 / 0,75 | – | **a** |
| gel | 1:21.00 | 476B → 597A | interpole | 7 | 22 | 768A (1,40 s) | 1,40 | 36,9 | – / 15,4 | 1,00 / **0,58** | 1:22.20 PAS, 1:22.40 TOP | **b** ✓ |
| dog | 6:16.16 | 522B → 670A | tespit | 5 | 2 | 86B (0,88 s) | 2,64 | 6,1 | 2,2 / 5,6 | 1,00 / 1,00 | 6:14.68 PAS, 6:17.08 PAS | **a** ✓ |
| dog | 6:17.04 | 670A → 86B | interpole | 16 | 5 | 5A (0,72 s) | 0,68 | 10,9 | 12,1 / 6,2 | 1,00 / 0,83 | 6:17.08 PAS, 6:18.52 PAS | **a** |
| dog | 6:22.28 | 971B → 3A | tespit | 9 | 32 | 9A (0,76 s) | 1,20 | 11,9 | 35,9 / 4,2 | 1,00 / 1,00 | – | **d** ✓ |
| dog | 7:20.32 | 3210A → 2108B | tespit | 5 | 6 | 3A (2,08 s) | 0,04 | 1,9 | 10,6 / 9,2 | 0,92 / 0,75 | 7:18.88 TOP, 7:20.36 PAS | **a** |
| dog | 7:22.40 | 2108B → 3A | tespit | 7 | 5 | 2A (0,84 s) | 1,92 | 11,0 | 2,1 / 5,6 | 0,75 / 1,00 | 7:23.56 PAS | **a** |
| dog | 7:57.56 | 4091B → 4684A | interpole | 12 | 11 | 2284A (0,48 s) | 2,48 | 0,6 | 1,2 / 1,2 | 0,75 / 0,92 | 7:59.12 TOP | **c** ✓ |
| dog | 8:01.32 | 4721B → 4684A | tespit | 10 | 2 | 4721B (0,40 s) | 0,04 | 1,3 | 4,2 / 1,8 | 0,67 / 0,92 | 8:00.40 PAS | **a** |
| dog | 8:10.04 | 5181B → 4684A | tespit | 21 | 22 | 3A (1,32 s) | 2,12 | 36,5 | – / 1,7 | 1,00* / 0,92 | 8:09.60 PAS | **b** |
| dog | 8:47.44 | 6229A → 6895B | tespit | 10 | 9 | 6733B (0,40 s) | 1,72 | 33,9 | 40,4 / 1,4 | 1,00 / 1,00 | – | **d** ✓ |
| dog | 8:50.12 | 6895B → 6506A | tespit | 5 | 10 | 6880B (0,20 s) | 2,16 | 4,5 | – / 4,1 | 1,00 / 1,00 | – | **a** |
| dog | 8:52.84 | 6506A → 6733B | tespit | 7 | 47 | 7005A (0,28 s) | 0,28 | 6,6 | 0,7 / 0,5 | 1,00 / 0,67 | – | **a** |

`*` = SigLIP bu izin takımını eski K-means'ten farklı veriyor. ✓ = annotasyonlu görselde gözle doğrulandı (diğerleri yalnız kural tabanlı).

Kategori kuralları (öncelik sırasıyla): **(c)** iz kimliği: iki izin ortak kare sayısı ≤20 ve mesafe ≤3 m; **(b)** takım etiketi: SigLIP takımı eski K-means'ten farklı veya oy oranı <0,6; **(a)** kısa/seken: yeni sahip serisinden sonra ≤1 sn içinde top eski takıma dönüyor, ya da eski sahip serisi ≤8 kare; **(d)** gerçek değişim, etiket yok: yeni sahip ≥1,2 sn tutuyor ve ±2 sn içinde etiket yok; **(e)** diğer. Görselde gördüklerim kuralı geçersiz kıldığında görsel esas alındı (6:22.28 ve 8:47.44: kural "e" dedi, görsel "d").

| Kategori | Sayı | Olaylar |
|---|---|---|
| (a) top yakından geçti / seken (kısa sahiplik) | **8** | 1:16.28; 6:16.16, 6:17.04, 7:20.32, 7:22.40, 8:01.32, 8:50.12, 8:52.84 |
| (b) takım etiketi hatası | 2 | 1:21.00, 8:10.04 |
| (c) iz kimliği / kutu birleşmesi | 1 | 7:57.56 |
| (d) gerçek değişim, etiket yok (olası) | 2 | 6:22.28, 8:47.44 |
| (e) diğer | 0 | – |
| Toplam | 13 | |

Görsel bulgular: **6:16.16** — sarı 522'de ("sahip") top ayağında değil, yanından geçiyor; sonra Barça 670 topu alıyor: sahte eski sahiplik (a). Ayrıca sarı bir oyuncunun kutusu A etiketli (iz 13). **6:22.28** — sarı 971 gerçekten topla, 1 sn sonra Barça 3 topu sürüyor (gerçek değişim, etiket görünmüyor). **7:57.56** — iki oyuncunun kutusu birleşmiş, iz 4684 hem sarı hem Barça oyuncusunu kapsıyor; top interpole (c). **8:47.44** — Barça 6229 topu (interpole) bırakıyor, kamera kayıyor, sarı 6895 topla ayakta; uzun top (33,9 m, ~19 m/sn) sonrası rakip alıyor gibi görünüyor (d). **1:21.00** — sarı oyuncu A etiketli kutuda, iz 597 iki takımı karıştırıyor (b).

Yorum: 13 FP'nin 8'i (%62) kısa/seken top; kural tabanlı çoğunluğu görselle doğrulanmadı (yalnız 6:16.16 doğrulandı). İki FP (%15) gerçek değişim gibi görünüyor — etiketleme boşluğu olabilir; bunlar "gerçek FP" olmayabilir.

### Görseller (her biri iki panel: sol = eski sahibin son karesi, sağ = olay karesi; `C:\Users\gorur\Desktop\futbol-ai-tez\` altında)
- `teshis_tk_fp_6-16.16.png` (a)
- `teshis_tk_fp_6-22.28.png` (d)
- `teshis_tk_fp_7-57.56.png` (c)
- `teshis_tk_fp_8-47.44.png` (d)
- `teshis_tk_fp_1-21.00.png` (b, geliştirme)

## 2. MIN_RECEIVE_FRAMES_LOSS taraması {5, 6, 8, 10, 12}
Mevcut = 5. Eşleştirilmiş bootstrap farkı (%95; P(>0)) genel F1 için tabana göre.

**Geliştirme (60–180)**
| MRFL | TK TP/FP/FN · TK F1 | Genel TP/FP/FN · F1 (%95) | PAS F1 | Genel fark (bootstrap) | PAS F1 farkı | Düzelen / TP→FN / yeni FP |
|---|---|---|---|---|---|---|
| **5** | 1/2/4 · 0,250 | 21/5/20 · 0,627 (0,49–0,76) | 0,678 | – | – | – |
| 6 | 1/2/4 · 0,250 | 21/5/20 · 0,627 | 0,678 | 0,000 (0…0) | 0,000 | 0/0/0 |
| 8 | 0/1/5 · 0,000 | 19/4/22 · 0,594 (0,45–0,73) | 0,655 | −0,033 (−0,093…0) P=0,00 | −0,023 | 0/2/0 |
| 10 | 0/1/5 · 0,000 | 19/4/22 · 0,594 | 0,655 | −0,033 | −0,023 | 0/2/0 |
| 12 | 0/0/5 · 0,000 | 18/3/23 · 0,581 (0,43–0,71) | 0,632 | −0,046 (−0,109…0) P=0,00 | −0,046 | 0/3/0 |

**Doğrulama (360–540)**
| MRFL | TK TP/FP/FN · TK F1 | Genel TP/FP/FN · F1 (%95) | PAS F1 | Genel fark (bootstrap) | PAS F1 farkı | Düzelen / TP→FN / yeni FP |
|---|---|---|---|---|---|---|
| **5** | 1/11/5 · 0,111 | 19/20/22 · 0,475 (0,33–0,60) | 0,581 | – | – | – |
| 6 | 1/5/5 · 0,167 | 19/17/22 · 0,494 (0,34–0,62) | 0,554 | +0,019 (0,000…+0,049) P=0,87 | −0,027 | 0/0/3 |
| 8 | 1/5/5 · 0,167 | 19/17/22 · 0,494 | 0,554 | +0,019 | −0,027 | 0/0/3 |
| 10 | 1/4/5 · 0,182 | 19/16/22 · 0,500 (0,35–0,63) | 0,554 | +0,025 (0,000…+0,057) P=0,95 | −0,027 | 0/0/3 |
| 12 | 1/3/5 · 0,200 | 19/15/22 · 0,507 (0,35–0,63) | 0,562 | +0,032 (+0,007…+0,061) P=0,99 | −0,019 | 0/0/4 |

Kabul kuralı: genel F1 farkı **> 0 her iki sette** VE **PAS F1 hiçbir sette 0,02'den fazla düşmemeli**.
| MRFL | Geliştirme genel fark | Doğrulama genel fark | PAS: geliştirme / doğrulama | Karar |
|---|---|---|---|---|
| 6 | 0,000 (> 0 değil) | +0,019 | 0,000 / **−0,027** | **önerilmez** |
| 8 | **−0,033** | +0,019 | **−0,023** / **−0,027** | **önerilmez** |
| 10 | **−0,033** | +0,025 | **−0,023** / **−0,027** | **önerilmez** |
| 12 | **−0,046** | +0,032 | **−0,046** / −0,019 | **önerilmez** |

**Hiçbir değer kuralı geçmiyor; "önerilir" işaretli ayar yok.**

Yorum:
- Doğrulamada filtreyi yükseltmek TK FP'lerini gerçekten azaltıyor (11 → 5 → 3), giden FP'ler tam olarak (a) kategorisindekiler: 6:16.16, 6:17.04, 7:20.32, 7:22.40, 8:50.12, 8:52.84 (ve MRFL=10'da 6:22.28, 12'de 8:01.32, 8:47.44 da). Yani (a) teşhisi tarama sonucuyla tutarlı.
- Ama reddedilen TOP KAYBI adayı topu eski sahipte bırakıyor; bir sonraki aday PAS olarak çıkıyor ve **3 yeni PAS FP** doğuyor (7:22.40, 8:50.32, 8:52.84) → PAS F1 −0,027. FP kısmen TK'dan PAS'a taşınıyor; net kazanç küçük (genel FP 20 → 17…15).
- Geliştirmede 8 ve üstü gerçek bir TK'yı (1:22.40, 7 kare) ve ona bağlı PAS TP'sini (1:22.20) öldürüyor; 12'de 1:18.76 PAS TP'si de gidiyor. Gerçek TK'ların alıcı serisi bazen 5–7 kare; filtre bunları ayırt edemiyor.
- Doğrulamada tutarlı küçük kazanç (+0,02…+0,03; MRFL=12 için aralık sıfırı dışlıyor: +0,007…+0,061) var, ama geliştirmede aynı yönde değil ve PAS düşüşü kuralı bozuyor. TK etiket sayısı çok az (geliştirme 5, doğrulama 6); TK F1 farkları anlamlı değil.
