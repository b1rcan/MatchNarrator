# 🎙️ MatchNarrator: AI Football Commentary System

![Version](https://img.shields.io/badge/version-v0.1.0--alpha-orange) ![Python](https://img.shields.io/badge/Python-3.10-blue) ![Platform](https://img.shields.io/badge/Platform-Apple%20Silicon-lightgrey)

**MatchNarrator**, futbol maç görüntülerini kare kare analiz eden ve yerel yapay zeka modelleri kullanarak (Offline-First) maç anlatımı (spikerlik) yapan otonom bir sistemdir.

> 🚧 **Not:** Bu proje henüz **Geliştirme Aşamasındadır (v0.1.0)**. Şu anki sürüm, sistemin mimari iskeletini ve temel görüntü işleme yeteneklerini barındırmaktadır.

---

## 🎯 Proje Amacı
Bu çalışma, **Manisa Celal Bayar Üniversitesi Yazılım Mühendisliği** kapsamında bir Ar-Ge projesi olarak geliştirilmektedir. 

Temel hedefler:
* Bilgisayarlı Görü (Computer Vision) ile top ve oyuncu takibi.
* Olay tabanlı (Event-Driven) sistem mimarisi kurmak.
* Yerel LLM'ler (Gemma/Llama) ile bağlama uygun, yaratıcı metin üretmek.
* Bulut bağımlılığı olmadan, kişisel donanım (Apple Silicon) üzerinde çalışan bir "AI Pipeline" oluşturmak.

---

## 🏗️ Mimari & Teknoloji Yığını (Tech Stack)

Bu proje, yüksek maliyetli sunucular yerine **Local Edge AI** mantığıyla tasarlanmıştır.

| Modül | Teknoloji | Görevi |
| :--- | :--- | :--- |
| **Göz (Vision)** | **YOLOv8 Nano** | Gerçek zamanlı nesne tespiti (Top Takibi). |
| **Mantık (Logic)** | **Python (OpenCV)** | Sanal kale çizgisi ve olay tetikleme algoritmaları. |
| **Beyin (Brain)** | **Gemma:1b (via Ollama)** | Google'ın hafif modeli ile anlık spiker metni üretimi. |
| **Ses (Voice)** | **Edge-TTS** | Metni doğal tonlamayla sese dönüştürme (AhmetNeural). |
| **Kurgu (Edit)** | **FFmpeg** | Görüntü ve sesin senkronize şekilde birleştirilmesi. |

---

## ⚙️ Nasıl Çalışır? (Pipeline)

Sistem şu an 5 aşamalı bir "Üretim Bandı" mantığıyla çalışmaktadır:

1.  **Input:** Ham maç videosu sisteme yüklenir.
2.  **Detection:** YOLO, her karede topun koordinatlarını `(x, y)` çıkarır.
3.  **Trigger:** Top belirlenen koordinatlara (Kale) girdiğinde sistem "GOL" sinyali üretir.
4.  **Generation:** Yapay zeka, duruma uygun coşkulu bir cümle kurar ve seslendirir.
5.  **Render:** Orijinal videonun ilgili anına ses montajlanır ve çıktı alınır.

---

## 🗺️ Yol Haritası (Roadmap)

- [x] **Faz 0:** Proje mimarisinin kurulması ve Git entegrasyonu.
- [ ] **Faz 1:** Görüntü İşleme (Vision) modülünün kodlanması.
- [ ] **Faz 2:** "Sanal Kale" ve Mantık (Logic) katmanının entegrasyonu.
- [ ] **Faz 3:** LLM (Gemma) ve TTS (Ses) entegrasyonu.
- [ ] **Faz 4:** Web Showcase (Vitrin) arayüzünün hazırlanması.

---

## 👨‍💻 Geliştirici

**Bircan Görür** *Yazılım Mühendisliği Öğrencisi* Manisa Celal Bayar Üniversitesi

---
*Disclaimer: This project is for educational and research purposes only.*