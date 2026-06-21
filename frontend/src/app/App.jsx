import { useState, useEffect } from 'react';
import { Sidebar, Topbar, allowedViews, defaultView } from './Shell';
import { fetchRoles } from '../api/employees';
import Dashboard from '../features/dashboard/Dashboard';
import Employees from '../features/employees/Employees';
import Onboarding from '../features/employees/Onboarding';
import Profile from '../features/employees/Profile';
import Attendance from '../features/attendance/Attendance';
import Recruitment from '../features/recruitment/Recruitment';
import Accounts from '../features/accounts/Accounts';
import TimeOff from '../features/timeoff/TimeOff';
import Payroll from '../features/payroll/Payroll';
import { LoadingState, ErrorState } from '../components/states';

export default function App() {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [view, setView] = useState(() => localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');

  const loadRoles = () => {
    setErr(null);
    fetchRoles().then(setMe).catch((e) => setErr(e.message));
  };
  useEffect(loadRoles, []);

  useEffect(() => { localStorage.setItem('hocba_view', view); setSearch(''); }, [view]);

  // Tách tài khoản: nhân viên thường không được mở các view quản lý.
  useEffect(() => {
    if (me && !allowedViews(me).has(view)) setView(defaultView(me));
  }, [me]); // eslint-disable-line react-hooks/exhaustive-deps

  if (err) return <ErrorState message={err} onRetry={loadRoles} />;
  if (!me) return <LoadingState label="Đang tải tài khoản…" />;

  const canManage = me.canManage;
  return (
    <div className="app">
      <Sidebar view={view} setView={setView} me={me} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} me={me} />
        {view === 'dashboard' && canManage && <Dashboard setView={setView} />}
        {view === 'employees' && canManage && <Employees search={search} />}
        {view === 'onboarding' && canManage && <Onboarding search={search} />}
        {view === 'attendance' && <Attendance search={search} />}
        {view === 'timeoff' && <TimeOff search={search} />}
        {view === 'payroll' && canManage && <Payroll search={search} />}
        {view === 'recruitment' && canManage && <Recruitment search={search} />}
        {view === 'accounts' && canManage && me.isHrUser && <Accounts search={search} />}
        {view === 'profile' && <Profile />}
      </div>
    </div>
  );
}
