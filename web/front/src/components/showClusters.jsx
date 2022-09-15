import React, { Component } from "react";
import Table from "./table";

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
      userName: userName
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
            data={this.state.data} />
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
      </div>
    );
  }
}

export default ShowClusters;