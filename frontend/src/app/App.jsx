import { useState, useEffect } from 'react';
import { Sidebar, Topbar } from './Shell';
import Dashboard from '../features/dashboard/Dashboard';
import Employees from '../features/employees/Employees';
import Attendance from '../features/attendance/Attendance';
import ComingSoon from '../components/ComingSoon';

export default function App() {
  const [view, setView] = useState(() => localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');

  useEffect(() => { localStorage.setItem('hocba_view', view); setSearch(''); }, [view]);

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} />
        {view === 'dashboard' && <Dashboard setView={setView} />}
        {view === 'employees' && <Employees search={search} />}
        {view === 'attendance' && <Attendance search={search} />}
        {view === 'timeoff' && <ComingSoon title="Nghỉ phép" owner="Nhật Anh" api="/hocba-hrm/api/timeoff/*" />}
        {view === 'payroll' && <ComingSoon title="Bảng lương" owner="Hùng" api="/hocba-hrm/api/payroll/*" />}
        {view === 'recruitment' && <ComingSoon title="Tuyển dụng" owner="Việt" api="/hocba-hrm/api/recruitment/*" />}
      </div>
    </div>
  );
}
