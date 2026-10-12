"""
saha_cizgi.py - Homografiyi goruntudeki GERCEK beyaz saha cizgilerine hizalayarak inceltir.

Neden: Saha anahtar noktasi modeli kaba bir homografi verir; goruntu kenarlarinda noktalar
birkac on piksel hatali olabilir (01:57 karesinde ust tac cizgisi 3.3 m kaymisti). Tac cizgisine
~3 m mesafedeki bir logoyu elemek icin sinirin birkac piksel dogrulukta olmasi gerekir.

Yontem (yinelemeli en yakin nokta / ICP benzeri):
  1) Beyaz cizgi maskesi: ince parlak yapilar (top-hat) + gevsek renk esigi (uzak cizgiler soluk)
     + yonlu morfolojik acma (yalnizca >=25 px duz devam eden yapilar; logo harfleri elenir).
     Her pikselin hangi yondeki bir cizgiye ait oldugu da tutulur.
  2) Sablondaki cizgilerden ve orta yuvarlaktan ornek noktalar alinir, mevcut H ile izdusurulur.
  3) Her ornekte cizgiye dik yonde arama: en yakin, AYNI YONDEKI beyaz cizgi pikseli bulunur.
  4) Bulunan piksel sablondaki cizgiye "oturtulur"; tum eslesmelerle en kucuk kareler homografisi
     hesaplanir (bariz aykiri eslesmeler atilir); arama yaricapi kucultulerek tekrarlanir.
  5) Kabul: inceltilmis H, cizgi ustune oturan ornek oranini (kapsama) artirmalidir.

Not: Yuvarlak ve duz cizgiler tek homografiyle ayni anda tam aciklanamiyor (muhtemelen goruntu
kenarindaki mercek bukulmesi). Logo/saha disi ayrimi icin sinir cizgileri onceliklidir;
bu yuzden yuvarlak ek agirlik almaz.
"""
import cv2
import numpy as np

from saha_geometri import VERTICES, EDGES, L, W, CC_R

_K_TOPHAT = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
_K_GREEN = np.ones((9, 9), np.uint8)
N_BINS = 12


def _line_kernels(length=25, n_angles=N_BINS):
    ks, c = [], length // 2
    for i in range(n_angles):
        a = np.pi * i / n_angles
        k = np.zeros((length, length), np.uint8)
        dx, dy = np.cos(a) * c, np.sin(a) * c
        cv2.line(k, (int(round(c - dx)), int(round(c - dy))), (int(round(c + dx)), int(round(c + dy))), 1, 1)
        ks.append(k)
    return ks


_LINE_KERNELS = _line_kernels()


def line_mask(frame):
    """(maske, yon) dondurur. yon: her piksel icin hangi aci kutularinda cizgiye ait (bit maskesi)."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, _K_TOPHAT)
    near_green = cv2.dilate(cv2.inRange(hsv, (30, 30, 30), (90, 255, 255)), _K_GREEN) > 0
    cand = ((tophat > 12) & (hsv[..., 2] > 140) & (hsv[..., 1] < 135) & near_green).astype(np.uint8)
    orient = np.zeros(cand.shape, np.uint16)
    for i, k in enumerate(_LINE_KERNELS):
        orient |= cv2.morphologyEx(cand, cv2.MORPH_OPEN, k).astype(np.uint16) << i
    return orient > 0, orient


# ---- Sablon ornekleri (bir kez hesaplanir) ----
def _samples(step_cm=100):
    pts, p0s, p1s, circ = [], [], [], []
    for a, b in EDGES:
        p, q = VERTICES[a - 1].astype(np.float64), VERTICES[b - 1].astype(np.float64)
        n = max(int(np.linalg.norm(q - p) // step_cm), 2)
        for t in np.linspace(0, 1, n + 1)[1:-1]:          # koseler atlanir (iki cizgi kesisir)
            pts.append(p + t * (q - p)); p0s.append(p); p1s.append(q); circ.append(False)
    c = np.array([L / 2, W / 2], np.float64)
    for ang in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        pts.append(c + CC_R * np.array([np.cos(ang), np.sin(ang)])); p0s.append(c); p1s.append(c); circ.append(True)
    pts, p0s, p1s, circ = map(np.array, (pts, p0s, p1s, circ))
    tang = np.where(circ[:, None],
                    np.stack([-(pts - p0s)[:, 1], (pts - p0s)[:, 0]], 1) / CC_R,
                    (p1s - p0s) / np.maximum(np.linalg.norm(p1s - p0s, axis=1, keepdims=True), 1e-9))
    return pts, p0s, p1s, circ, tang


_PTS, _P0, _P1, _CIRC, _TANG = _samples()


def _project(pts, Hinv):
    return cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float32), Hinv).reshape(-1, 2)


def _match(mask, orient, H, radius, ang_tol=1):
    """Vektorlesmis eslestirme: (goruntu noktalari, sablon noktalari) dondurur."""
    h, w = mask.shape
    Hinv = np.linalg.inv(H)
    img = _project(_PTS, Hinv)
    t = _project(_PTS + _TANG * 30, Hinv) - img
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    bins = np.round(np.mod(np.arctan2(t[:, 1], t[:, 0]), np.pi) / (np.pi / N_BINS)).astype(int) % N_BINS
    allowed = np.zeros(len(t), np.uint16)
    for d in range(-ang_tol, ang_tol + 1):
        allowed |= (1 << ((bins + d) % N_BINS)).astype(np.uint16)

    offs = np.concatenate([[0], np.ravel(np.column_stack([np.arange(1, radius + 1), -np.arange(1, radius + 1)]))])
    cand = img[:, None, :] + offs[None, :, None] * nrm[:, None, :]          # (N, K, 2)
    xs, ys = np.round(cand[..., 0]).astype(int), np.round(cand[..., 1]).astype(int)
    inb = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    xs_c, ys_c = np.clip(xs, 0, w - 1), np.clip(ys, 0, h - 1)
    good = inb & mask[ys_c, xs_c] & ((orient[ys_c, xs_c] & allowed[:, None]) > 0)
    vis = (img[:, 0] >= 0) & (img[:, 0] < w) & (img[:, 1] >= 0) & (img[:, 1] < h)
    has = good.any(axis=1) & vis
    if not has.any():
        return np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32), int(vis.sum())
    first = good.argmax(axis=1)
    idx = np.where(has)[0]
    found = cand[idx, first[idx]]
    q = cv2.perspectiveTransform(found.reshape(-1, 1, 2).astype(np.float32), H).reshape(-1, 2).astype(np.float64)
    # Sablon cizgisine oturt
    p0, p1, circ = _P0[idx], _P1[idx], _CIRC[idx]
    v = p1 - p0
    tt = np.clip(np.einsum("ij,ij->i", q - p0, v) / np.maximum(np.einsum("ij,ij->i", v, v), 1e-9), 0, 1)
    snap_seg = p0 + tt[:, None] * v
    dvec = q - p0
    snap_circ = p0 + CC_R * dvec / np.maximum(np.linalg.norm(dvec, axis=1, keepdims=True), 1e-6)
    dst = np.where(circ[:, None], snap_circ, snap_seg)
    return found.astype(np.float32), dst.astype(np.float32), int(vis.sum())


def coverage(mask, orient, H, tol=3):
    """Gorunen sablon orneklerinin kacta kaci gercek bir cizginin <= tol px yakininda (0-1)."""
    s, _, n_vis = _match(mask, orient, H, tol)
    return len(s) / max(n_vis, 1)


def _fit(src, dst):
    H, _ = cv2.findHomography(src, dst, 0)
    if H is None:
        return None
    res = np.linalg.norm(_project(dst, np.linalg.inv(H)) - src, axis=1)
    keep = res <= max(4.0, 3 * np.median(res))           # bariz aykirilar (oyuncu, baska cizgi) atilir
    if keep.sum() >= 8:
        H, _ = cv2.findHomography(src[keep], dst[keep], 0)
    return None if H is None else H / H[2, 2]


def refine(frame, H, radii=(40, 30, 20, 14, 10, 7, 5, 4, 3), min_matches=40, lines=None):
    """H'yi beyaz cizgilere hizalar. Donus: (H, kapsama_once, kapsama_sonra, eslesme_sayisi).
    Iyilesme yoksa orijinal H doner."""
    mask, orient = lines if lines is not None else line_mask(frame)
    cov0 = coverage(mask, orient, H)
    Hc, n = H, 0
    for r in radii:
        src, dst, _ = _match(mask, orient, Hc, r)
        n = len(src)
        if n < min_matches:
            return H, cov0, cov0, n
        Hn = _fit(src, dst)
        if Hn is None:
            return H, cov0, cov0, n
        Hc = Hn
    cov1 = coverage(mask, orient, Hc)
    if cov1 <= cov0:
        return H, cov0, cov0, n
    return Hc, cov0, cov1, n
