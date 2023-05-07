$(document).ready(function() {
    let debug = true;
    let trolley_remote_url = '';
    let trolley_local_url = 'localhost';
    let trolley_url = 'http://www.pavelzagalsky.com';
    let stored_user_type = window.localStorage.getItem("userType");
    if (isEmpty(stored_user_type) == true) {
        window.localStorage.setItem("userType", data['user_type']);
    } else {
        let user_type = window.localStorage.getItem("userType");
        if (user_type == "admin") {
            $("#users-div").show()
            $("#teams-div").show()
            $("#clients-div").show()
            $("#dashboards-div").show()
            $("#settings-div").show()
        }
    }
    window.localStorage.setItem("userName", data['user_name']);
    let user_name = window.localStorage.getItem("userName");
    window.localStorage.setItem("clusterName", data['cluster_name']);
    let clusterName = window.localStorage.getItem("clusterName");
    window.localStorage.setItem("objectsFilterType", "users");
    if (debug === true) {
        trolley_url = trolley_local_url;
        gitBranch = 'master'
        http = 'http://'
    } else {
        trolley_url = trolley_remote_url
        gitBranch = 'master'
        http = 'https://'
    }
    store_client_names()
    store_users_data()
    store_teams_data()
    store_clients_data()
    let query = false;
    let clustersManagePage = false;
    let instancesManagePage = false;
    let buildPage = false;
    let provider = 'something';
    let fullHREF = window.location.href;
    let pathname = window.location.pathname.split('/');
    if (fullHREF.includes("?")) {
        query = true;
    }

    let clusters_manage_table_header = `<table class="table table-striped projects">
        <thead>
        <tr><th style="width: 10%" class="text-center">Cluster Name</th>
            <th style="width: 10%" class="text-center">Cluster Region</th>
            <th style="width: 10%" class="text-center">Number of Nodes</th>
            <th style="width: 10%" class="text-center">Total vCPU</th>
            <th style="width: 10%" class="text-center">Total Memory</th>
            <th style="width: 10%" class="text-center">Kubernetes Version</th>
            <th style="width: 15%" class="text-center">Expiration Time</th>
            <th style="width: 15%" class="text-center" id="user-name-table">User Name</th>
            <th style="width: 15%" class="text-center" id="client-name-table">Client Name</th>
            <th style="width: 15%" class="text-center">Tags</th>
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let clusters_manage_table_footer = `</tr></tbody></table>`

    let instances_manage_table_header = `<div class="card-body p-0">
    <table class="table table-striped projects" >
        <thead>
        <tr><th style="width: 10%" class="text-center">Instance Name</th>
            <th style="width: 10%" class="text-center">Instance Region</th>
            <th style="width: 10%" class="text-center">Machine Type</th>
            <th style="width: 10%" class="text-center">Internal IP</th>
            <th style="width: 10%" class="text-center">External IP</th>
            <th style="width: 15%" class="text-center" id="user-name-table">User Name</th>
            <th style="width: 15%" class="text-center" id="client-name-table">Client Name</th>
            <th style="width: 15%" class="text-center">Tags</th>
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let instances_manage_table_footer = `</tr></tbody></table></div>`

    var clientElement = '';
    var userElement = '';
    var teamElement = '';

    if (query == true) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = true;
    } else if (pathname[1].includes('build')) {
        buildPage = true;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
    } else if ((pathname[1].includes('manage-eks')) || (pathname[1].includes('manage-aks')) || (pathname[1].includes('manage-gke'))) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = true;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
        window.localStorage.setItem("objectType", "cluster");
    } else if ((pathname[1].includes('manage-aws-ec2')) || (pathname[1].includes('manage-gcp-vm')) || (pathname[1].includes('manage-az-vm'))) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = true;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
        window.localStorage.setItem("objectType", "instance");
    } else if (pathname[1].includes('clusters-data')) {
        buildPage = false;
        clustersDataPage = true;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
    } else if (pathname[1].includes('data')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = true;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
    } else if (pathname[1].includes('users')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = true;
        teamsPage = false;
        queryPage = false;
    } else if (pathname[1].includes('teams')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = true;
        queryPage = false;
    } else if (pathname[1].includes('clients')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = true;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
    } else {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        teamsPage = false;
        queryPage = false;
    }
    if (($.inArray('build-aks-clusters', pathname) > -1) || ($.inArray('manage-aks-clusters', pathname) > -1) || ($.inArray('manage-az-vm-instances', pathname) > -1)) {
        clusterType = 'aks'
        provider = 'az'
        window.localStorage.setItem("clusterType", clusterType);
        window.localStorage.setItem("provider", provider);
    } else if (($.inArray('build-eks-clusters', pathname) > -1) || ($.inArray('manage-eks-clusters', pathname) > -1) || ($.inArray('manage-aws-ec2-instances', pathname) > -1)) {
        clusterType = 'eks'
        provider = 'aws'
        window.localStorage.setItem("clusterType", clusterType);
        window.localStorage.setItem("provider", provider);
    } else if (($.inArray('build-gke-clusters', pathname) > -1) || ($.inArray('manage-gke-clusters', pathname) > -1) || ($.inArray('manage-gcp-vm-instances', pathname) > -1)) {
        clusterType = 'gke'
        provider = 'gcp'
        window.localStorage.setItem("clusterType", clusterType);
        window.localStorage.setItem("provider", provider);
    }

    populate_logged_in_assets();

    if (buildPage) {
        populate_regions();
    }

    if (usersPage) {
        populate_users_data();
    }

    if (clientsPage) {
        populate_clients_data();
    }

    if (teamsPage) {
        populate_teams_data();
    }
    if (clustersManagePage) {
        store_clusters()
            .then((data) => {
                populate_kubernetes_clusters_objects()
            })
            .catch((error) => {
                console.log(error)
            })
        let user_type = window.localStorage.getItem("userType");
        if (user_type == 'admin') {
            $("#teams-users-dropdowns-box").show();
            $("#client-user-select-dropdowns-box").show();
            $("#client-name-table").show();
            populate_team_names()
            let teamNames = window.localStorage.getItem("teamNames");
            populate_user_names(teamNames.split(",")[0])
            populate_client_names()
        }

    }

    if (instancesManagePage) {
        store_instances(provider)
            .then((data) => {
                populate_instances_objects()
            })
            .catch((error) => {
                console.log(error)
            })
        let user_type = window.localStorage.getItem("userType");
        if (user_type == 'admin') {
            $("#teams-users-dropdowns-box").show();
            $("#client-user-select-dropdowns-box").show();
            $("#client-name-table").show();
            populate_team_names()
            let teamNames = window.localStorage.getItem("teamNames");
            populate_user_names(teamNames.split(",")[0])
            populate_client_names()
        }
    }

    if (clustersDataPage) {
        store_clusters()
            .then((data) => {
                store_client_names()
                populate_kubernetes_clusters_objects()
            })
            .catch((error) => {
                console.log(error)
            })
        populate_client_names();
    }

    if (queryPage) {
        populate_kubernetes_agent_data();
    }

    $("#build-cluster-button").click(function() {
        let data = ''

        AKSNodesAmount = $('#aks-nodes-amt').val();
        EKSNodesAmount = $('#eks-nodes-amt').val();
        GKENodesAmount = $('#gke-nodes-amt').val();
        HelmInstalls = $('#helm-installs-dropdown').val();
        AKSLocation = $('#aks-locations-dropdown').val();
        EKSLocation = $('#eks-locations-dropdown').val();
        EKSZones = $('#eks-zones-dropdown').val();
        EKSSubnets = $('#eks-subnets-dropdown').val();
        GKERegion = $('#gke-regions-dropdown').val();
        GKEZone = $('#gke-zones-dropdown').val();

        AKSKubernetesVersion = $('#aks-versions-dropdown').val();
        EKSKubernetesVersion = $('#eks-versions-dropdown').val();
        GKEKubernetesVersion = $('#gke-versions-dropdown').val();
        GKEImageType = $('#gke-image-types-dropdown').val();

        AKSExpirationTime = $('#aks-expiration-time').val();
        EKSExpirationTime = $('#eks-expiration-time').val();
        GKEExpirationTime = $('#gke-expiration-time').val();

        DeploymentYAML = $('#deployment-yaml').val();

        let trigger_aks_deployment_data = JSON.stringify({
            "user_name": user_name,
            "num_nodes": AKSNodesAmount,
            "version": AKSKubernetesVersion,
            "expiration_time": AKSExpirationTime,
            "aks_location": AKSLocation,
            "helm_installs": HelmInstalls,
            "deployment_yaml": DeploymentYAML
        });

        let trigger_eks_deployment_data = JSON.stringify({
            "user_name": user_name,
            "num_nodes": EKSNodesAmount,
            "version": EKSKubernetesVersion,
            "expiration_time": EKSExpirationTime,
            "eks_location": EKSLocation,
            "eks_zones": EKSZones,
            "eks_subnets": EKSSubnets,
            "helm_installs": HelmInstalls,
            "deployment_yaml": DeploymentYAML
        });

        let trigger_gke_deployment_data = JSON.stringify({
            "cluster_type": 'gke',
            "user_name": user_name,
            "num_nodes": GKENodesAmount,
            "version": GKEKubernetesVersion,
            "image_type": GKEImageType,
            "expiration_time": GKEExpirationTime,
            "gke_region": GKERegion,
            "gke_zone": GKEZone,
            "helm_installs": HelmInstalls,
            "deployment_yaml": DeploymentYAML
        });

        if (clusterType === 'aks') {
            url = http + trolley_url + "/trigger_aks_deployment";
            trigger_data = trigger_aks_deployment_data
            expiration_time = AKSExpirationTime
        } else if (clusterType == 'eks') {
            url = http + trolley_url + "/trigger_eks_deployment";
            trigger_data = trigger_eks_deployment_data
            expiration_time = EKSExpirationTime
        } else if (clusterType == 'gke') {
            url = http + trolley_url + "/trigger_gke_deployment";
            trigger_data = trigger_gke_deployment_data
            expiration_time = GKEExpirationTime
        } else {
            url = http + trolley_url + "/trigger_kubernetes_deployment";
            trigger_data = trigger_gke_deployment
            expiration_time = GKEExpirationTime
        }

        swal_message = 'An ' + clusterType + ' deployment was requested for ' +
            AKSKubernetesVersion + ' kubernetes version with ' +
            expiration_time + ' expiration time'

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(trigger_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
    });

    $("#add-provider-button").click(function() {
        let data = ''
        var cloud_provider = $('#cloud-providers-dropdown').val().toLowerCase();
        AWSAccessKeyID = $('#aws_access_key_id').val();
        AWSSecretAccessKey = $('#aws_secret_access_key').val();
        AzureCredentials = $('#azure_credentials').val();
        GoogleCredsJSON = $('#google_creds_json').val();


        let add_provider_data = JSON.stringify({
            "provider": cloud_provider,
            "aws_access_key_id": AWSAccessKeyID,
            "aws_secret_access_key": AWSSecretAccessKey,
            "azure_credentials": AzureCredentials,
            "google_creds_json": GoogleCredsJSON
        });


        url = http + trolley_url + "/provider";

        swal_message = 'A request to add a provider was sent'
        var forms = document.querySelectorAll('.needs-validation')

        // Loop over them and prevent submission
        Array.prototype.slice.call(forms)
            .forEach(function(form) {
                form.addEventListener('submit', function(event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    }

                    form.classList.add('was-validated')
                }, false)
            })
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(add_provider_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
    });

    $("#add-client-button").click(function() {
        $("#add-client-card-title-div").show();
        $("#add-client-button").hide();
        $("#submit-client-button").show();
        $("#clients-main-div").hide();
    })

    $("#add-user-button").click(function() {
        $("#add-user-card-title-div").show();
        $("#add-user-button").hide();
        $("#submit-user-button").show();
        $("#users-main-div").hide();
    })

    $("#add-team-button").click(function() {
        $("#add-team-card-title-div").show();
        $("#add-team-button").hide();
        $("#submit-team-button").show();
        $("#teams-main-div").hide();
    })

    $("#submit-user-button").click(function() {
        var userName = $('#user_name').val().toLowerCase();
        var userEmail = $('#user_email').val();
        var userTeamName = $('#user_team_name').val().toLowerCase();
        var userAdditionalInfo = $('#user_additional_info').val();


        let add_client_data = JSON.stringify({
            "user_name": userName,
            "user_email": userEmail,
            "team_name": userTeamName,
            "user_additional_info": userAdditionalInfo,
        });


        url = http + trolley_url + "/users";

        swal_message = 'A request to add a user was sent'

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(add_client_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
        location.reload();
    });

    $("#submit-team-button").click(function() {
        var teamName = $('#team_name').val().toLowerCase();
        var teamAdditionalInfo = $('#team_additional_info').val();


        let add_team_data = JSON.stringify({
            "team_name": teamName,
            "team_additional_info": teamAdditionalInfo,
        });


        url = http + trolley_url + "/teams";

        swal_message = 'A request to add a team was sent'

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(add_team_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
        location.reload();
    });

    $("#submit-client-button").click(function() {
        var clientName = $('#client_name').val().toLowerCase();
        var clientInternalProducts = $('#client-internal-products-used').val();
        var connectionName = $('#connection_name').val().toLowerCase();
        var connectionEmail = $('#connection_email').val().toLowerCase();
        var connectionPhoneNumber = $('#connection_phone_number').val();
        var clientWebAddress = $('#client_web_address').val().toLowerCase();
        var clientOfficeAddress = $('#client_office_address').val().toLowerCase();
        var clientAdditionalInfo = $('#client_additional_info').val();


        let add_client_data = JSON.stringify({
            "client_name": clientName,
            "client_internal_products": clientInternalProducts,
            "connection_name": connectionName,
            "connection_email": connectionEmail,
            "connection_phone_number": connectionPhoneNumber,
            "client_web_address": clientWebAddress,
            "client_office_address": clientOfficeAddress,
            "client_additional_info": clientAdditionalInfo,
        });


        url = http + trolley_url + "/clients";

        swal_message = 'A request to add a client was sent'

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(add_client_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
        location.reload();
    });

    $("#agent-deployment-button").click(function() {
        let clusterName = window.localStorage.getItem("clusterName");
        let clustersData = jQuery.parseJSON(window.localStorage.getItem("clustersData"));
        let clusterType = window.localStorage.getItem("clusterType");
        let trolleyServerURL = $('#trolley_server_url').val();

        $.each(clustersData, function(key, value) {
            if (value['cluster_name'] == clusterName) {
                cluster_name_to_send = value['cluster_name']
                regionName = value['region_name'][0]
            }
        });

        let deploy_trolley_agent_data = JSON.stringify({
            "cluster_name": clusterName,
            "cluster_type": clusterType,
            "region_name": regionName,
            "trolley_server_url": trolleyServerURL,
        });

        url = http + trolley_url + "/deploy_trolley_agent_on_cluster";

        swal_message = 'An trolley agent was deployed on ' + clusterName

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(deploy_trolley_agent_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })
    });

    $("#namespaces-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        namespaces = window.localStorage.getItem("namespaces");
        const namespacesArray = namespaces.split(",");
        $.each(namespacesArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value + '</li></ul>');
        });
    })

    $("#deployments-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        deployments = window.localStorage.getItem("deployments");
        deploymentsArray = JSON.parse(deployments)
        $.each(deploymentsArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value['deployment'] + '</li></ul>');
        });
    })

    $("#pods-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        pods = window.localStorage.getItem("pods");
        podsArray = JSON.parse(pods)
        $.each(podsArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value['pod'] + '</li></ul>');
        });
    })

    $("#containers-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        containers = window.localStorage.getItem("containers");
        containersArray = JSON.parse(containers);
        $.each(containersArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value['container_name'] + '</li></ul>');
        });
    })

    $("#daemonsets-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        daemonsets = window.localStorage.getItem("daemonsets");
        daemonsetsArray = JSON.parse(daemonsets);
        $.each(daemonsetsArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value['daemonsets'] + '</li></ul>');
        });
    })

    $("#services-more-info").click(function() {
        $("#objects-div").empty();
        $("#additional-data-div").show();
        services = window.localStorage.getItem("services");
        servicesArray = JSON.parse(services);
        $.each(servicesArray, function(key, value) {
            $('#objects-div').append('<ul><li>' + value['service'] + '</li></ul>');
        });
    })

    function assign_object(objectType, objectName, dataArray, assignedObject) {
        let discovered = false
        provider = window.localStorage.getItem("provider", provider)
        if (objectType == 'cluster') {
            $.each(dataArray, function(key, value) {
                if (value.cluster_name === objectName) {
                    discovered = value.discovered
                }
            });
            let clusterType = window.localStorage.getItem("clusterType");
            if (assignedObject == "user") {
                clientName = ""
                userName = $('#clusters-dropdown-' + objectName).val();
            } else if (assignedObject == "client") {
                clientName = $('#clusters-dropdown-' + objectName).val();
                userName = ""
            }
            var assign_client_data = JSON.stringify({
                "object_type": objectType,
                "cluster_type": clusterType,
                "cluster_name": objectName,
                "assigned_object": assignedObject,
                "user_name": userName,
                "client_name": clientName,
                "discovered": discovered
            });
        } else if (objectType == 'instance') {
            if (assignedObject == "user") {
                clientName = ""
                userName = $('#instances-dropdown-' + objectName).val();
            } else if (assignedObject == "client") {
                clientName = $('#instances-dropdown-' + objectName).val();
                userName = ""
            }

            var assign_client_data = JSON.stringify({
                "object_type": objectType,
                "instance_name": objectName,
                "assigned_object": assignedObject,
                "user_name": userName,
                "client_name": clientName,
                "provider": provider
            });
        }


        url = http + trolley_url + "/clients";

        const xhr = new XMLHttpRequest();
        xhr.open("PUT", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(assign_client_data);


        if (assignedObject == "user") {
            var user_name_array = userName.split("-")
            var cap_user_name_ = ""
            $.each(user_name_array, function(key, value) {
                cap_user_name_ += value.capitalize() + " "
            });
            cap_user_name = cap_user_name_.slice(0, -1)
            newHTML = '<a id="' + objectType + '-text-label-userName-div-' + objectName + '">' + cap_user_name + '</a>'
            $("#" + objectType + "s-dropdown-" + objectName).replaceWith(newHTML);
            $("#" + objectType + "s-button-" + objectName).hide();

        } else if (assignedObject == "client") {
            newHTML = '<a id="' + objectType + '-text-label-clientName-div-' + objectName + '">' + clientName + '</a>'
            $("#" + objectType + "s-dropdown-" + objectName).replaceWith(newHTML);
            $("#" + objectType + "s-button-" + objectName).hide();
        }
    }

    function store_client_names() {
        var clientNames = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/clients",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            clientNames.push(value['client_name'].capitalize())
                        });
                    }
                    window.localStorage.setItem("clientNames", clientNames);
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }

    function store_users_data() {
        var usersData = []
        var logged_user_name = window.localStorage.getItem("userName")
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/users?logged_user_name=" + logged_user_name,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            usersData.push({
                                first_name: value['first_name'],
                                last_name: value['last_name'],
                                user_name: value['user_name'],
                                team_name: value['team_name'],
                                user_email: value['user_email'],
                                profile_image_filename: value['profile_image_filename'],
                                registration_status: value['registration_status'],
                                user_type: value['user_type']
                            });
                        });
                    }
                    window.localStorage.setItem("usersData", JSON.stringify(usersData));
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }

    function store_teams_data() {
        var teamsData = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/teams",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            teamsData.push({
                                team_name: value['team_name'],
                                team_additional_info: value['team_additional_info']
                            });
                        });
                    }
                    window.localStorage.setItem("teamsData", JSON.stringify(teamsData));
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }

    function store_clients_data() {
        var clientsData = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/clients",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            clientsData.push({
                                client_name: value['client_name'],
                                client_additional_info: value['client_additional_info'],
                                connection_name: value['connection_name'],
                                client_office_address: value['client_office_address'],
                                connection_phone_number: value['connection_phone_number'],
                                client_web_address: value['client_web_address'],

                            });
                        });
                    }
                    window.localStorage.setItem("clientsData", JSON.stringify(clientsData));
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }




    function store_clusters() {
        var clustersData = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_clusters_data?cluster_type=" + clusterType + "&user_name=" + data['user_name'],
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            clustersData.push({
                                cluster_name: value['cluster_name'],
                                user_name: value['user_name'],
                                client_name: value['client_name'],
                                cluster_version: value['cluster_version'],
                                human_expiration_timestamp: value['human_expiration_timestamp'],
                                kubeconfig: value['kubeconfig'],
                                nodes_ips: value['nodes_ips'],
                                region_name: value['region_name'],
                                num_nodes: value['num_nodes'],
                                totalvCPU: value['totalvCPU'],
                                total_memory: value['total_memory'],
                                tags: value['tags'],
                                discovered: value['discovered']
                            });
                        });
                    }
                    window.localStorage.setItem("clustersData", JSON.stringify(clustersData));
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }

    function populate_clusters(userName, clientName) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_clusters_data?cluster_type=" + clusterType + "&user_name=" + userName + "&client_name=" + clientName,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        populate_kubernetes_clusters_objects(response)
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure populating clusters per user")
                },
            })
        })
    }

    function populate_instances(provider, userName, clientName) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_instances_data?provider=" + provider + "&user_name=" + userName + "&client_name=" + clientName,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        populate_instances_objects(response)
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure populating instances per user")
                },
            })
        })

    }

    function store_instances(provider) {
        var instancesData = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_instances_data?provider=" + provider + "&user_name=" + data['user_name'],
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            if (provider == 'aws') {
                                var instanceLocation = value['instance_zone']
                            } else if (provider == 'gcp') {
                                var instanceLocation = value['instance_zone']
                            }
                            instancesData.push({
                                instance_name: value['instance_name'],
                                machine_type: value['machine_type'],
                                instance_zone: instanceLocation,
                                internal_ip: value['internal_ip'],
                                external_ip: value['external_ip'],
                                client_name: value['client_name'],
                                user_name: value['user_name'],
                                tags: value['tags']
                            });
                        });
                    }
                    window.localStorage.setItem("instancesData", JSON.stringify(instancesData));
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                },
            })
        })
    }

    function populate_kubernetes_clusters_objects(passedClustersData) {
        var clustersHTML = '';
        var clustersData = '';
        var clusterNames = []
        var kubeconfigs_array = [];
        if (passedClustersData === undefined) {
            clustersData = jQuery.parseJSON(window.localStorage.getItem("clustersData"));
        } else {
            clustersData = passedClustersData
        }

        $.each(clustersData, function(key, value) {
            var user_name_array = value.user_name.split("-")
            var cap_user_name_ = ""
            $.each(user_name_array, function(key, value) {
                cap_user_name_ += value.capitalize() + " "
            });
            cap_user_name = cap_user_name_.slice(0, -1)
            clusterNames.push(value.cluster_name)
            var tags_string_ = JSON.stringify(value.tags);
            var tags_string__ = tags_string_.replace(/[{}]/g, "");
            var tags_string___ = tags_string__.replace(/[/"/"]/g, "");
            var tags_string = tags_string___.replace(/[,]/g, "<br>");
            var client_name_assign_element = '<select class="col-lg-8 align-content-lg-center" id="clusters-dropdown-' + value.cluster_name + '"></select> <button type="submit" class="btn btn-primary btn-sm" id="clusters-button-' + value.cluster_name + '" >Add</button>'
            clustersHTML += '<tr id="tr_' + value.cluster_name + '">';
            clustersHTML += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.cluster_name + '">' + value.cluster_name + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.region_name + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.num_nodes + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.totalvCPU + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.total_memory + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.cluster_version + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.human_expiration_timestamp + '</a></td>';
            if (!value.cluster_name) {
                clustersHTML += '<td class="text-center" id="clusters-userName-div-' + value.cluster_name + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                clustersHTML += '<td class="text-center" id="clusters-userName-div-' + value.cluster_name + '"><a id="clusters-text-label-userName-div-' + value.cluster_name + '">' + cap_user_name + '</a></td>';
            }
            if (!value.cluster_name) {
                clustersHTML += '<td class="text-center" id="clusters-clientName-div-' + value.cluster_name + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                clustersHTML += '<td class="text-center" id="clusters-clientName-div-' + value.cluster_name + '"><a id="clusters-text-label-clientName-div-' + value.cluster_name + '">' + value.client_name.capitalize() + '</a></td>';
            }
            clustersHTML += '<td class="text-center"><a>' + tags_string + '</a></td>';
            let manage_table_buttons = '<td class="project-actions text-right"> \
            <a class="btn btn-danger btn-sm" id="delete-button-' + value.cluster_name + '" href="#"><i class="fas fa-trash"></i>Delete</a> </td> </div>'
            clustersHTML += manage_table_buttons
            kubeconfigs_array.push({
                key: value.cluster_name,
                value: value.kubeconfig
            });
            full_table = clusters_manage_table_header + clustersHTML + clusters_manage_table_footer

        });
        if (clusterType == 'aks') {
            $('#aks-clusters-management-table').append(full_table);
        } else if (clusterType == 'eks') {
            $('#eks-clusters-management-table').append(full_table);
        } else if (clusterType == 'gke') {
            $('#gke-clusters-management-table').append(full_table);
        }

        object_filter_type = window.localStorage.getItem("objectsFilterType");
        if (object_filter_type == "users") {
            let user_type = window.localStorage.getItem("userType");
            if (user_type != "admin") {
                $("#user-name-table").hide();
                $("#client-name-table").hide();

                $.each(clustersData, function(key, value) {
                    client_name_text_to_hide = "#clusters-text-label-clientName-div-" + value.cluster_name
                    client_name_div_to_hide = "#clusters-clientName-div-" + value.cluster_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                    user_name_text_to_hide = "#clusters-text-label-userName-div-" + value.cluster_name
                    user_name_div_to_hide = "#clusters-userName-div-" + value.cluster_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                })
            } else {
                $("#user-name-table").show();
                $("#client-name-table").hide();
                $.each(clustersData, function(key, value) {
                    client_name_text_to_hide = "#clusters-text-label-clientName-div-" + value.cluster_name
                    client_name_div_to_hide = "#clusters-clientName-div-" + value.cluster_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                });
            }
        }
        if (object_filter_type == "clients") {
            let user_type = window.localStorage.getItem("userType");
            if (user_type != "admin") {
                $("#user-name-table").hide();
                $("#client-name-table").hide();

                $.each(clustersData, function(key, value) {
                    client_name_text_to_hide = "#clusters-text-label-clientName-div-" + value.cluster_name
                    client_name_div_to_hide = "#clusters-clientName-div-" + value.cluster_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                    user_name_text_to_hide = "#clusters-text-label-userName-div-" + value.cluster_name
                    user_name_div_to_hide = "#clusters-userName-div-" + value.cluster_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                })
            } else {
                $("#user-name-table").hide();
                $("#client-name-table").show();
                $.each(clustersData, function(key, value) {
                    user_name_text_to_hide = "#clusters-text-label-userName-div-" + value.cluster_name
                    user_name_div_to_hide = "#clusters-userName-div-" + value.cluster_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                });
            }
        }
    }

    function populate_instances_objects(passedInstancesData) {
        var instancesHTML = '';
        var instancesNames = []
        var kubeconfigs_array = [];
        if (passedInstancesData === undefined) {
            instancesData = jQuery.parseJSON(window.localStorage.getItem("instancesData"));
        } else {
            instancesData = passedInstancesData
        }

        $.each(instancesData, function(key, value) {
            var user_name_array = value.user_name.split("-")
            var cap_user_name_ = ""
            $.each(user_name_array, function(key, value) {
                cap_user_name_ += value.capitalize() + " "
            });
            cap_user_name = cap_user_name_.slice(0, -1)
            instancesNames.push(value.instance_name)
            var tags_string_ = JSON.stringify(value.tags);
            var tags_string__ = tags_string_.replace(/[{}]/g, "");
            var tags_string___ = tags_string__.replace(/[/"/"]/g, "");
            var tags_string = tags_string___.replace(/[,]/g, "<br>");
            var client_name_assign_element = '<select class="col-lg-8 align-content-lg-center" id="instances-dropdown-' + value.instance_name + '"></select> <button type="submit" class="btn btn-primary btn-sm" id="instances-button-' + value.instance_name + '" >Add</button>'
            instancesHTML += '<tr id="tr_' + value.instance_name + '">';
            instancesHTML += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.instance_name + '">' + value.instance_name + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.instance_zone + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.machine_type + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.internal_ip + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.external_ip + '</a></td>';
            if (!value.instance_name) {
                instancesHTML += '<td class="text-center" id="instances-userName-div-' + value.instance_name + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                instancesHTML += '<td class="text-center" id="instances-userName-div-' + value.instance_name + '"><a id="clusters-text-label-userName-div-' + value.instance_name + '">' + cap_user_name + '</a></td>';
            }
            if (!value.instance_name) {
                instancesHTML += '<td class="text-center" id="instances-clientName-div-' + value.instance_name + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                instancesHTML += '<td class="text-center" id="instances-clientName-div-' + value.instance_name + '"><a id="instances-text-label-clientName-div-' + value.instance_name + '">' + value.client_name.capitalize() + '</a></td>';
            }
            instancesHTML += '<td class="text-center"><a>' + tags_string + '</a></td>';
            let manage_table_buttons = '<td class="project-actions text-right"> \
            <a class="btn btn-danger btn-sm" id="delete-button-' + value.instance_name + '" href="#"><i class="fas fa-trash"></i>Delete</a> </td> \
            </div> </div> </div> </div>'
            instancesHTML += manage_table_buttons
            full_table = instances_manage_table_header + instancesHTML + instances_manage_table_footer

        });
        if (provider == 'aws') {
            $('#aws-ec2-instances-management-table').append(full_table);
        } else if (provider == 'gcp') {
            $('#gcp-vm-instances-management-table').append(full_table);
        } else if (provider == 'az') {
            $('#gcp-vm-instances-management-table').append(full_table);
        }

        $.each(instancesNames, function(index, value) {
            var clientNames = window.localStorage.getItem("clientNames");
            let clientNamesList = clientNames.split(',')
            $("#instances-dropdown-" + value['instanceName']).append($("<option />").val('').text('Add a client'));
            $.each(clientNamesList, function(index, clientNameValue) {
                $("#instances-dropdown-" + value).append($("<option />").val(clientNameValue).text(clientNameValue));
            });
        });

        object_filter_type = window.localStorage.getItem("objectsFilterType");
        if (object_filter_type == "users") {
            let user_type = window.localStorage.getItem("userType");
            if (user_type != "admin") {
                $("#user-name-table").hide();
                $("#client-name-table").hide();

                $.each(instancesData, function(key, value) {
                    client_name_text_to_hide = "#instances-text-label-clientName-div-" + value.instance_name
                    client_name_div_to_hide = "#instances-clientName-div-" + value.instance_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                    user_name_text_to_hide = "#instances-text-label-userName-div-" + value.instance_name
                    user_name_div_to_hide = "#instances-userName-div-" + value.instance_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                })
            } else {
                $("#user-name-table").show();
                $("#client-name-table").hide();
                $.each(instancesData, function(key, value) {
                    client_name_text_to_hide = "#instances-text-label-clientName-div-" + value.instance_name
                    client_name_div_to_hide = "#instances-clientName-div-" + value.instance_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                });
            }
        }
        if (object_filter_type == "clients") {
            let user_type = window.localStorage.getItem("userType");
            if (user_type != "admin") {
                $("#user-name-table").hide();
                $("#client-name-table").hide();

                $.each(instancesData, function(key, value) {
                    client_name_text_to_hide = "#instances-text-label-clientName-div-" + value.instance_name
                    client_name_div_to_hide = "#instances-clientName-div-" + value.instance_name
                    $(client_name_text_to_hide).hide();
                    $(client_name_div_to_hide).hide();
                    user_name_text_to_hide = "#instances-text-label-userName-div-" + value.instance_name
                    user_name_div_to_hide = "#instances-userName-div-" + value.instance_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                })
            } else {
                $("#user-name-table").hide();
                $("#client-name-table").show();
                $.each(instancesData, function(key, value) {
                    user_name_text_to_hide = "#instances-text-label-userName-div-" + value.instance_name
                    user_name_div_to_hide = "#instances-userName-div-" + value.instance_name
                    $(user_name_text_to_hide).hide();
                    $(user_name_div_to_hide).hide();
                });
            }
        }
    }

    function populate_kubernetes_agent_data() {
        url = http + trolley_url + "/get_agent_cluster_data?cluster_name=" + data['cluster_name'];
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if ((response.status === 'Failure') || (response[0].content === null)) {
                    $('#resources-title').replaceWith('Trolley Agent was not found on the cluster. Click to install!');
                    $('#agent-deployment-div').show();
                    let clustersData = jQuery.parseJSON(window.localStorage.getItem("clustersData"));
                    let clusterName = window.localStorage.getItem("clusterName")
                } else {
                    if (response.length < 0) {
                        $('#attach-client-div').show();
                    } else {
                        $.each(response, function(key, value) {
                            $('#agent-data-div').show();
                            $('#namespaces').append('<h3>' + value.namespaces.length + '</h3>');
                            $('#deployments').append('<h3>' + value.deployments.length + '</h3>');
                            $('#pods').append('<h3>' + value.pods.length + '</h3>');
                            $('#containers').append('<h3>' + value.containers.length + '</h3>');
                            $('#daemonsets').append('<h3>' + value.daemonsets.length + '</h3>');
                            $('#services').append('<h3>' + value.services.length + '</h3>');
                            window.localStorage.setItem("namespaces", value.namespaces);
                            window.localStorage.setItem("deployments", JSON.stringify(value.deployments));
                            window.localStorage.setItem("pods", JSON.stringify(value.pods));
                            window.localStorage.setItem("containers", JSON.stringify(value.containers));
                            window.localStorage.setItem("daemonsets", JSON.stringify(value.daemonsets));
                            window.localStorage.setItem("services", JSON.stringify(value.services));
                        })
                    }
                }
            },
            error: function() {
                console.log('error loading orchestration items')
            }
        })
    }

    function populate_regions() {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-locations-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-regions-dropdown");
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_regions?cluster_type=" + clusterType,
                type: 'GET',
                success: function(response) {
                    if (clusterType == 'aks') {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(key));
                        });
                    } else if (clusterType == 'eks') {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(value));
                        });
                        populate_zones('eu-north-1')
                    } else if (clusterType == 'gke') {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(value));
                        });
                        populate_zones('us-east1')
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching regions data")
                },
            })
        })
    }

    function populate_team_names() {
        var teamsData = window.localStorage.getItem("teamsData");
        var teamsDataArray = JSON.parse(teamsData)
        $.each(teamsDataArray, function(key, value) {
            $("#team-names-dropdown").append($("<option />").val(value['team_name']).text(value['team_name'].capitalize()));
        });
    }

    function populate_client_names() {
        var clientNames = window.localStorage.getItem("clientNames");
        let clientNamesList = clientNames.split(',')
        $.each(clientNamesList, function(key, value) {
            $("#client-names-dropdown").append($("<option />").val(value).text(value.capitalize()));
        });
    }

    function populate_user_names(team_name) {
        var usersData = window.localStorage.getItem("usersData");
        var usersDataArray = JSON.parse(usersData)

        $.each(usersDataArray, function(key, value) {
            if (value.team_name == team_name) {
                var cap_user_name = value.first_name.capitalize() + " " + value.last_name.capitalize()
                $("#user-names-dropdown").append($("<option />").val(value.user_name).text(cap_user_name));
            }
        });
    }

    function populate_users_data() {
        usersDataArray = jQuery.parseJSON(window.localStorage.getItem("usersData"));
        $.each(usersDataArray, function(index, user) {
            first_name = user.first_name.capitalize();
            last_name = user.last_name.capitalize();
            userElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column id="user-div-' + user.user_name + '>'
            userElement += '<div class="card bg-light d-flex flex-fill"><div class="row"><div class="card-body pt-0"><div class="col-7"><h2 class="lead"><br><b>' + user.first_name.capitalize() + " " + user.last_name.capitalize() + '</b></h2>'
            userElement += '<p class="text-muted text-sm"><b>User type: </b> ' + user.user_type.capitalize() + '<br>'
            userElement += '<b>Team Name: </b> ' + user.team_name.capitalize() + '</p>'
            userElement += '<ul class="ml-4 mb-0 fa-ul text-muted">'
            userElement += '<li class="small"><span class="fa-li"><i class="fa regular fa-at"></i></span> Email Address: <a href="mailto:' + user.user_email + '">' + user.user_email + '</a></li>'
            userElement += '<li class="small"><span class="fa-li"><i class="fas fa-tasks"></i></span> Registration Status: ' + user.registration_status.capitalize() + '</li>'
            userElement += '</ul></div><div class="col-4 text-center"><img src="' + user.profile_image_filename + '"' + 'class="img-circle img-fluid"></div></div></div>'
            userElement += '<div class="card-footer"><div class="text-center ">'
            userElement += '<button type="submit" class="btn btn-primary btn-sm"><i class="fas fa-user" id="' + user.user_name + '-info-user-button"></i>More Info</a>'
            userElement += '<div class="text-right">'
            userElement += '<button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-user" id="' + user.user_name + '-delete-user-button"></i>Delete User</a></div>'
            userElement += '</div></div></div></div></div>'
        });
        $('#users-main-div').append(userElement);
    }

    function populate_teams_data() {
        teamsDataArray = jQuery.parseJSON(window.localStorage.getItem("teamsData"));
        $.each(teamsDataArray, function(index, team) {
            team_name = team.team_name.capitalize();
            teamElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column id="team-div-' + team.team_name.capitalize() + '>'
            teamElement += '<div class="card bg-light d-flex flex-fill"><div class="row"><div class="card-body pt-0"><div class="col-7"><h2 class="lead"><br><b>' + team.team_name.capitalize() + '</b></h2>'
            teamElement += '<p class="text-muted text-sm"><b>About: </b> ' + team.team_additional_info + '<br>'
            teamElement += '<ul class="ml-4 mb-0 fa-ul text-muted">'
            teamElement += '</ul></div></div></div>'
            teamElement += '<div class="card-footer"><div class="text-center ">'
            teamElement += '<button type="submit" class="btn btn-primary btn-sm"><i class="fas fa-user" id="' + team.team_name + '-info-team-button"></i>More Info</a>'
            teamElement += '<div class="text-right">'
            teamElement += '<button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-user" id="' + team.team_name + '-delete-team-button"></i>Delete Team</a></div>'
            teamElement += '</div></div></div></div></div>'
        });
        $('#teams-main-div').append(teamElement);
    }

    function populate_clients_data() {
        clientsDataArray = jQuery.parseJSON(window.localStorage.getItem("clientsData"));
            $.each(clientsDataArray, function(index, client) {
                client_name = client.client_name.capitalize();
                clientElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column id="client-div-' + client.client_name.capitalize() + '>'
                clientElement += '<div class="card bg-light d-flex flex-fill"><div class="row"><div class="card-body pt-0"><div class="col-7"><h2 class="lead"><br><b>' + client.client_name.capitalize() + '</b></h2>'
                clientElement += '<p class="text-muted text-sm"><b>About: </b> ' + client.client_additional_info + '<br>'
                clientElement += '<ul class="ml-4 mb-0 fa-ul text-muted">'
                clientElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-building"></i></span> Address: ' + client.client_office_address + '</li>'
                clientElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-phone"></i></span> Phone #: ' + client.connection_phone_number + '</li>'
                clientElement += '<li class="small"><span class="fa-li"><i class="far fa-browser"></i></i></i></span> Web: <a href=' + client.client_web_address + ' target="_blank" >' + client.client_web_address + '</a></li>'
                clientElement += '</ul></div></div></div>'
                clientElement += '<div class="card-footer"><div class="text-center ">'
                clientElement += '<button type="submit" class="btn btn-primary btn-sm"><i class="fas fa-user" id="' + client.client_name + '-info-client-button"></i>More Info</a>'
                clientElement += '<div class="text-right">'
                clientElement += '<button type="submit" class="btn btn-danger btn-sm"><i class="fas fa-user" id="' + client.client_name + '-delete-client-button"></i>Delete Client</a></div>'
                clientElement += '</div></div></div></div></div>'
            });
            $('#clients-main-div').append(clientElement);
    }

    function populate_zones(region_name) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-zones-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-zones-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-zones-dropdown");
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_zones?cluster_type=" + clusterType + "&region_name=" + region_name,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        if (clusterType == 'aks') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value.name).text(value.displayName));
                            });
                        } else if (clusterType == 'eks') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value).text(value));
                            });
                        } else if (clusterType == 'gke') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value).text(value));
                            });
                            populate_kubernetes_versions('asia-east1-b')
                            populate_kubernetes_image_types('asia-east1-b')
                        }
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching zones data")
                },
            })
        })
    }

    function populate_subnets(zone_names) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-subnets-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-subnets-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-subnets-dropdown");
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_subnets?cluster_type=" + clusterType + "&zone_names=" + zone_names,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        if (clusterType == 'aks') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value.name).text(value.displayName));
                            });
                        } else if (clusterType == 'eks') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value).text(value));
                            });
                        } else if (clusterType == 'gke') {
                            $.each(response, function(key, value) {
                                $dropdown.append($("<option />").val(value).text(value));
                            });
                            populate_kubernetes_versions('asia-east1-b')
                            populate_kubernetes_image_types('asia-east1-b')
                        }
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching subnets data")
                },
            })
        })
    }

    function populate_vpcs(selected_location) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
            var url = http + trolley_url + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = http + trolley_url + "/fetch_aws_vpcs?aws_region=" + selected_location;
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_client_names",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(value));
                        });
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching VPCs names data")
                },
            })
        })
    }

    function populate_kubernetes_versions(selected_location) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-versions-dropdown");
            var url = http + trolley_url + "/fetch_aks_versions?az_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-versions-dropdown");
            var url = http + trolley_url + "/fetch_eks_versions?aws_region=" + selected_location;
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-versions-dropdown");
            var url = http + trolley_url + "/fetch_gke_versions?gcp_zone=" + selected_location;
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: url,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(value));
                        });
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching Kubernetes versions data")
                },
            })
        })
    }

    function populate_kubernetes_image_types(selected_location) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
            var url = http + trolley_url + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = http + trolley_url + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-image-types-dropdown");
            var url = http + trolley_url + "/fetch_gke_image_types?gcp_zone=" + selected_location;
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: url,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value).text(value));
                        });
                    }
                    resolve(response)
                },
                error: function(error) {
                    alert("Failure fetching Kubernetes image types")
                },
            })
        })
    }

    function trigger_cloud_provider_discovery(provider, objectType) {
        let cloud_provider_discovery_data = JSON.stringify({
            "provider": provider,
            "object_type": objectType
        });

        swal_message = 'Clusters scan for ' + provider + ' provider was triggered. Please check again in a couple of minutes'

        url = http + trolley_url + "/trigger_cloud_provider_discovery";
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(cloud_provider_discovery_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: true,
            timer: 5000
        })
    }

    function delete_cluster(clusterType, objectName, dataArray) {

        $.each(dataArray, function(key, value) {
            if (value.cluster_name === objectName) {
                discovered = value.discovered
            }
        });
        let cluster_deletion_data = JSON.stringify({
            "cluster_type": clusterType,
            "cluster_name": objectName,
            "discovered": discovered
        });

        swal_message = 'A ' + clusterName + ' ' + clusterType + ' cluster was requested for deletion'

        url = http + trolley_url + "/delete_cluster";
        const xhr = new XMLHttpRequest();
        xhr.open("DELETE", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(cluster_deletion_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: true,
            timer: 5000
        })

    }

    function delete_user(userName) {
        let user_deletion_data = JSON.stringify({
            "user_name": userName
        });


        url = http + trolley_url + "/users";
        const xhr = new XMLHttpRequest();
        xhr.open("DELETE", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(user_deletion_data);

    }


    function delete_team(teamName) {
        let team_deletion_data = JSON.stringify({
            "team_name": teamName
        });


        url = http + trolley_url + "/teams";
        const xhr = new XMLHttpRequest();
        xhr.open("DELETE", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(team_deletion_data);

    }

    function delete_client(clientName) {
        let client_deletion_data = JSON.stringify({
            "client_name": clientName
        });

        swal_message = 'A ' + clientName + ' was requested for deletion'
        url = http + trolley_url + "/clients";
        const xhr = new XMLHttpRequest();
        xhr.open("DELETE", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(client_deletion_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: true,
            timer: 5000
        })

    }

    function populate_logged_in_assets() {
        Object.defineProperty(String.prototype, 'capitalize', {
            value: function() {
                return this.charAt(0).toUpperCase() + this.slice(1);
            },
            enumerable: false
        });
        $("#userNameLabel").text(data['first_name'].capitalize());
    }

    $('#eks-locations-dropdown').change(function() {
        var eks_location = $('#eks-locations-dropdown').val();
        $("#eks-vpcs-dropdown").empty();
        $("#eks-zones-dropdown").empty();
        $("#eks-subnets-dropdown").empty();
        populate_zones(eks_location);
    })

    $('#eks-zones-dropdown').change(function() {
        var eks_zones = $('#eks-zones-dropdown').val();
        $("#eks-subnets-dropdown").empty();
        populate_subnets(eks_zones);
    })

    $('#gke-regions-dropdown').change(function() {
        var gke_region = $('#gke-regions-dropdown').val();
        $("#gke-zones-dropdown").empty();
        populate_zones(gke_region);
    })

    $('#gke-zones-dropdown').change(function() {
        var gke_zones = $('#gke-zones-dropdown').val();
        $("#gke-versions-dropdown").empty();
        populate_kubernetes_versions(gke_zones);
        populate_kubernetes_image_types(gke_zones);
    })

    $('#filter-type-dropdown').change(function() {
        var objectsSelector = $('#filter-type-dropdown').val();
        if (objectsSelector == "Users") {
            $("#teams-users-dropdowns-box").show();
            $("#clients-dropdowns-box").hide();
            $("#user-name-table").show();
            $("#client-name-table").hide();
            var userName = $('#user-names-dropdown').val();
            window.localStorage.setItem("objectsFilterType", "users");
        } else if (objectsSelector == "Clients") {
            $("#teams-users-dropdowns-box").hide();
            $("#clients-dropdowns-box").show();
            $("#user-name-table").hide();
            $("#client-name-table").show();
            var clientName = $('#client-names-dropdown').val();
            window.localStorage.setItem("objectsFilterType", "clients");
        }
        if (window.localStorage.getItem("objectType") == 'cluster') {
            if (provider == "gcp") {
                $("#gke-clusters-management-table").empty()
            } else if (provider == "aws") {
                $("#eks-clusters-management-table").empty()
            } else if (provider == "az") {
                $("#aks-clusters-management-table").empty()
            }

            if (objectsSelector == "Users") {
                var clientName = "";
            } else if (objectsSelector == "Clients") {
                var userName = "";
            }
            populate_clusters(userName, clientName);

        } else if (window.localStorage.getItem("objectType") == 'instance') {
            if (provider == "gcp") {
                $("#gcp-vm-instances-management-table").empty()
            } else if (provider == "aws") {
                $("#aws-ec2-instances-management-table").empty()
            } else if (provider == "az") {
                $("#az-vm-instances-management-table").empty()
            }
            if (objectsSelector == "Users") {
                var clientName = "";
            } else if (objectsSelector == "Clients") {
                var userName = "";
            }
            populate_instances(provider, userName, clientName);
        }
    })

    $('#team-names-dropdown').change(function() {
        var clientName = ""
        var teamName = $('#team-names-dropdown').val();
        $("#user-names-dropdown").empty();
        populate_user_names(teamName);
        var userName = $('#user-names-dropdown').val();
        var provider = window.localStorage.getItem("provider")
        if (window.localStorage.getItem("objectType") == 'cluster') {
            if (provider == "gcp") {
                $("#gke-clusters-management-table").empty()
            } else if (provider == "aws") {
                $("#eks-clusters-management-table").empty()
            }
            populate_clusters(userName, clientName);
        } else if (window.localStorage.getItem("objectType") == 'instance') {
            if (provider == "gcp") {
                $("#gcp-vm-instances-management-table").empty()
            } else if (provider == "aws") {
                $("#aws-ec2-instances-management-table").empty()
            }
            populate_instances(provider, userName, clientName);
        }
    })

    $('#user-names-dropdown').change(function() {
        $("#aks-clusters-management-table").empty()
        $("#eks-clusters-management-table").empty()
        $("#gke-clusters-management-table").empty()
        var clientName = "";
        var userName = $('#user-names-dropdown').val();
        var provider = window.localStorage.getItem("provider")
        if (window.localStorage.getItem("objectType") == 'cluster') {
            if (provider == "gcp") {
                $("#gke-clusters-management-table").empty()
            } else if (provider == "aws") {
                $("#eks-clusters-management-table").empty()
            }
            populate_clusters(userName, clientName);;
        } else if (window.localStorage.getItem("objectType") == 'instance') {
            if (provider == "gcp") {
                $("#gcp-vm-instances-management-table").empty()
            } else if (provider == "aws") {
                $("#aws-ec2-instances-management-table").empty()
            }
            populate_instances(provider, userName, clientName);
        }
    })

    $('#client-names-dropdown').change(function() {
        $("#aks-clusters-management-table").empty()
        $("#eks-clusters-management-table").empty()
        $("#gke-clusters-management-table").empty()
        var clientName = $('#client-names-dropdown').val();
        var userName = "";
        var provider = window.localStorage.getItem("provider")
        if (window.localStorage.getItem("objectType") == 'cluster') {
            if (provider == "gcp") {
                $("#gke-clusters-management-table").empty()
            } else if (provider == "aws") {
                $("#eks-clusters-management-table").empty()
            }
            populate_clusters(userName, clientName);
        } else if (window.localStorage.getItem("objectType") == 'instance') {
            if (provider == "gcp") {
                $("#gcp-vm-instances-management-table").empty()
            } else if (provider == "aws") {
                $("#aws-ec2-instances-management-table").empty()
            }
            populate_instances(provider, userName, clientName);
        }
    })

    $('#cloud-providers-dropdown').change(function() {
        var cloud_provider = $('#cloud-providers-dropdown').val();
        if (cloud_provider == "AWS") {
            $("#AWSAccessKeyIDDiv").show();
            $("#AWSSecretAccessKeyDiv").show();
            $("#AzureCredentialsDiv").hide();
            $("#GoogleCredsJSONDiv").hide();
        } else if (cloud_provider == "GCP") {
            $("#AWSAccessKeyIDDiv").hide();
            $("#AWSSecretAccessKeyDiv").hide();
            $("#AzureCredentialsDiv").hide();
            $("#GoogleCredsJSONDiv").show();
        } else if (cloud_provider == "Azure") {
            $("#AWSAccessKeyIDDiv").hide();
            $("#AWSSecretAccessKeyDiv").hide();
            $("#AzureCredentialsDiv").show();
            $("#GoogleCredsJSONDiv").hide();
        }
    })

    $(document).on("click", ".text-center", function() {
        var HTML = "";
        let valueID = this.id;
        if (valueID.length == 0) {
            valueID = window.localStorage.getItem("valueID");
            let divValue = valueID.split("-")
        } else {
            divValue = valueID.split("-");
        }
        var objectType = divValue[0]
        var clientName = this.children[0].innerText;
        if (divValue[1] == "clientName") {
            window.localStorage.setItem("assignedObject", "client");
            var instanceName_ = $(this).parent().attr('id');
            var instanceName = instanceName_.slice(3);
            var textLabelId = "#" + objectType + "-text-label-clientName-div-" + instanceName;
            $(textLabelId).hide();
            let clientNames = window.localStorage.getItem("clientNames")
            let clientNamesList = clientNames.split(',')
            var newDropDownHTML = '<td class="text-center"><select class="col-lg-8 align-content-lg-center" id="' + objectType + '-dropdown-' + instanceName + '"><a>';
            $.each(clientNamesList, function(index, clientNameValue) {
                newDropDownHTML += '<option value="' + clientNameValue + '">' + clientNameValue + '</option>'
            });
            newDropDownHTML += '</select>'
            newDropDownHTML += '<button type="submit" class="btn btn-primary btn-sm" id="' + objectType + '-button-' + instanceName + '"</a>Add</button></td>'
            $('#' + objectType + '-clientName-div-' + instanceName).replaceWith(newDropDownHTML);
        } else if (divValue[1] == "userName") {
            window.localStorage.setItem("assignedObject", "user");
            var instanceName_ = $(this).parent().attr('id');
            var instanceName = instanceName_.slice(3);
            var textLabelId = "#" + objectType + "-text-label-userName-div-" + instanceName;
            $(textLabelId).hide();
            let usersData = window.localStorage.getItem("usersData")
            var usersDataArray = JSON.parse(usersData)
            var newDropDownHTML = '<td class="text-center"><select class="col-lg-8 align-content-lg-center" id="' + objectType + '-dropdown-' + instanceName + '"><a>';
            $.each(usersDataArray, function(index, user) {
                newDropDownHTML += '<option value="' + user.user_name + '">' + user.first_name.capitalize() + " " + user.last_name.capitalize() + '</option>'
            });
            newDropDownHTML += '</select>'
            newDropDownHTML += '<button type="submit" class="btn btn-primary btn-sm" id="' + objectType + '-button-' + instanceName + '"</a>Add</button></td>'
            $('#' + objectType + '-userName-div-' + instanceName).replaceWith(newDropDownHTML);
        }
        window.localStorage.setItem("valueID", valueID);
        let thisID = window.localStorage.getItem("valueID");
    })

    $(document).on("click", ".btn", function() {
        var valueID = this.id;
        var discovered = "";
        var buttonValue = valueID.split("-")
        buttonValue.shift();
        buttonValue.shift();
        let objectName = buttonValue.join("-")
        let objectType = window.localStorage.getItem("objectType");
        let clusterType = window.localStorage.getItem("clusterType");
        if (objectType === 'cluster') {
            let clustersData = window.localStorage.getItem("clustersData")
            let clusterNamesArray = [];
            var dataArray = JSON.parse(clustersData)
        } else if (objectType === 'instance') {
            let instanceData = window.localStorage.getItem("instancesData")
            let instanceNamesArray = [];
            var dataArray = JSON.parse(instanceData)
        }
        if (this.innerText === "Add") {
            let assignedObject = window.localStorage.getItem("assignedObject")
            assign_object(objectType, objectName, dataArray, assignedObject);
        } else if (this.innerText === "More") {
            window.localStorage.removeItem("currentClusterName");
            window.localStorage.setItem("currentClusterName", objectName);
        } else if (this.innerText === "Back to clusters") {
            window.location.href = "manage-" + clusterType + "-clusters";
        } else if (this.innerText === "Delete") {
            delete_cluster(clusterType, objectName, dataArray)
        } else if (this.innerText === "Delete User") {
            userToDelete = this.firstChild.id.split("-")[0]
            delete_user(userToDelete)
            location.reload()
        } else if (this.innerText === "Delete Team") {
            teamToDelete = this.firstChild.id.split("-")[0]
            delete_team(teamToDelete)
            location.reload()
        } else if (this.innerText === "Delete Client") {
            clientToDelete = this.firstChild.id.split("-")[0]
            delete_client(clientToDelete)
            location.reload()
        } else if (this.innerText === "Scan for clusters") {
            trigger_cloud_provider_discovery(provider, objectType = 'cluster')
        } else if (this.innerText === "Scan for VMs") {
            trigger_cloud_provider_discovery(provider, objectType = 'instance')
        } else if (this.innerText === "Copy Kubeconfig") {
            clusterName = window.localStorage.getItem("currentClusterName");
            kubeconfig_data = window.localStorage.getItem("kubeconfigs")
            var kubeconfig_data_jsond = JSON.parse(kubeconfig_data);
            let clusterObj = kubeconfig_data_jsond.find(o => o.key === clusterName);
            kubeconfig_to_copy_clipboard = clusterObj.value
            copyToClipboard(kubeconfig_to_copy_clipboard);
            Swal.fire({
                position: 'top-end',
                icon: 'success',
                title: 'A Kubeconfig was copied to your clipboard!',
                showConfirmButton: false,
                timer: 1000
            })
        }
    })

    function copyToClipboard(textToCopy) {

        if (typeof(navigator.clipboard) == 'undefined') {
            console.log('navigator.clipboard');
            var textArea = document.createElement("textarea");
            textArea.value = textToCopy;
            textArea.style.position = "fixed";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                var successful = document.execCommand('copy');
                var msg = successful ? 'successful' : 'unsuccessful';
                console.log(msg);
            } catch (err) {
                console.log('Was not possible to copy te text: ', err);
            }

            document.body.removeChild(textArea)
            return;
        }
        navigator.clipboard.writeText(textToCopy).then(function() {
            console.log(`successful!`);
        }, function(err) {
            console.log('unsuccessful!', err);
        });

    }

    $(function() {
        var url = window.location;
        $('ul.nav-treeview a').filter(function() {
                return this.href == url;
            }).parentsUntil(".nav-sidebar > .nav-treeview")
            .css({
                'display': 'block'
            })
            .addClass('menu-open').prev('a')
            .addClass('active');
    });

    function isEmpty(val) {
        return (val === undefined || val == null || val.length <= 0) ? true : false;
    }
});