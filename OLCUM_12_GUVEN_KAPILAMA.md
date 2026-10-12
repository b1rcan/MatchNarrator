# OLCUM_12 — Güven kapılama analizi, takım adları ayarı, v2.1 dondurma

Tarih: 2026-10-12 · Yalnız geliştirme (60–180) ve doğrulama (360–540) setleri, ayrı ayrı. **Test seti (180–300) kullanılmadı.** Sistem ve parametreler değişmedi; yalnız çıktı üzerinde alt küme analizi.

## 1. Git (yerel ayar, push yok)
- `git config --local`: `user.name = Bircan GÖRÜR`, `user.email = sanatcan1can@gmail.com`. **Not:** istekte ad köşeli parantezli (`[Bircan GÖRÜR]`) yazılmıştı; parantezleri bir şablon kalıntısı sayıp kaldırdım. Parantezli istiyorsan `git config --local user.name "[Bircan GÖRÜR]"` ve `git commit --amend --reset-author` (etiket taşınır) gerekir.
- Etiket dosyaları (`gercek_olaylar.csv`, `_test`, `_val`) eklendi; commit mesajı OLCUM_11'deki taslak. Etiket: `v2.1`.
- `git log --oneline`: `f830c5c v2.1: sahiplik tabanli olay tespiti (donduruldu)` ve bu analizin commit'i (`Güven kapılama analizi ve takım adları ayarı`); `git tag`: `v2.1` (f830c5c'de).

## 2. Güven kapılama
**Yöntem.** `olaylar_zengin.json`'daki güven işaretleriyle 9 alt küme kuralı (+ K0 taban) **önceden sabitlendi**; eşikler (≥6 kare, ≥30 px, ≥%80, 30 m, 20 m/sn) ayarlanmadı, hedef (ör. precision ≥ 0,7) verilmedi ve seçim yapılmadı. Her kural için kalan olaylar tahmin kabul edilir, **etiketlerin tamamı** gerçek olarak kalır (recall bu yüzden düşebilir); eşleştirme `degerlendir.py` ile aynı (±1 sn, birebir, tip aynı). TP/FP/FN kapılanmış çıktıdan yeniden hesaplandı; K0 önceki ölçümlerle aynı (gel. 21/5/20, doğ. 19/20/22).

Kurallar: K1 olay karesinde top `tespit` · K2 olay karesi ve eski sahibin son karesinde top `tespit` · K3 K1 + başlangıç/bitiş konumu var ve saha içi · K4 yeni sahip serisi ≥ 6 kare · K5 K1 + seri ≥ 6 · K6 iki izin kutu yüksekliği ≥ 30 px · K7 olay karesi ±12 kare (±0,5 sn) içinde top bilinen oranı ≥ %80 (bu işaret JSON'da yok, `ball_track.csv`'den hesaplandı) · K8 K1 + seri ≥ 6 + kutu ≥ 30 px + K7 · K9 mesafe ≤ 30 m ve top hızı ≤ 20 m/sn (null hız kabul).
Betik: `guven_kapilama.py` (ham tablo `tarama/guven_kapilama.csv`).

Tablolarda "kalan/toplam" = kapıdan geçen / aralıktaki tüm olay (o tip için).

### GENEL

| Kural | Gel. kalan/toplam | Gel. TP/FP/FN | Gel. P / R / F1 | Doğ. kalan/toplam | Doğ. TP/FP/FN | Doğ. P / R / F1 |
|---|---|---|---|---|---|---|
| K0 tum olaylar (taban) | 26/26 | 21/5/20 | 0.808 / 0.512 / 0.627 | 39/39 | 19/20/22 | 0.487 / 0.463 / 0.475 |
| K1 olay karesinde top tespit | 24/26 | 20/4/21 | 0.833 / 0.488 / 0.615 | 32/39 | 17/15/24 | 0.531 / 0.415 / 0.466 |
| K2 top tespit: olay + eski sahip son kare | 19/26 | 16/3/25 | 0.842 / 0.390 / 0.533 | 28/39 | 14/14/27 | 0.500 / 0.341 / 0.406 |
| K3 K1 + konum var (baslangic+bitis) + saha ici | 23/26 | 20/3/21 | 0.870 / 0.488 / 0.625 | 30/39 | 16/14/25 | 0.533 / 0.390 / 0.451 |
| K4 yeni sahip serisi >= 6 kare | 20/26 | 17/3/24 | 0.850 / 0.415 / 0.557 | 32/39 | 18/14/23 | 0.562 / 0.439 / 0.493 |
| K5 K1 + seri >= 6 kare | 18/26 | 16/2/25 | 0.889 / 0.390 / 0.542 | 27/39 | 16/11/25 | 0.593 / 0.390 / 0.471 |
| K6 kutu yuksekligi >= 30 px (kimden ve kime) | 17/26 | 15/2/26 | 0.882 / 0.366 / 0.517 | 36/39 | 17/19/24 | 0.472 / 0.415 / 0.442 |
| K7 olay +-0,5 sn top bilinen >= %80 | 18/26 | 16/2/25 | 0.889 / 0.390 / 0.542 | 26/39 | 14/12/27 | 0.538 / 0.341 / 0.418 |
| K8 K1 + seri>=6 + kutu>=30 px + K7 (en siki) | 10/26 | 9/1/32 | 0.900 / 0.220 / 0.353 | 17/39 | 10/7/31 | 0.588 / 0.244 / 0.345 |
| K9 makul geometri: mesafe <= 30 m ve hiz <= 20 m/sn | 24/26 | 21/3/20 | 0.875 / 0.512 / 0.646 | 30/39 | 16/14/25 | 0.533 / 0.390 / 0.451 |

### PAS

| Kural | Gel. kalan/toplam | Gel. TP/FP/FN | Gel. P / R / F1 | Doğ. kalan/toplam | Doğ. TP/FP/FN | Doğ. P / R / F1 |
|---|---|---|---|---|---|---|
| K0 tum olaylar (taban) | 23/23 | 20/3/16 | 0.870 / 0.556 / 0.678 | 27/27 | 18/9/17 | 0.667 / 0.514 / 0.581 |
| K1 olay karesinde top tespit | 23/23 | 20/3/16 | 0.870 / 0.556 / 0.678 | 22/27 | 16/6/19 | 0.727 / 0.457 / 0.561 |
| K2 top tespit: olay + eski sahip son kare | 19/23 | 16/3/20 | 0.842 / 0.444 / 0.582 | 19/27 | 13/6/22 | 0.684 / 0.371 / 0.481 |
| K3 K1 + konum var (baslangic+bitis) + saha ici | 22/23 | 20/2/16 | 0.909 / 0.556 / 0.690 | 21/27 | 15/6/20 | 0.714 / 0.429 / 0.536 |
| K4 yeni sahip serisi >= 6 kare | 17/23 | 16/1/20 | 0.941 / 0.444 / 0.604 | 23/27 | 17/6/18 | 0.739 / 0.486 / 0.586 |
| K5 K1 + seri >= 6 kare | 17/23 | 16/1/20 | 0.941 / 0.444 / 0.604 | 20/27 | 15/5/20 | 0.750 / 0.429 / 0.545 |
| K6 kutu yuksekligi >= 30 px (kimden ve kime) | 17/23 | 15/2/21 | 0.882 / 0.417 / 0.566 | 25/27 | 16/9/19 | 0.640 / 0.457 / 0.533 |
| K7 olay +-0,5 sn top bilinen >= %80 | 16/23 | 15/1/21 | 0.938 / 0.417 / 0.577 | 19/27 | 13/6/22 | 0.684 / 0.371 / 0.481 |
| K8 K1 + seri>=6 + kutu>=30 px + K7 (en siki) | 10/23 | 9/1/27 | 0.900 / 0.250 / 0.391 | 13/27 | 9/4/26 | 0.692 / 0.257 / 0.375 |
| K9 makul geometri: mesafe <= 30 m ve hiz <= 20 m/sn | 22/23 | 20/2/16 | 0.909 / 0.556 / 0.690 | 21/27 | 15/6/20 | 0.714 / 0.429 / 0.536 |

### TOP KAYBI

| Kural | Gel. kalan/toplam | Gel. TP/FP/FN | Gel. P / R / F1 | Doğ. kalan/toplam | Doğ. TP/FP/FN | Doğ. P / R / F1 |
|---|---|---|---|---|---|---|
| K0 tum olaylar (taban) | 3/3 | 1/2/4 | 0.333 / 0.200 / 0.250 | 12/12 | 1/11/5 | 0.083 / 0.167 / 0.111 |
| K1 olay karesinde top tespit | 1/3 | 0/1/5 | 0.000 / 0.000 / 0.000 | 10/12 | 1/9/5 | 0.100 / 0.167 / 0.125 |
| K2 top tespit: olay + eski sahip son kare | 0/3 | 0/0/5 | – / 0.000 / 0.000 | 9/12 | 1/8/5 | 0.111 / 0.167 / 0.133 |
| K3 K1 + konum var (baslangic+bitis) + saha ici | 1/3 | 0/1/5 | 0.000 / 0.000 / 0.000 | 9/12 | 1/8/5 | 0.111 / 0.167 / 0.133 |
| K4 yeni sahip serisi >= 6 kare | 3/3 | 1/2/4 | 0.333 / 0.200 / 0.250 | 9/12 | 1/8/5 | 0.111 / 0.167 / 0.133 |
| K5 K1 + seri >= 6 kare | 1/3 | 0/1/5 | 0.000 / 0.000 / 0.000 | 7/12 | 1/6/5 | 0.143 / 0.167 / 0.154 |
| K6 kutu yuksekligi >= 30 px (kimden ve kime) | 0/3 | 0/0/5 | – / 0.000 / 0.000 | 11/12 | 1/10/5 | 0.091 / 0.167 / 0.118 |
| K7 olay +-0,5 sn top bilinen >= %80 | 2/3 | 1/1/4 | 0.500 / 0.200 / 0.286 | 7/12 | 1/6/5 | 0.143 / 0.167 / 0.154 |
| K8 K1 + seri>=6 + kutu>=30 px + K7 (en siki) | 0/3 | 0/0/5 | – / 0.000 / 0.000 | 4/12 | 1/3/5 | 0.250 / 0.167 / 0.200 |
| K9 makul geometri: mesafe <= 30 m ve hiz <= 20 m/sn | 2/3 | 1/1/4 | 0.500 / 0.200 / 0.286 | 9/12 | 1/8/5 | 0.111 / 0.167 / 0.133 |

### Tutarlılık (GENEL, K0'a göre fark; her iki sette işaret aynı mı?)

| Kural | ΔPrecision gel. / doğ. | ΔRecall gel. / doğ. | ΔF1 gel. / doğ. | P iki sette de ↑ | F1 iki sette de ↑ |
|---|---|---|---|---|---|
| K1 olay karesinde top tespit | +0.026 / +0.044 | -0.024 / -0.049 | -0.011 / -0.009 | evet | hayır |
| K2 top tespit: olay + eski sahip son kare | +0.034 / +0.013 | -0.122 / -0.122 | -0.094 / -0.069 | evet | hayır |
| K3 K1 + konum var (baslangic+bitis) + saha ici | +0.062 / +0.046 | -0.024 / -0.073 | -0.002 / -0.024 | evet | hayır |
| K4 yeni sahip serisi >= 6 kare | +0.042 / +0.075 | -0.098 / -0.024 | -0.069 / +0.018 | evet | hayır |
| K5 K1 + seri >= 6 kare | +0.081 / +0.105 | -0.122 / -0.073 | -0.084 / -0.004 | evet | hayır |
| K6 kutu yuksekligi >= 30 px (kimden ve kime) | +0.075 / -0.015 | -0.146 / -0.049 | -0.110 / -0.033 | hayır | hayır |
| K7 olay +-0,5 sn top bilinen >= %80 | +0.081 / +0.051 | -0.122 / -0.122 | -0.084 / -0.057 | evet | hayır |
| K8 K1 + seri>=6 + kutu>=30 px + K7 (en siki) | +0.092 / +0.101 | -0.293 / -0.220 | -0.274 / -0.130 | evet | hayır |
| K9 makul geometri: mesafe <= 30 m ve hiz <= 20 m/sn | +0.067 / +0.046 | +0.000 / -0.073 | +0.019 / -0.024 | evet | hayır |

## Okuma notları (seçim yapılmadı)
- **Precision her iki sette de artan kurallar:** K1, K2, K3, K4, K5, K7, K8, K9 (K6 doğrulamada −0,015). Bu artış her zaman recall kaybıyla geliyor: K0'a göre recall değişimi gel./doğ. −0,02…−0,29 / −0,02…−0,22 (K9 geliştirmede 0,00).
- **F1'i her iki sette de artıran kural yok.** Geliştirmede yalnız K9 F1'i artırıyor (+0,019, doğrulamada −0,024); doğrulamada yalnız K4 artırıyor (+0,018, geliştirmede −0,069).
- **PAS:** K1, K3, K4, K5, K9'da precision iki sette de ≥ K0 (gel. 0,87→0,87–0,94; doğ. 0,667→0,714–0,750); K6'da doğrulamada düşüyor. **TOP KAYBI:** geliştirmede 3 olay, doğrulamada 12 olay ve 6 etiket olduğundan alt küme sonuçları (0/1/2 olay, TP 0–1) istatistiksel olarak yorumlanamaz.
- Örnek küçük (gel. 41, doğ. 41 etiket; alt kümelerde 4–32 olay); tek tek TP/FP farkları 1–3 olaydan oluşuyor.

## 3. Takım adları (`config_takimlar.json`)
`{"A": "Barcelona", "B": "Espanyol"}` (renk bilgisi ayrı: `forma_rengi_hex` / `ad_yaklasik`). `olay_zenginlestir.py` bu dosyayı okur (`--config` ile değiştirilebilir, `--out` yeni); dosya **yoksa** çıktı önceki `olaylar_zengin.json` ile **bayt bayt aynı** (doğrulandı). Dosya varsa yalnız şu alanlar eklenir: `takimlar.A/B.ad` ve `kimden/kime.takim_adi`; bunlar çıkarılınca çıktı eskisiyle aynı (doğrulandı). Not: `ad` takım adı, `ad_yaklasik` forma renk adıdır.
