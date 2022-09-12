import React, { Component } from "react";
import Table from "./table";

class ShowClusters extends Component {

  constructor(props) {
    super(props);
    const { trolleyRemoteUrl, trolleyLocalUrl, debug, userName } = this.props.appData;
    this.state = {
      trolleyUrl: debug ? trolleyLocalUrl : trolleyRemoteUrl,
      port: 8081,
      clusterType: 'aks',
      data: [],
      userName: userName
    }
  }

  async componentDidMount() {
    const { trolleyUrl, port, clusterType, userName } = this.state;
    let url = `http://${trolleyUrl}:${port}/get_clusters_data?cluster_type=${clusterType}&user_name=${userName}`;
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
      throw new Error(error);
    }
  }

  renderTable() {
    if (this.state.data.length === 0){
      return <p>No clusters to show, Make a new one.</p>
    }
    return (
      <div className="table-responsive">
        <Table
          data={this.state.data} />
      </div>
    );
  }
  
  render() {
    return(
      <div className="col-lg-10 col-8 text-center">
        <br />
        <h2>Manage AKS clusters</h2>
        <br />
        {this.renderTable()}
      </div>
    );
  }
}

export default ShowClusters;