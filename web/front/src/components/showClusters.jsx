import React, { Component } from "react";
import Table from "./table";
import { Toast } from 'bootstrap/dist/js/bootstrap';
import mockData from './mockdata.json';

class ShowClusters extends Component {

  constructor(props) {
    super(props);
    this.state = {
      loading: true,
      data: [],
      toastMessage: ''
    }
  }

  async componentDidMount() {
    const { 
      appData: { trolleyUrl, port, userName },
      type: clusterType
    } = this.props;
    let url = `http://${trolleyUrl}:${port}/get_clusters_data?cluster_type=${clusterType}&user_name=${userName}`;
    console.log(url);
    try {
      const response = await fetch(url);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const data = await response.json();
      console.log(data);
      this.setState({ data });
    } catch(error) {
      console.log(error);
      let data = mockData;
      this.setState({ data });
    } finally {
      this.setState({ loading: false });
    }
  }

  deleteCluster = async (clusterName) => {
    const { 
      appData: { trolleyUrl, port },
      type: clusterType
          } = this.props;

    const clusterDeletionData = JSON.stringify({
      "cluster_type": clusterType,
      "cluster_name": clusterName
    });

    let toastMessage = `A ${clusterName} ${clusterType} cluster was requested for deletion`;
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
        const error = await response.text();
        throw new Error(error);
      }
      const json = await response.json();
    } catch(error) {
      console.log(error);
      toastMessage = `Error: ${error}`;
    } finally {
      this.setState({ toastMessage });
      const toastEl = document.getElementById('toast');
      const toast = new Toast(toastEl);
      toast.show();
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

  saveKubeConfig = async (clusterName, kubeConfig) => {
    //TODO
  }

  renderTable() {
    if (this.state.loading){
      return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
    }
    else {
      if (this.state.data.length === 0){
        return <p>No clusters to show, <a href={`/build-${this.props.type}-clusters`}>Make a new one</a>.</p>;
      }
      return (
        <div className="table-responsive">
          <Table
            data={this.state.data}
            deleteCluster={this.deleteCluster}
            copyKubeConfig={this.copyKubeConfig}
            saveKubeConfig={this.saveKubeConfig} />
        </div>
      );
      }
  }
  
  render() {
    return(
      <div className="col text-center"  style={{minWidth: '0px'}}>
        <br />
        <h2>Manage {this.props.type.toUpperCase()} clusters</h2>
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