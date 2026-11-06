#!/usr/bin/env bash
# Installs MuseTalk 1.5 into an isolated Python 3.10 environment (Kaggle/Linux, NVIDIA GPU).
# Follows the official MuseTalk README: torch 2.0.1+cu118, MMLab packages, pinned requirements.
# TensorFlow, TensorBoard and Gradio from the upstream requirements.txt are skipped: inference does not import them.
set -euo pipefail
WORK="${WORK:-/kaggle/working}"
ENV="$WORK/mt310"
PY="$ENV/bin/python"

command -v ffmpeg >/dev/null || (apt-get -qq update && apt-get -qq install -y ffmpeg)
pip -q install uv
[ -d "$ENV" ] || uv venv --seed --python 3.10 "$ENV"

uv pip install --python "$PY" "setuptools<70" wheel
uv pip install --python "$PY" torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
uv pip install --python "$PY" diffusers==0.30.2 accelerate==0.28.0 numpy==1.23.5 opencv-python==4.9.0.80 soundfile==0.12.1 \
  transformers==4.39.2 huggingface_hub==0.30.2 librosa==0.11.0 einops==0.8.1 omegaconf ffmpeg-python moviepy "imageio[ffmpeg]" \
  gdown requests tqdm pyyaml

# MMLab (DWPose landmarks). chumpy fails to build with isolation on new pip, so install it first without isolation.
"$PY" -m pip install -q -U openmim
"$PY" -m pip install -q chumpy --no-build-isolation || true
"$PY" -m mim install mmengine
"$PY" -m mim install "mmcv==2.0.1"
"$PY" -m mim install "mmdet==3.1.0"
"$PY" -m mim install "mmpose==1.1.0"

# MuseTalk source (official repository)
if [ ! -d "$WORK/MuseTalk" ]; then git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$WORK/MuseTalk"; fi
git -C "$WORK/MuseTalk" rev-parse HEAD > "$WORK/musetalk_commit.txt"

"$PY" - <<'EOF'
import torch, mmcv, mmpose, cv2
print('torch', torch.__version__, '| cuda available:', torch.cuda.is_available(), '| mmcv', mmcv.__version__, '| mmpose', mmpose.__version__, '| cv2', cv2.__version__)
assert torch.cuda.is_available(), 'No GPU: set Accelerator to GPU in the notebook settings'
EOF
echo "INSTALL OK"
