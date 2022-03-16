#!/bin/bash


echo "CLUSTER_NAME is $CLUSTER_NAME"
echo "PROJECT_NAME is $PROJECT_NAME"
echo "REGION_NAME is $REGION_NAME"
echo "EXPIRATION_TIME is: $EXPIRATION_TIME"

gcloud beta container --project $PROJECT_NAME clusters create-auto $CLUSTER_NAME --region $REGION_NAME --release-channel "regular" --network "projects/trolley/global/networks/default" --subnetwork "projects/trolley/regions/us-central1/subnetworks/default" --cluster-ipv4-cidr "/17" --services-ipv4-cidr "/22"
whoami

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

# Running post deployment Kubernetes script
echo "Running python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke_autopilot --project_id trolley --cluster_name $CLUSTER_NAME --region_name $REGION_NAME --expiration_time $EXPIRATION_TIME"
python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke_autopilot --project_id trolley --cluster_name $CLUSTER_NAME --region_name $REGION_NAME --expiration_time $EXPIRATION_TIME

# Removing a temp venv
rm -R $WORKSPACE/$RANDOM_VENV