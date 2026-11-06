#!/usr/bin/env python3
"""Render talking-head clips with MuseTalk 1.5 from a PRIVATE input folder.

  python scripts/render.py --inputs /kaggle/input/writspeak-examiner-inputs --out /kaggle/working/out
  python scripts/render.py --inputs private-inputs --out out --dry-run        (no GPU needed: shows the plan only)

One output file per (audio clip x base look):  out/<clip>__<base>.mp4
Default is the proof of concept (the clips listed in configs/render.json "poc_clips").
Use --all for every audio file in the input folder (only after the PoC is approved).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def find_file(inputs: Path, name: str):
    hits = list(inputs.rglob(name))
    return hits[0] if hits else None


def plan(inputs: Path, cfg: dict, all_clips: bool, clips_arg, bases_arg):
    bases = {}
    for key, fname in cfg['bases'].items():
        if bases_arg and key not in bases_arg:
            continue
        p = find_file(inputs, fname)
        if p:
            bases[key] = p
        else:
            print(f'warning: base "{key}" ({fname}) not found in {inputs}')
    exts = tuple(cfg['audio_extensions'])
    base_names = set(cfg['bases'].values())
    audio = {p.stem: p for p in sorted(inputs.rglob('*')) if p.suffix.lower() in exts and p.name not in base_names}
    if clips_arg:
        wanted = clips_arg
    elif all_clips:
        wanted = sorted(audio)
    else:
        wanted = cfg['poc_clips']
    missing = [c for c in wanted if c not in audio]
    if missing:
        sys.exit(f'audio not found in inputs: {missing}')
    return bases, {c: audio[c] for c in wanted}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', required=True, help='private input folder (portrait, base videos, Libby audio)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--config', default=str(ROOT / 'configs' / 'render.json'))
    ap.add_argument('--musetalk', default=os.environ.get('MUSETALK_DIR', '/kaggle/temp/MuseTalk'))
    ap.add_argument('--python', default=os.environ.get('MUSETALK_PY', '/kaggle/temp/mt310/bin/python'))
    ap.add_argument('--all', action='store_true', help='every audio file (after PoC approval)')
    ap.add_argument('--clips', nargs='*', help='audio file stems to render')
    ap.add_argument('--bases', nargs='*', help='subset of base looks, e.g. idle talking')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
    inputs, out = Path(a.inputs), Path(a.out)
    bases, clips = plan(inputs, cfg, a.all, a.clips, a.bases)
    if not bases or not clips:
        sys.exit('nothing to render (check input folder and configs/render.json)')

    mt = cfg['musetalk']
    tasks = {}
    for clip, apath in clips.items():
        for key, bpath in bases.items():
            tasks[f'{clip}__{key}'] = {'video_path': str(bpath), 'audio_path': str(apath)}
    print(f'{len(tasks)} renders: {len(clips)} clip(s) x {len(bases)} base look(s)')
    for k in tasks:
        print('  ', k)
    if a.dry_run:
        print('dry run only - nothing rendered')
        return 0

    import yaml  # installed by install_env.sh
    work = Path(a.musetalk) / 'data'
    work.mkdir(parents=True, exist_ok=True)
    yml = work / 'writspeak_tasks.yaml'
    yml.write_text(yaml.safe_dump(tasks), encoding='utf-8')
    res_dir = Path(a.musetalk) / 'results' / 'writspeak'
    shutil.rmtree(res_dir, ignore_errors=True)
    cmd = [a.python, '-m', 'scripts.inference', '--inference_config', str(yml), '--result_dir', str(res_dir),
           '--unet_model_path', 'models/musetalkV15/unet.pth', '--unet_config', 'models/musetalkV15/musetalk.json',
           '--version', mt['version'], '--fps', str(mt['fps_for_still_image']), '--batch_size', str(mt['batch_size']),
           '--parsing_mode', mt['parsing_mode'], '--extra_margin', str(mt['extra_margin']),
           '--left_cheek_width', str(mt['left_cheek_width']), '--right_cheek_width', str(mt['right_cheek_width'])]
    if mt['use_float16']:
        cmd.append('--use_float16')
    # Kaggle sets MPLBACKEND to a notebook-only value that the MuseTalk environment cannot load; force a plain backend.
    env = dict(os.environ, PATH=str(Path(a.python).parent) + os.pathsep + os.environ['PATH'], MPLBACKEND='Agg')
    print('running:', ' '.join(cmd))
    r = subprocess.run(cmd, cwd=a.musetalk, env=env)
    if r.returncode != 0:
        sys.exit(f'MuseTalk exited with code {r.returncode}')

    out.mkdir(parents=True, exist_ok=True)
    found = 0
    for key in tasks:
        base_stem = Path(tasks[key]['video_path']).stem
        clip_stem = Path(tasks[key]['audio_path']).stem
        cands = [p for p in res_dir.rglob(f'{base_stem}_{clip_stem}.mp4')]
        if not cands:
            print('NOT PRODUCED:', key)
            continue
        shutil.copy(cands[0], out / f'{key}.mp4')
        found += 1
    print(f'{found}/{len(tasks)} videos copied to {out}')
    return 0 if found == len(tasks) else 2


if __name__ == '__main__':
    sys.exit(main())
