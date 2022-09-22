import React, { Component } from "react";
import AKSLogo from './images/aks.png';
import EKSLogo from './images/eks.png';
import GKELogo from './images/gke.png';

class Main extends Component {

  render() {
    return(
      <div className="col text-center">
        <div className="row col-lg-10 mx-auto">
          <h2 className="mt-4 mb-5">Build a new cluster</h2>
          <div className="col-sm-4 text-center mt-4 pick-image" title="AKS">
            <button type="button" onClick={() => window.location.href="/build-aks-clusters"} className="btn btn-outline-secondary">
              <img src={AKSLogo} alt="AKS" />
            </button>
          </div>
          <div className="col-sm-4 text-center mt-4 pick-image" title="EKS">
            <button type="button" onClick={() => window.location.href="/build-eks-clusters"} className="btn btn-outline-secondary">
              <img src={EKSLogo} alt="EKS" />
            </button>
          </div>
          <div className="col-sm-4 text-center mt-4 pick-image" title="GKE">
            <button type="button" onClick={() => window.location.href="/build-gke-clusters"} className="btn btn-outline-secondary">
              <img src={GKELogo} alt="GKE" />
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default Main;