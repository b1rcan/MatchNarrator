# Geri Kurulum Raporu

Tarih: 2026-10-12

## Denetim bulguları
- Format sonrası kullanıcı adı `grrna` -> `gorur`. Proje: `C:\Users\gorur\Desktop\futbol-ai-tez`.
- Proje dosyalarının tamamı duruyor (modeller, videolar, v2 betikler, ara CSV'ler). Betik/CSV/meta.json içinde `grrna` yolu YOK (`meta.json` göreli yol kullanıyor); eski yolu içeren tek yer önceki not/promptlardı, artık `C:\Users\gorur\...` geçerli.
- Kayıp: Python, venv, paketler (yeniden kuruldu).
- `gercek_olaylar.csv` boş (yalnızca `zaman,tip` başlığı), yedeği yok; dokunulmadı.
- Ara CSV zaman sırası tutarlı (extract_v2 -> kalibrasyon -> events_v2); tam hat yeniden çalıştırılmadı.

## Kurulum sürümleri
| Bileşen | Sürüm |
|---|---|
| Python | 3.12.10 (winget, kullanıcı kapsamı) |
| venv | `.\.venv` (proje içi) |
| torch / torchvision | 2.11.0+cu128 / 0.26.0+cu128 |
| CUDA (sürücü) | 617.42, CUDA UMD 13.4; GPU: RTX 4050 Laptop 6 GB |
| ultralytics | 8.4.175 |
| opencv-python | 5.0.0.93 (headless YOK, GUI: WIN32UI) |
| supervision | 0.30.9 |
| numpy / pandas / scipy / scikit-learn | 2.5.2 / 3.0.6 / 1.18.1 / 1.9.1 |
| SoccerNet / gdown / lapx | 0.2.0 / 6.4.2 / 0.10.0 |

## Doğrulamalar
- `torch.cuda.is_available()` = True (ultralytics kurulumundan sonra da).
- Tüm `.py` dosyaları `py_compile` ile geçti.
- best.pt: `{0 player, 1 goalkeeper, 2 referee, 3 ball}`, GPU'da (cuda:0) tespit çalışıyor.
- football-pitch-detection.pt: pose modeli, çıktı (1, 32, 2).
- Videolar: barca_tactical 25 FPS 1280x720 72505 kare; kisa_klip 30 FPS 1920x1080 2700; mac2 30 FPS 1920x1080 51143; mac_klip 25 FPS 640x360 893.
- `saha_test.py`: 4 karede 13-15 nokta, hata 0.46-0.54 m, çizgi kapsaması %9-27 -> %42-58.

## Notlar / açık işler
- Bu terminal oturumunda `where python` hâlâ Store alias'ını (`WindowsApps\python.exe`) gösteriyor; gerçek kurulum `%LOCALAPPDATA%\Programs\Python\Python312`. Yeni terminal açınca düzelmezse: Ayarlar > Uygulamalar > Gelişmiş uygulama ayarları > Uygulama yürütme diğer adları > python.exe / python3.exe kapat. Betikler için `.\.venv\Scripts\Activate.ps1` kullanılır.
- `etiketleme.py` sessiz kapanma nedeni: `VIDEO` göreli yol; betik proje klasörü dışından çalıştırılınca `VideoCapture` açılmıyor, `frame is None` ile döngü sessizce kırılıyor ve "0 etiket" yazılıyor. imshow/waitKey ve GUI backend sağlam. Düzeltme önerisi diff olarak sunuldu, henüz uygulanmadı.
