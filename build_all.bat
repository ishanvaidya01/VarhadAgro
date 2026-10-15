@echo off
title VarhadCrop Model Training ^& Build Pipeline
echo Running end-to-end model training, CQR calibration, and evaluation...
python -m scripts.build_all
pause
