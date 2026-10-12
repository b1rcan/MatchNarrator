# OLCUM_09 — Doğrulama seti (360–540 sn) ve üç set taban tablosu

Tarih: 2026-10-12 · Varsayılan parametreler değişmedi (`POSS_DIST = 0.45`). Test seti (180–300) için yalnız toplu taban sayıları verildi; hata düzeyinde analiz yok. Araç: `tarama_val.py`.

## 1. Hat ve etiket dosyası
- Hat tamamlandı (`veri_360_540/hat_ilerleme.log`: 13:40:34 TAMAMLANDI). `veri_360_540/events.csv`: 39 olay (PAS 27, TOP KAYBI 12). Top: **%60,7 tespit, %77,9 bilinen** (4 500 kare, kare 9000–13499); homografi %100.
- `gercek_olaylar_val.csv` (değiştirilmedi):

| Kontrol | Sonuç |
|---|---|
| Satır | 41 (PAS 35, TOP KAYBI 6) |
| Aralık | 6:14.68 – 8:35.04 (374.68–515.04 sn); 360–540 dışında satır yok |
| Format / boş / tip | Hata yok; yalnız PAS / TOP KAYBI; sıralı; BOM yok |
| Yinelenen | 0 |
| <1 sn aralıklı | 5 çift: 6:18.52→6:19.16 (0,64), 6:19.16→6:19.92 (0,76), 7:12.68→7:12.88 (0,20), 7:25.32→7:26.16 (0,84), 7:40.24→7:40.60 (0,36) |

## 2. Doğrulama seti: POSS_DIST {0,45; 0,60; 0,65; 0,70}
±1 sn, birebir, tip aynı. Taban 0,45. (Notlar: bu sette `events.csv`'de `DEGISIM (takim belirsiz)` tipli olaylar da var — 8:49, 8:50 — her zaman FP sayılır.)

| | 0,45 (taban) | 0,60 | 0,65 | 0,70 |
|---|---|---|---|---|
| Tahmin | 39 | 49 | 49 | 50 |
| Genel TP/FP/FN | 19/20/22 | 24/25/17 | 24/25/17 | 23/27/18 |
| Genel P / R | 0,49 / 0,46 | 0,49 / 0,58 | 0,49 / 0,58 | 0,46 / 0,56 |
| **Genel F1 (%95)** | 0,475 (0,33–0,60) | 0,533 (0,41–0,65) | 0,533 (0,41–0,65) | 0,505 (0,38–0,63) |
| PAS TP/FP/FN · F1 (%95) | 18/9/17 · 0,581 (0,43–0,71) | 22/11/13 · 0,647 (0,52–0,77) | 22/7/13 · 0,688 (0,55–0,80) | 21/8/14 · 0,656 (0,52–0,77) |
| TOP KAYBI TP/FP/FN · F1 (%95) | 1/11/5 · 0,111 (0,00–0,30) | 2/12/4 · 0,200 (0,00–0,43) | 2/16/4 · 0,167 (0,00–0,37) | 2/19/4 · 0,148 (0,00–0,33) |
| Zaman farkı medyan / std (sn) | −0,12 / 0,44 | −0,10 / 0,48 | −0,14 / 0,46 | −0,16 / 0,47 |

### Eşleştirilmiş bootstrap (1000×, etiket düzeyinde; taban 0,45)
| Ayar | Genel F1 farkı (%95) · P(>0) | PAS farkı · P(>0) | TOP KAYBI farkı · P(>0) | Düzelen | TP→FN | Yeni FP (kayma) | **Fark (sıkı)** | Kaymasız | Karar |
|---|---|---|---|---|---|---|---|---|---|
| 0,60 | +0,058 (−0,047…+0,196) · 0,85 | +0,066 (−0,054…+0,210) · 0,86 | +0,089 (−0,056…+0,308) · 0,62 | 7 | 2 | 18 (7) | **−13** | −6 | **önerilmez** |
| 0,65 | +0,058 (−0,060…+0,197) · 0,84 | +0,107 (−0,011…+0,236) · 0,96 | +0,056 (−0,100…+0,264) · 0,59 | 7 | 2 | 19 (5) | **−14** | −9 | **önerilmez** |
| 0,70 | +0,030 (−0,097…+0,181) · 0,70 | +0,076 (−0,064…+0,228) · 0,86 | +0,037 (−0,111…+0,239) · 0,57 | 7 | 3 | 20 (6) | **−16** | −10 | **önerilmez** |

Düzelen / bozulan zamanlar:
| Ayar | Düzelen (FN→TP) | TP→FN | Yeni FP | Giden FP |
|---|---|---|---|---|
| 0,60 | 6:45.56, 7:25.32, 7:26.16, 7:40.60, 7:43.88, 7:52.28 (PAS); 7:59.12 (TOP) | 6:50.48, 8:15.08 (PAS) | 6:05.16, 6:09.20, 6:16.04, 6:17.00, 6:22.24, 7:22.36, 8:09.32, 8:33.16 (TOP); 6:06.60, 6:24.52, 7:07.92, 7:09.08, 7:39.28, 8:41.20, 8:42.12, 8:43.80 (PAS); 8:49.04, 8:50.76 (DEĞİŞİM) | 6:16.16, 6:17.04, 6:22.28, 7:22.40, 7:57.56, 8:10.04, 8:50.12 (TOP); 6:24.56, 7:10.72, 7:45.00, 8:24.48, 8:33.28, 8:44.04 (PAS) |
| 0,65 | aynı 7 olay | 7:06.48, 8:15.08 (PAS) | 19 yeni FP (çoğu TOP: 6:05–6:24, 7:03.84, 7:06.24, 7:22.24, 8:09.28, 8:34.84; PAS: 6:06.60, 7:39.28, 8:40.76, 8:42.12, 8:45.52; DEĞİŞİM: 8:49.04, 8:50.76) | 14 giden |
| 0,70 | aynı 7 olay | 7:06.48, 8:15.08, 8:35.04 (PAS) | 20 yeni FP (çoğu TOP: 6:05–6:26, 7:03.84, 7:06.24, 7:22.20, 8:09.24, 8:34.84, 8:57.80) | 13 giden |

**Yorum:**
- **Sıkı kural:** doğrulama setinde **hiçbir ayar önerilmez** (fark −13…−16). Geliştirme setindeki en iyi sıkı fark +1 (0,60) idi; yani 0,60 geliştirmede sınırda geçmedi, doğrulamada da geçmedi.
- **Yön tutarlı ama zayıf:** genel F1 farkı üç ayarda da pozitif (+0,03…+0,06) ve geliştirmeyle aynı yönde (+0,11; P(>0) 0,96 → 0,85), ancak %95 aralığı sıfırı içeriyor (0,60: −0,047…+0,196). TP +5 kazanılıyor ama FP de +5 (20→25), net F1 kazancı küçük.
- **Sıkı kuralın bu sette çok katı çıkması:** yeni FP 18–20, giden FP 13–14 — FP kümesi büyük ölçüde yer değiştiriyor (özellikle TOP KAYBI adayları), net FP artışı +5/+5/+7. Kaymasız sayım da −6…−10; sonuç değişmiyor.
- **TOP KAYBI:** geliştirmedeki kazanç (TP 1→4) doğrulamada yok (TP 1→2); TOP KAYBI FP'si zaten yüksek (taban 11) ve 0,65/0,70'te 16/19'a çıkıyor. Geliştirmedeki TOP KAYBI iyileşmesi bu sette tekrarlanmadı.
- **Sonuç:** POSS_DIST artırma, geliştirmede görülen faydayı doğrulama setinde (kuralın izin verdiği biçimde) göstermedi; önerilmez. Pooled bilgi (seçim yanlılığı var, geliştirme dahil): geliştirme+doğrulama birleşik F1 taban 0,544 (TP 40, FP 25, FN 42) → 0,60'ta 0,627 (TP 52, FP 32, FN 30).

## 3. Üç set — taban ayar (POSS_DIST = 0,45), `receiver_start`, eski K-means takım
| Set | Etiket | Tahmin | TP | FP | FN | Precision | Recall | F1 (%95) |
|---|---|---|---|---|---|---|---|---|
| Geliştirme (60–180) | 41 | 26 | 21 | 5 | 20 | 0,808 | 0,512 | 0,627 (0,49–0,76) |
| Test (180–300) | 24 | 22 | 10 | 12 | 14 | 0,455 | 0,417 | 0,435 (0,24–0,59) |
| Doğrulama (360–540) | 41 | 39 | 19 | 20 | 22 | 0,487 | 0,463 | 0,475 (0,33–0,60) |
| **Birleşik (3 set)** | **106** | **87** | **50** | **37** | **56** | **0,575** | **0,472** | **0,518 (0,43–0,60)** |

Birleşik: sayılar toplanıp (mikro) F1 = 2·50 / (2·50 + 37 + 56) = 0,518; %95 aralığı TP/FP/FN birimleri yerine koyarak bootstrap (1000×). Not: sistem ayarları geliştirme setindeki incelemelerle şekillendi (zaman tanımı, filtre taramaları); test ve doğrulama setleri bu geliştirmeyi görmeden ölçüldü (test yalnız toplu sayıyla). Geliştirme seti diğer ikisinden belirgin yüksek (0,627 vs 0,435 / 0,475); aralıklar örtüşüyor ama bu fark, geliştirme setinde yapılan ayar/teşhis kaynaklı iyimserliği gösteriyor olabilir — gerçekçi performans tahmini test+doğrulama (F1 ≈ 0,46) civarında.
