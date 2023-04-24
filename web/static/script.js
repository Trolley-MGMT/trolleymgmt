$(document).ready(function() {
    window.localStorage.setItem("userName", data['user_name']);
    let user_name = window.localStorage.getItem("userName");
    window.localStorage.setItem("clusterName", data['cluster_name']);
    let clusterName = window.localStorage.getItem("clusterName");
    let trolley_remote_url = '';
    let trolley_local_url = 'localhost';
    let trolley_url = 'http://www.pavelzagalsky.com';
    let debug = true;
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

    let clusters_manage_table_header = `<div class="card-body p-0">
    <table class="table table-striped projects" >
        <thead>
        <tr><th style="width: 10%" class="text-center">Cluster Name</th>
            <th style="width: 10%" class="text-center">Cluster Region</th>
            <th style="width: 10%" class="text-center">Number of Nodes</th>
            <th style="width: 10%" class="text-center">Total vCPU</th>
            <th style="width: 10%" class="text-center">Total Memory</th>
            <th style="width: 10%" class="text-center">Kubernetes Version</th>
            <th style="width: 15%" class="text-center">Expiration Time</th>
            <th style="width: 15%" class="text-center">Client Name</th>
            <th style="width: 15%" class="text-center">Tags</th>
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let clusters_manage_table_footer = `</tr></tbody></table></div>`

    let instances_manage_table_header = `<div class="card-body p-0">
    <table class="table table-striped projects" >
        <thead>
        <tr><th style="width: 10%" class="text-center">Instance Name</th>
            <th style="width: 10%" class="text-center">Instance Region</th>
            <th style="width: 10%" class="text-center">Internal IP</th>
            <th style="width: 10%" class="text-center">External IP</th>
            <th style="width: 15%" class="text-center">Client Name</th>
            <th style="width: 15%" class="text-center">Tags</th>
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let instances_manage_table_footer = `</tr></tbody></table></div>`

    var clientElement = '';
    var userElement = '';

    if (debug === true) {
        trolley_url = trolley_local_url;
        gitBranch = 'master'
        http = 'http://'
    } else {
        trolley_url = trolley_remote_url
        gitBranch = 'master'
        http = 'https://'
    }
    if (query == true) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        queryPage = true;
    } else if (pathname[1].includes('build')) {
        buildPage = true;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        queryPage = false;
    } else if ((pathname[1].includes('manage-eks')) || (pathname[1].includes('manage-aks')) || (pathname[1].includes('manage-gke'))){
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = true;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        queryPage = false;
        window.localStorage.setItem("objectType", "cluster");
    } else if ((pathname[1].includes('manage-aws-ec2')) || (pathname[1].includes('manage-gcp-vm')) || (pathname[1].includes('manage-az-vm'))){
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = true;
        clientsPage = false;
        usersPage = false;
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
        queryPage = false;
    } else if (pathname[1].includes('data')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = true;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
        queryPage = false;
    } else if (pathname[1].includes('clients')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = true;
        usersPage = false;
        queryPage = false;
    } else if (pathname[1].includes('users')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = true;
        queryPage = false;
    } else {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        clustersManagePage = false;
        instancesManagePage = false;
        clientsPage = false;
        usersPage = false;
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
    if (clustersManagePage) {
        store_clusters()
            .then((data) => {
                console.log(data)
                store_client_names()
                populate_kubernetes_clusters_objects()
            })
            .catch((error) => {
                console.log(error)
            })

    }

    if (instancesManagePage) {
        store_instances(provider)
            .then((data) => {
                console.log(data)
                store_client_names()
                populate_instances_objects()
            })
            .catch((error) => {
                console.log(error)
            })

    }

    if (clustersDataPage) {
        store_clusters()
            .then((data) => {
                console.log(data)
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
            .forEach(function (form) {
              form.addEventListener('submit', function (event) {
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

    $("#submit-user-button").click(function() {
        var userName = $('#user_name').val().toLowerCase();
        var userEmail = $('#user_email').val();
        var userTeamName = $('#user_team_name').val();
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


        url = http + trolley_url + "/client";

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
        let clusterType = window.localStorage.getItem("clusterType");
        let regionName = window.localStorage.getItem("regionName");
        let trolleyServerURL = $('#trolley_server_url').val();

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

    function store_client_names() {
        var clientNames = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_clients_data",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            clientNames.push(value['client_name'])
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
                            clusterName: value['cluster_name'],
                            clientName: value['client_name'],
                            clusterVersion: value['cluster_version'],
                            humanExpirationTimestamp: value['human_expiration_timestamp'],
                            kubeconfig: value['kubeconfig'],
                            nodesIPs: value['nodes_ips'],
                            regionName: value['region_name'],
                            numNodes: value['num_nodes'],
                            totalvCPU: value['totalvCPU'],
                            totalMemory: value['totalMemory'],
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

    function store_instances(provider) {
        var instancesData = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_instances_data?provider=" + provider,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                       $.each(response, function(key, value) {
                        if (provider == 'aws') {
                            var instanceLocation = value['instance_region']
                        }
                        else if (provider == 'gcp') {
                            var instanceLocation = value['instance_zone']
                        }
                        instancesData.push({
                            instanceName: value['instance_name'],
                            instanceType: value['instance_type'],
                            instanceZone: instanceLocation,
                            internalIP: value['internal_ip'],
                            externalIP: value['external_ip'],
                            clientName: value['client_name'],
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

    function populate_kubernetes_clusters_objects(){
        var clustersHTML = '';
        var clusterNames = []
        var kubeconfigs_array = [];
        let clustersData = jQuery.parseJSON(window.localStorage.getItem("clustersData"));
        $.each(clustersData, function(key, value) {
            clusterNames.push(value.clusterName)
            var tags_string_ = JSON.stringify(value.tags);
            var tags_string__ = tags_string_.replace(/[{}]/g, "");
            var tags_string___ = tags_string__.replace(/[/"/"]/g, "");
            var tags_string = tags_string___.replace(/[,]/g, "<br>");
            var client_name_assign_element = '<select class="col-lg-8 align-content-lg-center" id="clusters-dropdown-' + value.clusterName + '"></select> <button type="submit" class="btn btn-primary btn-sm" id="clusters-button-' + value.clusterName + '" >Add</button>'
            clustersHTML += '<tr id="tr_' + value.clusterName + '">';
            clustersHTML += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.clusterName + '"><p>' + value.clusterName + '</p></a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.regionName + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.numNodes + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.totalvCPU + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.totalMemory + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.clusterVersion + '</a></td>';
            clustersHTML += '<td class="text-center"><a>' + value.humanExpirationTimestamp + '</a></td>';
            if (!value.clientName) {
                clustersHTML += '<td class="text-center" id="clusters-clientName-div-' + value.clusterName + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                clustersHTML += '<td class="text-center" id="clusters-clientName-div-' + value.clusterName + '"><a id="clusters-text-label-clientName-div-' + value.clusterName + '">' + value.clientName + '</a></td>';
            }
            clustersHTML += '<td class="text-center"><a>' + tags_string + '</a></td>';
            let manage_table_buttons = '<td class="project-actions text-right"> \
            <a class="btn btn-danger btn-sm" id="delete-button-' + value.clusterName + '" href="#"><i class="fas fa-trash"></i>Delete</a> </td> \
            <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true"> \
            <div class="modal-dialog modal-lg" role="document"> <div class="modal-content"> <div class="modal-header"> \
            <h5 class="modal-title" id="exampleModalLabel">Modal title</h5> \
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"> \
            <span aria-hidden="true">&times;</span></button> </div> <div class="modal-body"> \
            Testing stuff</div> <div class="modal-footer"> \
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> \
            <button type="button" class="btn btn-primary" id="copyKubeconfig-button-' + value.clusterName + '">Copy Kubeconfig</button> \
            </div> </div> </div> </div>'
            clustersHTML += manage_table_buttons
            kubeconfigs_array.push({
                key: value.clusterName,
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

        $.each(clusterNames, function( index, value ) {
            var clientNames = window.localStorage.getItem("clientNames");
            let clientNamesList = clientNames.split(',')
            $("#clusters-dropdown-" + value['clusterName']).append($("<option />").val('').text('Add a client'));
            $.each(clientNamesList, function( index, clientNameValue ) {
                $("#clusters-dropdown-" + value).append($("<option />").val(clientNameValue).text(clientNameValue));
            });
        });
    }

    function populate_instances_objects(){
        var instancesHTML = '';
        var instancesNames = []
        var kubeconfigs_array = [];
        let instancesData = jQuery.parseJSON(window.localStorage.getItem("instancesData"));
        $.each(instancesData, function(key, value) {
            instancesNames.push(value.instanceName)
            var tags_string_ = JSON.stringify(value.tags);
            var tags_string__ = tags_string_.replace(/[{}]/g, "");
            var tags_string___ = tags_string__.replace(/[/"/"]/g, "");
            var tags_string = tags_string___.replace(/[,]/g, "<br>");
            var client_name_assign_element = '<select class="col-lg-8 align-content-lg-center" id="instances-dropdown-' + value.instanceName + '"></select> <button type="submit" class="btn btn-primary btn-sm" id="instances-button-' + value.instanceName + '" >Add</button>'
            instancesHTML += '<tr id="tr_' + value.instanceName + '">';
            instancesHTML += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.instanceName + '"><p>' + value.instanceName + '</p></a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.instanceZone + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.internalIP + '</a></td>';
            instancesHTML += '<td class="text-center"><a>' + value.externalIP + '</a></td>';
            if (!value.clientName) {
                instancesHTML += '<td class="text-center" id="instances-clientName-div-' + value.instanceName + '"><a>' + client_name_assign_element + '</a></td>';
            } else {
                instancesHTML += '<td class="text-center" id="instances-clientName-div-' + value.instanceName + '"><a id="instances-text-label-clientName-div-' + value.instanceName + '">' + value.clientName + '</a></td>';
            }
            instancesHTML += '<td class="text-center"><a>' + tags_string + '</a></td>';
            let manage_table_buttons = '<td class="project-actions text-right"> \
            <a class="btn btn-danger btn-sm" id="delete-button-' + value.instanceName + '" href="#"><i class="fas fa-trash"></i>Delete</a> </td> \
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

        $.each(instancesNames, function( index, value ) {
            var clientNames = window.localStorage.getItem("clientNames");
            let clientNamesList = clientNames.split(',')
            $("#instances-dropdown-" + value['instanceName']).append($("<option />").val('').text('Add a client'));
            $.each(clientNamesList, function( index, clientNameValue ) {
                $("#instances-dropdown-" + value).append($("<option />").val(clientNameValue).text(clientNameValue));
            });
        });
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
                        const searchObject= clustersData.find((cluster) => cluster.clusterName==clusterName);
                        window.localStorage.setItem("regionName", searchObject.regionName[0]);
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

    function populate_regions_() {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-locations-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-regions-dropdown");
        }
        url = http + trolley_url + "/fetch_regions?cluster_type=" + clusterType;
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    alert("Failure to fetch regions data")
                } else {
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
                }
            }
        }, )
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
                    reject(error)
                    alert("Failure fetching regions data")
                },
            })
        })
    }

    function populate_users_data() {

        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_users_data",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                        first_name = value['first_name'].capitalize();
                        last_name = value['last_name'].capitalize();
                        userElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column id="user-div-' + value['user_name'] + '>'
                        userElement += '<div class="card bg-light d-flex flex-fill"><div class="card-body pt-0"><div class="row"><div class="col-7"><h2 class="lead"><br><b>' + value['user_name'] + '</b></h2>'
                        userElement += '<p class="text-muted text-sm"><b>User type: </b> ' + value['user_type'] + '<br>'
                        userElement += '<b>Team Name: </b> ' + value['team_name'] + '</p>'
                        userElement += '<ul class="ml-4 mb-0 fa-ul text-muted">'
                        userElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-building"></i></span> Address: ' + value['user_email'] + '</li>'
                        userElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-phone"></i></span> Registration Status: ' + value['registration_status'] + '</li>'
                        userElement += '<li class="small"><span class="fa-li"><i class="far fa-browser"></i></i></i></span> Full Name: ' + first_name  + ' ' + last_name +  '</li>'
                        userElement += '</ul></div><div class="col-4 text-center"><img src="data:image/png;base64,' + value['profile_image_str'] + 'alt="user-avatar" class="img-circle img-fluid"></div></div></div>'
                        userElement += '<div class="card-footer"><div class="text-right">'
                        userElement += '<a href="client-data?client_name=' + value['user_name'] + '" class="btn btn-sm btn-primary"><i class="fas fa-user" id="' + value['user_name'] + '-delete-user-button"></i> Delete User</a></div></div></div></div>'
                        });
                    }
                    $('#users-main-div').append(userElement);
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                    alert("Failure fetching client names data")
                },
            })
        })
    }

    function populate_clients_data() {

        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_clients_data",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                        clientElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column id="client-div-' + value['client_name'] + '>'
                        clientElement += '<div class="card bg-light d-flex flex-fill"><div class="card-body pt-0"><div class="row"><div class="col-7"><h2 class="lead"><br><b>' + value['client_name'] + '</b></h2>'
                        clientElement += '<p class="text-muted text-sm"><b>About: </b> ' + value['client_additional_info'] + '<br>'
                        clientElement += '<b>Contact Name: </b> ' + value['connection_name'] + '</p>'
                        clientElement += '<ul class="ml-4 mb-0 fa-ul text-muted">'
                        clientElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-building"></i></span> Address: ' + value['client_office_address'] + '</li>'
                        clientElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-phone"></i></span> Phone #: ' + value['connection_phone_number'] + '</li>'
                        clientElement += '<li class="small"><span class="fa-li"><i class="far fa-browser"></i></i></i></span> Web: <a href=' + value['client_web_address'] + ' target="_blank" >' + value['client_web_address'] + '</li>'
                        clientElement += '</ul></div></div></div>'
                        clientElement += '<div class="card-footer"><div class="text-right">'
                        clientElement += '<a href="client-data?client_name=' + value['client_name'] + '" class="btn btn-sm btn-primary"><i class="fas fa-user" id="' + value['client_name'] + '-view-profile-button"></i> View Profile</a></div></div></div></div>'
                        });
                    }
                    $('#clients-main-div').append(clientElement);
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                    alert("Failure fetching client names data")
                },
            })
        })
    }

    function populate_client_names(objectType) {
        if (objectType == 'cluster') {
            var $dropdown = $("#clusters-dropdown");
        }
        else if (objectType == 'instance') {
            var $dropdown = $("#instances-dropdown");
        }

        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/fetch_clients_data",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                            $dropdown.append($("<option />").val(value['client_name']).text(value['client_name']));
                        });
                    }
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                    alert("Failure fetching client names data")
                },
            })
        })
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
                    reject(error)
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
                    reject(error)
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
                    reject(error)
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
                    reject(error)
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
                    reject(error)
                    alert("Failure fetching Kubernetes image types")
                },
            })
        })
    }

    function populate_k8s_agent_data(clusterName) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: http + trolley_url + "/get_agent_cluster_data?cluster_name=" + clusterName,
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                        console.log(key);
                        console.log(value);
                    });
                    }
                    resolve(response)
                },
                error: function(error) {
                    reject(error)
                    alert("Failure fetching K8S agent data")
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
            if (value['clusterName'] === objectName) {
                discovered = value['discovered']
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

    function delete_client(clientName) {
        let client_deletion_data = JSON.stringify({
            "client_name": clientName
        });

        swal_message = 'A ' + clientName + ' was requested for deletion'
        url = http + trolley_url + "/client";
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

    $('#cloud-providers-dropdown').change(function() {
        var cloud_provider = $('#cloud-providers-dropdown').val();
        if (cloud_provider == "AWS") {
            $("#AWSAccessKeyIDDiv").show();
            $("#AWSSecretAccessKeyDiv").show();
            $("#AzureCredentialsDiv").hide();
            $("#GoogleCredsJSONDiv").hide();
        }
        else if (cloud_provider == "GCP") {
            $("#AWSAccessKeyIDDiv").hide();
            $("#AWSSecretAccessKeyDiv").hide();
            $("#AzureCredentialsDiv").hide();
            $("#GoogleCredsJSONDiv").show();
        }
        else if (cloud_provider == "Azure") {
            $("#AWSAccessKeyIDDiv").hide();
            $("#AWSSecretAccessKeyDiv").hide();
            $("#AzureCredentialsDiv").show();
            $("#GoogleCredsJSONDiv").hide();
        }
    })
    $(document).on("click", ".text-center", function() {
        var HTML = "";
        var valueID = this.id;
        var divValue = valueID.split("-")
        var objectType = divValue[0]
        var clientName = this.children[0].innerText;
        if (divValue[1] == "clientName") {
            var instanceName_ = $(this).parent().attr('id');
            var instanceName = instanceName_.slice(3);
            var textLabelId = "#" + objectType + "s-text-label-clientName-div-" + instanceName;
            $(textLabelId).hide();
            let clientNames = window.localStorage.getItem("clientNames")
            let clientNamesList = clientNames.split(',')
            var newDropDownHTML = '<td class="text-center"><select class="col-lg-8 align-content-lg-center" id="' + objectType + '-dropdown-' + instanceName + '"><a>';
            $.each(clientNamesList, function( index, clientNameValue ) {
                newDropDownHTML +=  '<option value="' + clientNameValue + '">' + clientNameValue + '</option>'
            });
            newDropDownHTML += '</select>'
            newDropDownHTML += '<button type="submit" class="btn btn-primary btn-sm" id="' + objectType + '-button-' + instanceName + '"</a>Add</button></td>'
            $('#' + objectType + '-clientName-div-' + instanceName).replaceWith(newDropDownHTML);
            console.log(newDropDownHTML)
        }
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
        }
        else if (objectType === 'instance') {
            let instanceData = window.localStorage.getItem("instancesData")
            let instanceNamesArray = [];
            var dataArray = JSON.parse(instanceData)
//        } if (this.innerText === "Add a new client!") {
//            assign_client_name(objectType, objectName, dataArray);
        } else if (this.innerText === "More") {
            console.log("Logic for viewing " + objectName + " cluster")
            window.localStorage.removeItem("currentClusterName");
            window.localStorage.setItem("currentClusterName", objectName);
        } else if (this.innerText === "Edit") {
            console.log("Logic for editing " + objectName + " cluster")
        } else if (this.innerText === "Back to clusters") {
            window.location.href = "manage-" + clusterType + "-clusters";
        } else if (this.innerText === "Delete") {
            console.log("Logic for deleting " + objectName + " cluster")
            delete_cluster(clusterType, objectName, dataArray)
        } else if (this.innerText === "Scan for clusters") {
            console.log("Logic for triggering a clusters scan")
            trigger_cloud_provider_discovery(provider, objectType='cluster')
        } else if (this.innerText === "Scan for VMs") {
            console.log("Logic for triggering a VMs scan")
            trigger_cloud_provider_discovery(provider, objectType='instance')
        } else if (this.innerText === "Copy Kubeconfig") {
            clusterName = window.localStorage.getItem("currentClusterName");
            console.log("Logic for copying kubeconfig for " + clusterName + " cluster")
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
        } else if ((this.lastChild.id.split("-")).includes("delete")){
            var clientName = this.lastChild.id.split("-")[1]
            delete_client(clientName)
            location.reload()
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
});