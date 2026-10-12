import pandas as pd
import numpy as np

df = pd.read_csv("tracking_data.csv")  

ball = df[df["class_name"] == "ball"].sort_values("frame")
ball = ball.loc[ball.groupby("frame")["conf"].idxmax()].sort_values("frame").reset_index(drop=True)

ball["frame_gap"] = ball["frame"].diff()
ball["dx"] = ball["cx"].diff()
ball["dy"] = ball["cy"].diff()
ball["dist"] = np.sqrt(ball["dx"]**2 + ball["dy"]**2)
ball["speed"] = ball["dist"] / ball["frame_gap"]
ball["angle"] = np.arctan2(ball["dy"], ball["dx"])

# Fiziksel olarak imkansız sıçramaları ele
MAX_PLAUSIBLE_SPEED = 100
ball_clean = ball[ball["speed"] <= MAX_PLAUSIBLE_SPEED].copy().reset_index(drop=True)

# İvme (hızdaki ani değişim)
ball_clean["accel"] = ball_clean["speed"].diff().abs()

# Açı değişimi (yön ne kadar sert kırıldı), -pi..pi aralığına normalize
angle_diff = ball_clean["angle"].diff()
ball_clean["angle_change"] = np.abs((angle_diff + np.pi) % (2 * np.pi) - np.pi)

ACCEL_THRESHOLD = 30
EVENT_GAP_FRAMES = 15

# Sınıflandırma eşikleri (deneyerek ayarlanacak)
SHOT_SPEED_THRESHOLD = 45
PASS_SPEED_THRESHOLD = 15

def classify_event(idx, ball_df, window=5):
    """Olay sonrası birkaç karedeki zirve hıza bakarak sınıflandırır."""
    end = min(idx + window, len(ball_df))
    following = ball_df.iloc[idx:end]
    peak_speed = following["speed"].max()

    if peak_speed >= SHOT_SPEED_THRESHOLD:
        return "ŞUT", peak_speed
    elif peak_speed >= PASS_SPEED_THRESHOLD:
        return "PAS", peak_speed
    else:
        return "BELİRSİZ", peak_speed

candidate_frames = ball_clean[ball_clean["accel"] >= ACCEL_THRESHOLD].copy()

events = []
last_frame = -999
for idx, row in candidate_frames.iterrows():
    if row["frame"] - last_frame > EVENT_GAP_FRAMES:
        event_type, peak_speed = classify_event(idx, ball_clean)
        events.append({
            "frame": row["frame"],
            "type": event_type,
            "accel": row["accel"],
            "peak_speed": peak_speed,
            "angle_change_deg": np.degrees(row["angle_change"]) if not pd.isna(row["angle_change"]) else 0
        })
    last_frame = row["frame"]

print(f"Toplam top tespiti: {len(ball)}, temizlik sonrası: {len(ball_clean)}")
print(f"İvme eşiğini geçen aday kare sayısı: {len(candidate_frames)}")
print(f"Kümeleme sonrası benzersiz olay sayısı: {len(events)}\n")

for e in events:
    print(f"Kare {int(e['frame'])}: {e['type']} "
          f"(ivme: {e['accel']:.1f}, zirve hız: {e['peak_speed']:.1f}, "
          f"açı değişimi: {e['angle_change_deg']:.0f}°)")

# Sınıf dağılımını özetle
if events:
    events_df = pd.DataFrame(events)
    print("\n--- Olay Türü Dağılımı ---")
    print(events_df["type"].value_counts())