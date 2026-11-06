#!/usr/bin/env python3
"""Objective checks on a rendered clip. Needs opencv-python, numpy, soundfile (all installed by install_env.sh).

Numbers are indicators to compare the three base looks, NOT a replacement for watching the video.
  mouth_sharpness_ratio : Laplacian sharpness of the mouth area / sharpness of the eye area (1.0 = equally sharp; <0.6 = soft mouth)
  mouth_motion          : mean frame-to-frame change in the mouth area
  av_corr, av_lag_ms    : correlation between mouth change and audio loudness, and the lag that fits best
                          (|lag| above ~120 ms or corr below ~0.25 suggests weak lip sync)
  face_drift            : how far the upper face (eyes/forehead) is from the first frame, mean over time (identity consistency)
  head_motion           : frame-to-frame change of the upper face (0 = frozen head)
Usage: python scripts/analyze_quality.py out/p1-food-4__idle.mp4 --audio private-inputs/p1-food-4.mp3 [--json x.json]
"""
import argparse
import json
import sys

import cv2
import numpy as np


def face_box(frame):
    """Haar face detector when OpenCV has it, else a fixed box for this portrait framing (fractions of the frame)."""
    h, w = frame.shape[:2]
    try:
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cas = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = cas.detectMultiScale(g, 1.1, 5, minSize=(w // 8, h // 8))
        if len(faces):
            return max(faces, key=lambda b: b[2] * b[3])
    except Exception:
        pass
    return int(w * 0.36), int(h * 0.16), int(w * 0.30), int(h * 0.36)


def crops(frame, box):
    x, y, w, h = box
    mouth = frame[y + int(h * 0.62):y + int(h * 0.98), x + int(w * 0.2):x + int(w * 0.8)]
    upper = frame[y + int(h * 0.12):y + int(h * 0.5), x + int(w * 0.1):x + int(w * 0.9)]
    return cv2.resize(mouth, (96, 48)), cv2.resize(upper, (128, 48))


def lap_var(img):
    return float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


def audio_envelope(path, fps, n):
    import soundfile as sf
    y, sr = sf.read(path, always_2d=True)
    y = y.mean(axis=1)
    hop = int(sr / fps)
    env = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y) - hop, hop)])
    return env[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--audio')
    ap.add_argument('--face-box', help='x,y,w,h in pixels, to override detection')
    ap.add_argument('--json')
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    if len(frames) < 5:
        print('could not read frames from', a.video)
        return 1
    box = tuple(int(v) for v in a.face_box.split(',')) if a.face_box else face_box(frames[0])
    m, u = zip(*[crops(f, box) for f in frames])
    m, u = [x.astype(np.float32) for x in m], [x.astype(np.float32) for x in u]
    sm = np.mean([lap_var(x.astype(np.uint8)) for x in m])
    su = np.mean([lap_var(x.astype(np.uint8)) for x in u])
    mouth_change = np.array([np.mean(np.abs(m[i] - m[i - 1])) for i in range(1, len(m))])
    head_change = np.array([np.mean(np.abs(u[i] - u[i - 1])) for i in range(1, len(u))])
    drift = float(np.mean([np.mean(np.abs(x - u[0])) for x in u]))
    res = {
        'file': a.video, 'frames': len(frames), 'fps': round(fps, 2), 'face_box': [int(v) for v in box],
        'mouth_sharpness_ratio': round(sm / su, 2) if su else None,
        'mouth_motion': round(float(mouth_change.mean()), 2),
        'head_motion': round(float(head_change.mean()), 2),
        'face_drift': round(drift, 2),
    }
    if a.audio:
        env = audio_envelope(a.audio, fps, len(mouth_change))
        n = min(len(env), len(mouth_change))
        if n > 10 and env[:n].std() > 0 and mouth_change[:n].std() > 0:
            best = (-2, 0)
            maxlag = int(0.35 * fps)
            for lag in range(-maxlag, maxlag + 1):
                a1 = env[max(0, lag):n + min(0, lag)]
                b1 = mouth_change[max(0, -lag):n - max(0, lag)]
                k = min(len(a1), len(b1))
                if k > 10 and a1[:k].std() > 0 and b1[:k].std() > 0:
                    c = float(np.corrcoef(a1[:k], b1[:k])[0, 1])
                    if c > best[0]:
                        best = (c, lag)
            res['av_corr'] = round(best[0], 2)
            res['av_lag_ms'] = int(round(best[1] * 1000 / fps))
    print(json.dumps(res, indent=1))
    if a.json:
        open(a.json, 'w').write(json.dumps(res, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
