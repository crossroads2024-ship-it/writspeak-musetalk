#!/usr/bin/env python3
"""Build out/report.md + report.json comparing the base looks (sharpness, motion, lip-sync fit, size).
Runs scripts/validate_outputs.py and scripts/analyze_quality.py on every <clip>__<base>.mp4 and on the silent base videos
(so a result can be compared with the clip it started from).
  python scripts/report.py --out out --inputs /kaggle/input/writspeak-examiner-inputs
"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sh(args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--inputs', required=True)
    a = ap.parse_args()
    out, inputs = Path(a.out), Path(a.inputs)
    audio = {p.stem: p for p in inputs.rglob('*') if p.suffix.lower() in ('.mp3', '.wav', '.m4a')}
    rows = []
    for v in sorted(out.glob('*__*.mp4')):
        clip, base = v.stem.split('__', 1)
        rc, so, se = sh([HERE / 'analyze_quality.py', v] + (['--audio', audio[clip]] if clip in audio else []))
        try:
            m = json.loads(so)
        except Exception:
            m = {'error': (se or so)[-300:]}
        m.update(clip=clip, base=base, mb=round(v.stat().st_size / 1e6, 3))
        rows.append(m)
    # baseline: the silent base videos themselves
    base_rows = []
    for b in sorted(inputs.rglob('*.mp4')):
        rc, so, se = sh([HERE / 'analyze_quality.py', b])
        try:
            m = json.loads(so)
            m['base'] = b.stem
            base_rows.append(m)
        except Exception:
            pass
    rc, vo, ve = sh([HERE / 'validate_outputs.py', out, '--expect-audio-dir', inputs])
    lines = ['# MuseTalk proof of concept report', '', '## File checks (size, audio/video length, audio track)', '```', vo.strip(), '```', '',
             '## Look comparison (higher sharpness ratio, higher av_corr, lower |lag|, lower face_drift = better; head_motion 0 = frozen)', '',
             '| clip | base | MB | sharpness ratio | mouth motion | head motion | face drift | av corr | av lag ms |', '|---|---|---|---|---|---|---|---|---|']
    for m in rows:
        lines.append('| {clip} | {base} | {mb} | {mouth_sharpness_ratio} | {mouth_motion} | {head_motion} | {face_drift} | {av_corr} | {av_lag_ms} |'.format(
            **{k: m.get(k, '-') for k in ['clip', 'base', 'mb', 'mouth_sharpness_ratio', 'mouth_motion', 'head_motion', 'face_drift', 'av_corr', 'av_lag_ms']}))
    lines += ['', '## Averages per base look', '', '| base | avg MB | sharpness | head motion | face drift | av corr |', '|---|---|---|---|---|---|']
    g = defaultdict(list)
    for m in rows:
        g[m['base']].append(m)
    for base, ms in g.items():
        def avg(k):
            vals = [x[k] for x in ms if isinstance(x.get(k), (int, float))]
            return round(sum(vals) / len(vals), 2) if vals else '-'
        lines.append(f"| {base} | {avg('mb')} | {avg('mouth_sharpness_ratio')} | {avg('head_motion')} | {avg('face_drift')} | {avg('av_corr')} |")
    lines += ['', '## Silent base videos (reference, no new mouth)', '']
    for m in base_rows:
        lines.append(f"- {m['base']}: sharpness {m.get('mouth_sharpness_ratio')}, head motion {m.get('head_motion')}, face drift {m.get('face_drift')}")
    lines += ['', 'These numbers are indicators only. Watch the videos: lip-sync accuracy, mouth sharpness and facial consistency are judged by eye.']
    (out / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    (out / 'report.json').write_text(json.dumps({'renders': rows, 'bases': base_rows}, indent=1))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
