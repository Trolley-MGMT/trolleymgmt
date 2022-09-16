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
      clusterType: 'gke',
      toastMessage: '',
      // selected
      nodesAmt: '1',
      version: '',
      imageType: '',
      location: '',
      zone: '',
      helmInstall: [],
      expirationTime: '1',
      // needs to be populated
      locations: [],
      versions: [],
      imageTypes: [],
      zones: [],
      helmInstalls: [],
    }
  }

  async componentDidMount(){
    const { trolleyUrl, port, clusterType } = this.state;
    // Get locations/regions
    const url_locations = `http://${trolleyUrl}:${port}/fetch_regions?cluster_type=${clusterType}`;
    try {
      const response = await fetch(url_locations);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const locations = await response.json();
      this.setState({ locations, location: locations[0] });
      await this.getZones(locations[1]);
    } catch(error) {
      throw new Error(error);
    }      
    // Get helm installs
    const url2 = `http://${trolleyUrl}:${port}/fetch_helm_installs?names=True`;
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

  async getZones(location) {
    const { trolleyUrl, port, clusterType } = this.state;
    const url_zones = `http://${trolleyUrl}:${port}/fetch_zones?cluster_type=${clusterType}&region_name=${location}`;
    try {
      const response = await fetch(url_zones);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const zones = await response.json();
      this.setState({ zones, zone: zones[0] });
      await this.getVersions(zones[0]);
      await this.getImageTypes(zones[0]);
    } catch(error) {
      throw new Error(error);
    }
  }

  async getVersions(zone) {
    const { trolleyUrl, port } = this.state;
    const url = `http://${trolleyUrl}:${port}/fetch_gke_versions?gcp_zone=${zone}`;
    try {
      const response = await fetch(url);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const versions = await response.json();
      this.setState({ versions, version: versions[0] });
    } catch(error) {
      throw new Error(error);
    }
  }

  async getImageTypes(zone) {
    const { trolleyUrl, port } = this.state;
    const url = `http://${trolleyUrl}:${port}/fetch_gke_image_types?gcp_zone=${zone}`;
    try {
      const response = await fetch(url);
      if (!response.ok){
        const error = response.statusText;
        throw new Error(error);
      }
      const imageTypes = await response.json();
      this.setState({ imageTypes, imageType: imageTypes[0] });
    } catch(error) {
      throw new Error(error);
    }
  }

  populateVersions() {
    return(
      this.state.versions.map((item) => (
        <option value={item}>{item}</option>
      ))
    );
  }

  populateImageTypes() {
    return(
      this.state.imageTypes.map((item) => (
        <option value={item}>{item}</option>
      ))
    );
  }

  populateLocations() {
    return(
      this.state.locations.map((item) => (
        <option value={item}>{item}</option>
      ))
    );
  }

  populateZones() {
    return(
      this.state.zones.map((item) => (
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

  handleImageTypeChange = (e) => {
    this.setState({ imageType: e.target.value });
  }

  handleLocationChange = (e) => {
    this.setState({ location: e.target.value });
    this.getZones(e.target.value);
  }

  handleZonesChange = (e) => {
    this.setState({ zone: e.target.value });
  }

  handleHelmInstallsChange = (e) => {
    this.setState({ helmInstall: [...e.target.selectedOptions].map(opt => opt.value) });
  }

  handleExpirationTimeChange = (e) => {
    this.setState({ expirationTime: e.target.value });
  }

  async buildCluster() {
    const { nodesAmt, version, imageType, expirationTime, location, zone, helmInstall, trolleyUrl, port, clusterType } = this.state;

    const triggerData = JSON.stringify({
      "cluster_type": 'gke',
      "user_name": this.props.appData.userName,
      "num_nodes": nodesAmt,
      "version": version,
      "image_type": imageType,
      "expiration_time": expirationTime,
      "gke_region": location,
      "gke_zone": zone,
      "helm_installs": helmInstall
    });
    console.log(triggerData);

    const url = `http://${trolleyUrl}:${port}/trigger_kubernetes_deployment`;
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
        <h2 className="mt-4 mb-4">Build a GKE cluster</h2>
        <div className="row justify-content-md-center">
          <div className="form col-lg-6">
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="nodes-amt" style={{ paddingRight: '26px' }}>Select the amount of nodes</label>
              <select
                className="form-select"
                value={this.state.nodesAmt}
                onChange={this.handleNodesAmtChange}
                id="nodes-amt"
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
                { this.populateVersions() }
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="image-types-dropdown">Select Kubernetes Image type</label>
              <select
                className="form-select"
                value={this.state.imageType}
                onChange={this.handleImageTypeChange}
                id="image-types-dropdown"
              >
                { this.populateImageTypes() }
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="locations" style={{ paddingRight: '125px' }}>Select Region</label>
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
              <label className="input-group-text input-color" htmlFor="zones" style={{ paddingRight: '138px' }}>Select Zone</label>
              <select
                className="form-select"
                value={this.state.zone}
                onChange={this.handleZonesChange}
                id="zones"
              >
                { this.populateZones() }
              </select>
            </div>
            <div className="input-group mt-3 mb-3">
              <label className="input-group-text input-color" htmlFor="helm-installs" style={{ paddingRight: '48px' }}>Select Helm Installations</label>
              <select multiple
                className="form-select"
                value={this.state.helmInstall}
                onChange={this.handleHelmInstallsChange}
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
            <button onClick={() => this.buildCluster()} className="btn btn-outline-light mb-2" id="build-cluster-button">Build Cluster!</button>
          </div>
        </div>
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

export default CreateCluster;