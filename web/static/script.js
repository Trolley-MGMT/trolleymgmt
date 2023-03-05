$(document).ready(function() {
    window.localStorage.setItem("userName", data['user_name']);
    let user_name = window.localStorage.getItem("userName");
    window.localStorage.setItem("clusterName", data['cluster_name']);
    let clusterName = window.localStorage.getItem("clusterName");
    let clusterType = clusterName.split('-')[1]
    window.localStorage.setItem("clusterType", clusterType);
    let trolley_remote_url = '34.123.171.234';
    let trolley_local_url = 'localhost';
    let trolley_url = 'http://www.pavelzagalsky.com';
    let debug = false;
    let managePage = false;
    let buildPage = false;
    let pathname = window.location.pathname.split('/');

    let manage_table_header = `<div class="card-body p-0">
    <table class="table table-striped projects" >
        <thead>
        <tr><th style="width: 10%" class="text-center">Cluster Name</th>
            <th style="width: 10%" class="text-center">Cluster Region</th>
            <th style="width: 10%" class="text-center">Kubernetes Version</th>
            <th style="width: 15%" class="text-center">Expiration Time</th>
            <th style="width: 15%" class="text-center">Client Name</th>
            <th style="width: 15%" class="text-center">Tags</th>
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let manage_table_footer = `</tr></tbody></table></div>`
    var clientElement = '';
    var clientElementHeader = '<div class="row">';
    var clientElementFooter = '</div>';


    if (debug === true) {
        trolley_url = trolley_local_url;
        gitBranch = 'master'
        port = 8081
    } else {
        trolley_url = trolley_remote_url
        gitBranch = 'master'
        port = 80
    }

    if (pathname[1].includes('build')) {
        buildPage = true;
        clustersDataPage = false;
        dataPage = false;
        managePage = false;
        clientsPage = false;
    } else if (pathname[1].includes('manage')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        managePage = true;
        clientsPage = false;
    } else if (pathname[1].includes('clusters-data')) {
        buildPage = false;
        clustersDataPage = true;
        dataPage = false;
        managePage = false;
        clientsPage = false;
    } else if (pathname[1].includes('data')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = true;
        managePage = false;
        clientsPage = false;
    } else if (pathname[1].includes('clients')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        managePage = false;
        clientsPage = true;
    } else {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        managePage = false;
        clientsPage = false;
}
    if (($.inArray('build-aks-clusters', pathname) > -1) || ($.inArray('manage-aks-clusters', pathname) > -1)) {
        clusterType = 'aks'
        window.localStorage.setItem("clusterType", clusterType);
    } else if (($.inArray('build-eks-clusters', pathname) > -1) || ($.inArray('manage-eks-clusters', pathname) > -1)) {
        clusterType = 'eks'
        window.localStorage.setItem("clusterType", clusterType);
    } else if (($.inArray('build-gke-clusters', pathname) > -1) || ($.inArray('manage-gke-clusters', pathname) > -1)) {
        clusterType = 'gke'
        window.localStorage.setItem("clusterType", clusterType);
    } else {
        clusterType = clusterType
    }

    populate_logged_in_assets();

    if (buildPage) {
        populate_regions();
    }

    if (clientsPage) {
        populate_clients_data();

    }
    if (managePage) {
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
        populate_kubernetes_agent_data();
        populate_client_names();
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
            url = "http://" + trolley_url + ":" + port + "/trigger_aks_deployment";
            trigger_data = trigger_aks_deployment_data
            expiration_time = AKSExpirationTime
        } else if (clusterType == 'eks') {
            url = "http://" + trolley_url + ":" + port + "/trigger_eks_deployment";
            trigger_data = trigger_eks_deployment_data
            expiration_time = EKSExpirationTime
        } else if (clusterType == 'gke') {
            url = "http://" + trolley_url + ":" + port + "/trigger_gke_deployment";
            trigger_data = trigger_gke_deployment_data
            expiration_time = GKEExpirationTime
        } else {
            url = "http://" + trolley_url + ":" + port + "/trigger_kubernetes_deployment";
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


        url = "http://" + trolley_url + ":" + port + "/provider";

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


        url = "http://" + trolley_url + ":" + port + "/client";

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
        let clusterType = clusterName.split('-')[1]
        let trolleyServerURL = $('#trolley_server_url').val();

        let deploy_trolley_agent_data = JSON.stringify({
            "cluster_name": clusterName,
            "cluster_type": clusterType,
            "trolley_server_url": trolleyServerURL,
        });

        url = "http://" + trolley_url + ":" + port + "/deploy_trolley_agent_on_cluster";

        swal_message = 'An trolley agent was deployed on' + clusterName

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

    function assign_client_name(clusterName) {
        let cluster_names_array = jQuery.parseJSON(window.localStorage.getItem("clusterNames"))
        let discovered = false
        $.each(cluster_names_array, function(key, value) {
            if (value['clusterName'] === clusterName) {
                discovered = true
            }
            });

        let clusterType = window.localStorage.getItem("clusterType");
        let clientName = $('#clientnames-dropdown-' + clusterName).val();

        let assign_client_data = JSON.stringify({
            "cluster_type": clusterType,
            "cluster_name": clusterName,
            "client_name": clientName,
            "discovered": discovered

        });


        url = "http://" + trolley_url + ":" + port + "/client";

        swal_message = 'A request to assign a ' + clientName + ' client to ' + clusterName + ' was sent'

        const xhr = new XMLHttpRequest();
        xhr.open("PUT", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
            }
        };
        xhr.send(assign_client_data);

        Swal.fire({
            position: 'top-end',
            icon: 'success',
            title: swal_message,
            showConfirmButton: false,
            timer: 5000
        })

        $("#clientnames-dropdown-" + clusterName).hide();
        $("#clientnames-button-" + clusterName).hide();
        $("#" + clusterName + "-div").append("<a>" + clientName + "</a>");
    }

    function store_client_names() {
        var clientNames = []
        return new Promise((resolve, reject) => {
            $.ajax({
                url: "http://" + trolley_url + ":" + port + "/fetch_clients_data",
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
                url: "http://" + trolley_url + ":" + port + "/get_clusters_data?cluster_type=" + clusterType + "&user_name=" + data['user_name'],
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

    function populate_kubernetes_clusters_objects(){
        var clusterHTML = '';
        var clusterNames = []
        var kubeconfigs_array = [];
        let clustersData = jQuery.parseJSON(window.localStorage.getItem("clustersData"));
        $.each(clustersData, function(key, value) {
            clusterNames.push(value.clusterName)
            var tags_string_ = JSON.stringify(value.tags);
            var tags_string__ = tags_string_.replace(/[{}]/g, "");
            var tags_string___ = tags_string__.replace(/[/"/"]/g, "");
            var tags_string = tags_string___.replace(/[,]/g, "<br>");
            var client_name_assign_element = '<select class="col-lg-8 align-content-lg-center" id="clientnames-dropdown-' + value.clusterName + '"></select> <button type="submit" class="btn btn-primary btn-sm" id="clientnames-button-' + value.clusterName + '" >Add</button>'
            clusterHTML += '<tr id="tr_' + value.clusterName + '">';
            clusterHTML += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.clusterName + '"><p>' + value.clusterName + '</p></a></td>';
            clusterHTML += '<td class="text-center"><a>' + value.regionName + '</a></td>';
            clusterHTML += '<td class="text-center"><a>' + value.clusterVersion + '</a></td>';
            clusterHTML += '<td class="text-center"><a>' + value.humanExpirationTimestamp + '</a></td>';
            if (value.clientName === '') {
                clusterHTML += '<td class="text-center" id="' + value.clusterName + '-div"><a>' + client_name_assign_element + '</a></td>';
            } else {
                clusterHTML += '<td class="text-center"><a>' + value.clientName + '</a></td>';
            }
            clusterHTML += '<td class="text-center"><a>' + tags_string + '</a></td>';
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
            clusterHTML += manage_table_buttons
            kubeconfigs_array.push({
                key: value.clusterName,
                value: value.kubeconfig
            });
        full_table = manage_table_header + clusterHTML + manage_table_footer

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
            $("#clientnames-dropdown-" + value['clusterName']).append($("<option />").val('').text('Add a client'));
            $.each(clientNamesList, function( index, clientNameValue ) {
                $("#clientnames-dropdown-" + value).append($("<option />").val(clientNameValue).text(clientNameValue));
            });
        });
    }

    function populate_kubernetes_agent_data() {
        url = "http://" + trolley_url + ":" + port + "/get_agent_cluster_data?cluster_name=" + data['cluster_name'];
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if ((response.status === 'Failure') || (response[0].content === null)) {
                        $('#resources-title').replaceWith('Trolley Agent was not found on the cluster. Click to install!');
                        $('#agent-deployment-div').show();
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
        url = "http://" + trolley_url + ":" + port + "/fetch_regions?cluster_type=" + clusterType;
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
                url: "http://" + trolley_url + ":" + port + "/fetch_regions?cluster_type=" + clusterType,
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

    function populate_clients_data() {

        return new Promise((resolve, reject) => {
            $.ajax({
                url: "http://" + trolley_url + ":" + port + "/fetch_clients_data",
                type: 'GET',
                success: function(response) {
                    if (response.length > 0) {
                        $.each(response, function(key, value) {
                               clientElement += '<div class="col-12 col-sm-6 col-md-4 d-flex align-items-stretch flex-column" id="client-div-' + value['client_name'] + '> <div class="card bg-light d-flex flex-fill">'
                               clientElement += '<div class="card-body pt-0"><div class="row"><div class="col-7"><h2 class="lead"><b>' + value['client_name'] + '</b></h2>'
                               clientElement += '<p class="text-muted text-sm"><b>About: ' + value['client_additional_info'] + ' </p><ul class="ml-4 mb-0 fa-ul text-muted"> <li class="small"><span class="fa-li">'
                               clientElement += '<i class="fas fa-lg fa-building"></i></span> Address: ' + value['client_office_address'] + '</li>'
                               clientElement += '<li class="small"><span class="fa-li"><i class="fas fa-lg fa-phone"></i></span> Phone #: ' + value['connection_phone_number'] + '</li></ul></div></div></div>'
                               clientElement += '<div class="card-footer"><div class="text-right"><a href="#" class="btn btn-sm bg-teal"><i class="fas fa-trash" id="delete-' + value['client_name'] + '-client"></i></a>'
                               clientElement += '<a href="#" class="btn btn-sm btn-primary"><i class="fas fa-user"></i> View Profile</a></div></div></div></div>'
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

    function populate_client_names() {
        var $dropdown = $("#clientnames-dropdown");
        return new Promise((resolve, reject) => {
            $.ajax({
                url: "http://" + trolley_url + ":" + port + "/fetch_clients_data",
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
                url: "http://" + trolley_url + ":" + port + "/fetch_zones?cluster_type=" + clusterType + "&region_name=" + region_name,
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
                url: "http://" + trolley_url + ":" + port + "/fetch_subnets?cluster_type=" + clusterType + "&zone_names=" + zone_names,
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
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        }
        return new Promise((resolve, reject) => {
            $.ajax({
                url: "http://" + trolley_url + ":" + port + "/fetch_client_names",
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
            var url = "http://" + trolley_url + ":" + port + "/fetch_aks_versions?az_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-versions-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_eks_versions?aws_region=" + selected_location;
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-versions-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_gke_versions?gcp_zone=" + selected_location;
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
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-image-types-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_gke_image_types?gcp_zone=" + selected_location;
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
                url: "http://" + trolley_url + ":" + port + "/get_agent_cluster_data?cluster_name=" + clusterName,
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

    function delete_cluster(clusterType, clusterName) {
        let cluster_deletion_data = JSON.stringify({
            "cluster_type": clusterType,
            "cluster_name": clusterName
        });

        swal_message = 'A ' + clusterName + ' ' + clusterType + ' cluster was requested for deletion'

        url = "http://" + trolley_url + ":" + port + "/delete_cluster";
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

        url = "http://" + trolley_url + ":" + port + "/client";
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

    $(document).on("click", ".btn", function() {
        var valueID = this.id;
        var buttonValue = valueID.split("-")
        buttonValue.splice(0, 2)
        var clusterName = buttonValue.join("-")
        if (this.innerText === "Add") {
            assign_client_name(clusterName);
        }
        if (this.innerText === "More") {
            console.log("Logic for viewing " + clusterName + " cluster")
            window.localStorage.removeItem("currentClusterName");
            window.localStorage.setItem("currentClusterName", clusterName);
        } else if (this.innerText === "Edit") {
            console.log("Logic for editing " + clusterName + " cluster")
        } else if (this.innerText === "Back to clusters") {
            window.location.href = "manage-" + clusterType + "-clusters";
        } else if (this.innerText === "Delete") {
            console.log("Logic for deleting " + clusterName + " cluster")
            delete_cluster(clusterType, clusterName)
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