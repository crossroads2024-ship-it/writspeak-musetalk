@echo off
rem One-click: upload private inputs to YOUR private Kaggle dataset, run the notebook on a free GPU, download the results.
rem Usage: run_poc.cmd "C:\path\to\private-inputs"
if "%~1"=="" (
  echo Usage: run_poc.cmd "C:\path\to\private-inputs"
  exit /b 1
)
cd /d "%~dp0"
python -m pip install --quiet kaggle
python scripts\privacy_check.py || exit /b 1
python scripts\kaggle_run.py --inputs "%~1"
