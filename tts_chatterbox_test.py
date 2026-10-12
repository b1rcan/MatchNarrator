"""
tts_chatterbox_test.py - Chatterbox Multilingual ile ~10 sablon cumlesini Turkce (tr) sentezle; gecikme, VRAM, ses suresi olc.
AYRI venv'de calisir (C:\\Users\\gorur\\tts_venv); ana .venv KULLANILMAZ. Ollama ile ayni anda GPU kullanma: once `ollama stop <model>`.
Cikti: tts_ornekler/*.wav, tts_olcum.json
"""
import json
import os
import subprocess
import time

import torch
import torchaudio as ta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tts_ornekler")
os.makedirs(OUT, exist_ok=True)

sablon = json.load(open(os.path.join(HERE, "spiker_sablon_v2.json"), encoding="utf-8"))
gor, cumleler = set(), []
for x in sablon:                       # ilk 10 BENZERSIZ sablon cumlesi
    if x["metin"] not in gor:
        gor.add(x["metin"])
        cumleler.append((x["id"], x["metin"]))
    if len(cumleler) == 10:
        break


def nvsmi():
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.split()[0])
    except Exception:
        return None


from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402

v0 = nvsmi()
t = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
yukleme = time.time() - t
v_yuk = nvsmi()
print(f"model yuklendi: {yukleme:.1f} sn, VRAM(nvidia-smi) {v0} -> {v_yuk} MiB, sr={model.sr}", flush=True)

sonuc = []
torch.cuda.reset_peak_memory_stats()
for n, (sid, metin) in enumerate(cumleler):
    torch.manual_seed(42)
    t = time.time()
    wav = model.generate(metin, language_id="tr")
    torch.cuda.synchronize()
    dt = time.time() - t
    sure = wav.shape[-1] / model.sr
    fn = os.path.join(OUT, f"cumle_{n + 1:02d}_{sid}.wav")
    ta.save(fn, wav.cpu(), model.sr)
    sonuc.append(dict(id=sid, metin=metin, uretim_sn=round(dt, 2), ses_suresi_sn=round(sure, 2), rtf=round(dt / sure, 2), dosya=os.path.basename(fn), vram_nvsmi_mib=nvsmi()))
    print(sonuc[-1], flush=True)
meta = dict(model="ChatterboxMultilingualTTS (chatterbox-tts)", dil="tr", yukleme_sn=round(yukleme, 1), vram_once_mib=v0, vram_model_yuklu_mib=v_yuk,
            vram_tepe_nvsmi_mib=max(s["vram_nvsmi_mib"] or 0 for s in sonuc), torch_tepe_ayrilan_mib=round(torch.cuda.max_memory_allocated() / 1048576),
            ilk_cumle_sn=sonuc[0]["uretim_sn"], ort_uretim_sn_ilk_haric=round(sum(s["uretim_sn"] for s in sonuc[1:]) / max(len(sonuc) - 1, 1), 2),
            ort_ses_suresi_sn=round(sum(s["ses_suresi_sn"] for s in sonuc) / len(sonuc), 2), cumleler=sonuc)
json.dump(meta, open(os.path.join(HERE, "tts_olcum.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BITTI")
