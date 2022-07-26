
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

