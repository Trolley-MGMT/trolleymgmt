#!/usr/bin/env bash
export PYTHONPATH=/home/pavelzagalsky/trolley
export SECRET_KEY=s3cr3tk3y
which python3
source /home/pavelzagalsky/venv/bin/activate
cd /home/pavelzagalsky/trolley/web || exit
python3 main.py &