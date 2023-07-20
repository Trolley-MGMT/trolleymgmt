# Trolley

Trolley is a multi cloud Kubernetes management system. A simplified UI which allows the user to Deploy, Edit and Delete
clusters and deployments within them on AWS, Azure and GCP.

## The problem

For many, the deployment and the management process of a Kubernetes cluster isn’t trivial. Product people, marketing,
testers, junior programmers. They all know it can be a pain. With this simple GUI, the deployment process becomes so
much easier. You choose the different required parameters via multi selection live list, i.e. server location, cluster
version etc, and click deploy. That’s it. deploy>boom>cluster.

Many team leaders know how painful trying to monitor and supervise their team’s clusters can be. Even more when your
team is using more than one cloud provider. At some point, you find this hidden cluster which has been bleeding your
money dry for the last two weeks.

The clusters built with Trolley have an expiration date, and they will show on your UI monitoring screen and database.

## The solution

In order to deploy a cluster on a managed Kubernetes platform such as GKE/AKS and EKS all the user needs to do is select
a few simple options from the provided build menu and set the expiration time.
Once the build concludes the user will get an Email/Slack alert (tba) with all the info they need.
Alternatively, the user can go to the management menus and see there all the clusters they deployed.

## High level architecture

![](documentation/trolley_diagram.png)

# **Deployment**

Trolley deployment can be done in the following ways:

## Local deployment

To run the service locally and play with the code just do the following:

1. Run a local/remote/managed MongoDB instance. The details are here:
   https://www.mongodb.com/docs/manual/installation/
   After the installation is done, create a new database and call it "trolley" or whatever you want your fork to be
   called.
2. Fork the trolley repository and then clone it locally.
   You will need to fork it in order to trigger your own GitHub Actions that will build the clusters
3. Generate a personal GitHub Token that will allow you to use GitHun Actions. The token should The tokens can be
   obtained from here:
   https://github.com/settings/tokens
   It should look something like this: ghp_XXXXXXXXXXXXXXXX
4. Build a virtual environment:
   ```
   python3 -m venv trolley_venv
   ```
5. Install all the requirements:
   ```
   pip install -r web/requirements.txt
   ```
6. To run the flask based Python web app in your PyCharm IDE of choice you can edit the provided web/.env file that will
   include the following variables:

```shell
export GCP_PROJECT_NAME=<name of your gcp_project>
export GITHUB_ACTION_TOKEN=ghp_<github_token>
export GITHUB_REPOSITORY=<your_fork>/Trolley-Management
export EMAIL_AUTHENTICATION=Yes
export GMAIL_PASSWORD=<password>
export GMAIL_USER=<user>@gmail.com
export KUBECONFIG=/.kube/config
export MONGO_PASSWORD=<password>
export MONGO_URL=<mongo_url>
export MONGO_USER=admin
export PROJECT_NAME=trolley
export SECRET_KEY=<secret_kek>
export FLASK_APP=main.py
export TROLLEY_URL=https://localhost

```

### The parameters are:

### General Trolley parameters

```
SECRET_KEY(str): This 44 chars long key is needed for the encryption in the application. 
String example: 65L2Is2PGz9fMCSrg8eTRL1kcXDmH9BRS83JQ0YItqE0
```

```
GITHUB_ACTION_TOKEN(str):  This 44 chars long token allows the application to trigger GitHub Actions which will build EKS/GKE/AKS clusters using your forked Trolley GitHub Repository.
String example: ghp_p7R7O4mllCQTl1F5tQdyWS5Y6RWjRNU1ACH9
```

````
KUBECONFIG(str): Default location of your kubeconfig file with the build Kubernetes cluster definitions String example: /Users/<your_user>/.kube/config
````

### Mongo DB parameters

````
MONGO_URL: str The URL for the Mongo installation. This can be either a local installation
````

String example: localhost
Or with an Atlas DB installation:  
String example: trolley-fork.something.mongodb.net

More info here: [Atlas DB Tutorial](https://www.mongodb.com/basics/mongodb-atlas-tutorial)

````
MONGO_PASSWORD(str): Mongo DB Password
````

````
MONGO_USER(str): Mongo DB User
````

### Email parameters

For registrations and alerting we need access to a mail server.
I personally use a custom gmail account that takes care of it but any other email provider should do the trick just fine

````
GMAIL_USER(str): youruser@gmail.com
````

````
GMAIL_PASSWORD(str): yourpassword
````

To run the app in your IDE just set the script path to web/main.py and it should work from there

### GitHub Actions parameters

The project uses GitHub Actions functionality in order to build/monitor and delete various cloud assets.
In order to work with them properly we will need to pass AWS/GCP/Azure/Mongo related parameters.
Here are the parameters:

```shell
ACTION_TOKEN(mandatory): "ghp_xxxxxxxxxx"
````    

````    
AWS_ACCESS_KEY_ID(mandatory for aws): "AKIAIOSFODNN7EXAMPLE"
````

````
AWS_SECRET_ACCESS_KEY(mandatory for aws): "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
````

````
AZURE_CREDENTIALS(mandatory for azure): "d8er22sc-0000-5esd-be90-example"
````

````
DOCKERHUB_TOKEN(mandatory): "dckr_pat_example-example"
````

````
DOCKERHUB_USER(mandatory): "yourname"
````

````
GCP_PROJECT_ID(mandatory for gcp): "something-something"
````

````
GOOGLE_CREDS_JSON(mandatory for gcp): "{gcp_service_account json}"
````

````
MONGO_PASSWORD(optional): "mongopassword"
````

````
MONGO_URL(optional): "mongourl"
````

````
MONGO_USER(optional): "mongouser"
````

![](documentation/github_actions_secrets.png)

--------------

## Docker image build and deployment using Docker-Compose.

You can use a provided Docker image and build/run it on your local machine as well as a VM machine on your Cloud
Provider.
The Docker image and the provided docker-compose.yml will spin it a self contained Trolley app and a Mongo DB instance.
This is great for demoing the application locally or on the cloud.

In order to work with the Docker image as a composable Docker container the following steps must be taken:

1. Fork the repository and clone it locally.
2. Make sure Docker-Compose is locally installed.
3. Edit the docker-compose.yml file according to the directions provided within the file.
4. Run the following command from the project's root to build and run the Docker image:

````shell
docker-compose up --build
````

------------
## Deployment on Kubernetes.

Trolley Server can be deployed on a Kubernetes cluster using `trolley_server_deployment.yaml` file under the `web/`
directory
The same parameters as above need to be added under the `env:` column. There is 1 additional parameter here that need to
be taken care as well:
`TROLLEY_URL`. Under this parameter we want to pass the address against which the Trolley UI will operate with.
In our example we will use Kuberenets Port Forwarding to forward the requests from the deployed application
to http://localhost:8080

Prerequisites:

1. Working Kubernetes cluster. Minikube is ok as well.
2. Working MongoDB installation. Local or Remote.
3. kubectl installed in your workstation

Steps:

1. Let's start with changing all the parameters under `env:` parameter and adding the `TROLLEY_URL` parameter:
2.         - name: TROLLEY_URL
          value: "http://localhost:8080
3. After the yaml file was properly edited, make sure you have a connection to your k8s
   cluster: `kubectl get pods --all-namespaces`
4. Create a `trolley` namespace using: `kubectl create namespace trolley`
5. Run: `kubectl apply -f trolley_server_deployment.yaml`
6. Verify deployment is up and running: `kubectl get pods -n trolley` and
   then `kubectl describe pod -n trolley trolley-deployment-<pod_id>`.
7. Verify the pod is in the running status.
8. Run port-forwarding for kubernetes to allow access
   locally: `kubectl port-forward deployment/trolley-deployment -n trolley 8080:80 &`
9. Check the port forwarding works well:

```shell
   curl http://localhost:8080/healthz
```

```commandline
   Handling connection for 8080
   "OK"
```

If you get this response it means you can register and log into Trolley: http://localhost:8080

-----------

# Infracost Integration
It is possible, starting v0.6, to add Infracost API Integration to Trolley to allow predicting clusters' billing.
The prediction is done using Infracost's Pricing API and is calculated by counting the expiration time of the clusters that are being built and the nodes it is expected to use.
To activate the feature simply register for a Token on their webpage: https://www.infracost.io/ and use the created token to add in the Settings Menu

![](documentation/infracost_settings.png)

The calculation is expected to start withing 15 minutes following the token insertion. 
# UI Overview

Short Video Demo:

[![Watch the video](https://i9.ytimg.com/vi/GHJHqFtwDHc/mq2.jpg?sqp=CMSns6MG&rs=AOn4CLAkfQDCGLI02dkYu2PPDsX8tj3aGg)](https://www.youtube.com/watch?v=GHJHqFtwDHc)

## First user logging in flow


Trolley comes preloaded with an admin user that can be used to start inviting the users and teams into the project.
To log in as an admin please use the following credentials:

```shell
user: admin@trolley.org
password: tr00lley
```
This is the Login menu that will allow the users to login to the system

![](documentation/login.png)

### Setting up teams in Trolley:

In order to add new teams to Trolley please use the Teams page:

![](documentation/add_teams.png)

### Inviting users to Trolley:

To invite users go to the Users page and add new users within their teams.
The users will receive an invitation to join Trolley

![](documentation/invite_users.png)

### Setting up access to AWS/GCP/Azure and GitHub

Under the Settings menu we have an option to add credentials of the cloud provider we want to work with and for our
forked repository.

![](documentation/aws_settings.png)
![](documentation/gcp_settings.png)
![](documentation/azure_settings.png)

Notice that without the correct credentials you will not be able to access the Build/Manage pages for these cloud
providers!
After the providers were properly configured a discovery service will be triggered and will start to scan the cloud
services for the accounts that were provided. 
Please allow a few minutes after initial scan is completed and all the Regions and Zones will appear in the GUI

### Building AKS/GKE/EKS clusters

![](documentation/build_aks_clusters.png)
![](documentation/build_gke_clusters.png)
![](documentation/build_eks_clusters.png)

### Managing AKS/GKE/EKS clusters

![](documentation/manage_aks.png)
![](documentation/manage_gke.png)
![](documentation/manage_eks.png)

### Managing VM Instances (AWS/GCP/Azure(TBC))

![](documentation/manage_aws_ec2_instances.png)
![](documentation/manage_gcp_vm_instances.png)

Upon pressing the cluster name you will be prompted with an option to install a Trolley Agent or if it was installed,
additional cluster info
![](documentation/cluster_install_trolley_agent.png)
The server address is an external IP/URL that runs your Trolley Server. You can use [ngrok](https://ngrok.com/) to
tunnel into your local environment for debugging
![](documentation/cluster_additional_info.png)
Clicking on More Info will fetch you more information
The project is still at a very early stage and would appreciate any contributions and feedback.

### Managing Users

![](documentation/manage_users.png)
![](documentation/add_user.png)

### Managing Teams

![](documentation/manage_teams.png)
![](documentation/add_team.png)

### Managing Clients

![](documentation/manage_clients.png)
![](documentation/add_client.png)

### Billing Dashboards TBD
