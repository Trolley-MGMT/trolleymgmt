import React, { Component } from "react";
import AKSLogo from './aks.png';
import EKSLogo from './eks.png';
import GKELogo from './gke.png';

class Main extends Component {

  render() {
    return(
      <div className="col-lg-10 col-8 text-center">
        <div className="row col-lg-8 mx-auto">
          <h2 className="mt-4 mb-5">Build a new cluster</h2>
          <div className="col-md-4 text-center mt-4" title="AKS">
            <button type="button" onClick={() => window.location.href="/build-aks-clusters"} className="btn btn-outline-secondary">
              <img src={AKSLogo} width="150" alt="AKS" />
            </button>
          </div>
          <div className="col-md-4 text-center mt-4" title="EKS">
            <button type="button" onClick={() => window.location.href="/build-eks-clusters"} className="btn btn-outline-secondary">
              <img src={EKSLogo} width="150" />
            </button>
          </div>
          <div className="col-md-4 text-center mt-4" title="GKE">
            <button type="button" onClick={() => window.location.href="/build-gke-clusters"} className="btn btn-outline-secondary">
              <img src={GKELogo} width="150" />
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default Main;