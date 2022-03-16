#!/bin/bash


echo "CLUSTER_NAME is $CLUSTER_NAME"
echo "NUM_NODES is $NUM_NODES"
echo "AKS_VERSION is $AKS_VERSION"
echo "HELM_INSTALLS is $HELM_INSTALLS"

# az group create --name myResourceGroup --location eastus
echo "Running az aks create --resource-group myResourceGroup --location $AKS_LOCATION --name $CLUSTER_NAME --node-count $NUM_NODES --enable-addons monitoring --generate-ssh-keys --kubernetes-version $AKS_VERSION"
az aks create --resource-group myResourceGroup --location $AKS_LOCATION --name $CLUSTER_NAME --node-count $NUM_NODES --enable-addons monitoring --generate-ssh-keys --kubernetes-version $AKS_VERSION


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
echo "Running python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type aks --cluster_name $CLUSTER_NAME --resource_group $RESOURCE_GROUP --expiration_time $EXPIRATION_TIME --helm_installs $HELM_INSTALLS"
python3 $WORKSPACE/deployment_utils/kubernetes_post_deployment.py --cluster_type aks --cluster_name $CLUSTER_NAME --resource_group $RESOURCE_GROUP --expiration_time $EXPIRATION_TIME --helm_installs $HELM_INSTALLS

# Removing a temp venv
rm -R $WORKSPACE/$RANDOM_VENV