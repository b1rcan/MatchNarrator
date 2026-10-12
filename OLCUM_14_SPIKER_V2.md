# OLCUM_14 — Spiker v2: korumalı LLM, ablation, kör puanlama tablosu, takvim, TTS keşfi

Tarih: 2026-10-12 · Test seti (180–300 sn), etiket dosyaları ve dondurulmuş v2.1 parametrelerine dokunulmadı; mevcut dosyaların üzerine yazılmadı (hepsi `*_v2` adlı yeni dosya). Girdi yalnız olay çıktıları (`olaylar_zengin.json`, `pencere_ozet.json`). Push yok.

## Dosyalar (yeni)
`spiker_ortak_v2.py` (takvim) · `spiker_sablon_v2.py` → `spiker_sablon_v2.json`, `spiker_girdi_v2.json` · `spiker_llm_v2.py` → `spiker_llm_naif_v2.json`, `spiker_llm_korumali_v2.json`, `spiker_llm_v2_meta.json` · `ablasyon_v2.py` → `ablasyon_v2.csv` · `puanlama_kor_uret.py` → `puanlama_kor.csv`, `puanlama_kor_anahtar.csv` · `tts_chatterbox_test.py` → `tts_ornekler/*.wav`, `tts_olcum.json`.

## Görev 4 — Takvim (4 sn kuralı)
**Sorun:** v1 takvimi soldan sağa açgözlü yerleştiriyordu; 1:00–2:30'daki 23 olayın yalnız 6'sı tekil cümle aldı (kapsama %26; 8 pencere özeti dışarıda).
**Uygulanan kural (`spiker_ortak_v2.py`):** olaylar 4 sn'lik kovalara ayrılır (kova ilk olayda başlar, `[s, s+4)` olayları toplar). Kova başına tek cümle: kovada TOP KAYBI varsa en güvenilir TOP KAYBI (top `tespit`, sonra yeni sahip serisi uzun); yalnız PAS ise aynı takımdan ≥ 2 pas **tek birleşik cümle** ("N pas"), tek pas tekil, farklı takımların PAS'larında en güvenilir olan. Cümleler ≥ 4 sn arayla (gerekirse cümle geciktirilir; ort. gecikme 0,6 sn, en çok 2,0 sn). 10 sn özetleri boş kalan uygun ana konur. Kapsama = bir cümlenin (tekil ya da birleşik) temsil ettiği olay / toplam olay.

| Karşılaştırma | Olay | Olay cümlesi (tekil+birleşik) | Özet cümlesi | Temsil edilen olay | **Kapsama** | Olay başına cümle |
|---|---|---|---|---|---|---|
| ESKİ, 1:00–2:30 | 23 | 6 | 8 | 6 | **%26** | 0,26 |
| YENİ, aynı pencere (1:00–2:30) | 23 | 12 (7 birleşik) | 1 | 20 | **%87** | 0,52 |
| YENİ, 1:00–3:00 (geliştirme seti) | 26 | 15 | 3 | 23 | %88 | 0,58 |
| YENİ, kullanılan: 1:00–3:00 + 6:00–7:00 (doğrulama setinin ilk dk.) | 34 | 19 (8 birleşik) | 5 | 28 | %82 | 0,56 |

Anılmayan olaylar: aynı 4 sn kovada TOP KAYBI varken PAS'lar, ve bir kovada ikinci TOP KAYBI (kullanılan takvimde 4 PAS + 2 TOP KAYBI anılmadı; 6 TOP KAYBI'nın 4'ü anılıyor). 20 slot hedefi için 1:00–2:30 yetmedi (13 slot); 3:00'a kadar uzatınca 18, doğrulama setinin ilk dakikası eklenince **24 slot**. Test setine (180+) girilmedi. v1 dosyaları (`spiker_ortak.py`, `spiker_sablon.json`) değişmedi.

## Görev 1 — Korumalı LLM (`spiker_llm_v2.py`)
Akış: şablon cümlesi (olgu kaynağı) → LLM yeniden ifade → doğrula → en çok 2 yeniden deneme (sıcaklık 0,3 → 0,2 → 0,1, seed 42) → hâlâ geçmezse şablona dön ve logla. Prompt: rol + 6 kural + **5 few-shot** (hedge ve takım adları korunuyor) + "yalnız cümleyi döndür". Doğrulama: `olgu_kontrol.py` (takım adı, yasak öğe, olgu uyumu, uzunluk, dil) + ek: (a) çıktıdaki her sayı şablonda/olgularda bulunmalı, (b) tekil olay ve birleşik pas cümlelerinde hedge korunmalı, (c) takım adı kümesi şablonla aynı, ≤ 15 kelime, tek cümle. Modeller sırayla çalıştırıldı, her modelden sonra `ollama stop`. Slot başına kayıt: `{model, deneme_sayisi, geri_donus, ihlal_turleri (deneme başına), denemeler, sure_sn}` → `spiker_llm_korumali_v2.json`.

## Görev 2 — Ablation (aynı 24 slot)
K1 = naif LLM (OLCUM_13'teki istem, ham olgudan cümle), K2 = korumalı LLM (nihai çıktı), K3 = yalnız şablon.

| Koşul | Model | Slot | İhlal (a–e) | İhlal (genişletilmiş*) | Yeniden deneme | Şablona dönüş | Şablonla aynı cümle | Ort. süre (sn/slot) | TTR | Ort. cümle uzunluğu (kelime) |
|---|---|---|---|---|---|---|---|---|---|---|
| K3 yalnız şablon | – | 24 | 0% | 0% | 0% | 0% | 100% | 0,00 | 0,34 | 8,1 |
| K1 naif LLM | gemma3:4b | 24 | 17% | 96% | – | – | 0% | 2,74 | 0,24 | 8,2 |
| K2 korumalı LLM | gemma3:4b | 24 | 0% | 0% | 4% | 4% | 25% | 3,04 | 0,33 | 8,7 |
| K1 naif LLM | qwen3.5:4b | 24 | 17% | 100% | – | – | 0% | 2,84 | 0,31 | 9,2 |
| K2 korumalı LLM | qwen3.5:4b | 24 | 0% | 0% | 25% | 25% | 25% | 4,76 | 0,33 | 8,3 |
| K1 naif LLM | llama3.1:8b | 24 | 4% | 83% | – | – | 0% | 3,13 | 0,32 | 7,4 |
| K2 korumalı LLM | llama3.1:8b | 24 | 0% | 0% | 0% | 0% | 8% | 3,31 | 0,34 | 8,6 |

*Genişletilmiş ihlal = a–e + yeni sayı + hedge kaybı + takım adı kümesi değişimi. TTR = tür/sözcük oranı (aynı slot sayısında karşılaştırılabilir). K2'de "yeniden deneme" = ilk denemede ihlal oranı.

Ayrıntılar:
- **K1 ihlal türleri (24 slot):** hedge kaybı 19/19 olay ve birleşik pas cümlesinde **(her üç modelde %100)**; takım adı kümesi değişimi 5/7/5; yasak öğe (skor, "dakika", gol) 4/4/0; olgu uyumsuzluğu 0/0/1. OLCUM_13'ün 14 slotundaki naif oranlar (a–e: gemma %57, qwen %57, llama %0) bu takvimde düşük çıktı, çünkü uydurmanın yoğun olduğu 10 sn özetleri 24 slotun yalnız 5'i (öncekinde 8/14).
- **K2 ilk deneme ihlali:** gemma 1/24 (olgu+yeni sayı), qwen 6/24 (hepsi hedge kaybı), llama 0/24. Yeniden denemeler **işe yaramadı**: gemma'nın 1 ve qwen'in 6 slotu 3 denemede de aynı ihlali yaptı ve şablona döndü (qwen'in "…gibi." ile biten kısa cümlelerinde hedge'i hep atıyor).
- **K2 çeşitlilik:** şablonla aynı cümle oranı gemma %25, qwen %25, llama %8 (geri dönüşler + birebir kopyalar). Few-shot örneklerinin kalıpları ("…oyunu sürdürmüş", "…Barcelona'da kalmış") modellerde tekrarlanıyor; TTR şablonla aynı düzeyde (0,33–0,34), K1'den yüksek (naif LLM'in kendi içinde tekrarı daha çok: gemma 0,24).
- **K2 nihai ihlal %0'ın anlamı:** doğrulayıcı ile değerlendirici aynı kural kümesi olduğu için bu **tasarım gereği**dir; bağımsız bir doğruluk ölçüsü değildir. Gözle görülen sorunlar (dilbilgisi, anlam kayması: "Bu bölümden top…", "ele geçirmiş" vb.) otomatik kontrolden geçti → **kör puanlama şart**.
- **Süre/VRAM:** K2 slot başına gemma 3,04 sn, qwen 4,76 sn (yeniden denemeler), llama 3,31 sn; VRAM tepe 3 697 / 3 675 / 4 071 MiB (llama %22 CPU'ya taşıyor). Yükleme 9–19 sn.

## Görev 3 — Kör puanlama tablosu
- **`puanlama_kor.csv`**: **60 satır** (20 slot × [şablon + 3 model], birebir aynı cümleler tek satırda birleştirildi: 20 birleşme), sütunlar `id, slot_bilgisi, cumle, dogruluk (e/h), akicilik (1-5)`; satır sırası sabit tohumla tamamen karıştırıldı, model adı yok (kontrol edildi). UTF-8 BOM.
- **`puanlama_kor_anahtar.csv`**: `id → slot_id, uretici(ler)` (ör. `sablon+qwen3.5:4b`). Puanlamadan önce açma.
- Slotlar 24'ten sabit tohumla (7) seçildi: 7 birleşik pas, 10 tekil olay, 3 pencere özeti. Modellerin şablona döndüğü ya da birebir kopyaladığı cümleler şablon satırında birleşir (anahtarda hepsi yazılı).
- **Tahmini puanlama süresi:** satır başına 20–30 sn → **≈ 20–30 dk**.

## Görev 5 — TTS keşfi
### Voicebox
- Gereksinimler (docs.voicebox.sh, v0.5.0, 25 Nisan 2026): Windows 10+, ≥ 8 GB RAM, ≥ 5 GB disk (öneri 16 GB RAM, CUDA GPU, 10+ GB disk); kurulum paketi `Voicebox_0.5.0_x64-setup.exe` (517 MB, GitHub sürüm özeti ile SHA-256 doğrulandı) ya da `.msi`; CUDA arka ucu ayrı arşivler (`voicebox-server-cuda.tar.gz` 987 MB + `cuda-libs-cu128` 2,0 GB); TTS ağırlıkları motor ilk kullanıldığında iner (350 MB–8 GB; Chatterbox motoru dahil). REST API: `http://localhost:17493` (`/docs` etkileşimli), `POST /generate` (`text`, `profile_id`, `language`, `engine`), yanıt JSON (`generation_id`, `status`), ses `GET /generations/{id}/audio`. **Bu şemalar topluluk kaynaklarından**; canlı çalışan sürümde doğrulanmadı.
- **Kurulamadı:** sessiz kurulum (`/S`) komutu yönetici izni bekleyerek takıldı (süreç ~7 dk dosya yazmadı, kullanıcı etkileşimi gerektiren bir izin penceresi varsayımı; doğrulayamadım) ve sonlandırıldı. Uygulama tabanlı yol bu oturumda denenmedi; ana sistem etkilenmedi (hiçbir şey kurulmadı). Alternatif olarak doğrudan Chatterbox kullanıldı (aşağıda).

### Chatterbox Multilingual (doğrudan, ayrı venv)
- Ayrı venv: `C:\Users\gorur\tts_venv` (Python 3.12, torch 2.6.0+cu124, `chatterbox-tts` 0.1.7; yaklaşık 5,4 GB); ana `.venv` dokunulmadı. Model ağırlıkları `ResembleAI/chatterbox` ≈ 3,1 GB (HF önbelleği). Ollama modelleri o sırada yüklü değildi (sırayla çalışma).
- 10 benzersiz şablon cümlesi, `language_id="tr"`, seed 42, varsayılan ses. Ses dosyaları: `tts_ornekler/cumle_01_v01.wav … cumle_10_v11.wav` (24 kHz).

| Ölçüt | Değer |
|---|---|
| Model yükleme (ilk çalıştırma: ağırlık indirmesi dahil) | 151,7 sn |
| VRAM, model yüklü / tepe (nvidia-smi toplam) | 3 181 MiB / 3 587 MiB (torch tepe ayrılan 3 248 MiB); boşta 0 |
| İlk cümle (ısınma) | 14,95 sn |
| Sonraki 9 cümle, ort. üretim süresi | **2,94 sn** (2,2–4,1 sn) |
| Ort. ses süresi | 3,72 sn (2,8–5,4 sn) |
| Gerçek zaman çarpanı (üretim sn / ses sn) | 0,75–0,91 (ısınma hariç ≈ 0,8): üretim sesten **hızlı** ama cümle başına ≈ 3 sn gecikme |

- **Değerlendirilemedi:** sesin anlaşılırlığı, Türkçe telaffuz kalitesi ve doğallığı dinlenmedi (ben dinleyemiyorum); `tts_ornekler/` klasörünü sen dinlemelisin.
- Spiker hattı için toplam gecikme: LLM yeniden ifade ≈ 3–5 sn + TTS ≈ 3 sn ⇒ cümle başına ≈ 6–8 sn (canlı akışta olaydan ≈ 7–9 sn sonra); 4 sn'lik cümle aralığıyla birlikte düşünülürse gerçek zamanlı için ciddi gecikme/kuyruk sorunu var. GPU'da TTS (≈ 3,2–3,6 GB) ve Ollama (3,7–4,1 GB) aynı anda 6 GB'a sığmaz, sırayla çalışmak zorunda.
- Alternatifler (denenmedi): `edge-tts` (bulut, ağ gerektirir), `piper` (yerel, tr modeli var, CPU'da hızlı, kalite daha düşük), Voicebox içindeki diğer motorlar.

## Sınırlar
- 24 slot; kör puanlama henüz yapılmadı (doğruluk/akıcılık bilinmiyor); K2'nin %0 ihlali doğrulayıcıyla aynı kural kümesi olduğundan bağımsız değil.
- Birleşik pas cümleleri ("N pas") olay sayısına bağlı; birleşik slotlar ölçüm hatalarını da sayıya taşır (olay sayısı doğru kabul edilir).
- TTS ses kalitesi dinlenmedi; Voicebox uygulaması denenemedi.
