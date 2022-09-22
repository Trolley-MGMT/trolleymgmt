import React, { Component } from "react";
import logo from './images/trolley.png';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCubes, faWrench, faRightFromBracket } from '@fortawesome/free-solid-svg-icons';

class Sidebar extends Component {

  render() {
    let image = '';
    console.log(document.getElementById('image').textContent);
    if (document.getElementById('image').textContent == '{{ image|default("")|tojson }}') {
      image = logo;
    } else {
      image = document.getElementById('image').textContent;
      image = image.substring(1, image.length - 1);
    }
    const { firstName } = this.props.appData;
    const fontStyle = { color: 'rgba(255, 255, 255, 0.5)' };
    return (
      <div className="col-lg-2 col-1 sidebar">
        <div className="logo" onClick={() => window.location.href="/index"}>
          <img src={logo} className="App-logo" alt="logo" />
          <br />
          <span className="sidebar-text">Trolley</span>
        </div>
        <hr />
        <div className="sidebar-text">
          <div className="user">
            <img src={image} width="20px" className="rounded-circle me-2" />
            { firstName }
          </div>
          <hr />
        </div>
        <div className="sidebar-navigation">
          <ul className="list">
            <h5><FontAwesomeIcon icon={faCubes} style={fontStyle} /><span className="sidebar-text"><strong>Build Clusters</strong></span></h5>
            <li onClick={() => window.location.href="/build-aks-clusters"}>AKS<span className="sidebar-text"> Clusters</span></li>
            <li onClick={() => window.location.href="/build-eks-clusters"}>EKS<span className="sidebar-text"> Clusters</span></li>
            <li onClick={() => window.location.href="/build-gke-clusters"}>GKE<span className="sidebar-text"> Clusters</span></li>
          </ul>
          <ul className="list">
            <h5><FontAwesomeIcon icon={faWrench} style={fontStyle} /><span className="sidebar-text"><strong>Cluster Management</strong></span></h5>
            <li onClick={() => window.location.href="/manage-aks-clusters"}>AKS<span className="sidebar-text"> Clusters</span></li>
            <li onClick={() => window.location.href="/manage-eks-clusters"}>EKS<span className="sidebar-text"> Clusters</span></li>
            <li onClick={() => window.location.href="/manage-gke-clusters"}>GKE<span className="sidebar-text"> Clusters</span></li>
          </ul>
          <ul className="list">
            <li onClick={() => window.location.href="/logout"} style={{ paddingLeft: '15px', fontSize: '1rem' }}><FontAwesomeIcon icon={faRightFromBracket} style={fontStyle} /><span className="sidebar-text">Log Out</span></li>
          </ul>
        </div>
      </div>
    );
  }
}

export default Sidebar;