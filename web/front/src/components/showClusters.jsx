import React, { Component } from "react";
import Table from "./table";
import { Toast } from 'bootstrap/dist/js/bootstrap';

class ShowClusters extends Component {

  constructor(props) {
    super(props);
    const { trolleyRemoteUrl, trolleyLocalUrl, debug, userName } = this.props.appData;
    this.state = {
      loading: true,
      trolleyUrl: debug ? trolleyLocalUrl : trolleyRemoteUrl,
      port: 8081,
      clusterType: this.props.type,
      data: [],
      userName: userName,
      toastMessage: ''
    }
  }

  async componentDidMount() {
    const { trolleyUrl, port, clusterType, userName } = this.state;
    let url = `http://${trolleyUrl}:${port}/get_clusters_data?cluster_type=${clusterType}&user_name=${userName}`;
    //let url = `http://${trolleyUrl}:${port}/get_clusters_data?cluster_type=${clusterType}&user_name=einatsoferman`;
    try {
      const response = await fetch(url);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const data = await response.json();
      console.log(data);
      this.setState({ data, loading: false });
    } catch(error) {
      throw new Error(error);
    }
  }

  deleteCluster = async (clusterName) => {
    const { trolleyUrl, port, clusterType } = this.state;

    const clusterDeletionData = JSON.stringify({
      "cluster_type": clusterType,
      "cluster_name": clusterName
    });

    const toastMessage = `A ${clusterName} ${clusterType} cluster was requested for deletion`;
    this.setState({ toastMessage });
    const url = `http://${trolleyUrl}:${port}/delete_cluster`;
    const options = {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: clusterDeletionData
    };
    try {
      const response = await fetch(url, options);
      console.log(response);
      if (!response.ok){
        const err = await response.text();
        throw new Error(err);
      }
      const json = await response.json();
      const toastEl = document.getElementById('toast');
      const toast = new Toast(toastEl);
      toast.show();
    } catch(error) {
      throw new Error(error);
    }     
  }

  copyKubeConfig = async (kubeConfig) => {
    if (typeof(navigator.clipboard) == 'undefined') {
      console.log('navigator.clipboard');
      var textArea = document.createElement("textarea");
      textArea.value = kubeConfig;
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
    try {
      await navigator.clipboard.writeText(kubeConfig);
      console.log(`successful!`);
      const toastMessage = `A Kubeconfig was copied to your clipboard!`;
      this.setState({ toastMessage });
      const toastEl = document.getElementById('toast');
      const toast = new Toast(toastEl);
      toast.show();
    } catch (error) {
      console.log('unsuccessful!', error);
    }
  }

  renderTable() {
    if (this.state.loading){
      return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
    }
    else {
      if (this.state.data.length === 0){
        const link = `/build-${this.props.type}-clusters`;
        return <p>No clusters to show, <a href={link}>Make a new one</a>.</p>;
      }
      return (
        <div className="table-responsive">
          <Table
            data={this.state.data}
            deleteCluster={this.deleteCluster}
            copyKubeConfig={this.copyKubeConfig} />
        </div>
      );
      }
  }
  
  render() {
    return(
      <div className="col-lg-10 col-8 text-center">
        <br />
        <h2>Manage {this.state.clusterType.toUpperCase()} clusters</h2>
        <br />
        {this.renderTable()}
        <div className="toast-container position-absolute top-0 end-0 p-3">
          <div className="toast" id="toast" role="alert" aria-atomic="true" data-bs-delay="5000">
            <div className="toast-header">
              { this.state.toastMessage }
              <button type="button" className="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ShowClusters;