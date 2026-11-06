# writspeak-musetalk

Free, self-run pipeline that turns **one portrait + existing audio clips** into **talking-head MP4 videos** with
[MuseTalk 1.5](https://github.com/TMElyralab/MuseTalk), using Kaggle's free GPU. Built for the WritSpeak IELTS Speaking examiner.
This repository holds **code only**. Your portrait, voice clips and any other private files never go into it.

> **Status (honest):** the helper scripts are tested locally on a PC without a GPU (see table). The MuseTalk install and render
> have **not yet been run on a GPU**; that is the first thing the Kaggle run will prove. Do not treat the rendering part as working until it has.

## Privacy rules (enforced, not just promised)
- `.gitignore` blocks images, audio, video, archives, model weights, keys and `kaggle.json`.
- `scripts/privacy_check.py` scans everything git would commit and fails on any of those, files over 1 MB, or text that looks like a secret.
  `.githooks/pre-commit` runs it on every commit (`git config core.hooksPath .githooks`).
- Private inputs live in a folder **outside** this repo (for example `C:\...\private-inputs`) and in a **private** Kaggle dataset.
- No GitHub Actions, no Git LFS, no third-party service: nothing here can create a bill.

## What you need
1. A free Kaggle account with phone verification (Kaggle requires it to switch on GPU and internet). Only you can do this.
2. A Kaggle API token saved as `%USERPROFILE%\.kaggle\kaggle.json` (kaggle.com > Settings > API > Create New Token). Only you can do this; I never see it.
3. A folder with your private files, exactly these names:
   - `examiner-source.jpg` (the portrait), `idle.mp4`, `talking.mp4` (existing silent clips of the same woman)
   - `p1-food-4.mp3`, `p1-food.mp3` (two Libby clips; names listed in `configs/render.json`)
4. Python 3 on your PC.

## Run it - automatic (about 3 commands)
```bat
git clone https://github.com/crossroads2024-ship-it/writspeak-musetalk.git
cd writspeak-musetalk
run_poc.cmd "C:\path\to\private-inputs"
```
It uploads the inputs to your **private** Kaggle dataset, starts the notebook on a free GPU, waits, downloads the 6 videos and `report.md` into `results\`.
(`python scripts\kaggle_run.py --inputs private-inputs --dry-run` shows what would be sent without calling Kaggle.)

## Run it - manual (no command line)
1. Kaggle > Datasets > New Dataset: upload your private files, name it `writspeak-examiner-inputs`, keep it Private.
2. Kaggle > Code > New Notebook > File > Import Notebook: upload `notebooks/writspeak_musetalk.ipynb` from this repo.
3. Right panel: Accelerator = GPU, Internet = On, Add Input = your dataset. Run All.
4. Download the files from the Output tab.

## What the notebook does
`install_env.sh` (Python 3.10 environment, torch 2.0.1+cu118, MMLab, pinned requirements) ->
`download_models.sh` (only inference weights; list in docs/LICENSES.md) ->
`render.py` (2 clips x 3 base looks = 6 videos) ->
`validate_outputs.py` + `analyze_quality.py` + `report.py` (checks and comparison).

The three base looks compared: `idle` (silent idle clip), `talking` (silent talking clip), `still` (the 1024 px portrait only).

## What is verified so far
| Item | Status |
|---|---|
| `privacy_check.py` blocks media/keys, passes clean repo | tested locally |
| `validate_outputs.py` reads real MP4 (size, resolution, fps, audio track, A/V length) | tested locally on the real base clips |
| `analyze_quality.py` metrics run; no false lip-sync on unrelated audio | tested locally (control) |
| `render.py --dry-run` plan, error on unknown clip | tested locally |
| `kaggle_run.py --dry-run` stages dataset + kernel metadata | tested locally |
| Notebook JSON valid, all code cells parse | tested locally |
| MuseTalk install on Kaggle | **not yet run** |
| Model download (incl. Google Drive file) | **not yet run** |
| MuseTalk render quality and lip-sync | **not yet run** |
| Kaggle API upload/run/download | **not yet run** (needs your credentials) |

## Troubleshooting
- **Google Drive "quota exceeded" for the face-parsing file:** download `79999_iter.pth` manually from the link in `docs/LICENSES.md` row 8, add it to your private dataset, and tell the maintainer; the script will be changed to read it from there.
- **No GPU / "cuda available: False":** notebook settings > Accelerator > GPU.
- **Internet off:** notebook settings > Internet > On (phone verification needed).
- Any red error: copy the last 30 lines and send them to whoever maintains this; do not edit the notebook.

## Licences
Our scripts: MIT (`LICENSE`). MuseTalk and models keep their own licences: see **docs/LICENSES.md** (three helper weights are UNRESOLVED for commercial use).
Moving approved videos into WritSpeak: **docs/INTEGRATION_PLAN.md**.
