"""
saha_geometri.py - Futbol sahasi sablonu (cm) ve 32 anahtar noktanin sirasi.
Nokta sirasi, kullandigimiz hazir saha modelinin (roboflow/sports, MIT lisansi) cikti sirasiyla aynidir.
Olculer: profesyonel lig standardi 105 x 68 m ve kural kitabindaki cizgi olculeri.
(Hazir projenin sablonu 120 x 70 m ve ceza sahasi boyu 20.15 m idi; bu, ceza sahasi cizgisinden
disariya dogru tahmin edilen kale/tac cizgilerini birkac metre DISARI kaydiriyordu.)
"""
import numpy as np

W, L = 6800, 10500                      # saha eni / boyu (cm) - 105 x 68 m
PB_W, PB_L = 4032, 1650                 # ceza sahasi (40.32 x 16.5 m)
GB_W, GB_L = 1832, 550                  # kale alani
CC_R, PS = 915, 1100                    # orta yuvarlak yaricapi, penalti noktasi

VERTICES = np.array([
    (0, 0), (0, (W - PB_W) / 2), (0, (W - GB_W) / 2), (0, (W + GB_W) / 2), (0, (W + PB_W) / 2), (0, W),
    (GB_L, (W - GB_W) / 2), (GB_L, (W + GB_W) / 2), (PS, W / 2),
    (PB_L, (W - PB_W) / 2), (PB_L, (W - GB_W) / 2), (PB_L, (W + GB_W) / 2), (PB_L, (W + PB_W) / 2),
    (L / 2, 0), (L / 2, W / 2 - CC_R), (L / 2, W / 2 + CC_R), (L / 2, W),
    (L - PB_L, (W - PB_W) / 2), (L - PB_L, (W - GB_W) / 2), (L - PB_L, (W + GB_W) / 2), (L - PB_L, (W + PB_W) / 2),
    (L - PS, W / 2), (L - GB_L, (W - GB_W) / 2), (L - GB_L, (W + GB_W) / 2),
    (L, 0), (L, (W - PB_W) / 2), (L, (W - GB_W) / 2), (L, (W + GB_W) / 2), (L, (W + PB_W) / 2), (L, W),
    (L / 2 - CC_R, W / 2), (L / 2 + CC_R, W / 2),
], dtype=np.float32)

EDGES = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (7, 8), (10, 11), (11, 12), (12, 13), (14, 15), (15, 16),
         (16, 17), (18, 19), (19, 20), (20, 21), (23, 24), (25, 26), (26, 27), (27, 28), (28, 29), (29, 30),
         (1, 14), (2, 10), (3, 7), (4, 8), (5, 13), (6, 17), (14, 25), (18, 26), (23, 27), (24, 28),
         (21, 29), (17, 30)]

CORNERS = VERTICES[[0, 5, 29, 24]]      # saha alaninin 4 kosesi (poligon sirasiyla)