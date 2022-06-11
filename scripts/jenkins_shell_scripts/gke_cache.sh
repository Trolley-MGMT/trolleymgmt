#!/bin/bash

echo "Running gcloud compute zones list --format json --zone $ZONE_NAME"
gcloud compute zones list --format json --zone $ZONE_NAME
echo "Running gcloud compute regions list --format jaon --region $REGION_NAME"
gcloud compute regions list --format jaon --region $REGION_NAME

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
echo "Installing projects requirements"
pip3 install -r $WORKSPACE/requirements.txt

# Running post deployment Kubernetes script
echo "Running python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke --project_id $PROJECT_NAME --cluster_name $CLUSTER_NAME --user_name $USER_NAME --zone_name $ZONE_NAME --helm_installs $HELM_INSTALLS --expiration_time $EXPIRATION_TIME"
python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke --project_id $PROJECT_NAME --cluster_name $CLUSTER_NAME --user_name $USER_NAME --zone_name $ZONE_NAME --helm_installs $HELM_INSTALLS --expiration_time $EXPIRATION_TIME

rm -R $WORKSPACE/$RANDOM_VENV