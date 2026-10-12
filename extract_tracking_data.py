import csv
from ultralytics import YOLO

model = YOLO("best.pt")

results_gen = model.track(
    source="barca_tactical.mp4",
    device=0,
    imgsz=960,
    conf=0.25,
    tracker="bytetrack.yaml",
    persist=True,
    stream=True,
    verbose=False
)

CLASS_NAMES = ["player", "goalkeeper", "referee", "ball"]

with open("tracking_data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["frame", "track_id", "class_id", "class_name", "cx", "cy", "conf"])

    for frame_idx, r in enumerate(results_gen):
        if r.boxes.id is None:
            continue
        for box in r.boxes:
            track_id = int(box.id[0]) if box.id is not None else -1
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0]
            cx, cy = float((x1 + x2) / 2), float((y1 + y2) / 2)
            writer.writerow([frame_idx, track_id, cls_id, CLASS_NAMES[cls_id], cx, cy, conf])

print("tracking_data.csv oluşturuldu")