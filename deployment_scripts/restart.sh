#!/usr/bin/env bash
kill $(lsof -i:8081 | awk '{print $2}'| awk 'NR==2{print $1}')
export PYTHONPATH=/home/lioryardeni/trolley
export SECRET_KEY=s3cr3tk3y
which python3
source /home/lioryardeni/venv/bin/activate
cd /home/lioryardeni/trolley || exit
python3 main.py &