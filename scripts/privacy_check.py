#!/usr/bin/env python3
"""Fail if anything private could end up in this PUBLIC repository.

Checks every file git would commit (tracked + not-ignored untracked):
  * forbidden extensions (images, audio, video, archives, model weights)
  * files over 1 MB
  * text that looks like a secret (API keys, tokens, private keys, kaggle.json contents)
Run by .githooks/pre-commit and by hand:  python scripts/privacy_check.py
Exit code 0 = clean, 1 = problem found.
"""
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_EXT = {
    '.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff',
    '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.opus',
    '.mp4', '.mov', '.webm', '.mkv', '.avi',
    '.zip', '.7z', '.rar', '.tar', '.gz',
    '.pth', '.pt', '.bin', '.safetensors', '.ckpt', '.onnx',
    '.pem', '.key', '.p12',
}
FORBIDDEN_NAMES = {'kaggle.json', '.env'}
MAX_BYTES = 1_000_000
SECRET_PATTERNS = [
    (r'sk-[A-Za-z0-9_-]{20,}', 'API key (sk-...)'),
    (r'AIza[0-9A-Za-z_-]{30,}', 'Google API key'),
    (r'gh[pousr]_[A-Za-z0-9]{30,}', 'GitHub token'),
    (r'KGAT_[A-Za-z0-9]{10,}', 'Kaggle token'),
    (r'-----BEGIN [A-Z ]*PRIVATE KEY-----', 'private key'),
    (r'"key"\s*:\s*"[0-9a-f]{20,}"', 'kaggle.json style key'),
    (r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\'\s]{16,}["\']', 'hard-coded secret'),
]


ROOT = Path(__file__).resolve().parent.parent


def git_names(*args):
    """File names git would commit. -z + utf-8 so non-ASCII Windows paths are read correctly."""
    r = subprocess.run(['git', '-c', 'core.quotepath=off', *args, '-z'], capture_output=True, cwd=ROOT, check=True)
    return {n for n in r.stdout.decode('utf-8').split(chr(0)) if n}


def candidate_files():
    names = git_names('ls-files') | git_names('ls-files', '-o', '--exclude-standard')
    return ROOT, sorted(names)


def main():
    root, files = candidate_files()
    problems = []
    for name in files:
        p = root / name
        if not p.is_file():
            if (root / name).exists():
                continue
            problems.append(f'{name}: listed by git but not found on disk (cannot be checked)')
            continue
        ext = p.suffix.lower()
        if ext in FORBIDDEN_EXT:
            problems.append(f'{name}: forbidden file type {ext} (private media / weights / archive)')
            continue
        if p.name in FORBIDDEN_NAMES:
            problems.append(f'{name}: credential file')
            continue
        if p.stat().st_size > MAX_BYTES:
            problems.append(f'{name}: larger than 1 MB')
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            problems.append(f'{name}: binary file not allowed')
            continue
        if p.name == 'privacy_check.py':
            continue  # this file contains the patterns themselves
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                problems.append(f'{name}: looks like a secret ({label})')
    if problems:
        print('PRIVACY CHECK FAILED - nothing should be committed until fixed:')
        for pr in problems:
            print('  -', pr)
        return 1
    print(f'privacy check OK ({len(files)} files)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
