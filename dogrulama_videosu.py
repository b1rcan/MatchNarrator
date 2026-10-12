"""
dogrulama_videosu.py - events_v2.py ciktilarini videonun uzerine cizer.

Gordugun seyler:
  - Oyuncu kutulari takim rengiyle (A: kirmizi, B: mavi, belirsiz: gri)
  - Top (sari daire; tahmini/doldurulmus konumsa ici bos)
  - Topun sahibi olan oyuncu kalin yesil cerceve
  - Olay aninda ekranin ustunde 1.5 sn boyunca olay yazisi
Cikti: dogrulama.mp4
"""
import json

import cv2
import pandas as pd

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # goreli yollar betigin klasorune gore cozulur
meta = json.load(open("meta.json"))
fps = meta["fps"]
import os
players = pd.read_csv("players_fixed.csv" if os.path.exists("players_fixed.csv") else "players.csv")
ball = pd.read_csv("ball_track.csv").set_index("frame")
poss = pd.read_csv("possession.csv").set_index("frame")["track_id"].to_dict()
teams = pd.read_csv("teams.csv").set_index("track_id")["team"].to_dict()
events = pd.read_csv("events.csv")

# Homografi varsa saha sinirini (tac/kale cizgileri) her karede cizmek icin
HINV = {}
if os.path.exists("homography.csv"):
    import numpy as np
    from saha_geometri import CORNERS
    hdf = pd.read_csv("homography.csv")
    hdf = hdf[hdf["durum"] > 0]
    for fr, h in zip(hdf["frame"].astype(int), hdf[[f"h{i}" for i in range(9)]].to_numpy(float)):
        try:
            HINV[fr] = np.linalg.inv(h.reshape(3, 3))
        except np.linalg.LinAlgError:
            pass

TEAM_COLORS = {0: (0, 0, 255), 1: (255, 128, 0)}
GREY, YELLOW, GREEN = (160, 160, 160), (0, 255, 255), (0, 255, 0)
ev_by_frame = {int(r.frame): f"{r.tip}  ({r.kimden} -> {r.kime})" for r in events.itertuples()}
by_frame = {f: g for f, g in players.groupby("frame")}

cap = cv2.VideoCapture(meta["video"])
cap.set(cv2.CAP_PROP_POS_FRAMES, meta["start_frame"])
out = cv2.VideoWriter("dogrulama.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps,
                      (meta["width"], meta["height"]))

banner, banner_left = "", 0
for f in range(meta["start_frame"], meta["end_frame"]):
    ok, frame = cap.read()
    if not ok:
        break
    if f in HINV:
        poly = cv2.perspectiveTransform(CORNERS.reshape(-1, 1, 2), HINV[f]).reshape(-1, 2).astype("int32")
        cv2.polylines(frame, [poly], True, GREEN, 2)          # topun kabul edildigi saha siniri
    owner = poss.get(f)
    g = by_frame.get(f)
    if g is not None:
        for r in g.itertuples():
            if r.class_id == 2:
                color = (0, 0, 0)                      # hakem: siyah
            else:
                color = TEAM_COLORS.get(teams.get(r.track_id), GREY)
            cv2.rectangle(frame, (r.x1, r.y1), (r.x2, r.y2), color, 2)
            cv2.putText(frame, str(r.track_id), (r.x1, r.y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            if owner is not None and r.track_id == owner:
                cv2.rectangle(frame, (r.x1 - 3, r.y1 - 3), (r.x2 + 3, r.y2 + 3), GREEN, 3)

    if f in ball.index and pd.notna(ball.at[f, "bx"]):
        center = (int(ball.at[f, "bx"]), int(ball.at[f, "by"]))
        cv2.circle(frame, center, 7, YELLOW, -1 if ball.at[f, "detected"] else 2)

    if f in ev_by_frame:
        banner, banner_left = ev_by_frame[f], int(1.5 * fps)
    if banner_left > 0:
        cv2.rectangle(frame, (0, 0), (meta["width"], 40), (0, 0, 0), -1)
        cv2.putText(frame, banner, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        banner_left -= 1

    t = f / fps
    cv2.putText(frame, f"{int(t // 60)}:{t % 60:05.2f}", (meta["width"] - 140, meta["height"] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    out.write(frame)

cap.release()
out.release()
print("dogrulama.mp4 olusturuldu")