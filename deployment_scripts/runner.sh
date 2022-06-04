#!/usr/bin/env bash
export PYTHONPATH=/home/lioryardeni/trolley
export JENKINS_PASSWORD=r4d10h34d0kc0mput3r
export SECRET_KEY=s3cr3tk3y
which python3
source /home/lioryardeni/venv/bin/activate
cd /home/lioryardeni/trolley || exit
python3 main.py &