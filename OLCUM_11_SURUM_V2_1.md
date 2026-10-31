# OLCUM_11 — Sürüm v2.1 (donduruldu), zengin olay çıktısı, hız tablosu

Tarih: 2026-10-12 · Yeni ölçüm yok; yalnız mevcut çıktılar ve log'lar kullanıldı.

## 1. Sürüm dondurma (git)
- `git init -b main` yapıldı. `.gitignore`: `*.mp4`, `*.pt`, `*.zip`, `.venv/`, `__pycache__/`, `veri_*/`, `tarama/`, `runs/`, `sonuc_bytetrack/`, `*.bak*`, `*.png`, ara/üretilmiş CSV ve JSON (players, ball_*, homography, possession, teams, events*, tracking_data, meta, olaylar_zengin).
- İndekse eklendi: `.gitignore`, tüm `*.py` (25), `OLCUM_*.md` (11, bu dosya dahil) ve `GERI_KURULUM_RAPORU.md`. Etiket dosyaları (`gercek_olaylar*.csv`) bilerek ignore edilmedi ama istenmediği için eklenmedi (untracked).
- **Commit ve `v2.1` etiketi henüz yapılmadı: git'te `user.name` / `user.email` tanımlı değil** (global yok). Bilgiyi verdiğinde commit + annotated tag `v2.1` yapılacak.

Taslak commit mesajı:
```
v2.1: sahiplik tabanli olay tespiti (donduruldu)

Dondurulan parametreler (events_v2.py varsayilanlari):
  EVENT_TIME_ANCHOR=receiver_start  POSS_DIST=0.45  MIN_POSS_FRAMES=2  DRIBBLE_GAP=12
  MIN_RECEIVE_FRAMES=4  MIN_RECEIVE_FRAMES_LOSS=5  MAX_PASS_GAP_SEC=3.0  SAME_PLAYER_DIST=0.5
  MIN_PASS_DIST_M=3.0  MAX_BALL_SPEED_MS=35.0  MAX_INTERP_GAP=10  DOGRULAMA_KARE=3
  ID_MERGE_REQUIRE_SAME_TEAM=0  takim: K-means (SigLIP --teams opsiyonel, varsayilan degil)
  tolerans +-1 sn, birebir eslestirme, tip ayni

Nihai sonuc (test seti 180-300 sn, 24 etiket): TP 10 / FP 12 / FN 14,
  Precision 0.455, Recall 0.417, F1 0.435 (%95: 0.24-0.59)
Gelistirme (60-180): F1 0.627; dogrulama (360-540): F1 0.475; birlesik (3 set, 106 etiket): F1 0.518.
```

## 2. Zengin olay çıktısı (`olay_zenginlestir.py` → `olaylar_zengin.json`)
95 olay: **70 PAS, 25 TOP KAYBI** (`ana_60_360`: 56, `veri_360_540`: 39). Kaynaklar farklı izleme çalıştırmaları olduğu için **iz numaraları kaynak içinde geçerlidir**; kayıt `id` = `<kaynak>_<kare>`.

Alanlar: `zaman_sn`, `zaman` (m:ss, saniye aşağı yuvarlı), `tip`, `takimlar` (A/B baskın forma rengi: takımın oyuncu-sınıflı izlerinin (≥25 kare) medyan Lab değeri → hex + kaba ad), `kimden`/`kime` (iz, takım), `konum_baslangic_m` / `konum_bitis_m` (eski sahibin son, yeni sahibin ilk sahiplik karesindeki **ayak** noktası; kareye özgü homografi; 105×68 m, x = boy, y = en), `mesafe_m`, `yon_x` (`+x`/`-x`/`~0`, |dx| ≤ 1 m için `~0`) ve `dx_m`/`dy_m`, `top_hizi_ms`, `bosluk_sn`, `bolge_baslangic`/`bolge_bitis` (`x_ucte_bir`: dusuk_x / orta / yuksek_x; `enine`: kanat_y_dusuk / merkez / kanat_y_yuksek), `guven` (olay karesinde ve eski sahibin son karesinde top durumu `tespit`/`interpole`/`yok`; kutu yüksekliği px; yeni sahip serisi kare sayısı; homografi durumu).

Notlar ve sınırlar:
- **Hücum yönü bilinmiyor**: `yon_x` yalnız x ekseninde işaret (+x/−x); `savunma/orta/hücum` ayrımı yapılmadı, x üçte biri nötr adlarla verildi. `kanat_y_dusuk/yuksek` hangi çizgi olduğu bilinmeden verilen y üçte birleridir.
- **Takım A rengi güvenilmez**: A (Barça, iki tonlu) için medyan Lab gri-kahve (`#7f6c61`) çıkıyor, ad "karışık/soluk"; B (sarı) `#c6bb4a`. Mevcut K-means yeterli denmişti, bu yüzden renk tanımı iyileştirilmedi.
- **Top hızı** `(mesafe − 1,5) / boşluk` ile yaklaşıktır (ölçülmüş top hızı değil); olay anında top çoğunlukla havada ya da iki oyuncu arasında olduğundan, kayıtlarda aşırı değerler (ör. 1:21.00, 36,9 m / 25,3 m/sn) saha izdüşümü/top izi sıçramasının göstergesi olabilir. Bu olay zaten bilinen bir FP (OLCUM_06/10).
- Konum `null` olan 5 olay: `ana_60_360_3635` (PAS), `…_6148` (PAS), `…_8425` (TOP KAYBI), `veri_360_540_10796` (PAS), `veri_360_540_13253` (TOP KAYBI) — eski/yeni sahibin o karede kutusu ya da geçerli homografi yok; değer uydurulmadı.
- Tüm olaylar saha sınırları içinde (−1…+1 m payla). Mesafe, `events.csv`'deki `mesafe_m` ile 53 olayda medyan 0,00 m, en çok 1,6 m farklı (aynı geometri, kare eşleme farkı).
- Olay karesinde top: 77 `tespit`, 18 `interpole`.

İlk 10 kaydın özeti (JSON'daki tüm alanlar; konum m, 105×68):
| # | id | Zaman (sn) | Tip | Kimden → kime | Konum başlangıç → bitiş | Mesafe m | Yön x (dx) | Hız m/sn | Bölge (bitiş) | Top (olay/eski) | Kutu px (kimden/kime) | Yeni seri kare |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ana_60_360_1616 | 1:04 (64.64) | PAS | 6A → 1A | (50.48, 42.31) → (56.39, 55.36) | 14.3 | +x (5.9) | 6.3 | orta/kanat_y_yuksek | tespit/tespit | 48/51 | 4 |
| 2 | ana_60_360_1667 | 1:06 (66.68) | PAS | 1A → 6A | (56.72, 55.68) → (52.54, 42.42) | 13.9 | −x (−4.2) | 6.5 | orta/merkez | tespit/tespit | 50/46 | 5 |
| 3 | ana_60_360_1729 | 1:09 (69.16) | PAS | 6A → 8A | (54.07, 37.27) → (61.10, 19.35) | 19.3 | +x (7.0) | 15.8 | orta/kanat_y_dusuk | tespit/tespit | 37/32 | 7 |
| 4 | ana_60_360_1907 | 1:16 (76.28) | TOP KAYBI | 392A → 505B | (76.34, 18.39) → (87.13, 20.37) | 11.0 | +x (10.8) | 4.1 | yuksek_x/kanat_y_dusuk | tespit/interpole | 28/29 | 10 |
| 5 | ana_60_360_1969 | 1:18 (78.76) | PAS | 505B → 476B | (87.08, 20.40) → (90.69, 6.09) | 14.8 | +x (3.6) | 6.3 | yuksek_x/kanat_y_dusuk | tespit/tespit | 31/27 | 22 |
| 6 | ana_60_360_2025 | 1:21 (81.00) | TOP KAYBI | 476B → 597A | (90.83, 3.02) → (54.40, 8.70) | 36.9 | −x (−36.4) | 25.3 | orta/kanat_y_dusuk | interpole/tespit | 27/28 | 7 |
| 7 | ana_60_360_2060 | 1:22 (82.40) | PAS | 597A → 768A | (54.88, 8.03) → (62.42, 4.03) | 8.5 | +x (7.5) | 6.1 | orta/kanat_y_dusuk | tespit/tespit | 26/26 | 4 |
| 8 | ana_60_360_2071 | 1:22 (82.84) | TOP KAYBI | 768A → 843B | (61.88, 3.99) → (57.62, 9.47) | 6.9 | −x (−4.3) | 17.0 | orta/kanat_y_dusuk | interpole/tespit | 28/39 | 7 |
| 9 | ana_60_360_2259 | 1:30 (90.36) | PAS | 597A → 6A | (38.03, 3.74) → (34.42, 24.26) | 20.8 | −x (−3.6) | 8.3 | dusuk_x/merkez | tespit/tespit | 31/34 | 27 |
| 10 | ana_60_360_2476 | 1:39 (99.04) | PAS | 6A → 597A | (48.91, 28.45) → (53.47, 12.55) | 16.5 | +x (4.6) | 14.5 | orta/kanat_y_dusuk | tespit/interpole | 32/30 | 41 |

Örnek tam kayıt (#1, kısaltılmış `takimlar` ile): `{"id": "ana_60_360_1616", "kaynak": "ana_60_360", "kare": 1616, "zaman_sn": 64.64, "zaman": "1:04", "tip": "PAS", "takimlar": {"A": {"forma_rengi_hex": "#7f6c61", "ad_yaklasik": "karisik/soluk (ad guvenilmez)", "iz_sayisi": 191}, "B": {"forma_rengi_hex": "#c6bb4a", "ad_yaklasik": "sari", "iz_sayisi": 213}}, "kimden": {"iz": 6, "takim": "A"}, "kime": {"iz": 1, "takim": "A"}, "konum_baslangic_m": {"x": 50.48, "y": 42.31}, "konum_bitis_m": {"x": 56.39, "y": 55.36}, "mesafe_m": 14.3, "yon_x": "+x", "dx_m": 5.9, "dy_m": 13.0, "top_hizi_ms": 6.3, "bosluk_sn": 2.04, "bolge_baslangic": {"x_ucte_bir": "orta", "enine": "merkez"}, "bolge_bitis": {"x_ucte_bir": "orta", "enine": "kanat_y_yuksek"}, "guven": {"top_durumu_olay_kare": "tespit", "top_durumu_eski_sahip_son_kare": "tespit", "kutu_yuksekligi_px": {"kimden": 48.0, "kime": 51.0}, "yeni_sahip_seri_kare": 4, "homografi_durum_olay_kare": "bu karede hesaplandi"}, …}`

## 3. Hız tablosu (gerçek zamanlılık)
Kaynak: `veri_360_540/extract.log`, `kalibrasyon.log`, `hat_ilerleme.log` (aynı çalıştırma, 4 500 kare = 180 sn video, 25 FPS, 1280×720; RTX 4050 Laptop 6 GB). Yeniden çalıştırma yapılmadı. Gerçek zaman = 25 kare/sn.

| Modül | Ölçülen verim (kare/sn) | Gerçek zamana göre | Duvar süresi (4 500 kare) | Kaynak |
|---|---|---|---|---|
| Tespit + takip (`extract_v2`: YOLO+BoT-SORT 960 px, top için 640 px dilimli tespit, saha maskesi, forma rengi) | **6,2** (döngü); 6,15 (modül başlangıcı dahil) | **×0,25 → 4,0× yavaş** | 12 dk 11 sn | extract.log, hat_ilerleme.log |
| Saha kalibrasyonu, **çizgi inceltmeli** (`saha_kalibrasyon`, varsayılan `REFINE=True`) | **7,7** (döngü); 7,6 (duvar) | **×0,31 → 3,2× yavaş** | 9 dk 49 sn | kalibrasyon.log, hat_ilerleme.log |
| Saha kalibrasyonu, **inceltmesiz** (`REFINE=False`) | **ölçülmedi** | ölçülmedi | ölçülmedi | – |
| Olay tespiti (`events_v2`) | **≈2 250** (2 sn / 4 500 kare; log saniye çözünürlüklü, aralık ≈1 500–4 500) | **≈×90 (60–180×) hızlı** | ≈2 sn | hat_ilerleme.log |
| **Toplam hat (sıralı)** | **≈3,4** (1 / (1/6,2 + 1/7,7 + 1/2 250)) | **×0,14 → 7,3× yavaş** | 22 dk 02 sn (ölçülen; 13:18:32–13:40:34) | hat_ilerleme.log |

Notlar: `events_v2` süresi son iki çalıştırmada ~4 sn (7 500 kare, Python başlatma dahil, oturum çıktısı; log dosyası değil) olarak da görüldü, tutarlı. Modül içi dağılım (top dilimli tespiti, takip, forma rengi, saha maskesi) **ölçülmedi**; hangisinin baskın olduğu profil çıkarılmadan bilinmiyor. Hat çevrimdışı çalışıyor; canlı akışta kullanım için bugünkü donanımda toplam yaklaşık 7× hızlanma gerekir (kalibrasyon ve tespit modülleri ayrı GPU akışlarında paralel çalışsa teorik olarak ≈0,25×'e kadar çıkar; bu da yetmez).

### Hızlandırma önerileri (uygulanmadı; kazançlar tahmin, ölçülmedi)
1. **Top tespitini seyrelt / ROI'ye bağla** (`extract_v2`): şu an `InferenceSlicer` her karede 640×640 dilimlerle (128 px bindirme, 1280×720'de ~6 dilim) ayrı YOLO çağrısı yapıyor, ayrıca 960 px'te oyuncu takibi. Top bilinirken yalnız son konum çevresindeki bir ROI'de (örn. 640×360) tek çağrı, kayıp olunca tam dilim taraması; dilimleri tek batch'te çalıştırmak çağrı sayısını kare başına ~7'den 1–2'ye indirebilir. Öncelikle profil ile payı doğrulanmalı.
2. **Model hızlandırma**: `best.pt`'yi FP16 / TensorRT'ye (`model.export(format="engine", half=True)`) çevirmek, video okuma+ön işlemeyi ayrı iş parçacığına almak (CPU'daki saha maskesi, forma rengi ve kare okuma GPU'yu bekletiyor olabilir). Oyuncu ve top için aynı ağırlıkla iki ayrı YOLO nesnesi yerine tek model üzerinden toplu çağrı.
3. **Kalibrasyonu seyrelt** (`saha_kalibrasyon`): saha anahtar nokta modelini ve çizgi inceltmesini her karede değil her 3.–5. karede çalıştırıp aradaki karelerde homografiyi kamera hareketiyle (ECC / optik akış tabanlı kare-kare dönüşüm) güncellemek; inceltmeyi yalnız çizgi kapsaması eşiğin altına düştüğünde çağırmak. Önce `REFINE=False` süresi ölçülmeli (inceltmenin maliyeti şu an bilinmiyor).
