import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFolder, faPencil, faTrash } from '@fortawesome/free-solid-svg-icons';
import YamlEditor from './yamlEditor';

export default function Table({ data, deleteCluster, copyKubeConfig, saveKubeConfig }) {

  return(
    <table className="table table-striped table-dark text-white table-hover align-middle">
      <thead>
        <tr>
        <th className="align-middle" style={{width: '10%'}}>Cluster Name</th>
        <th className="align-middle" style={{width: '10%'}}>Cluster Region</th>
        <th className="align-middle" style={{width: '10%'}}>Kubernetes Version</th>
        <th className="align-middle" style={{width: '30%'}}>Nodes IPs</th>
        <th className="align-middle" style={{width: '15%'}}>Expiration Time</th>
        <th className="align-middle" style={{width: '20%'}}></th>
        </tr>
      </thead>
      <tbody>
        {data.map((item, i) => (
          <React.Fragment>
            <tr key={i}>
              <td>
                {item.cluster_name}
              </td>
              <td>
                <div className="d-flex align-items-center"><span className="ml-2">{item.region_name}</span></div>
              </td>
              <td>{item.cluster_version}</td>
              <td>{item.nodes_ips}</td>
              <td>{item.human_expiration_timestamp}</td>
              <td>
                <div className="btn-group">
                  <button type="button" title="More" data-bs-toggle="collapse" data-bs-target={`#${item.cluster_name}`} className="btn btn-outline-secondary"><FontAwesomeIcon icon={faFolder} /></button>
                  <button type="button" title="Edit" className="btn btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#editModal"><FontAwesomeIcon icon={faPencil} /></button>
                  <button type="button" title="Delete" onClick={() => deleteCluster(item.cluster_name)} className="btn btn-outline-secondary"><FontAwesomeIcon icon={faTrash} /></button>
                </div>
                {/* Modal */}
                <div className="modal fade" id="editModal">
                  <div className="modal-dialog" style={{ maxWidth: '100%' }}>
                    <div className="modal-content">
                      {/* Modal Header */}
                      {/* <div className="modal-header">
                        <h4 className="modal-title">Modal Heading</h4>
                        <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                      </div> */}
                      {/* Modal body */}
                      <div className="modal-body" style={{ textAlign: 'left', color: 'black' }}>
                        <YamlEditor text={item.kubeconfig} />
                      </div>
                      {/* Modal footer */}
                      <div className="modal-footer">
                        <button type="button" onClick={() => copyKubeConfig(item.kubeconfig)} className="btn btn-primary">Copy Kubeconfig</button>
                        <button type="button" className="btn btn-success">Save changes</button>
                        <button type="button" onClick={() => saveKubeConfig(item.cluster_name, item.kubeconfig)} className="btn btn-danger" data-bs-dismiss="modal">Close</button>
                      </div>
                    </div>
                  </div>
                </div>
                {/* End of Modal */}
              </td>
            </tr>
            <tr key={`${i}-more`}>
              <td colSpan={6} style={{textAlign: 'left'}}> {/*style={{padding: '0px'}}*/}
                <div id={item.cluster_name} className="collapse">
                  More info about {item.cluster_name} cluster....
                </div>
              </td>
            </tr>
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
}