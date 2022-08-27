#!/usr/bin/env bash
kill $(lsof -i:8081 | awk '{print $2}'| awk 'NR==2{print $1}')
export PYTHONPATH=/home/pavelzagalsky/trolley
export SECRET_KEY=s3cr3tk3y
which python3
source /home/pavelzagalsky/venv/bin/activate
cd /home/pavelzagalsky/trolley/web || exit
python3 main.py &