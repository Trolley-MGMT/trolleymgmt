$(document).ready(function() {
    window.localStorage.setItem("user_name", data['user_name']);
    let user_name = window.localStorage.getItem("user_name");
    window.localStorage.setItem("cluster_name", data['cluster_name']);
    let cluster_name = window.localStorage.getItem("cluster_name");
    let trolley_remote_url = ''
    let trolley_local_url = 'localhost';
    let trolley_url = '';
    let debug = true;
    let clusterType = ''
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
            <th style="width: 20%" class="text-center">
            </th></tr></thead><tbody><tr>`

    let manage_table_footer = `</tr></tbody></table></div>`

    if (debug === true) {
        trolley_url = trolley_local_url;
        gitBranch = 'master'
        port = 8081
    } else {
        trolley_url = trolley_remote_url
        gitBranch = 'master'
        port = 8081
    }

    if (pathname[1].includes('build')) {
        buildPage = true;
        clustersDataPage = false;
        dataPage = false;
        managePage = false;
    } else if (pathname[1].includes('manage')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = false;
        managePage = true;
    } else if (pathname[1].includes('clusters-data')) {
        buildPage = false;
        clustersDataPage = true;
        dataPage = false;
        managePage = false;
    } else if (pathname[1].includes('data')) {
        buildPage = false;
        clustersDataPage = false;
        dataPage = true;
        managePage = false;
    }

    if (($.inArray('build-aks-clusters', pathname) > -1) || ($.inArray('manage-aks-clusters', pathname) > -1)) {
        clusterType = 'aks'
    } else if (($.inArray('build-eks-clusters', pathname) > -1) || ($.inArray('manage-eks-clusters', pathname) > -1)) {
        clusterType = 'eks'
    } else if (($.inArray('build-gke-clusters', pathname) > -1) || ($.inArray('manage-gke-clusters', pathname) > -1)) {
        clusterType = 'gke'
    } else {
        clusterType = 'aks'
    }
    populate_logged_in_assets();

    if (buildPage) {
        populate_regions();
        populate_helm_installs();
    }
    if (managePage) {
        populate_kubernetes_clusters_objects();
    }
    if (clustersDataPage) {
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

    $("#agent-deployment-button").click(function() {
        let cluster_name = window.localStorage.getItem("cluster_name");
        let cluster_type = cluster_name.split('-')[1]
        let trolley_server_url = $('#trolley_server_url').val();

        let deploy_trolley_agent_data = JSON.stringify({
            "cluster_name": cluster_name,
            "cluster_type": cluster_type,
            "trolley_server_url": trolley_server_url,
        });

        url = "http://" + trolley_url + ":" + port + "/deploy_trolley_agent_on_cluster";

        swal_message = 'An trolley agent was deployed on' + cluster_name

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

    function populate_kubernetes_clusters_objects() {
        url = "http://" + trolley_url + ":" + port + "/get_clusters_data?cluster_type=" + clusterType + "&user_name=" + data['user_name'];
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                var cluster_data = '';
                var kubeconfigs_array = [];
                if (response.status === 'Failure') {
                    cluster_data += '<tr data-widget="expandable-table" aria-expanded="false">;>';
                    cluster_data += '<td>No Kubernetes clusters were found</td>';
                } else {
                    window.localStorage.removeItem("kubeconfigs");
                    $.each(response, function(key, value) {
                        cluster_data += '<tr id="tr_' + value.cluster_name + '">';
                        cluster_data += '<td class="text-center"><a href="clusters-data?cluster_name=' + value.cluster_name + '"><p>' + value.cluster_name + '</p></a></td>';
                        cluster_data += '<td class="text-center"><a>' + value.region_name + '</a></td>';
                        cluster_data += '<td class="text-center"><a>' + value.cluster_version + '</a></td>';
                        cluster_data += '<td class="text-center"><a>' + value.human_expiration_timestamp + '</a></td>';

                        let manage_table_buttons = '<td class="project-actions text-right"> \
                        <a class="btn btn-primary btn-sm " data-toggle="modal" data-target="#exampleModal" id="more-button-' + value.cluster_name + '" href="#"  ><i class="fas fa-folder"></i>More</a> \
                        <a class="btn btn-info btn-sm" id="edit-button-' + value.cluster_name + '" href="#"><i class="fas fa-pencil-alt"></i>Edit</a> \
                        <a class="btn btn-danger btn-sm" id="delete-button-' + value.cluster_name + '" href="#"><i class="fas fa-trash"></i>Delete</a> </td> \
                        <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true"> \
                        <div class="modal-dialog modal-lg" role="document"> <div class="modal-content"> <div class="modal-header"> \
                        <h5 class="modal-title" id="exampleModalLabel">Modal title</h5> \
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"> \
                        <span aria-hidden="true">&times;</span></button> </div> <div class="modal-body"> \
                        Testing stuff</div> <div class="modal-footer"> \
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button> \
                        <button type="button" class="btn btn-primary" id="copyKubeconfig-button-' + value.cluster_name + '">Copy Kubeconfig</button> \
                        </div> </div> </div> </div>'
                        cluster_data += manage_table_buttons
                        kubeconfigs_array.push({
                            key: value.cluster_name,
                            value: value.kubeconfig
                        });
                    })
                    window.localStorage.setItem("kubeconfigs", JSON.stringify(kubeconfigs_array));
                }
                full_table = manage_table_header + cluster_data + manage_table_footer
                if (clusterType == 'aks') {
                    $('#aks-clusters-management-table').append(full_table);
                } else if (clusterType == 'eks') {
                    $('#eks-clusters-management-table').append(full_table);
                } else if (clusterType == 'gke') {
                    $('#gke-clusters-management-table').append(full_table);
                }

            },
            error: function() {
                console.log('error loading orchestration items')
            }
        })
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
                    $.each(response, function(key, value) {
                        $('#agents-data-div').show();
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
            },
            error: function() {
                console.log('error loading orchestration items')
            }
        })
    }

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

    function populate_regions() {
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
                    console.log('error')
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

    function populate_zones(region_name) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-zones-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-zones-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-zones-dropdown");
        }
        url = "http://" + trolley_url + ":" + port + "/fetch_zones?cluster_type=" + clusterType + "&region_name=" + region_name;
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
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
            }
        }, )
    }

    function populate_subnets(zone_names) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-subnets-dropdown");
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-subnets-dropdown");
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-subnets-dropdown");
        }
        url = "http://" + trolley_url + ":" + port + "/fetch_subnets?cluster_type=" + clusterType + "&zone_names=" + zone_names;
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
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
            }
        }, )
    }

    function populate_vpcs(selected_location) {
        if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        }
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
                    $.each(response, function(key, value) {
                        $dropdown.append($("<option />").val(value).text(value));
                    });
                }
            }
        })
    }

    function populate_helm_installs() {
        var $dropdown = $("#helm-installs-dropdown");
        url = "http://" + trolley_url + ":" + port + "/fetch_helm_installs?names=True";
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
                    $.each(response, function(key, value) {
                        $dropdown.append($("<option />").val(value).text(value));
                    });
                }
            }
        }, )
    }

    function populate_kubernetes_versions(selected_location) {
         if (clusterType == 'aks') {
            var $dropdown = $("#aks-locations-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'eks') {
            var $dropdown = $("#eks-vpcs-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_aws_vpcs?aws_region=" + selected_location;
        } else if (clusterType == 'gke') {
            var $dropdown = $("#gke-versions-dropdown");
            var url = "http://" + trolley_url + ":" + port + "/fetch_gke_versions?gcp_zone=" + selected_location;
        }
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
                    $.each(response, function(key, value) {
                        $dropdown.append($("<option />").val(value).text(value));
                    });
                }
            }
        }, )
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
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
                    $.each(response, function(key, value) {
                        $dropdown.append($("<option />").val(value).text(value));
                    });
                }
            }
        }, )
    }

    function populate_k8s_agent_data(clusterName) {
        var url = "http://" + trolley_url + ":" + port + "/get_agent_cluster_data?cluster_name=" + clusterName;
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                if (response.status === 'Failure') {
                    console.log('error')
                } else {
                    $.each(response, function(key, value) {
                        console.log(key);
                        console.log(value);
                    });
                }
            }
        }, )
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
            showConfirmButton: false,
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
        if (this.innerText === "More") {
            console.log("Logic for viewing " + clusterName + " cluster")
            window.localStorage.removeItem("currentClusterName");
            window.localStorage.setItem("currentClusterName", clusterName);
            populate_k8s_agent_data(clusterName)
        } else if (this.innerText === "Edit") {
            console.log("Logic for editing " + clusterName + " cluster")
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