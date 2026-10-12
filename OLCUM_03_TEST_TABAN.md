Bu dosya iyileştirmelerden önceki taban ölçümdür. Test setinde parametre ayarı yapılmaz.

# OLCUM_03 — Test seti taban ölçümü (180–300 sn)

Tarih: 2026-10-12 · Sistem değişmeden: `events_v2.py`, `EVENT_TIME_ANCHOR = "receiver_start"`, `events.csv` = `events_receiver_start.csv` (bayt bayt aynı doğrulandı). Hata (FP/FN) analizi yapılmadı.

## 1. Etiket dosyası (gercek_olaylar_test.csv)
| Kontrol | Sonuç |
|---|---|
| Satır | 24 (PAS 20, TOP KAYBI 4) |
| Aralık | 3:01.16 – 4:58.76 (181.16–298.76 sn); 180–300 dışında satır yok |
| Format / tip / boş | Hata yok; sıralı |
| Yinelenen satır | 0 |
| <1 sn aralıklı | 1 çift: 4:38.56 PAS → 4:39.24 PAS (0.68 sn). Değiştirilmedi. |

## 2. Ara CSV kapsaması
`meta.json` kare 1500–9000 (60–360 sn, 25 fps). players, ball_candidates, homography, ball_track: kare 1500–8999 → 180–300 sn tamamen kapsanıyor. `events.csv` 64.6–352.1 sn aralığında olay içeriyor.

## 3. Taban ölçüm (180–300 sn, ±1 sn, birebir, tip aynı)
24 etiket · aralıkta 22 tahmin (aralık dışı 34 yok sayıldı)

| Grup | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| **Genel** | 10 | 12 | 14 | 0.455 | 0.417 | **0.435** |
| PAS | 7 | 8 | 13 | 0.467 | 0.350 | 0.400 |
| TOP KAYBI | 3 | 4 | 1 | 0.429 | 0.750 | 0.545 |

İşaretli zaman farkı (tahmin − gerçek, n = 10 eşleşme): **medyan −0.20 sn, std 0.46 sn**.

Not: 24 etiketle TP/FP/FN sayıları küçük; tip bazında (özellikle 4 TOP KAYBI) F1 çok oynak, yorumlarken dikkat. Geliştirme setindeki (60–180 sn) 0.627 ile karşılaştırma için tek başına ayarın aşırı uyum yapıp yapmadığı sorusu bu ölçümle izlenecek.
