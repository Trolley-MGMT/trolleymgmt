# Trolley

Trolley is a multi cloud Kubernetes management system. A simplified UI which allows the user to Deploy, Edit and Delete clusters and deployments within them on AWS, Azure and GCP. 

## The headache 
For many, the deployment process of a cluster isn’t trivial. Product people, marketing, testers, junior programmers. They all know it can be a pain. With this simple GUI, the deployment process becomes so much easier. You choose the different required parameters via multi selection live list, i.e. server location, cluster version etc, and click deploy. That’s it. deploy>boom>cluster.

Many team leaders know how painful trying to monitor and supervise their team’s clusters can be. Even more when your team is using more than one cloud provider. At some point, you find this hidden cluster which has been bleeding your money dry for the last two weeks. 

The clusters built with Trolley have an expiration date, and they will show on your UI  monitoring screen and database.

## The boom part
In order to deploy a cluster on a managed Kubernetes platform such as GKE/AKS and EKS all the user needs to do is select a few simple options from the provided build menu and set the expiration time. 
Once the build concludes the user will get an Email/Slack alert (tba) with all the info they need.
Alternatively, the user can go to the management menus and see there all the clusters they deployed.


## Deployment
Trolley deployment can be done in the following ways:

### Local deployment
To run the service locally and play with the code just do the following:
1. Run a local/remote/managed MongoDB instance. The details are here:
https://www.mongodb.com/docs/manual/installation/
After the installation is done, create a new database and call it "trolley" or whatever you want your fork to be called.
2. Fork the trolley repository and then clone it locally.
You will need to fork it in order to trigger your own GitHub Actions that will build the clusters
3. Generate a personal GitHub Token that will allow you to use GitHun Actions. The token should The tokens can be obtained from here:
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
6. To run the flask based Python web app in your PyCharm IDE of choice you can:
Set your Environment Variables menu the following:

    ```
    PYTHONUNBUFFERED=1;SECRET_KEY=<44_chars_binary>;GCP_PROJECT_NAME=<gcp_project_name>;GITHUB_ACTION_TOKEN=ghp_<token>;GITHUB_REPOSITORY=Trolley-MGMT/Trolley-Management;KUBECONFIG=/Users/<your_user>/.kube/config_temp;MONGO_PASSWORD=<mongo_password>;MONGO_URL=<mongo_url>;MONGO_USER=<mongo_user>;PROJECT_NAME=trolley
    ```

7. To run the app in your IDE just set the script path to web/main.py and it should work from there


### Docker image build and deployment.
1. In order to work with the Docker image the following steps must be taken.
2. Assuming the repository was forked and cloned and docker-compose is installed:
3. Run the following command from the project's root to build and run the Docker image:

``
docker-compose up --build
``

## GitHub Actions parameters
The project uses GitHub Actions functionality in order to build/monitor and delete various cloud assets.
In order to work with them properly we will need to pass AWS/GCP/Azure/Mongo related parameters.
Here are the parameters:

`
ACTION_TOKEN(mandatory) = "ghp_xxxxxxxxxx"
`

`
AWS_ACCESS_KEY_ID(mandatory for aws) = "AKIAIOSFODNN7EXAMPLE"
`

`
AWS_SECRET_ACCESS_KEY(mandatory for aws) = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
`

`
AZURE_CREDENTIALS(mandatory for azure) = "d8er22sc-0000-5esd-be90-example"
`

`
DOCKERHUB_TOKEN(mandatory) = "dckr_pat_example-example"
`

`
DOCKERHUB_USER(mandatory) = "yourname"
`

`
GCP_PROJECT_ID(mandatory for gcp) = "something-something"
`

`
GOOGLE_CREDS_JSON(mandatory for gcp) = "{gcp_service_account json}"
`
### Mongo parameters are for cases when we have a remote installed MongoDB we want to work with
`
MONGO_PASSWORD(optional) = "mongopassword"
`

`
MONGO_URL(optional) = "mongourl"
`

`
MONGO_USER(optional) = "mongouser"
`

`
PROJECT_NAME = "trolley"
`

## UI Overview
The UI currently consists of the following flows:

This is the Registration menu that will allow the user to register with his current team's name

![](documentation/register.png)


This is the Login menu that will allow the users to login to the system

![](documentation/login.png)

Under the Settings menu we have an option to add credentials of the cloud provider we want to work with.

![](documentation/credentials.png)

### Building AKS/GKE/EKS clusters
![](documentation/build_aks.png)
![](documentation/build_gke.png)
![](documentation/build_eks.png)

### Managing AKS/GKE/EKS clusters
![](documentation/manage_aks.png)
![](documentation/manage_gke.png)
![](documentation/manage_eks.png)

### Managing VM Instances (AWS/GCP/Azure(TBC))
![](documentation/manage_aws_ec2_instances.png)
![](documentation/manage_gcp_vm_instances.png)



Upon pressing the cluster name you will be prompted with an option to install a Trolley Agent or if it was installed, additional cluster info
![](documentation/cluster_install_trolley_agent.png)
The server address is an external IP/URL that runs your Trolley Server. You can use [ngrok](https://ngrok.com/) to tunnel into your local environment for debugging
![](documentation/cluster_additional_info.png)
Clicking on More Info will fetch you more information
The project is still at a very early stage and would appreciate any contributions and feedback.  

### Clients/Users/Teams management TBD
### Billing Dashboards TBD
