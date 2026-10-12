# OLCUM_05 — SigLIP ile takım ataması

Tarih: 2026-10-12 · Varsayılan davranış değişmedi (`teams.csv`, `events_v2.py` varsayılanı). Karşılaştırma yalnız geliştirme seti (60–180 sn); test seti (180–300) kullanılmadı.

## 1. Yöntem (`takim_siglip.py`)
- İz başına en fazla 12 rastgele kare (seed 0), kırpım = kutunun üst %60'ı, tüm sınıflar (oyuncu / kaleci / hakem-sınıflı). 12 393 kırpım (oyuncu 8 815, kaleci 121, hakem-sınıflı 3 457), 2 590 iz.
- **Sapma:** yükseklik eşiği 40 px yerine **25 px**. Kutu yüksekliği medyanı 35 px; ≥40 px yalnız 1 096 iz bırakıyor (eski `teams.csv` izlerinin 1 070/2 502'si = %43), ≥25 px ile 2 486/2 502 (%99). Eşik `--min-h` ile değişir. Küçük kırpımlar 224'e büyütüldüğü için gömülümler daha gürültülü olabilir.
- Model: `google/siglip-base-patch16-224` (yalnız görüntü kolu, son katman ortalaması, GPU fp16). Kurulanlar: transformers 5.19.0, umap-learn 0.5.12.
- UMAP(3) + KMeans, kırpım düzeyinde, seed 0. Kaleci kırpımları fit'e girmedi (`umap.transform` + `kmeans.predict`), `rol=gk` işaretli. İz kararı = çoğunluk oyu; `oy_orani`, `kume_mesafesi` (izin kırpımlarının UMAP uzayında merkeze ort. uzaklığı) kaydedildi. Küme numaraları eski `teams.csv` ile en çok örtüşecek şekilde hizalandı.
- Çıktılar: `teams_siglip.csv` (K=2, ana), `teams_siglip_k3.csv`, sütunlar `track_id, team, oy_orani, kume_mesafesi, rol, n_kirpim`.

## 2. Kümeler ve görsel doğrulama
Kontak sayfaları (kume başına 40 rastgele kırpım, etiket = sınıf harfi P/G/R + iz no):
- `C:\Users\gorur\Desktop\futbol-ai-tez\kume_0.png`
- `C:\Users\gorur\Desktop\futbol-ai-tez\kume_1.png`
- K=3 karşılaştırması: `kume_k3_0.png`, `kume_k3_1.png`, `kume_k3_2.png` (aynı klasör)

Benim bakışım (sen de bak; kesin değil): **kume_1** tamamen sarı formalı oyuncular, çok temiz. **kume_0** lacivert-bordo (Barça) oyuncuları + gürültü: seyirci, pembe formalı hakem/yan hakem, turuncu yelekli görevli, bir açık mavi kaleci, birkaç sarı+Barça çakışan kırpım. İç içe oyuncu kırpımları (komşu oyuncu kutuya giriyor) hata kaynağı.

| K | Küme | Kırpım | İz: oyuncu | hakem-sınıflı | gk |
|---|---|---|---|---|---|
| 2 | 0 | 4 957 | 570 | 108 | 21 |
| 2 | 1 | 7 436 | 1 032 | 853 | 6 |
| 3 | 0 | 4 420 | 500 | 105 | 21 |
| 3 | 1 | 7 463 | 1 037 | 854 | 6 |
| 3 | 2 | 510 | 65 | 2 | 0 |

**K=3 gerçek hakemi ayırmıyor:** 3. küme turuncu yelekli görevliler ve seyirci kırpımlarını topluyor (hakem-sınıflı yalnız 2 iz), pembe hakem Barça kümesinde (kume_0) kalıyor. K=2 ile devam edilmesi daha mantıklı; hakem ayrımı için `kume_mesafesi` daha iyi (aşağıda).

**Eski K-means ile fark:** ortak 2 486 izde **108 iz farklı** (%4,3): 92 oyuncu-sınıflı, 16 hakem-sınıflı; 78'inde oy oranı ≥0,9. Farklı izlerin medyan uzunluğu 5 kare (toplam 8 824 / 175 498 kare, %5). 60–180 sn sahiplik izlerinden yalnız 3'ü farklı (421, 540, 562). Eski dağılım A/B = 510/1 992; SigLIP (ortak oyuncu izleri) 604/1 882. Eski teams.csv'de olup SigLIP'te olmayan 16 iz (25 px üstü kırpımı yok) için eski takım korunuyor.

## 3. `events_v2.py --teams` ve hakem kuralı
- Seçenek eklendi (`--teams teams_siglip.csv`); verilmezse eski davranış. Doğrulama: varsayılan çalıştırma `tarama/baseline` ile `events/teams/possession/ball_track/events_adaylar` dosyalarında bayt bayt aynı. Yedek `events_v2.py.bak3_20261012`.
- Davranış: hakem düzeltmesi (REF_KEEP_RATIO, MAX_REF_CONCURRENT) ve sınıf kararları **eskisi gibi** (renk tabanlı) çalışır; yalnız oyuncu sayılan izlerin takımı SigLIP'ten gelir. `rol=gk` izleri eskisi gibi takımsız kalır.
- Etkileşim incelemesi (972 hakem-sınıflı iz): eski kural 890'ını oyuncuya çeviriyor, 82'sini hakem bırakıyor.

| Grup | İz | SigLIP kümesi 0 / 1 | oy ≥0,9 | medyan `kume_mesafesi` | medyan kare |
|---|---|---|---|---|---|
| Eski kuralla oyuncuya çevrilen | 884 | 34 / 850 | 864 | 1,90 | 2 |
| Eski kuralla hakem kalan | 77 | 74 / 3 | 76 | 3,90 | 3 |
| (referans: oyuncu-sınıflı iz) | – | – | – | 1,88 (p90 3,63) | – |

  - Çevrilenlerin 868/884'ünde eski K-means takımı SigLIP ile aynı → renk tabanlı çevirme SigLIP'le tutarlı, çoğu (850) sarı takım.
  - Kalan "hakem" izlerinin 74'ü kume_0'a (pembe hakem + Barça) düşüyor; en uzun 14 kalan hakem izinin (≥25 kare) 12'sinde `kume_mesafesi` 7,4–8,4 (oyuncu p90'ı 3,6): gerçek hakemler küme merkezinden çok uzak. **Yani hakemi ayıran özellik takım oyu değil, `kume_mesafesi`.**
  - Dikkat: 476 numaralı iz (OLCUM_01–04'te hakem karışması olarak işaretlediğim) SigLIP'te oyuncu gibi (B, oy 1,0, mesafe 2,25). Bu iz için "hakem" teşhisim kesin değil.
- **Öneri (UYGULANMADI, onayını bekliyor):** "hakem-sınıflı iz, SigLIP'te `oy_orani ≥ 0,9` ve `kume_mesafesi ≤ 3,5` ise oyuncu say; aksi halde hakem". Bu kural eski kuralla karşılaştırıldığında 884 çevrilenin 841'ini oyuncu tutar (43'ü hakeme döner), 77 kalan hakemin 34'ünü oyuncuya çevirir; 34'ün çoğu kısa izler, ama doğrulayacak referans yok. Önce kontak sayfalarıyla (R-izleri) bu 34+43 izin örneği görülmeli; eşik 3,5 kabaca oyuncu p90'ı, ayarlanabilir.

## 4. Karşılaştırma (60–180 sn, ±1 sn)
| | Eski (K-means) | SigLIP K=2 |
|---|---|---|
| TP / FP / FN | 21 / 5 / 20 | 21 / 6 / 20 |
| Precision / Recall | 0,808 / 0,512 | 0,778 / 0,512 |
| F1 genel (%95) | 0,627 (0,49–0,76) | 0,618 (0,48–0,75) |
| F1 PAS | 0,678 (0,53–0,80) | 0,667 (0,52–0,79) |
| F1 TOP KAYBI | 0,250 (0,00–0,60) | 0,250 (0,00–0,60) |
| Zaman farkı medyan / std | −0,08 / 0,35 | aynı |

- Düzelen (FN→TP): **yok**. Bozulan: TP→FN **yok**; yeni FP **1** (1:15.00 PAS). Düzelen − bozulan = **−1** → kabul kuralı (≥ +2) geçilmedi: **önerilmez**.
- TOP KAYBI etiketleri: 1:11.64 FN, 1:22.40 TP, 1:56.48 FN, 1:58.76 FN, 2:55.40 FN — **iki yöntemde de aynı**. TOP KAYBI tahminleri: 1:16.28 (392→505 | SigLIP: 540→505, yalnız kimden değişti), 1:21.00 (476→597), 1:22.84 (768→843): ikisinde de aynı üçlü, FP'ler yerinde.
- "Yanlış takım" hataları (1:56.48, 1:58.76, 2:55.40 FN; 1:58.72 FP) değişmedi. İlgili izlerin SigLIP takımları eskisiyle aynı: 601, 12, 1304 → hepsi takım 0; 3839, 3894 → hepsi takım 1.

## 5. Yorum
- Bu hatalar iz düzeyinde takım etiketinin yanlışlığından değil, **iz içinde takım karışmasından / kirli kırpımlardan** geliyor olabilir. Kanıt: 60–180 sn sahiplik izlerinin 42'sinden 13'ünde `oy_orani < 0,9`, 8'inde < 0,75; düşük oylular tam hata anlarındaki izler: 12 (0,58), 3839 (0,58), 3894 (0,67), 450 (0,58), 3325 (0,50), 597 (0,58), 392 (0,75). Çoğunluk oyu bu izlerde kararsız; iz kimliği (ID) iki takım arasında kayıyor veya düello kırpımında komşu oyuncu giriyor olabilir. Bu bir hipotez; kırpım düzeyi etiketler kaydedilmediği için doğrudan doğrulanmadı.
- Sonraki adım adayı (uygulanmadı): olay anında **zaman-yerel takım** (iz ID'si yerine olay çevresindeki kırpımlar), daha dar kırpım (üst %60 yerine gövde merkezi), ya da `oy_orani` düşük izleri "takım belirsiz" bırakmak.
- SigLIP takım ayrımında eskisinden anlamlı bir olay kazancı vermedi (−1); ek maliyet: ~5 dk, 1 GB model. Hakem ayrımında `kume_mesafesi` umut verici ama olay metriğine etkisi henüz ölçülmedi.
