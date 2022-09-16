import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFolder, faPencil, faTrash } from '@fortawesome/free-solid-svg-icons';

export default function Table({ data }) {

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
                <button type="button" title="More" className="btn btn-outline-secondary"><FontAwesomeIcon icon={faFolder} /></button>
                <button type="button" title="Edit" className="btn btn-outline-secondary"><FontAwesomeIcon icon={faPencil} /></button>
                <button type="button" title="Delete" className="btn btn-outline-secondary"><FontAwesomeIcon icon={faTrash} /></button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}