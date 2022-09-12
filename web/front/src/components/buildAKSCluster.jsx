import React, { Component } from "react";
import { Toast } from 'bootstrap/dist/js/bootstrap';

class CreateCluster extends Component {

  constructor(props) {
    super(props);
    const { trolleyRemoteUrl, trolleyLocalUrl, debug } = this.props.appData;
    this.state = {
      // data
      trolleyUrl: debug ? trolleyLocalUrl : trolleyRemoteUrl,
      port: 8081,
      clusterType: 'aks',
      toastMessage: '',
      // selected
      nodesAmt: '1',
      version: '1.24.0',
      location: '',
      helmInstall: [],
      expirationTime: '1',
      // needs to be populated
      locations: [],
      helmInstalls: [],
    }
  }

  async componentDidMount(){
    const { trolleyUrl, port, clusterType } = this.state;
    // Get locations/regions
    let url = `http://${trolleyUrl}:${port}/fetch_regions?clusters_type=${clusterType}`;
    try {
      const response = await fetch(url);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const locations = await response.json();
      this.setState({ locations, location: locations[0] });
    } catch(error) {
      throw new Error(error);
    }      
    // Get helm installs
    let url2 = `http://${trolleyUrl}:${port}/fetch_helm_installs?names=True`;
    try {
      const response = await fetch(url2);
      if (!response.ok){
        const err = await response.text();
        throw new Error(err);
      }
      const helmInstalls = await response.json();
      this.setState({ helmInstalls });
    } catch(error) {
      console.log(error);
    }      
  }

  populateLocations() {
    return(
      this.state.locations.map((item) => (
        <option value={item}>{item}</option>
      ))
    );
  }

  populateHelmInstalls() {
    return(
      this.state.helmInstalls.map((item) => (
        <option value={item}>{item}</option>
      ))
    );
  }

  handleNodesAmtChange = (e) => {
    this.setState({ nodesAmt: e.target.value });
  }

  handleVersionChange = (e) => {
    this.setState({ version: e.target.value });
  }

  handleLocationChange = (e) => {
    this.setState({ location: e.target.value });
  }

  handleHelmInstallChange = (e) => {
    this.setState({ helmInstall: [...e.target.selectedOptions].map(opt => opt.value) });
  }

  handleExpirationTimeChange = (e) => {
    this.setState({ expirationTime: e.target.value });
  }

  async buildCluster() {
    const { nodesAmt, version, expirationTime, location, helmInstall, trolleyUrl, port, clusterType } = this.state;

    const triggerData = JSON.stringify({
      "user_name": this.props.appData.userName,
      "num_nodes": nodesAmt,
      "version": version,
      "expiration_time": expirationTime,
      "aks_location": location,
      "helm_installs": helmInstall
    });
    console.log(triggerData);

    const url = `http://${trolleyUrl}:${port}/trigger_aks_deployment`;
    const toastMessage = `An ${clusterType} deployment was requested for ${version} kubernetes version with ${expirationTime} expiration time`;
    this.setState({ toastMessage });
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: triggerData
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
      console.log(error);
    }
  }

  renderToast(message) {

  }

  render() {
    return (
      <div className="col-lg-10 col-8 text-center">
        <h2 className="mt-4 mb-4">Build an AKS cluster</h2>
        <div className="row justify-content-md-center">
          <div className="form col-lg-6">
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="aks-nodes-amt" style={{ paddingRight: '26px' }}>Select the amount of nodes</label>
              <select
                className="form-select"
                value={this.state.nodesAmt}
                onChange={this.handleNodesAmtChange}
                id="aks-nodes-amt"
              >
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="versions-dropdown">Select the Kubernetes version</label>
              <select
                className="form-select"
                value={this.state.version}
                onChange={this.handleVersionChange}
                id="versions-dropdown"
              >
                <option value="1.24.0">1.24.0</option>
                <option value="1.23.8">1.23.8</option>
                <option value="1.22.11">1.22.11</option>
                <option value="1.21.14">1.21.14</option>
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="locations" style={{ paddingRight: '118px' }}>Select location</label>
              <select
                className="form-select"
                value={this.state.location}
                onChange={this.handleLocationChange}
                id="locations"
              >
                { this.populateLocations() }
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="helm-installs" style={{ paddingRight: '48px' }}>Select Helm Installations</label>
              <select multiple
                className="form-select"
                value={this.state.helmInstall}
                onChange={this.handleHelmInstallChange}
                id="helm-installs"
              >
                { this.populateHelmInstalls() }
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="expiration-time" style={{ paddingRight: '39px'}}>Select the expiration time</label>
              <select
                className="form-select"
                value={this.state.expirationTime}
                onChange={this.handleExpirationTimeChange}
                id="expiration-time"
              >
                <option value="1">1h</option>
                <option value="2">2h</option>
                <option value="4">4h</option>
                <option value="8">8h</option>
                <option value="12">12h</option>
                <option value="24">24h</option>
                <option value="48">2d</option>
                <option value="96">4d</option>
                <option value="168">7d</option>
                <option value="336">14d</option>
                <option value="720">30d</option>
              </select>
            </div>
            <button onClick={() => this.buildCluster()} className="btn btn-outline-light" id="build-cluster-button">Build Cluster!</button>
          </div>
        </div>
        <div class="toast-container position-absolute top-0 end-0 p-3">
          <div class="toast" id="toast" role="alert" aria-atomic="true" data-bs-delay="5000">
            <div class="toast-header">
              { this.state.toastMessage }
              <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default CreateCluster;