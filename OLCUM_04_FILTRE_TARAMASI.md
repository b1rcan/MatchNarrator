# OLCUM_04 — Filtre log'u ve tek-parametre taraması (yalnız geliştirme seti)

Tarih: 2026-10-12 · Aralık 60–180 sn, ±1 sn, `EVENT_TIME_ANCHOR = "receiver_start"`. Test seti (180–300) kullanılmadı. Hiçbir değişiklik `events_v2.py`'ye kalıcı parametre olarak uygulanmadı (varsayılanlar aynı).

## 1. Kod değişikliği (davranış korunarak)
- `events_v2.py`: (a) her sahiplik-değişimi adayı için `events_adaylar.csv` (zaman, tip, kimden, kime, alıcı kare, boşluk, mesafe, hız, karar, neden); (b) `--set PARAM=DEĞER` (tekrarlanabilir); (c) `--out-dir`. Yedek: `events_v2.py.bak2_20261012`.
- Doğrulama: parametresiz çalıştırınca `events.csv` önceki dosyayla bayt bayt aynı.
- Red nedenleri: `bosluk_buyuk`, `ayni_oyuncu`, `ayni_kisi_id_degisimi`, `kisa_alim`, `kisa_kayip`, `imkansiz_hiz`, `min_mesafe` (bu sette hiç tetiklenmedi).
- Yeni betikler: `tarama_filtre.py` (tarama, çıktılar `tarama/`), `red_analizi.py`.
- Kapsam dışı: `MIN_POSS_FRAMES` altındaki seri düzeyi filtre (adaydan önce) loglanmıyor.

## 2. Tek parametre taraması
Her satırda yalnız o parametre değişti. Düzelen = FN→TP; bozulan = TP→FN + yeni FP. Kabul: düzelen − bozulan ≥ 2.

| Parametre | Değer | TP | FP | FN | F1 | %95 aralık | Düzelen | Bozulan | Öneri |
|---|---|---|---|---|---|---|---|---|---|
| MIN_RECEIVE_FRAMES | 2 | 26 | 7 | 15 | 0.703 | 0.57–0.81 | 5 | 4 (0 TP→FN + 4 yeni FP) | önerilmez (fark +1) |
| MIN_RECEIVE_FRAMES | 3 | 22 | 4 | 19 | 0.657 | 0.52–0.78 | 1 | 0 | önerilmez (fark +1) |
| MIN_RECEIVE_FRAMES | **4** | 21 | 5 | 20 | 0.627 | 0.49–0.76 | – | – | mevcut |
| MIN_RECEIVE_FRAMES_LOSS | 3 | 21 | 8 | 20 | 0.600 | 0.47–0.73 | 0 | 4 yeni FP | önerilmez |
| MIN_RECEIVE_FRAMES_LOSS | 4 | 21 | 6 | 20 | 0.618 | 0.48–0.75 | 0 | 2 yeni FP | önerilmez |
| MIN_RECEIVE_FRAMES_LOSS | **5** | 21 | 5 | 20 | 0.627 | 0.49–0.76 | – | – | mevcut |
| DRIBBLE_GAP | 6 | 21 | 5 | 20 | 0.627 | 0.49–0.76 | 0 | 0 | önerilmez (etkisiz) |
| DRIBBLE_GAP | 9 | 21 | 5 | 20 | 0.627 | 0.49–0.76 | 0 | 0 | önerilmez (etkisiz) |
| DRIBBLE_GAP | **12** | 21 | 5 | 20 | 0.627 | 0.49–0.76 | – | – | mevcut |
| MAX_INTERP_GAP | **10** | 21 | 5 | 20 | 0.627 | 0.49–0.76 | – | – | mevcut |
| MAX_INTERP_GAP | 15 | 22 | 5 | 19 | 0.647 | 0.52–0.77 | 1 | 1 yeni FP | önerilmez |
| MAX_INTERP_GAP | 20 | 22 | 5 | 19 | 0.647 | 0.52–0.77 | 1 | 1 yeni FP | önerilmez |
| DOGRULAMA_KARE | 2 | 21 | 5 | 20 | 0.627 | 0.49–0.76 | 0 | 0 | önerilmez (etkisiz) |
| DOGRULAMA_KARE | **3** | 21 | 5 | 20 | 0.627 | 0.49–0.76 | – | – | mevcut |

Düzelen / bozulan olayların zamanları:
| Ayar | Düzelen (FN→TP) | Bozulan (yeni FP; TP→FN yok) |
|---|---|---|
| MIN_RECEIVE_FRAMES=2 | 1:03.60, 1:57.12, 2:00.32, 2:23.64, 2:51.52 (hepsi PAS) | 1:13.96, 1:49.48, 1:54.44, 2:13.72 (PAS) |
| MIN_RECEIVE_FRAMES=3 | 1:03.60 | – |
| MIN_RECEIVE_FRAMES_LOSS=3 | – | 1:15.00 TK, 1:16.28 PAS, 1:26.00 TK, 2:51.20 TK |
| MIN_RECEIVE_FRAMES_LOSS=4 | – | 1:15.00 TK, 1:16.28 PAS |
| MAX_INTERP_GAP=15 / 20 | 1:03.60 | 2:12.44 PAS |

**Sonuç: bu taramada eşiği geçen (fark ≥ 2) ayar yok; hiçbir değişiklik önerilmez.**
- `MIN_RECEIVE_FRAMES=2` en çok kazandıran ayar (F1 0.627→0.703, +5 olay), ama 4 yeni FP getiriyor; net +1, kural eşiğinin altında. Aralıklar örtüşüyor (0.57–0.81 ↔ 0.49–0.76); 41 etiketle fark güvenilir değil. `=3` bozulma getirmedi ama kazancı yalnız 1 olay.
- `MIN_RECEIVE_FRAMES_LOSS`'u düşürmek yalnız FP ekliyor (hiç TOP KAYBI düzelmedi).
- `DRIBBLE_GAP` ve `DOGRULAMA_KARE` bu aralıkta olay sonucunu değiştirmedi (DRIBBLE_GAP yalnız "aynı oyuncu" serilerinin bölünmesini etkiliyor, olay/possession çıktısı aynı; DOGRULAMA_KARE=2 top izi ve events dosyalarını değiştirdi ama 60–180 sn TP/FP/FN aynı kaldı).
- Parametreler birlikte denenmedi (tek-parametre kuralı); etkileşimler bilinmiyor.

## 3. Reddedilen adaylar ve etiketler (baseline, 60–180 sn)
Aralıkta 76 aday: 26 kabul, 50 red. "Etikete denk" = aday zamanı (receiver_start) ±1 sn içinde etiket var (tipi belli adaylarda aynı tip); "bunlardan FN" = o etiket şu an kaçırılan etiketlerden.

| Red nedeni | Aday | Etikete denk | Tekil etiket | Bunlardan FN | Not |
|---|---|---|---|---|---|
| kisa_alim | 11 | 8 | 8 | 4 | PAS; kalan 4 eşleşme zaten TP olan etiketlerin yanında (çift sayım riski) |
| kisa_kayip | 9 | 0 | 0 | 0 | filtre zarar vermiyor |
| imkansiz_hiz | 2 | 0 | 0 | 0 | filtre zarar vermiyor |
| ayni_oyuncu | 19 | 9 | 11 | 6 | tip yok, tip-bağımsız eşleşme |
| bosluk_buyuk | 6 | 4 | 5 | 5 | tip yok, tip-bağımsız eşleşme |
| ayni_kisi_id_degisimi | 3 | 1 | 1 | 1 | tip yok, tip-bağımsız eşleşme |

Yorum:
- `kisa_alim` doğrudan zarar veriyor: 11 reddin 8'i etikete denk geliyor, 4'ü kaçırılan bir etiket. Ancak rastgele bir zamanın bir PAS etiketine ±1 sn içinde düşme olasılığı bile ≈ %53 (tip bağımsız ≈ %56; TOP KAYBI için ≈ %8). 8/11 = %73 bunun yalnızca biraz üstünde; küçük örnekte güçlü kanıt değil. Sonuç taramayla tutarlı: gevşetince 5 FN düzeliyor ama 4 FP geliyor.
- `kisa_kayip` ve `imkansiz_hiz`: 0 etiket. TOP KAYBI tarafında filtre doğru çalışıyor (rastgele eşleşme oranı da düşük, %8), yani TOP KAYBI kaçırmalarının nedeni bu filtre değil.
- `ayni_oyuncu` / `bosluk_buyuk` / `ayni_kisi_id_degisimi` eşleşmeleri tipsiz olduğu için şansla beklenen düzeyde (~%56) veya biraz üstünde; tek başına anlam taşımıyor. `bosluk_buyuk`'taki 5 FN ilgi çekici (6 adayın 4'ü, 5 tekil etiket): top >3 sn kaybolmuş olabilir, ama tip yok ve örnek çok küçük.
