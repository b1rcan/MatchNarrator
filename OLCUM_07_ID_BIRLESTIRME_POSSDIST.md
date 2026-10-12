# OLCUM_07 — ID birleştirme kuralı, POSS_DIST ve MIN_POSS_FRAMES taramaları

Tarih: 2026-10-12 · Yalnız geliştirme seti (60–180 sn, ±1 sn, `receiver_start`, eski K-means takım). Test seti kullanılmadı. Hiçbir değişiklik kalıcı uygulanmadı (`events_v2.py` varsayılanları aynı; yeni parametre varsayılanı 0).
Kabul kuralı (değişmedi): **düzelen (FN→TP) − bozulan (TP→FN + yeni FP) ≥ 2** → "ÖNERİLİR". Karşılaştırma tabanı: F1 0,627 (21/5/20; %95 aralık 0,49–0,76).

## 1. `ID_MERGE_REQUIRE_SAME_TEAM`
- `events_v2.py`: yeni sabit `ID_MERGE_REQUIRE_SAME_TEAM = 0`. `=1` iken "aynı kişi, ID değişmiş" birleştirmesi, iki izin takımı da biliniyor ve farklıysa yapılmaz. Yedek `events_v2.py.bak4_20261012`.
- Doğrulama: varsayılan (0) çıktı `tarama/baseline` ile **bayt bayt aynı** (events, teams, possession, ball_track, events_adaylar, players_fixed).

| Ayar | TP/FP/FN | F1 (%95) | F1 PAS | Düzelen | Bozulan | Fark | Karar |
|---|---|---|---|---|---|---|---|
| 0 (mevcut) | 21/5/20 | 0,627 (0,49–0,76) | 0,678 | – | – | – | mevcut |
| **1** | 21/7/20 | 0,609 (0,45–0,74) | 0,656 | 0 | 3 yeni FP | **−3** | onerilmez |

- Bozulanlar: 1:13.00 TOP KAYBI, 1:15.00 PAS, 1:16.28 PAS (yeni FP); giden FP: 1:16.28 TOP KAYBI.
- Yorum: 392A→450B geçişi artık aday oluyor (1:13.00 TOP KAYBI), ama etiketli 1:11.64'ten 1,36 sn uzakta olduğu için TP olmuyor; yalnız FP ekliyor. OLCUM_06'daki hipotez (kural A→B geçişini yutuyor) doğru bir mekanizma, ama etiketle zaman uyuşmadığı için ölçümde kazanç yok. 1:11.64'ün asıl nedeni top izinin yokluğuydu.

## 2. POSS_DIST taraması (mevcut 0,45)
| POSS_DIST | TP/FP/FN | F1 (%95) | F1 PAS | F1 TOP KAYBI (TP) | Düzelen | Bozulan | Fark | Karar |
|---|---|---|---|---|---|---|---|---|
| 0,40 | 20/6/21 | 0,597 (0,46–0,73) | 0,644 | 0,250 (1) | 0 | 4 | −4 | onerilmez |
| **0,45** | 21/5/20 | 0,627 (0,49–0,76) | 0,678 | 0,250 (1) | – | – | – | mevcut |
| 0,50 | 22/5/19 | 0,647 (0,52–0,77) | 0,700 | 0,250 (1) | 1 | 3 | −2 | onerilmez |
| 0,55 | 25/7/16 | 0,685 (0,55–0,80) | 0,730 | 0,400 (2) | 5 | 7 | −2 | onerilmez |
| **0,60** | 28/7/13 | **0,737** (0,61–0,83) | 0,750 | **0,667 (4)** | 8 | 7 | **+1** | **onerilmez** (kural: ≥ +2) |

Düzelen / bozulan zamanlar:
| Ayar | Düzelen (FN→TP) | Bozulan |
|---|---|---|
| 0,40 | – | 2:10.24 PAS (TP→FN); yeni FP: 1:58.76 PAS, 2:11.32 PAS, 2:26.96 PAS |
| 0,50 | 1:03.60 PAS | yeni FP: 1:58.64 PAS, 2:13.60 PAS, 2:26.84 PAS |
| 0,55 | 1:03.60, 2:23.64, 2:35.48, 2:53.24 (PAS), 2:55.40 TOP | 1:18.76 PAS (TP→FN); yeni FP: 1:14.76 PAS, 1:18.72 TOP, 1:25.88 TOP, 1:58.64 PAS, 2:13.56 PAS, 2:26.72 PAS |
| 0,60 | 1:03.60, 2:23.64, 2:30.36, 2:35.48, 2:53.24 (PAS), **1:56.48, 1:58.76, 2:55.40 (TOP KAYBI)** | 1:18.76 PAS (TP→FN); yeni FP: 1:14.72 PAS, 1:18.72 TOP, 1:25.88 TOP, 1:58.64 PAS, 2:13.44 PAS, 2:26.68 PAS |
| (giden FP, 0,55/0,60) | 1:04.64 PAS, 1:16.28 TOP, 1:58.72 PAS, 2:26.92 PAS | |

**Kuralın sıkı okunuşu: 0,60 bile eşiği geçmiyor (+1).** Dikkat edilmesi gereken: "yeni FP" sayımı, aynı FP'nin birkaç kare kaymasını (örn. 1:58.72 → 1:58.64, 2:26.92 → 2:26.68) hem "giden" hem "yeni" yazıyor. Bu kaymaları (≤1 sn, aynı tip) yeni FP saymayınca fark şöyle:

| Ayar | Düzelen | TP→FN | Yeni FP | bunlardan kayma | Gerçek yeni FP | Kaymasız fark |
|---|---|---|---|---|---|---|
| 0,50 | 1 | 0 | 3 | 2 | 1 | 0 |
| 0,55 | 5 | 1 | 6 | 2 | 4 | 0 |
| **0,60** | 8 | 1 | 6 | 2 | 4 | **+3** |

Bu düzeltilmiş sayım **sonradan** tanımlandı (kurala eklenmedi); resmî kural sonucu "önerilmez"dir. 0,60'ın kaymasız farkı +3 ama: (i) 41 etiketle ayar yapıldı ve aralıklar örtüşüyor (0,61–0,83 ↔ 0,49–0,76); (ii) gerçek yeni FP'ler (1:14.72, 1:18.72 TOP, 1:25.88 TOP, 2:13.44) komşu/ikili mücadele kaynaklı olabilir; 1:18.76 PAS TP'si kaybediliyor. TOP KAYBI tarafındaki artış (TP 1→4) OLCUM_06'daki (c)/(d) teşhisini destekliyor: kaçan 3 etiket bu eşik büyüdüğünde yakalanıyor (1:56.48, 1:58.76, 2:55.40). Karar sende; test setinde ayrıca doğrulanmadan önerilmez.

## 3. MIN_POSS_FRAMES taraması (mevcut 2)
| MIN_POSS_FRAMES | TP/FP/FN | F1 (%95) | F1 PAS | Düzelen | Bozulan | Fark | Karar |
|---|---|---|---|---|---|---|---|
| 1 | 21/6/20 | 0,618 (0,48–0,75) | 0,656 | 0 | 2 yeni FP (1:15.00 PAS, 1:16.28 PAS) | −2 | onerilmez |
| **2** | 21/5/20 | 0,627 | 0,678 | – | – | – | mevcut |
| 3 | 20/5/21 | 0,606 (0,47–0,74) | 0,655 | 0 | 1 (2:57.20 PAS, TP→FN) | −1 | onerilmez |

## 4. 1:58.76 ve 1:56.48'de top–ayak uzaklığı
Top konumu `ball_track.csv`, ayak noktası kutunun alt-orta noktası; ikisi de `homography.csv` ile saha metresine çevrildi (tüm karelerde homografi geçerli). `tespit` = YOLO'dan seçilen aday, `interpole` = boşluk doldurma.

**1:58.76 (kare 2969).** Etiket karesi **tespit**; ±0,5 sn penceresinde 22 tespit, 3 interpole, 0 yok.
| ofset | top | en yakın oyuncu (ayak) | en yakın rakip B |
|---|---|---|---|
| −12 kare | tespit | 12A 0,71 m (nd 0,26) | 2033B 5,05 m |
| −6 | tespit | 12A 0,30 m (0,16) | 977B 6,97 m |
| −3 | tespit | 601A 1,25 m (0,46) | 977B 11,45 m |
| **0** | **tespit** (538,482) | **601A 0,84 m (0,36)** | **2123B 2,40 m (nd 1,17)** |
| +3 | tespit | 601A 0,75 m (0,28) | 2123B 2,41 m (1,25) |
| +6 | tespit | 601A 0,61 m (0,28) | 2123B 2,45 m (1,31) |
| +12 | tespit | 601A 1,72 m (1,05) | 2137B 3,46 m (1,87) |

**1:56.48 (kare 2912).** Etiket karesi **tespit**; pencerede 22 tespit, 3 interpole.
| ofset | top | en yakın oyuncu (ayak) | en yakın rakip B |
|---|---|---|---|
| −12 | tespit | 1011B 7,31 m | 1011B 7,31 m |
| −6 | tespit | 977B 2,28 m (nd 1,09) | 977B 2,28 m |
| −3 | tespit | 977B 2,92 m (2,09) | 977B 2,92 m |
| **0** | **tespit** (724,469) | **12A 2,83 m (nd 1,81)** | **977B 3,93 m (3,09)** |
| +3 | tespit | 12A 1,42 m (0,99) | 1806B 3,14 m (2,13) |
| +6 | tespit | 12A 0,64 m (0,27) | 1806B 2,17 m (1,48) |
| +12 | **interpole** | 2033B 1,61 m (0,50) | 2033B 1,61 m (0,50) |

Yorum: 1:58.76'da top etiket anında 601'in ayağında (0,84 m) ve rakip 2,4 m uzakta; yani etiket anında rakip temasının geometrik izi yok, temas muhtemelen biraz sonra/önce. 1:56.48'de top etiket anında açık alanda (en yakın oyuncu 2,8–3,9 m); rakibe (2033B) yakınlaşma (1,6 m, nd 0,50) ancak +0,5 sn'de ve **interpole** karede. POSS_DIST = 0,60 ile `events.csv`'de bu anlarda şu olaylar oluşuyor: 1:56.92 TOP KAYBI 12A→2033B (etiket 1:56.48'e −0,44 sn; yön A→B, etiketle tutarlı), 1:58.28 TOP KAYBI 2033B→12A (etiket 1:58.76'ya +0,48 sn) ve 2:55.04 TOP KAYBI 12A→3839B. **Uyarı:** 1:58.28 olayı B→A yönünde (topu rakipten alıyor); ölçüm yalnız zaman ve tip eşleştirdiği için yönü doğrulamıyor, yani 1:58.76 "düzelmesi" tesadüf olabilir. 1:56.48 ve 2:55.40 düzelmeleri ise A→B yönüyle tutarlı. Mekanizma: 2033B'nin nd değeri ~0,50 olduğundan (OLCUM_06) 0,60 eşiği onu sahip yapıyor.
