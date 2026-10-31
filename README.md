# MatchNarrator

Futbol maçı videosundan **pas / top kaybı** olaylarını tespit eden ve bunları yerel bir dil modeli (LLM) ile TTS kullanarak **otomatik Türkçe anlatıma** dönüştüren bir araştırma prototipi. Manisa Celal Bayar Üniversitesi Yazılım Mühendisliği kapsamında Ar-Ge projesi olarak geliştirilmektedir.

## Proje durumu

| Bileşen | Durum |
|---|---|
| Olay tespiti (pas / top kaybı) | **v2.1 donduruldu** (git etiketi `v2.1`) |
| Spiker prototipi (şablon + korumalı LLM) | **v2 hazır**; kör puanlama tablosu üretildi, puanlama henüz yapılmadı |
| TTS | Chatterbox Multilingual ile 10 cümlelik deneme yapıldı; ses kalitesi henüz dinlenip değerlendirilmedi |
| Uçtan uca demo | Sıradaki iş |
| TTS seçimi | Sıradaki iş |

## Yöntem (özet)

**Olay tespiti**
1. **Tespit:** YOLO ile oyuncu, kaleci, hakem ve top (`best.pt`; top için ayrıca 640 px dilimli tarama).
2. **Takip:** BoT-SORT.
3. **Saha koordinatı:** Saha anahtar nokta modeli (`football-pitch-detection.pt`) ile kare başına homografi; konumlar 105×68 m saha düzleminde.
4. **Takım ayrımı:** Forma rengi üzerinden K-means (SigLIP tabanlı ayrım `takim_siglip.py` ile denendi, varsayılan değil).
5. **Olay çıkarımı:** Topa **sahiplik** tabanlı: sahip değişimi aynı takımda ise PAS, takım değişiyorsa TOP KAYBI (`events_v2.py`; parametreler v2.1'de dondurulmuştur).

**Spiker**
1. Olaylardan **olgu tabanlı şablon cümleler** (`spiker_sablon_v2.py`).
2. **Korumalı LLM** (`spiker_llm_v2.py`): şablon cümlesini LLM'e yeniden ifade ettir → kurallarla doğrula (takım adı, sayılar, belirsizlik ifadesi, uzunluk, dil) → en çok 2 yeniden deneme → hâlâ geçmezse şablona dön.
3. **TTS:** Chatterbox Multilingual (`tts_chatterbox_test.py`, ayrı sanal ortamda).

## Sonuçlar

Olay tespiti, ±1 sn tolerans, birebir eşleştirme, tip aynı olmak zorunda. Aralıklar %95 bootstrap. Kaynak: `OLCUM_09_DOGRULAMA_SETI.md`, `OLCUM_11_SURUM_V2_1.md`.

| Set | Aralık | Etiket | TP | FP | FN | Precision | Recall | F1 (%95) |
|---|---|---|---|---|---|---|---|---|
| Geliştirme | 60–180 sn | 41 | 21 | 5 | 20 | 0,808 | 0,512 | 0,627 (0,49–0,76) |
| Test | 180–300 sn | 24 | 10 | 12 | 14 | 0,455 | 0,417 | 0,435 (0,24–0,59) |
| Doğrulama | 360–540 sn | 41 | 19 | 20 | 22 | 0,487 | 0,463 | 0,475 (0,33–0,60) |
| **Birleşik (3 set)** | – | 106 | 50 | 37 | 56 | 0,575 | 0,472 | **0,518 (0,43–0,60)** |

Sistem ayarları geliştirme setindeki incelemelerle şekillendi; bu yüzden geliştirme sonucu iyimserdir. Doğrulama seti sonradan incelendi (OLCUM_09–12), bu yüzden geliştirme havuzuna dahildir; yalnızca test seti (180–300 sn) ayar yapılırken kullanılmadı (baseline ölçümü dışında hiç incelenmedi). Setler arası fark, küçük etiket sayısıyla birlikte aralıkların geniş olmasına yol açıyor.

**Spiker ablation** (aynı 24 cümle slotu, 3 yerel model; `OLCUM_14_SPIKER_V2.md`). Slotlar yalnızca geliştirme ve doğrulama setlerinden alındı, test setine girilmedi.

| Model | Naif LLM ihlal (a–e) | Naif LLM ihlal (genişletilmiş) | Korumalı LLM ihlal | Korumalı: şablona dönüş |
|---|---|---|---|---|
| gemma3:4b | %17 | %96 | %0 | %4 |
| qwen3.5:4b | %17 | %100 | %0 | %25 |
| llama3.1:8b | %4 | %83 | %0 | %0 |

**Sütunlar neyi ölçüyor.** *İhlal (a–e)*, `olgu_kontrol.py`'deki beş kategoriden en az birinin ihlalidir: (a) izinli takım adları dışında ad veya "A takımı/B takımı"; (b) yasak öğe (gol, skor, dakika, hız, forma numarası, hakem, sağ/sol/ileri/geri gibi yön, bilinmeyen özel isim); (c) cümledeki sayıların olgularla ±1 uyuşmaması ya da PAS cümlesinde olgudaki takımdan başka takım; (d) 15 kelimeden uzun veya çok cümleli; (e) Türkçe olmayan. Yani uydurma içerik (skor/dakika/gol vb.) bu sütunda ayrıca sayılır. *Genişletilmiş ihlal*, (a–e)'ye üç kontrol ekler: şablonda olmayan yeni sayı, temkinli dil (hedge, "gibi/sanki/görünüyor") kaybı ve takım adı kümesinin şablondan farklı olması.

Genişletilmiş ihlalin büyük kısmı **temkinli dil kaybıdır**: 24 slotun 19'u olay veya birleşik pas cümlesidir ve naif LLM bu 19'unun **19'unda da** hedge'i düşürmüştür (üç modelde de). Uydurma içerik ise yalnızca (b) sütununa girer (yasak öğe: gemma 4, qwen 4, llama 0 slot; olgu uyumsuzluğu: llama 1 slot). Önceki 14 slotluk ölçümde (`OLCUM_13`) gemma ve qwen için görülen %57 (8/14), yalnızca bu (b) kategorisindeki yasak öğeleri sayar (hedge kaybı o tabloda "bilgi" sütunudur, ihlale dahil değildir); o örnekte uydurmanın yoğun olduğu 10 sn'lik özet slotları 14'ün 8'iydi, bu tabloda ise 24'ün yalnızca 5'i olduğundan (b) oranı %17'ye düştü.

Korumalı LLM'deki %0, doğrulayıcı ile değerlendiricinin **aynı kural kümesi** olması nedeniyle tasarım gereğidir; bağımsız bir doğruluk ölçüsü değildir. Doğruluk ve akıcılık için kör puanlama (`puanlama_kor.csv`, 60 satır) gereklidir ve henüz yapılmamıştır.

## Sınırlamalar

- **Tek maç, tek kamera** (`barca_tactical.mp4`); farklı kamera açısı veya maçlarda genelleme ölçülmedi.
- **Küçük etiket sayısı:** toplam 106 etiket, test setinde 24; güven aralıkları geniş. TOP KAYBI için etiket sayısı çok az (geliştirme 5, doğrulama 6), bu tipin sonuçları yorumlanamaz.
- **Lens bozulması modellenmiyor:** homografi düzlemsel kabul edilir, kodda mercek bozulması düzeltmesi yok.
- **Havadaki top:** top havadayken saha düzlemine izdüşüm güvenilmez; mesafe ve hız değerlerinde sapma olabilir.
- **F1 ≈ 0,5** (birleşik 0,518); ayarlar küçük iyileştirmeler getirdi ancak bunların çoğu güven aralığı dışında anlamlı değil (bkz. `OLCUM_04`, `OLCUM_08`, `OLCUM_09`, `OLCUM_12`).
- **Gerçek zamanlı değil:** tüm hat (tespit+takip → kalibrasyon → olay tespiti) yaklaşık **3,4 kare/sn**, yani gerçek zamana göre yaklaşık 7× yavaş (RTX 4050 Laptop 6 GB, 25 FPS video; `OLCUM_11` §3). LLM (≈3–5 sn) ve TTS (≈3 sn) gecikmeleri eklenince cümle başına ≈6–8 sn; TTS ve Ollama 6 GB GPU'ya aynı anda sığmıyor.
- TTS ses kalitesi (anlaşılırlık, Türkçe telaffuz) henüz değerlendirilmedi.

## Kurulum

Gereksinimler: Windows, NVIDIA GPU (geliştirme: RTX 4050 Laptop 6 GB), Python 3.12, `ffmpeg`, [Ollama](https://ollama.com).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# CUDA'lı torch (cu128) önce, sonra diğer paketler
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install ultralytics supervision opencv-python numpy pandas scipy scikit-learn lapx langdetect requests
```

Geliştirmede kullanılan sürümler: torch 2.11.0+cu128, ultralytics 8.4.175, supervision 0.30.9, opencv-python 5.0.0.93, numpy 2.5.2, pandas 3.0.6, scipy 1.18.1, scikit-learn 1.9.1, lapx 0.10.0, langdetect 1.0.9. (Repoda `requirements.txt` yok.)

Spiker için yerel modeller:

```powershell
ollama pull gemma3:4b
ollama pull qwen3.5:4b
ollama pull llama3.1:8b
```

TTS **ayrı bir sanal ortamda** çalıştırılır (ana `.venv` kullanılmaz): Python 3.12, `torch 2.6.0+cu124`, `chatterbox-tts 0.1.7`. Ollama ile aynı anda GPU kullanmamak için önce `ollama stop <model>` çalıştırın.

## Çalıştırma

Betikler proje klasöründen çalıştırılır (göreli yol kullanır). Video adı ve model yolları betiklerin başındaki ayarlarda tanımlıdır (`VIDEO = "barca_tactical.mp4"`, `best.pt`, `football-pitch-detection.pt`).

**1. Olay tespiti hattı**

```powershell
# Ana çalıştırma (betik varsayılanı: 60. sn'den 300 sn; geliştirme ve test setleri buradan)
python extract_v2.py
python saha_kalibrasyon.py
python events_v2.py

# Doğrulama seti (360–540 sn), ayrı klasöre
python extract_v2.py --start-sec 360 --duration-sec 180 --out-dir veri_360_540
python saha_kalibrasyon.py --out-dir veri_360_540
python events_v2.py --in-dir veri_360_540 --out-dir veri_360_540
```

**2. Değerlendirme** (yalnızca `--start`/`--end` aralığındaki etiket ve tahminler sayılır)

```powershell
python degerlendir.py --events events.csv --labels gercek_olaylar.csv --start 60 --end 180        # geliştirme
python degerlendir.py --events events.csv --labels gercek_olaylar_test.csv --start 180 --end 300  # test
python degerlendir.py --events veri_360_540/events.csv --labels gercek_olaylar_val.csv --start 360 --end 540  # doğrulama
```

`--diagnose` hata kategorilerini, `--compare EVENTS_CSV` iki ayarı eşleştirilmiş bootstrap ile karşılaştırır.

**3. Zengin olay çıktısı ve spiker**

```powershell
python olay_zenginlestir.py        # config_takimlar.json -> olaylar_zengin.json
python spiker_ozet.py              # 10 sn pencere özetleri -> pencere_ozet.json
python spiker_sablon_v2.py         # şablon cümleler + takvim
python spiker_llm_v2.py --models gemma3:4b qwen3.5:4b llama3.1:8b --modlar naif korumali
python ablasyon_v2.py              # ablation tablosu -> ablasyon_v2.csv
python puanlama_kor_uret.py        # kör puanlama tablosu (+ yerel anahtar dosyası)
```

TTS denemesi (`tts_venv` içinden): `python tts_chatterbox_test.py`.

Her ölçümün tarihi, yöntemi ve ham sayıları `OLCUM_*.md` raporlarındadır (01–14); `GERI_KURULUM_RAPORU.md` ortam kurulum notlarını içerir.

## Klasör yapısı

| Yol | İçerik |
|---|---|
| `extract_v2.py`, `saha_kalibrasyon.py`, `events_v2.py` | Olay tespiti hattı |
| `degerlendir.py`, `guven_kapilama.py`, `tarama_*.py`, `teshis_*.py` | Değerlendirme, tarama ve teşhis betikleri |
| `olay_zenginlestir.py`, `config_takimlar.json` | Zengin olay çıktısı, takım adları |
| `spiker_*.py`, `ablasyon_v2.py`, `puanlama_kor_uret.py` | Spiker hattı |
| `gercek_olaylar*.csv` | El ile etiketlenmiş olaylar (geliştirme / test / doğrulama) |
| `OLCUM_*.md` | Ölçüm raporları |
| `puanlama_kor.csv` | Kör puanlama tablosu (model adları gizli) |

## Repoda olmayanlar

Video ve veri telif/boyut nedeniyle repoda yoktur. Aşağıdakiler `.gitignore` ile dışarıda tutulur:

- Maç videoları (`*.mp4`) ve çıkarılan ara veriler (`veri_360_540/`, `players*.csv`, `ball_*.csv`, `homography.csv` vb.)
- Model ağırlıkları (`best.pt`, `football-pitch-detection.pt`, `*.pt`, `*.onnx`, `*.safetensors`, `*.gguf`)
- TTS ses örnekleri (`tts_ornekler/*.wav`)
- Sanal ortamlar (`.venv/`, `tts_venv/`), `__pycache__/`, `*.bak*`
- Kör puanlama anahtar dosyası (`puanlama_kor_anahtar.csv`): puanlama bitene kadar yayımlanmaz

Dolayısıyla repo tek başına klonlanıp çalıştırılamaz; hat için video ve model dosyalarının proje klasörüne ayrıca konması gerekir.

## Lisans

TODO
