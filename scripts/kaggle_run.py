#!/usr/bin/env python3
"""One-command Kaggle run: upload PRIVATE inputs as a private dataset, run the notebook on a free GPU, download results.

Needs (once): Kaggle account with phone verified, and an API token saved by you at  %USERPROFILE%\\.kaggle\\kaggle.json
(Kaggle > Settings > API > Create New Token), plus  pip install kaggle.
Usage:
  python scripts/kaggle_run.py --inputs private-inputs --dry-run      # builds everything locally, calls nothing
  python scripts/kaggle_run.py --inputs private-inputs                # real run (uses your free Kaggle quota)
The script never prints or stores your token. Inputs go ONLY to your private Kaggle dataset.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_SLUG = 'writspeak-examiner-inputs'
KERNEL_SLUG = 'writspeak-musetalk-poc'


def username(cli_value):
    if cli_value:
        return cli_value
    if os.environ.get('KAGGLE_USERNAME'):
        return os.environ['KAGGLE_USERNAME']
    kj = Path.home() / '.kaggle' / 'kaggle.json'
    if kj.exists():
        try:
            return json.loads(kj.read_text())['username']
        except Exception:
            pass
    sys.exit('Kaggle username not found. Save kaggle.json in %USERPROFILE%\\.kaggle or pass --username')


def run(cmd, check=True):
    print('>', ' '.join(cmd))
    return subprocess.run(cmd, check=check, text=True, capture_output=False)


def out(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', required=True, help='PRIVATE folder: portrait, base videos, Libby mp3/wav')
    ap.add_argument('--username')
    ap.add_argument('--results', default=str(ROOT / 'results'))
    ap.add_argument('--stage', default=str(ROOT / '.work'))
    ap.add_argument('--timeout-min', type=int, default=120)
    ap.add_argument('--full', action='store_true', help='render EVERY audio clip with ONE base look (use only after the proof of concept is approved)')
    ap.add_argument('--base', default='still', help='base look for --full: idle, talking or still')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    user = a.username if a.dry_run and a.username else username(a.username)
    inputs, stage = Path(a.inputs), Path(a.stage)
    if not (inputs / 'examiner-source.jpg').exists():
        sys.exit(f'{inputs}\\examiner-source.jpg not found: put your private portrait, base videos and audio there first')

    # 1) dataset folder (private)
    ds = stage / 'dataset'
    shutil.rmtree(ds, ignore_errors=True)
    ds.mkdir(parents=True)
    cfg = json.loads((ROOT / 'configs' / 'render.json').read_text(encoding='utf-8'))
    if a.full:
        wanted = {cfg['bases'][a.base]}
        wanted |= {p.name for p in inputs.rglob('*') if p.suffix.lower() in tuple(cfg['audio_extensions']) and p.name not in cfg['bases'].values()}
        (ds / 'job.json').write_text(json.dumps({'all': True, 'bases': [a.base]}))
    else:
        wanted = set(cfg['bases'].values()) | {c + e for c in cfg['poc_clips'] for e in cfg['audio_extensions']}
    n = 0
    for p in inputs.rglob('*'):
        if p.is_file() and p.name in wanted:
            shutil.copy(p, ds / p.name)
            n += 1
    (ds / 'dataset-metadata.json').write_text(json.dumps({
        'title': DATASET_SLUG, 'id': f'{user}/{DATASET_SLUG}', 'licenses': [{'name': 'other'}]}, indent=1))
    print(f'dataset staged: {n} private files -> {ds}')

    # 2) kernel folder
    kn = stage / 'kernel'
    shutil.rmtree(kn, ignore_errors=True)
    kn.mkdir(parents=True)
    shutil.copy(ROOT / 'notebooks' / 'writspeak_musetalk.ipynb', kn / 'writspeak_musetalk.ipynb')
    (kn / 'kernel-metadata.json').write_text(json.dumps({
        'id': f'{user}/{KERNEL_SLUG}', 'title': KERNEL_SLUG, 'code_file': 'writspeak_musetalk.ipynb',
        'language': 'python', 'kernel_type': 'notebook', 'is_private': 'true', 'enable_gpu': 'true',
        'enable_internet': 'true', 'dataset_sources': [f'{user}/{DATASET_SLUG}'],
        'competition_sources': [], 'kernel_sources': [], 'model_sources': []}, indent=1))
    print(f'kernel staged -> {kn}')
    if a.dry_run:
        print('DRY RUN: nothing uploaded. Staged files above are exactly what a real run would send.')
        return 0

    if not shutil.which('kaggle'):
        sys.exit('Kaggle CLI missing: run  pip install kaggle')

    # 3) upload dataset (private by default)
    exists = out(['kaggle', 'datasets', 'status', f'{user}/{DATASET_SLUG}']).returncode == 0
    if exists:
        run(['kaggle', 'datasets', 'version', '-p', str(ds), '-m', 'update inputs', '--dir-mode', 'zip'])
    else:
        run(['kaggle', 'datasets', 'create', '-p', str(ds), '--dir-mode', 'zip'])
    print('waiting 30 s for Kaggle to process the dataset...')
    time.sleep(30)

    # 4) push + run kernel
    run(['kaggle', 'kernels', 'push', '-p', str(kn)])
    t0 = time.time()
    while True:
        time.sleep(60)
        r = out(['kaggle', 'kernels', 'status', f'{user}/{KERNEL_SLUG}'])
        line = (r.stdout or r.stderr).strip().splitlines()[-1:] or ['?']
        print(f'[{int((time.time() - t0) / 60)} min]', line[0])
        txt = (r.stdout or '').lower()
        if 'complete' in txt:
            break
        if 'error' in txt or 'cancel' in txt:
            print('kernel failed. Open https://www.kaggle.com/code/%s/%s and copy the red error text.' % (user, KERNEL_SLUG))
            return 3
        if time.time() - t0 > a.timeout_min * 60:
            print('timeout - check the kernel page on kaggle.com; it may still be running')
            return 4

    # 5) results
    res = Path(a.results)
    res.mkdir(parents=True, exist_ok=True)
    run(['kaggle', 'kernels', 'output', f'{user}/{KERNEL_SLUG}', '-p', str(res)])
    run([sys.executable, str(ROOT / 'scripts' / 'validate_outputs.py'), str(res)], check=False)
    print('done. Videos and report.json are in', res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
