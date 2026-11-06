"""Regenerates notebooks/writspeak_musetalk.ipynb. Run:  python tools/make_notebook.py <github-owner>"""
import json
import sys
from pathlib import Path

OWNER = sys.argv[1] if len(sys.argv) > 1 else 'OWNER'


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n").splitlines(True)}


cells = [
    md("""
# WritSpeak x MuseTalk 1.5 - proof of concept (Kaggle free GPU)
Public code, private data. This notebook downloads the public scripts from GitHub, installs MuseTalk, renders the **6 proof-of-concept videos**
from YOUR private dataset, checks them, and writes everything to `/kaggle/working/out`.

**One-time settings** (right panel): Accelerator = GPU T4/P100, Internet = On, Add Input = your private dataset `writspeak-examiner-inputs`.
Then **Run All**. First run takes about 20-40 minutes. If a cell turns red, copy the red text and send it back.
Nothing here uploads your files anywhere except your own private Kaggle session.
"""),
    code("""
import glob, os, subprocess
REPO = 'https://github.com/__OWNER__/writspeak-musetalk.git'
hits = glob.glob('/kaggle/input/**/examiner-source.jpg', recursive=True)
assert hits, 'Private dataset not attached: use Add Input > Your Datasets > writspeak-examiner-inputs'
INPUTS = os.path.dirname(hits[0]); print('private inputs:', INPUTS, sorted(os.listdir(INPUTS)))
if not os.path.isdir('/kaggle/working/repo'):
    subprocess.run(['git', 'clone', '--depth', '1', REPO, '/kaggle/working/repo'], check=True)
print(subprocess.run(['git', '-C', '/kaggle/working/repo', 'log', '-1', '--format=%h %s'], capture_output=True, text=True).stdout)
""".replace("__OWNER__", OWNER)),
    md("## 1. Install MuseTalk 1.5 (official repo, pinned versions)"),
    code("""
import subprocess
def run(cmd, log):
    r = subprocess.run(cmd + ' > ' + log + ' 2>&1', shell=True, executable='/bin/bash')
    tail = subprocess.run(['tail', '-30', log], capture_output=True, text=True).stdout
    print(tail)
    if r.returncode != 0:
        raise RuntimeError('FAILED (exit %d). Copy the lines above and send them back.' % r.returncode)
run('bash /kaggle/working/repo/scripts/install_env.sh', '/kaggle/working/install.log')
"""),
    md("## 2. Download the open model weights (sources and licences: docs/LICENSES.md)"),
    code("run('bash /kaggle/working/repo/scripts/download_models.sh', '/kaggle/working/models.log')"),
    md("## 3. Plan, then render the 6 proof-of-concept videos (2 Libby clips x 3 base looks)"),
    code("run('python /kaggle/working/repo/scripts/render.py --inputs \"%s\" --out /kaggle/working/out --dry-run' % INPUTS, '/kaggle/working/plan.log')"),
    code("run('python /kaggle/working/repo/scripts/render.py --inputs \"%s\" --out /kaggle/working/out' % INPUTS, '/kaggle/working/render.log')"),
    md("## 4. Check the results (file checks + comparison of the three looks)"),
    code("""
run('/kaggle/working/mt310/bin/python /kaggle/working/repo/scripts/report.py --out /kaggle/working/out --inputs "%s"' % INPUTS, '/kaggle/working/report.log')
print(open('/kaggle/working/out/report.md').read())
"""),
    code("""
import glob
from IPython.display import Video, display
for f in sorted(glob.glob('/kaggle/working/out/*.mp4'))[:6]:
    print(os.path.basename(f)); display(Video(f, embed=True, width=360))
"""),
    md("""
## 5. Get the files
Run finished: open the **Output** tab (or `/kaggle/working/out`) and download the mp4 files and `report.md`.
If you ran this with `scripts/kaggle_run.py` on your PC, they are downloaded for you into `results\\`.
"""),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                    "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
Path('notebooks').mkdir(exist_ok=True)
Path('notebooks/writspeak_musetalk.ipynb').write_text(json.dumps(nb, indent=1), encoding='utf-8')
print('notebook written for', OWNER)
