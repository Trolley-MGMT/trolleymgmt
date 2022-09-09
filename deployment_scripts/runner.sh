#!/usr/bin/env bash
export PYTHONPATH=/home/lioryardeni/trolley
export SECRET_KEY=s3cr3tk3y
which python3
source /home/lioryardeni/trolley_venv/bin/activate
cd /home/lioryardeni/trolley/web || exit
python3 main.py &