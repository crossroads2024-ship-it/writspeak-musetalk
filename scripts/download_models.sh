#!/usr/bin/env bash
# Downloads ONLY the weights MuseTalk 1.5 needs for inference. Source of every file is listed in docs/LICENSES.md.
# Not downloaded on purpose: syncnet (latentsync_syncnet.pt, OpenRAIL++) and MuseTalk 1.0 weights - training/old version only.
set -euo pipefail
WORK="${WORK:-/kaggle/working}"
cd "$WORK/MuseTalk"
PY="$WORK/mt310/bin/python"
HF="$WORK/mt310/bin/huggingface-cli"
mkdir -p models/musetalkV15 models/dwpose models/face-parse-bisent models/sd-vae models/whisper
"$PY" -m pip install -q "huggingface_hub[cli]==0.30.2" gdown

$HF download TMElyralab/MuseTalk --local-dir models --include "musetalkV15/musetalk.json" "musetalkV15/unet.pth"
$HF download stabilityai/sd-vae-ft-mse --local-dir models/sd-vae --include "config.json" "diffusion_pytorch_model.bin"
$HF download openai/whisper-tiny --local-dir models/whisper --include "config.json" "pytorch_model.bin" "preprocessor_config.json"
$HF download yzd-v/DWPose --local-dir models/dwpose --include "dw-ll_ucoco_384.pth"
curl -fL https://download.pytorch.org/models/resnet18-5c106cde.pth -o models/face-parse-bisent/resnet18-5c106cde.pth

# Face-parsing weights (BiSeNet) are published on Google Drive by the face-parsing.PyTorch project.
# Drive sometimes refuses automated downloads ("quota exceeded"). If this step fails, see README > Troubleshooting.
"$WORK/mt310/bin/gdown" --id 154JgKpzCPW82qINcVieuPH3fZ2e0P812 -O models/face-parse-bisent/79999_iter.pth

# S3FD face detector and FAN landmark weights are fetched by MuseTalk itself at first run (adrianbulat.com, see docs/LICENSES.md).
for f in models/musetalkV15/unet.pth models/musetalkV15/musetalk.json models/sd-vae/diffusion_pytorch_model.bin \
         models/whisper/pytorch_model.bin models/dwpose/dw-ll_ucoco_384.pth \
         models/face-parse-bisent/resnet18-5c106cde.pth models/face-parse-bisent/79999_iter.pth; do
  [ -s "$f" ] || { echo "MISSING: $f"; exit 1; }
done
echo "MODELS OK"; du -sh models
