#!/usr/bin/env python3
"""Check rendered MP4 files without ffmpeg (pure Python box parser).

For each file: size, resolution, fps, video/audio duration, whether an audio track exists,
and whether audio and video lengths agree. Optional --expect-audio-dir compares the muxed audio
length with the original Libby clip length (WAV/MP3 header via soundfile if installed).
Usage:  python scripts/validate_outputs.py results/ [--max-mb 1.5] [--json report.json]
Exit code 1 if any file fails a hard check.
"""
import argparse
import json
import struct
import sys
from pathlib import Path


def boxes(data, start=0, end=None):
    end = len(data) if end is None else end
    pos = start
    while pos + 8 <= end:
        size, typ = struct.unpack('>I4s', data[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack('>Q', data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr:
            break
        yield typ.decode('latin1'), pos + hdr, pos + size
        pos += size


def find(data, path, start=0, end=None):
    """Return (payload_start, end) of the first box at the nested path."""
    for typ, s, e in boxes(data, start, end):
        if typ == path[0]:
            return (s, e) if len(path) == 1 else find(data, path[1:], s, e)
    return None


def parse_mp4(path):
    data = Path(path).read_bytes()
    moov = find(data, ['moov'])
    if not moov:
        raise ValueError('no moov box (not a finished MP4)')
    tracks = []
    for typ, s, e in boxes(data, *moov):
        if typ != 'trak':
            continue
        t = {}
        hdlr = find(data, ['mdia', 'hdlr'], s, e)
        t['kind'] = data[hdlr[0] + 8:hdlr[0] + 12].decode('latin1') if hdlr else '?'
        mdhd = find(data, ['mdia', 'mdhd'], s, e)
        if mdhd:
            v = data[mdhd[0]]
            if v == 1:
                ts, dur = struct.unpack('>IQ', data[mdhd[0] + 20:mdhd[0] + 32])
            else:
                ts, dur = struct.unpack('>II', data[mdhd[0] + 12:mdhd[0] + 20])
            t['seconds'] = dur / ts if ts else 0
        tkhd = find(data, ['tkhd'], s, e)
        if tkhd:
            w, h = struct.unpack('>II', data[tkhd[1] - 8:tkhd[1]])
            t['width'], t['height'] = w >> 16, h >> 16
        stts = find(data, ['mdia', 'minf', 'stbl', 'stts'], s, e)
        if stts and t.get('seconds'):
            n = struct.unpack('>I', data[stts[0] + 4:stts[0] + 8])[0]
            frames = sum(struct.unpack('>I', data[stts[0] + 8 + 8 * i:stts[0] + 12 + 8 * i])[0] for i in range(n))
            t['frames'] = frames
            t['fps'] = frames / t['seconds'] if t['kind'] == 'vide' else None
        tracks.append(t)
    return tracks


def audio_seconds(path):
    try:
        import soundfile as sf
        i = sf.info(str(path))
        return i.frames / i.samplerate
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--max-mb', type=float, default=1.5, help='warn above this size per clip')
    ap.add_argument('--expect-audio-dir', help='folder with the original audio to compare length with')
    ap.add_argument('--json')
    a = ap.parse_args()
    files = sorted(Path(a.folder).rglob('*.mp4'))
    if not files:
        print('no mp4 files found in', a.folder)
        return 1
    rows, failed = [], False
    for f in files:
        row = {'file': f.name, 'mb': round(f.stat().st_size / 1e6, 3), 'problems': [], 'warnings': []}
        try:
            tr = parse_mp4(f)
            v = next((t for t in tr if t['kind'] == 'vide'), None)
            s = next((t for t in tr if t['kind'] == 'soun'), None)
            if not v:
                row['problems'].append('no video track')
            else:
                row.update(width=v.get('width'), height=v.get('height'), fps=round(v['fps'], 2) if v.get('fps') else None, video_s=round(v['seconds'], 2))
            if not s:
                row['problems'].append('no audio track')
            else:
                row['audio_s'] = round(s['seconds'], 2)
            if v and s and abs(v['seconds'] - s['seconds']) > 0.15:
                row['problems'].append(f"audio/video length differ by {abs(v['seconds'] - s['seconds']):.2f}s")
            if a.expect_audio_dir and s:
                stem = f.stem.split('__')[-1] if '__' in f.stem else f.stem
                for ext in ('.mp3', '.wav'):
                    src = Path(a.expect_audio_dir) / (stem + ext)
                    if src.exists():
                        sec = audio_seconds(src)
                        if sec and abs(sec - s['seconds']) > 0.2:
                            row['problems'].append(f"audio length {s['seconds']:.2f}s differs from original {sec:.2f}s")
                        break
            if row['mb'] > a.max_mb:
                row['warnings'].append(f'larger than {a.max_mb} MB')
        except Exception as ex:
            row['problems'].append(f'unreadable: {ex}')
        failed |= bool(row['problems'])
        rows.append(row)
    for r in rows:
        status = 'FAIL' if r['problems'] else 'ok'
        print(f"[{status}] {r['file']}: {r['mb']} MB, {r.get('width')}x{r.get('height')} @ {r.get('fps')} fps, video {r.get('video_s')}s, audio {r.get('audio_s')}s", *r['problems'], *r['warnings'], sep=' | ')
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
