"""
saha_test.py - Saha anahtar noktasi modelini birkac karede test eder.

Her test karesi icin:
  - Modelin buldugu saha noktalarini (numarali, pembe) cizer
  - Bu noktalarla homografi hesaplar
  - Gercek saha cizgilerini homografi ile goruntuye geri izdusurur (sari cizgiler)
  - Saha alanini (tac/kale cizgileri icini) yesil boyar: top yalnizca burada kabul edilecek

Sari cizgiler (inceltilmis) gercek beyaz saha cizgilerinin USTUNE oturuyorsa kalibrasyon dogrudur.
Ince kirmizi cizgiler modelin inceltme oncesi kaba tahminidir.

Saha sablonu saha_geometri.py'dedir (105 x 68 m).
"""
import cv2
import numpy as np
from ultralytics import YOLO

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # goreli yollar betigin klasorune gore cozulur
VIDEO = "barca_tactical.mp4"
PITCH_MODEL = "football-pitch-detection.pt"
TEST_SECONDS = [65, 120, 200, 300]
KP_CONF = 0.5

from saha_geometri import VERTICES, EDGES, L, W, CC_R   # 105 x 68 m saha sablonu
from saha_cizgi import refine

model = YOLO(PITCH_MODEL)
cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS)

for k, sec in enumerate(TEST_SECONDS):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ok, frame = cap.read()
    if not ok:
        continue
    r = model(frame, verbose=False)[0]
    out = frame.copy()
    if r.keypoints is None or r.keypoints.conf is None or len(r.keypoints.xy) == 0:
        print(f"{sec}s: model hic nokta bulamadi")
        cv2.imwrite(f"saha_test_{k}.png", out)
        continue

    xy = r.keypoints.xy[0].cpu().numpy()
    conf = r.keypoints.conf[0].cpu().numpy()
    good = (conf > KP_CONF) & (xy[:, 0] > 1) & (xy[:, 1] > 1)
    n = int(good.sum())

    for i in np.where(good)[0]:
        x, y = int(xy[i, 0]), int(xy[i, 1])
        cv2.circle(out, (x, y), 6, (147, 20, 255), -1)
        cv2.putText(out, str(i + 1), (x + 6, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (147, 20, 255), 2)

    if n < 4:
        print(f"{sec}s: sadece {n} guvenilir nokta, homografi icin en az 4 gerekli")
        cv2.imwrite(f"saha_test_{k}.png", out)
        continue

    H, inl = cv2.findHomography(xy[good], VERTICES[good], cv2.RANSAC, 100.0)  # 100 cm RANSAC esigi
    if H is None:
        print(f"{sec}s: homografi hesaplanamadi")
        cv2.imwrite(f"saha_test_{k}.png", out)
        continue

    # Kalite: modelin buldugu noktalar homografiyle sahaya cevrilince gercek yerlerine ne kadar uzak?
    proj = cv2.perspectiveTransform(xy[good].reshape(-1, 1, 2), H).reshape(-1, 2)
    err_m = float(np.mean(np.linalg.norm(proj - VERTICES[good], axis=1))) / 100

    # Cizgi inceltmesi: modelin kaba homografisi gercek beyaz cizgilere hizalanir
    H_model = H
    H, cov0, cov1, _ = refine(frame, H)
    for a, b in EDGES:   # modelin kaba tahmini: ince kirmizi
        pts = cv2.perspectiveTransform(VERTICES[[a - 1, b - 1]].reshape(-1, 1, 2), np.linalg.inv(H_model)).reshape(-1, 2)
        cv2.line(out, tuple(pts[0].astype(int)), tuple(pts[1].astype(int)), (0, 0, 255), 1)

    # Saha alani (4 kose) ve cizgiler goruntuye geri izdusuruluyor (inceltilmis H, sari)
    Hinv = np.linalg.inv(H)
    corners = cv2.perspectiveTransform(VERTICES[[0, 5, 29, 24]].reshape(-1, 1, 2), Hinv).reshape(-1, 2)
    overlay = out.copy()
    cv2.fillPoly(overlay, [corners.astype(np.int32)], (0, 200, 0))
    out = cv2.addWeighted(overlay, 0.25, out, 0.75, 0)
    for a, b in EDGES:
        pts = cv2.perspectiveTransform(VERTICES[[a - 1, b - 1]].reshape(-1, 1, 2), Hinv).reshape(-1, 2)
        cv2.line(out, tuple(pts[0].astype(int)), tuple(pts[1].astype(int)), (0, 255, 255), 2)

    ang = np.linspace(0, 2 * np.pi, 90)
    circ = np.stack([L / 2 + CC_R * np.cos(ang), W / 2 + CC_R * np.sin(ang)], 1).astype(np.float32)
    cv2.polylines(out, [cv2.perspectiveTransform(circ.reshape(-1, 1, 2), Hinv).astype(np.int32)], True, (0, 255, 255), 2)
    cv2.putText(out, f"{n} nokta | hata {err_m:.2f} m | cizgi kapsamasi %{100*cov0:.0f} -> %{100*cov1:.0f}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.imwrite(f"saha_test_{k}.png", out)
    print(f"{sec}s ({sec // 60}:{sec % 60:02d}): {n} nokta, hata {err_m:.2f} m, cizgi kapsamasi "
          f"%{100 * cov0:.0f} -> %{100 * cov1:.0f} "
          f"-> saha_test_{k}.png")

cap.release()