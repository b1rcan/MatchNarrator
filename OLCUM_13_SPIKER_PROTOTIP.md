# OLCUM_13 — Spiker modülü ilk prototip (şablon + 3 yerel LLM)

Tarih: 2026-10-12 · Girdi: yalnız `olaylar_zengin.json` / `pencere_ozet.json` (geliştirme seti içindeki sabit pencere 1:00–2:30). Etiketlere ve test setine bakılmadı. Bu aşamada ölçülen şey cümle **üretim ve politika uyumu**; doğruluk/akıcılık insan puanına bırakıldı (`degerlendirme_tablosu.csv`).

## 1. Araçlar
| Araç | Durum |
|---|---|
| ffmpeg | winget ile kuruldu: Gyan.FFmpeg 9.0.2 (`ffmpeg -version` doğrulandı). Not: winget PATH takma adı bu kabukta görünmüyor; yürütülebilir `…\WinGet\Packages\Gyan.FFmpeg_…\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe`. |
| Ollama | **0.40.3**, `ollama --version` ve `/api/version` doğrulandı. winget indirmesi 1,58 GB'ın yaklaşık %19'unda takıldı (dosya önceden yer ayrılmış göründüğü için boyut yanıltıcıydı); winget'i durdurdum. Kurulum paketini paralel aralıklı (Range) indirmeyle sıfırdan aldım ve **SHA-256'sını Ollama'nın yayımladığı `sha256sum.txt` ile karşılaştırdım (aynı: `ab81db6c…8c80`)**, sonra sessiz kurdum. Yani Ollama winget ile değil doğrulanmış doğrudan paketle kuruldu. |
| GPU | RTX 4050 Laptop 6 GB (sürücü 617.42). `ollama ps`: gemma3:4b ve qwen3.5:4b **%100 GPU**, llama3.1:8b **%22 CPU / %78 GPU** (5,3 GB, 6 GB kartta tam sığmadı, kısmi CPU'ya taştı). |
| langdetect | 1.0.9 (venv'e kuruldu) |

## 2. Model seçimi (Ollama kütüphanesi taraması, 12 GB sınırı)
| Aday | Ollama etiketi | İndirme | Gerekçe |
|---|---|---|---|
| Gemma 3 4B | `gemma3:4b` | 3,4 GB | Google; çok dilli (Türkçe dahil), 6 GB'a rahat sığıyor. |
| Qwen 3.5 4B | `qwen3.5:4b` | 3,3 GB | Qwen'in güncel serisi; çok dilli. Düşünme modu kapatıldı (`think:false`). |
| Llama 3.1 8B | `llama3.1:8b` | 4,9 GB | Llama ailesinin en büyük küçük modeli; resmen desteklenen diller arasında Türkçe yok (zayıf Türkçe beklentisi). 6 GB'a tam sığmıyor. |
Toplam diskte 11 059 MiB (~11,6 GB). Elenenler: `gemma4:e4b` (6,6 GB) ve `qwen3.5:9b` (6,6 GB) 6 GB VRAM'e tam sığmaz; `llama3.2:3b` Türkçe için daha zayıf. Kütüphane sayfasındaki boyutlar çekilen boyutlarla uyumlu (`ollama list`).

## 3. Takvim ve çıktılar
- `spiker_ozet.py` → `pencere_ozet.json`: 48 pencere (60–360 ve 360–540 sn, 10 sn). Takım adları `config_takimlar.json`'dan; sahiplik = possession.csv kare oranı (yalnız sahibi bilinen/takımlı karelerden; fark < 10 puan "dengeli").
- `spiker_ortak.py`: **tüm üreticiler için aynı takvim** (14 cümle slotu: 6 olay + 8 pencere özeti): önce TOP KAYBI, sonra 10 sn özetleri, sonra PAS, iki cümle ≥ 4 sn arayla. 1:00–2:30'daki 23 olaydan 17'si aralık kuralı nedeniyle tekil cümle almadı (özetlerde yer alıyor). Olgu alanları: tip, takım adları, yuvarlak mesafe, nötr bölge metni (iz no, hız, ham konum verilmedi).
- `spiker_sablon.py` → `spiker_sablon.json` (id, zaman, metin, kaynak_olay_ids): her olay tipi için 5 şablon, özet için 7; "…gibi görünüyor" ile temkinli; ≤ 15 kelime.
- `spiker_llm.py` → `spiker_llm.json` (+ model, süre, token): sıcaklık 0,3, seed 42, aynı istem, Ollama REST.
- `olgu_kontrol.py` → `olgu_kontrol_detay.csv`, `ihlal_tablosu.csv`; `degerlendirme_tablosu.csv` (UTF-8 BOM, 14 satır; her cümle için boş `dogru_mu (e/h)` ve `akicilik (1-5)` sütunları).

## 4. Otomatik olgu kontrolü (14 cümle / üretici)
| Üretici | (a) takım adı ihlali | (b) yasak öğe | (c) olgu uyumsuzluğu | (d) >15 kelime / çok cümle | (e) Türkçe değil | **Herhangi ihlal** | Temkinli ifade yok (6 tekil olaydan) | Ort. kelime |
|---|---|---|---|---|---|---|---|---|
| Şablon | 0 (%0) | 0 (%0) | 0 (%0) | 0 (%0) | 0 (%0) | **0 / 14 (%0)** | 0 | 8,6 |
| gemma3:4b | 0 | **8 (%57)** | 0 | 0 | 0 | **8 / 14 (%57)** | 6 | 8,8 |
| qwen3.5:4b | 0 | **8 (%57)** | 0 | 1 (%7) | 0 | **8 / 14 (%57)** | 6 | 11,9 |
| llama3.1:8b | 0 | 0 | 0 | 0 | 0 | **0 / 14 (%0)** | 6 | 6,9 |

- **gemma3:4b**: 8 cümlede **skor uydurması** ("Espanyol'u 3-0 mağlup etti", "4-0'lık skorla…" — özet penceresinde pas sayısı ve sahiplik yüzdesi verildi, skor verilmedi). Tamamı yasak skor kalıbı.
- **qwen3.5:4b**: 8 cümlede yasak: skor kalıbı (3), "dakika" (6 cümlede "10. dakikada", yanlışlıkla pencere süresini dakika sanıyor), "gol attı" (1); ayrıca 1 cümle çok uzun.
- **llama3.1:8b**: otomatik kontrolden ihlal çıkmadı, ama cümleleri kısa ve bazıları anlamsız ("Barcelona 97'si sahipliği payına sahiptir", "Barcelona 98'ini sahipliğinde tutuyor"); otomatik kontrol bunu yakalamıyor → **insan puanı gerekli**.
- Tüm modeller tekil olay cümlelerinde istenen temkinli dili **kullanmadı** (6/6); yalnız şablon "gibi görünüyor" diyor.
- Takım adı ve sayı uyumu (a, c) hiçbir üreticide ihlal çıkarmadı; ama (c) yalnız sayıları karşılaştırıyor, TOP KAYBI rol tutarlılığı yaklaşık sezgisel (ilk anılan takım, "kaybet/kazan" ile eşleşme); anlamsal doğruluk kontrol edilmedi.
- Kontrol sınırları: (e) langdetect ile (güven ≥ 0,8 ve dil ≠ tr ihlal; kısa cümlede belirsiz tahminler ihlal sayılmaz, ilk sürümde şablonun bir cümlesi yanlış pozitifti ve düzeltildi); "bilinmeyen özel isim" yalnızca cümle içi büyük harfli sözcüklere bakar.

## 5. Üretim süresi ve VRAM (aynı 14 cümle, num_ctx 2048)
| Model | İlk çağrı (yükleme dahil) | Cümle başına ort. / maks (sn) | Ort. üretilen token | VRAM tepe (nvidia-smi, toplam kullanılan) | İşlemci dağılımı |
|---|---|---|---|---|---|
| gemma3:4b | 29,1 sn | **2,75** / 2,86 | 18,7 | 3 693 MiB | %100 GPU |
| qwen3.5:4b | 48,9 sn | **2,97** / 3,33 | 25,5 | 3 673 MiB | %100 GPU |
| llama3.1:8b | 19,2 sn | **3,13** / 3,61 | 17,2 | 4 055 MiB | %22 CPU / %78 GPU |
| Şablon | – | ≈ 0 | – | – | CPU |

Süreler uzun sistem isteminin işlenmesini içerir (istem başına ~2–3 sn). Boşta VRAM 0 MiB; VRAM değeri tüm GPU kullanımıdır (başka süreç yoktu). Cümle başına ~3 sn, spiker için 4 sn'lik cümle aralığında yetişiyor ama gerçek zamanlı akışta olay gecikmesine ek olarak ~3 sn ekler.

## 6. Notlar ve sınırlar
- Örnek küçük (14 cümle slotu, 1:00–2:30); yüzdeler 1 cümle = %7,1 granülaritesinde.
- Pencere özeti sahiplik yüzdeleri yalnız topun sahibi bilinen karelerden hesaplanır (60–180 sn aralığında topun sahibi kurulan kare oranı ≈ %38, OLCUM_08); "yüzde 97 sahiplik" ifadesi bu nedenle fazla kesin olabilir.
- Hiçbir cümle oyuncu ismi, forma numarası, hız içermiyor (kelime listesi ve kontrol ile doğrulandı); LLM cümlelerinde skor/dakika/gol uydurması görüldü.
- İnsan puanlaması (`degerlendirme_tablosu.csv`) bekleniyor.
