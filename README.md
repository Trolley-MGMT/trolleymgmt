# trolley


Trolley is a multi cloud Kubernetes management system. A simplified UI which allows the user to Deploy, edit and delete clusters on AWS, Azure and GCP. 

##The headache 
For many, the deployment process of a cluster isn’t trivial. Product people, marketing, testers, junior programmers. They all know it can be a pain. With this simple GUI, the deployment process becomes so much easier. You choose the different required parameters via multi selection live list, i.e. server location, cluster version etc, and click deploy. That’s it. deploy>boom>cluster.

Many team leaders know how painful trying to monitor and supervise their team’s clusters can be. Even more when your team is using more than one cloud provider. At some point, you find this hidden cluster which has been bleeding your money dry for the last two weeks. 

The clusters built with Trolley have an expiration date, and they will show on your UI  monitoring screen and database.

##The boom part
When the user clicks deploy, it triggers a Jenkins build which formulates the specific CLI command and deploys the desired cluster. The built cluster would then register in the mongoDB database and be available to monitor, extract data or delete via the UI. 



The project is still at a very early stage and would appreciate any contributions and feedback.  
