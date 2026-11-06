# Licence and cost report (checked 6 Nov 2026)

**Not legal advice.** I read each project's own LICENSE / README / Hugging Face model card on 6 Nov 2026. "Verified" means I read that text;
"UNRESOLVED" means a restriction exists or I could not confirm commercial rights. The main MuseTalk MIT licence does NOT automatically cover the
helper models, so each one is listed separately.

## What the pipeline loads at inference (and nothing else)
| # | Component | Used for | Where it comes from | Licence (verified from) | Commercial use |
|---|---|---|---|---|---|
| 1 | MuseTalk code | the lip-sync pipeline | github.com/TMElyralab/MuseTalk | MIT (LICENSE file) | **Yes** |
| 2 | MuseTalk 1.5 weights `unet.pth` | repaints the mouth | huggingface.co/TMElyralab/MuseTalk | MIT (model card) + README: "available for any purpose, even commercially". README says trained on HDTF and a private dataset; I cannot verify the HDTF dataset terms | **Yes per authors**; training-data terms not verifiable by me |
| 3 | sd-vae-ft-mse | image encoder/decoder | huggingface.co/stabilityai/sd-vae-ft-mse | MIT (model card) | **Yes** |
| 4 | whisper-tiny | audio features | huggingface.co/openai/whisper-tiny | Apache-2.0 (model card) | **Yes** |
| 5 | DWPose `dw-ll_ucoco_384.pth` | face landmarks | huggingface.co/yzd-v/DWPose | Apache-2.0 (model card) | **Yes** (trained on COCO-WholeBody/UBody; dataset terms not checked) |
| 6 | mmengine / mmcv 2.0.1 / mmdet 3.1.0 / mmpose 1.1.0 | runs DWPose | pip (OpenMMLab) | Apache-2.0 (LICENSE files read for mmcv, mmdet, mmengine; mmpose earlier) | **Yes** |
| 7 | torch 2.0.1, torchvision, diffusers, transformers, accelerate, opencv-python, librosa, numpy | runtime | pip | BSD / Apache / MIT (standard; not individually re-read) | Yes |
| 8 | **Face-parsing BiSeNet `79999_iter.pth`** | blends the new mouth into the face | Google Drive file (id `154JgKpzCPW82qINcVieuPH3fZ2e0P812`, https://drive.google.com/file/d/154JgKpzCPW82qINcVieuPH3fZ2e0P812/view) published by github.com/zllrunning/face-parsing.PyTorch | Code: MIT (LICENSE read). **Weights were trained on CelebAMask-HQ, whose own README says "non-commercial research purposes only"** | **UNRESOLVED** |
| 9 | resnet18 ImageNet weights | backbone of #8 | download.pytorch.org (torchvision) | torchvision code BSD-3; ImageNet-pretrained weights follow ImageNet terms (research) | **UNRESOLVED** (widely used commercially; risk accepted by many, not mine to decide) |
| 10 | S3FD face detector `s3fd-619a316812.pth` and FAN landmark weights | face box | downloaded by MuseTalk at first run from adrianbulat.com (face-alignment project) | face-alignment code: BSD-3 (LICENSE read). Weights trained on WIDER FACE / 300W-style research datasets; weight licence not stated in the repo | **UNRESOLVED** |

## Deliberately NOT used
- `latentsync_syncnet.pt` (ByteDance/LatentSync, licence OpenRAIL++): MuseTalk loads it only for training. `scripts/download_models.sh` skips it.
- MuseTalk 1.0 weights: not needed.
- Wav2Lip, SadTalker, LivePortrait: rejected earlier (see COMPARISON in the private project folder).

## What this means
- Software cost: $0. Everything above can be downloaded without payment or sign-in.
- **Three helper weights (#8, #9, #10) have unresolved commercial status because they were trained on research-only datasets.** For a free
  proof of concept this does not matter. Before the clips go on a paid product, WritSpeak should either (a) accept the risk knowingly,
  (b) ask the authors, or (c) replace them: MuseTalk's blending can run without the face parser (`--parsing_mode raw` still builds the parser, so a small
  code change would be needed), and the face detector could be swapped for an Apache/MIT one. I have NOT done (c); it is a later, optional step.
- The 77 output videos are ordinary MP4 files. Generated output does not itself carry the MIT/Apache licence text, but attribution to the projects
  should appear in your credits/notices page (see NOTICE below).
- The portrait is an invented person generated with Jogenesis (nano-banana-2-1). Check Jogenesis/KIE terms for commercial use of generated images separately; I did not.

## Kaggle (free GPU) terms
Free GPU quota is reported by third-party sources as about 30 GPU-hours/week, 16 GB T4/P100. Phone verification is required to enable GPU and internet.
I did NOT read Kaggle's terms of service for commercial use of outputs; the render is a one-off batch of non-confidential material on your own private notebook.

## Costs
| Item | Cost |
|---|---|
| MuseTalk + models | $0 |
| Free Kaggle GPU for 6-video PoC | $0 (estimate 20-40 min incl. install, unverified) |
| Free Kaggle GPU for 77 clips | $0 (estimate, unverified) |
| GitHub public repo, no Actions, no Git LFS | $0 |
| Hosting 77 mp4 on Cloudflare Workers static assets | $0 extra (estimate about 15-25 MB total, to be measured) |
| Jogenesis credits, paid avatar API, paid GPU | none used |

## Attribution to publish (NOTICE)
MuseTalk, Copyright (c) 2024 Tencent Music Entertainment Group, MIT. sd-vae-ft-mse (stabilityai), MIT per its model card. whisper-tiny (OpenAI), Apache-2.0 per its model card.
DWPose (yzd-v/DWPose weights), Apache-2.0 per its model card; OpenMMLab projects, Apache-2.0. face-parsing.PyTorch, Copyright (c) 2019 zll, MIT. face-alignment, Copyright (c) 2017 Adrian Bulat, BSD-3-Clause.
Keep the full licence texts of these projects in your credits/notices page before publishing the videos commercially.
