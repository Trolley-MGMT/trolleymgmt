
#!/bin/bash


echo "CLUSTER_NAME is $CLUSTER_NAME"
echo "VERSION is $VERSION"
echo "NUM_NODES is $NUM_NODES"
echo "EXPIRATION_TIME is $EXPIRATION_TIME"

eksctl create cluster --region=us-east-2 --zones=us-east-2a,us-east-2b,us-east-2c --name $CLUSTER_NAME \
--version $VERSION \
--nodes $NUM_NODES \


echo "Adding a PYTHONPATH"
root_path=$WORKSPACE
export PYTHONPATH=${root_path}
echo $PYTHONPATH
echo "WORKSPACE is $WORKSPACE"



# Generating a temp venv
#echo "Generating a temp venv"
#export RANDOM_VENV=venv_$(shuf -i 1-100000 -n 1)

# Creating a new Python3 virtual environment
# echo "Creating a random venv"
# python3 -m venv $RANDOM_VENV

# Activating the temp venv
# echo "Activating the temp venv"
# source $WORKSPACE/$RANDOM_VENV/bin/activate

# Installing project's requirements
# echo "Installing project's requirements"
# pip3 install -r $WORKSPACE/requirements.txt

# Running post deployment Kubernetes script
# echo "Running python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke --project_id trolley --cluster_name $CLUSTER_NAME --zone_name $ZONE_NAME --expiration_time $EXPIRATION_TIME"
# python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type gke --project_id trolley --cluster_name $CLUSTER_NAME --zone_name $ZONE_NAME --expiration_time $EXPIRATION_TIME

# Removing a temp venv
# rm -R $WORKSPACE/$RANDOM_VENV
