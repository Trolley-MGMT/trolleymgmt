import { Outlet } from 'react-router-dom';
import Sidebar from './sidebar';

const AppLayout = ({ appData }) => (
  <>
    <div className="row flex-grow-1">
      {/* <Topbar /> */}
      <Sidebar appData={appData} />
      <Outlet />
    </div>
  </>
);

export default AppLayout;