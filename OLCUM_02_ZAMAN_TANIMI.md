# OLCUM_02 — Olay zamanı tanımı değişikliği

Tarih: 2026-10-12 · Tek değişiklik: olay zamanı tanımı. Eşik/parametre ayarı yapılmadı.

Etiket tanımı: PAS = alıcının topa ilk temas anı; TOP KAYBI = rakibin topa ilk temas anı.

## Değişiklikler
| Dosya | Değişiklik |
|---|---|
| `events_v2.py` | Yeni parametre `EVENT_TIME_ANCHOR`. `"receiver_start"` (yeni varsayılan): olay karesi = alıcının / rakibin sahiplik serisinin ilk karesi (`nxt["start"]`). `"passer_end"`: eski davranış (`cur["end"]`). Başka satıra dokunulmadı. Yedek: `events_v2.py.bak_20261012`. |
| `degerlendir.py` (yeni) | Tek ölçüm kaynağı. `--events --labels --start --end --tol` (+ `--diagnose`: hata kategorileri). Birebir, tip aynı, en yakın çift önce. İşaretli fark = tahmin − gerçek. |
| `etiketleme.py` | `--start/--end/--out` (varsayılanlar 60 / 180 / gercek_olaylar.csv). Yedek: `etiketleme.py.bak_20261012`. Ek olarak başlıktaki p/k tuş açıklamaları yeni tanıma göre güncellendi (yalnız metin). |
| Çıktılar | `events_passer_end.csv`, `events_receiver_start.csv` (karşılaştırma kopyaları); `events.csv` = receiver_start. |

Doğrulama: `passer_end` modu, değişiklikten önceki `events.csv` ile bayt bayt aynı çıktı (davranış korunmuş) ve OLCUM_01 sayılarını aynen verdi.

## Sonuç (1:00–3:00, ±1 sn, 41 etiket)
| | passer_end (eski) | receiver_start (yeni) |
|---|---|---|
| Tahmin (aralıkta) | 27 | 26 |
| TP / FP / FN (genel) | 12 / 15 / 29 | **21 / 5 / 20** |
| Precision | 0.444 | **0.808** |
| Recall | 0.293 | **0.512** |
| **F1 genel** | 0.353 | **0.627** |
| F1 PAS (TP/FP/FN) | 0.367 (11/13/25) | **0.678** (20/3/16) |
| F1 TOP KAYBI (TP/FP/FN) | 0.250 (1/2/4) | 0.250 (1/2/4) |
| Tip karışıklığı | 3 | 1 (1:58.76 gerçek TOP KAYBI → PAS) |

**İşaretli zaman farkı (tahmin − gerçek):**
| | n | medyan | ort | std | mutlak ort |
|---|---|---|---|---|---|
| passer_end | 12 | +0.08 | −0.04 | 0.67 | 0.53 sn |
| receiver_start | 21 | **−0.08** | **−0.10** | **0.35** | **0.28 sn** |

Yeni tanımda fark sıfır civarında toplanıyor (medyan −0.08, ort −0.10 sn); yayılma yarıya indi (std 0.67→0.35). Ofset ayarı yapılmadı. n farklı olduğu için iki satır tam kıyaslanabilir değil (yeni modda eşleşen olay sayısı arttı). Küçük negatif eğilim: sistem etiketten ortalama ~0.1 sn (2–3 kare) erken.

## Hata kategorileri (kural tabanlı, `degerlendir.py --diagnose`)
| Kategori | eski FN | eski FP | eski Σ | yeni FN | yeni FP | yeni Σ |
|---|---|---|---|---|---|---|
| Zamanlama farkı (1–3 sn) | 11 | 9 | 20 | 2 | 1 | **3** |
| Çok kısa sahiplik (filtre) | 6 | 0 | 6 | 7 | 0 | **7** |
| Yanlış takım ataması | 3 | 2 | 5 | 4 | 1 | **5** |
| Top kaybolmuş | 5 | 0 | 5 | 4 | 0 | **4** |
| Atlanan pas (alıcıda sahiplik yok) | 3 | 0 | 3 | 3 | 0 | **3** |
| Hakem karışması | 1 | 2 | 3 | 0 | 1 | **1** |
| Çift sayım | 0 | 0 | 0 | 0 | 1 | **1** |
| Etiket yok / karşılıksız | 0 | 2 | 2 | 0 | 1 | **1** |
| **Toplam** | 29 | 15 | 44 | 20 | 5 | **25** |

Kalan hatalar (yeni): FN 20 (TOP KAYBI 4, PAS 16), FP 5 — 1:04.64 PAS (6→1), 1:16.28 TOP KAYBI (392→505), 1:21.00 TOP KAYBI (476→597), 1:58.72 PAS (12→601), 2:26.92 PAS (2857→6).

Notlar / sınırlar:
- Zamanlama hatalarının 20→3'e inmesi, OLCUM_01'deki kaymanın büyük kısmının tanım farkından geldiğini gösteriyor; geri kalan hatalar yeni tanımda öne çıktı.
- Yeni modda "çok kısa sahiplik" 7 FN ile en büyük kategori; yeni FN'ler (2:23.64, 2:35.48 vb.) daha önce başka olaylarla eşleşip maskelenmişti. 
- TOP KAYBI performansı değişmedi (5 etiketin 4'ü kaçıyor); 3'ü yanlış takım ataması kategorisinde (iki takım rengi/hakem sorunu, OLCUM_01'deki 510 A / 1992 B dengesizliği).
- Kategoriler kural-tabanlıdır (ball_track/possession/teams/players.csv); video izlenmedi.
- Yeni tanımda `events.csv`'deki `frame/sec` alıcının serisinin ilk karesidir; `MIN_RECEIVE_FRAMES` onayı sonrası değil, seri başı kullanılır.

## etiketleme.py testi
- `--help` çalışıyor; argümansız varsayılanlar eski değerlerle aynı (60/180/gercek_olaylar.csv).
- `--start 180 --end 300 --out <geçici csv>` ile başlatıldı: süreç 8 sn boyunca hatasız çalıştı (video açılamasa `SystemExit` verirdi); `gercek_olaylar.csv` hash'i değişmedi.
- **Doğrulanamadı:** pencerenin ekranda görünmesi ve tuşların çalışması (arka planda başlatıldı, başlık okunamadı). Bunu `python etiketleme.py --start 180 --end 300 --out gercek_olaylar_test.csv` ile ilk çalıştırmanda görmen gerekiyor.
