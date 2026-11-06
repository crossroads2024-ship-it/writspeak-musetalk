# Plan: moving approved videos into WritSpeak (do NOT start before the proof of concept is approved)

Nothing here has been done. The production WritSpeak repo is untouched.

## 1. Render all clips (after approval)
`python scripts/kaggle_run.py --inputs private-inputs --all` (or the notebook with `--all`). Output: `<clip>__<base>.mp4`, one per question, chosen base look only.
Run `scripts/validate_outputs.py` and watch a sample of at least 10 clips before copying anything.

## 2. Files and naming
WritSpeak serves everything in `public/` as static assets (Cloudflare Workers, limit 25 MiB per file; each clip is far below).
Suggested path: `public/avatar/talk/<question id>.mp4` (same ids as `public/audio/examiner/<question id>.mp3`). The mp4 contains the Libby audio, so the
existing "Hear the question" mp3 can stay as a fallback.
Size budget: aim for under 0.4 MB per clip (about 30 MB total). If larger, re-encode with `ffmpeg -crf 26 -movflags +faststart`.

## 3. Code change in WritSpeak (small, on a branch + PR, as AGENTS.md requires)
- In `public/app.js`, where the avatar idle/listening/talking clips are chosen (avatar.js), when a Speaking question is read aloud play `/avatar/talk/<id>.mp4`
  (unmuted, with `playsinline`) instead of the mp3 + silent `talking.mp4`; on `ended` return to the idle or listening loop.
- Keep idle/listening/thinking from the same base look so the face does not jump. If the PoC shows a visible jump at start/end, add a 150 ms cross-fade.
- Autoplay: browsers require a user click first. The existing "Hear the question" button already is that click.
- Preload the first clip's metadata only; do not preload all 77 (mobile data).

## 4. Security rules (checked against `public/_headers`)
`media-src 'self' blob:` already allows same-origin video. No script, worker, WebAssembly, font or connect-src change is needed. No third-party host.
Run `npm test` and add one test that every question id in `src/bank_speaking.js` has a matching mp4 when the feature is on.

## 5. Deployment (owner decision)
Merge to main triggers the existing deploy workflow. First check Cloudflare's current static-asset file count limit for the plan (about 77 more files).
Roll back by removing the branch change; the old mp3 button keeps working.

## 6. Before going live
- Resolve or accept the three UNRESOLVED helper-model licences in docs/LICENSES.md.
- Add the attribution list to a public credits/privacy section (the repo rule says only privacy.html may name providers).
- Confirm Jogenesis/KIE terms for commercial use of the portrait.
