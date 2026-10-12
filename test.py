import cv2
import numpy as np

cap = cv2.VideoCapture("barca_tactical.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)

GREEN_LOW = np.array([30, 30, 30])
GREEN_HIGH = np.array([90, 255, 255])
kernel = np.ones((25, 25), np.uint8)

for sec in [65, 90, 120, 200, 300]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ret, frame = cap.read()
    if not ret:
        print(f"{sec}s: kare okunamadı")
        continue
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    field = np.zeros_like(m)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        cv2.drawContours(field, [largest], -1, 255, cv2.FILLED)
    coverage = 100 * (field > 0).sum() / field.size
    print(f"{sec}s ({sec//60}:{sec%60:02d}): saha maskesi ekranın %{coverage:.1f}'ini kaplıyor")

cap.release()