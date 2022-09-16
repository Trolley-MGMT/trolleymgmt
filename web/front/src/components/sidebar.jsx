import React, { Component } from "react";
import logo from './trolley.png';

class Sidebar extends Component {

  render() {
    const { firstName } = this.props.appData;
    return (
      <div className="col-lg-2 col-4 sidebar">
        <div className="logo">
          <img src={logo} width="200px" className="App-logo" alt="logo" />
          <br />
          Trolley
        </div>
        <hr />
        <div className="user">
         { firstName }
        </div>
        <hr />
        <div className="sidebar-navigation">
          <ul className="list">
            <h5><strong>Build Clusters</strong></h5>
            <li onClick={() => window.location.href="/index"}>Build a cluster</li>
            <li onClick={() => window.location.href="/build-aks-clusters"}>AKS Clusters</li>
            <li onClick={() => window.location.href="/build-eks-clusters"}>EKS Clusters</li>
            <li onClick={() => window.location.href="/build-gke-clusters"}>GKE Clusters</li>
          </ul>
          <ul className="list">
            <h5><strong>Cluster Management</strong></h5>
            <li onClick={() => window.location.href="/manage-aks-clusters"}>AKS Clusters</li>
            <li onClick={() => window.location.href="/manage-eks-clusters"}>EKS Clusters</li>
            <li onClick={() => window.location.href="/manage-gke-clusters"}>GKE Clusters</li>
          </ul>
          <ul className="list">
            <li onClick={() => window.location.href="/logout"}>Log Out</li>
          </ul>
        </div>
      </div>
    );
  }
}

export default Sidebar;