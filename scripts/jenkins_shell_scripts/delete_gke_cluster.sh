#!/bin/bash

echo "CLUSTER_NAME is $CLUSTER_NAME"
echo "REGION_NAME is $REGION_NAME"

gcloud beta container clusters delete $CLUSTER_NAME --region $REGION_NAME --quiet

echo "Adding a PYTHONPATH"
root_path=$WORKSPACE
export PYTHONPATH=${root_path}
echo $PYTHONPATH
echo "WORKSPACE is $WORKSPACE"


# Generating a temp venv
echo "Generating a temp venv"
export RANDOM_VENV=venv_$(shuf -i 1-100000 -n 1)

# Creating a new Python3 virtual environment
echo "Creating a random venv"
python3 -m venv $RANDOM_VENV

# Activating the temp venv
echo "Activating the temp venv"
source $WORKSPACE/$RANDOM_VENV/bin/activate

# Installing project's requirements
echo "Installing project's requirements"
pip3 install -r $WORKSPACE/requirements.txt

# Removing a temp venv
rm -R $WORKSPACE/$RANDOM_VENV