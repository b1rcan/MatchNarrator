# OLCUM_08 — POSS_DIST genişletme ve eşleştirilmiş bootstrap

Tarih: 2026-10-12 · Yalnız geliştirme seti (60–180 sn, ±1 sn, `receiver_start`, eski K-means takım, diğer tüm parametreler mevcut). Test seti kullanılmadı. **Hiçbir şey kalıcı uygulanmadı** (`events_v2.py` varsayılanı `POSS_DIST = 0.45`). Kabul kuralı değişmedi: düzelen − bozulan ≥ 2.

Araçlar: `tarama_08.py` (tarama + tablolar), `degerlendir.py` (yeni: `paired_bootstrap`, CLI `--compare`; yedek `degerlendir.py.bak_20261012`).
Eşleştirilmiş bootstrap yöntemi: birim = gerçek etiket (41); her etiketin taban ve ayar sistemindeki sonucu (TP/FN) ve o etikete zamanca en yakın FP'ler birlikte yerine koyarak 1000 kez örneklenir; F1 = 2TP/(2TP+FP+FN); fark = ayar − taban; %95 yüzdelik aralığı ve P(fark > 0) raporlanır. İki sistem her tekrarda aynı örneklemi kullanır. Sınırlar: FP'ler "en yakın etikete" atanıyor (yaklaşık), 41 etiketle aralıklar geniş.

## A1. POSS_DIST taraması (taban 0,45)
| POSS_DIST | TP/FP/FN | F1 genel (%95) | PAS TP/FP/FN, F1 (%95) | TOP KAYBI TP/FP/FN, F1 (%95) |
|---|---|---|---|---|
| 0,40 | 20/6/21 | 0,597 (0,46–0,73) | 19/4/17 · 0,644 (0,49–0,79) | 1/2/4 · 0,250 (0,00–0,60) |
| **0,45** | 21/5/20 | 0,627 (0,49–0,76) | 20/3/16 · 0,678 (0,53–0,80) | 1/2/4 · 0,250 (0,00–0,60) |
| 0,50 | 22/5/19 | 0,647 (0,52–0,77) | 21/3/15 · 0,700 (0,56–0,82) | 1/2/4 · 0,250 (0,00–0,60) |
| 0,55 | 25/7/16 | 0,685 (0,55–0,80) | 23/4/13 · 0,730 (0,60–0,84) | 2/3/3 · 0,400 (0,00–0,67) |
| 0,60 | 28/7/13 | 0,737 (0,61–0,83) | 24/4/12 · 0,750 (0,62–0,86) | 4/3/1 · 0,667 (0,22–0,93) |
| 0,65 | 28/8/13 | 0,727 (0,60–0,83) | 24/5/12 · 0,738 (0,61–0,86) | 4/3/1 · 0,667 (0,22–0,93) |
| 0,70 | 30/10/11 | **0,741** (0,62–0,84) | 26/6/10 · 0,765 (0,65–0,86) | 4/4/1 · 0,615 (0,20–0,88) |
| 0,80 | 31/13/10 | 0,729 (0,61–0,84) | 27/8/9 · 0,761 (0,65–0,87) | 4/5/1 · 0,571 (0,18–0,82) |
| 1,00 | 26/19/15 | 0,605 (0,48–0,72) | 23/7/13 · 0,697 (0,57–0,82) | 3/12/2 · 0,300 (0,11–0,52) |

F1 0,60–0,80 arasında yaklaşık bir plato (0,727–0,741) oluşturuyor; 1,00'da FP patlıyor (özellikle TOP KAYBI: 12 FP). Tüm aralıklar birbiriyle geniş örtüşüyor.

### Belirsiz sahiplik ve sahiplik süresi (60–180 sn, top bilinen 4 500 karelik pencerenin kareleri)
"Aday" = çevresinde nd < POSS_DIST olan oyuncu/kaleci (düzeltilmiş sınıf). "Belirsiz" = aynı karede ≥ 2 aday.

| POSS_DIST | Sahiplik kurulan kare % | Belirsiz kare % (tüm kareler) | Belirsiz % (sahipli kareler içinde) | Ort. / medyan sahiplik süresi (sn) | Sahiplik serisi | Olay |
|---|---|---|---|---|---|---|
| 0,40 | 32,7 | 0,4 | 1,3 | 0,44 / 0,28 | 74 | 26 |
| 0,45 | 37,8 | 0,8 | 2,0 | 0,50 / 0,28 | 77 | 26 |
| 0,50 | 43,3 | 1,3 | 3,0 | 0,53 / 0,28 | 81 | 27 |
| 0,55 | 48,5 | 1,9 | 4,0 | 0,52 / 0,24 | 93 | 32 |
| 0,60 | 54,8 | 2,3 | 4,2 | 0,57 / 0,28 | 95 | 35 |
| 0,65 | 58,7 | 2,7 | 4,7 | 0,58 / 0,28 | 99 | 36 |
| 0,70 | 62,5 | 3,2 | 5,1 | 0,56 / 0,28 | 107 | 40 |
| 0,80 | 68,0 | 4,0 | 5,8 | 0,57 / 0,28 | 114 | 44 |
| 1,00 | 75,1 | 8,6 | 11,4 | 0,57 / 0,24 | 124 | 45 |

Yarıçap büyüdükçe belirsizlik **artıyor ama yavaş**: 0,45→0,70 arasında sahipli karelerde %2→%5; 0,80'de %5,8; 1,00'da %11,4'e sıçrıyor (FP patlamasıyla aynı yerde). Ortalama sahiplik süresi 0,44→0,57 sn'de düz kalıyor (medyan ~0,28); yani artan yarıçap sahipliği uzatmıyor, **yeni kısa seriler ekliyor** (77→124 seri) ve olay sayısı (26→45) buna paralel artıyor.

## A2–A3. Taban 0,45'e karşı eşleştirilmiş fark
`fark_sıkı` = düzelen − (TP→FN + yeni FP) (resmî kural). `kaymasız` = aynı FP'nin ≤1 sn kaymasını (aynı tip) yeni FP saymayan, **sonradan tanımlanmış** bilgi amaçlı sayım.

| POSS_DIST | F1 farkı genel (%95) · P(>0) | PAS farkı (%95) · P(>0) | TOP KAYBI farkı (%95) · P(>0) | Düzelen | TP→FN | Yeni FP (kayma) | **Fark (sıkı)** | Kaymasız | Karar |
|---|---|---|---|---|---|---|---|---|---|
| 0,50 | +0,020 (−0,021…+0,088) · 0,64 | +0,022 (−0,027…+0,100) · 0,63 | 0,000 (0…0) · 0,00 | 1 | 0 | 3 (2) | −2 | 0 | önerilmez |
| 0,55 | +0,058 (−0,043…+0,183) · 0,85 | +0,052 (−0,048…+0,178) · 0,81 | +0,150 (−0,107…+0,545) · 0,63 | 5 | 1 | 6 (2) | −2 | 0 | önerilmez |
| 0,60 | +0,110 (−0,007…+0,240) · 0,96 | +0,072 (−0,036…+0,206) · 0,87 | +0,417 (0,000…+0,857) · 0,96 | 8 | 1 | 6 (2) | **+1** | +3 | **önerilmez** |
| 0,65 | +0,100 (−0,017…+0,231) · 0,95 | +0,060 (−0,047…+0,192) · 0,83 | +0,417 (0,000…+0,857) · 0,96 | 8 | 1 | 7 (2) | 0 | +2 | önerilmez |
| 0,70 | +0,114 (−0,007…+0,258) · 0,97 | +0,087 (−0,033…+0,240) · 0,91 | +0,365 (−0,056…+0,800) · 0,95 | 10 | 1 | 9 (2) | 0 | +2 | önerilmez |
| 0,80 | +0,103 (−0,029…+0,255) · 0,93 | +0,083 (−0,044…+0,230) · 0,87 | +0,321 (−0,095…+0,783) · 0,92 | 12 | 2 | 12 (1) | −2 | −1 | önerilmez |
| 1,00 | −0,022 (−0,173…+0,144) · 0,40 | +0,019 (−0,121…+0,180) · 0,58 | +0,050 (−0,307…+0,455) · 0,66 | 9 | 4 | 18 (1) | −13 | −12 | önerilmez |

Düzelen / bozulan zamanlar (0,50–0,60 için OLCUM_07'de; 0,65 ve üstü):
| Ayar | Düzelen (FN→TP) | TP→FN | Yeni FP | Giden FP |
|---|---|---|---|---|
| 0,65 | 1:03.60, 2:23.64, 2:30.36, 2:35.48, 2:53.24 (PAS); 1:56.48, 1:58.76, 2:55.40 (TOP) | 1:18.76 PAS | 1:14.52, 1:58.64, 2:13.40, 2:15.48, 2:26.68 (PAS); 1:18.72, 1:25.72 (TOP) | 1:04.64, 1:58.72, 2:26.92 (PAS); 1:16.28 (TOP) |
| 0,70 | 0,65'tekilere ek: 1:57.12, 2:00.32, 2:51.52 (PAS) | 1:18.76 PAS | 1:14.52, 1:54.40, 1:58.64, 2:12.68, 2:15.48, 2:26.68 (PAS); 1:18.64, 1:25.68, 2:35.32 (TOP) | aynı 4 |
| 0,80 | 0,70'e ek: 1:09.96, 1:12.56 (PAS) | 1:18.76, 1:59.60 PAS | 12 yeni FP (2:51.12, 2:52.32 TOP dahil) | aynı 4 |
| 1,00 | 9 olay (1:03.60 … 2:30.36) | 1:18.76, 1:59.60, 2:49.20, 2:57.20 PAS | 18 yeni FP (çoğu TOP KAYBI, 2:34–2:59 arası yığılma) | aynı 4 |

## Yorum
- **Resmî karar: hiçbir ayar önerilmez** (en iyi sıkı fark +1, 0,60'ta).
- Eşleştirilmiş bootstrap yönü tutarlı biçimde pozitif gösteriyor (0,60–0,80 için P(fark>0) 0,93–0,97), ama **hiçbir genel F1 farkının %95 aralığı sıfırı dışlamıyor** (0,60: −0,007…+0,240; 0,70: −0,007…+0,258). TOP KAYBI farkı 0,60'ta (0,000…+0,857) sınırda, çünkü yalnız 5 etiket var.
- Kazanç ile maliyet birlikte büyüyor: 0,60'tan 0,70'e düzelen 8→10, ama yeni FP 6→9; 0,80'de FP daha hızlı artıyor; 1,00 çöküyor. **0,60 en dengeli noktadır** (sıkı +1, kaymasız +3, belirsiz sahiplik %4,2); 0,65–0,70 aynı seviyede ama daha fazla FP ve belirsizlik getiriyor. Bu, 10 farklı değer aynı 41 etiket üzerinde denendiği için seçim yanlılığı taşır (çoklu karşılaştırma).
- 1:18.76 PAS tüm ≥0,55 ayarlarda TP→FN oluyor; yeni FP'lerin ortak grubu 1:14.5, 1:18.7 (TOP), 1:25.7 (TOP), 2:13, 2:15, 2:26.7; bu FP'lerin nedeni (ikili mücadele, takım karışması vb.) bu ölçümde incelenmedi.
- Bu nedenle 0,60'ı önermiyorum; olası bir sonraki adım, yön kontrolü (A→B beklenen TOP KAYBI) veya test setinde tek seferlik doğrulama için karar vermek (senin onayınla).
