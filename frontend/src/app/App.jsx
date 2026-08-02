import { useState, useEffect } from 'react';
import { Sidebar, Topbar, allowedViews, defaultView } from './Shell';
import { fetchRoles } from '../api/employees';
import Dashboard from '../features/dashboard/Dashboard';
import Employees from '../features/employees/Employees';
import Onboarding from '../features/employees/Onboarding';
import Profile from '../features/employees/Profile';
import Attendance from '../features/attendance/Attendance';
import Recruitment from '../features/recruitment/Recruitment';
import Reviews from '../features/reviews/Reviews';
import Accounts from '../features/accounts/Accounts';
import Departments from '../features/departments/Departments';
import TimeOff from '../features/timeoff/TimeOff';
import Offboarding from '../features/offboarding/Offboarding';
import OnboardingConfig from '../features/onboarding/OnboardingConfig';
import RecruitmentConfig from '../features/recruitment/RecruitmentConfig';
import Payroll from '../features/payroll/Payroll';
import Finance from '../features/finance/Finance';
import TimeoffConfig from '../features/timeoff-config/TimeoffConfig';
import Service from '../features/service/Service';
import { LoadingState, ErrorState } from '../components/states';
import Login from '../features/auth/Login';

export default function App() {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [unauthenticated, setUnauthenticated] = useState(false);
  const [view, setView] = useState(() => localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');
  // Đơn cần mở khi bấm 1 thông báo ở chuông (Phase 5). nonce để re-trigger dù trùng id.
  const [focus, setFocus] = useState(null);

  /* Bấm 1 thông báo ở chuông → nhảy tới view đích; timeoff cần focus để mở
     đúng đơn/tab (kind giữ semantic cũ: sub_request → tab dạy thay).
     Chỉ điều hướng khi vai trò được thấy view đích (vd NV thường nhận nhắc hạn
     trỏ 'employees' → bỏ qua, tránh content trống + breadcrumb sai). */
  const openNotification = (n) => {
    const view = n.targetView || 'timeoff';
    if (!allowedViews(me).has(view)) return;
    setView(view);
    // timeoff + service đều cần focus để mở đúng đơn từ thông báo.
    // targetTab: service dùng để chọn tab người gửi / người xử lý.
    if (view === 'timeoff' || view === 'service') {
      setFocus({
        requestId: n.targetRef, kind: n.kind,
        targetTab: n.targetTab, nonce: Date.now(),
      });
    }
  };

  const loadRoles = () => {
    setErr(null);
    setUnauthenticated(false);
    fetchRoles()
      .then(setMe)
      .catch((e) => {
        if (e.status === 401 || e.code === 'login_required') {
          setUnauthenticated(true);
        } else {
          setErr(e.message);
        }
      });
  };
  useEffect(loadRoles, []);

  useEffect(() => { localStorage.setItem('hocba_view', view); setSearch(''); }, [view]);

  // Tách tài khoản: nhân viên thường không được mở các view quản lý.
  useEffect(() => {
    if (me && !allowedViews(me).has(view)) setView(defaultView(me));
  }, [me]); // eslint-disable-line react-hooks/exhaustive-deps

  if (unauthenticated) return <Login onSuccess={loadRoles} />;
  if (err) return <ErrorState message={err} onRetry={loadRoles} />;
  if (!me) return <LoadingState label="Đang tải tài khoản…" />;

  const canManage = me.canManage;
  return (
    <div className="app">
      <Sidebar view={view} setView={setView} me={me} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} me={me} onOpenNotification={openNotification} />
        {view === 'dashboard' && canManage && <Dashboard setView={setView} />}
        {view === 'employees' && canManage && <Employees search={search} />}
        {view === 'onboarding' && canManage && <Onboarding search={search} />}
        {view === 'attendance' && <Attendance search={search} onNavigate={setView} />}
        {view === 'timeoff' && <TimeOff search={search} focus={focus} />}
        {view === 'service' && <Service search={search} focus={focus} />}
        {view === 'offboarding' && <Offboarding search={search} />}
        {view === 'payroll' && canManage && <Payroll search={search} />}
        {view === 'finance' && me.isFinance && <Finance search={search} />}
        {view === 'reviews' && canManage && <Reviews search={search} />}
        {view === 'recruitment' && canManage && <Recruitment search={search} />}
        {view === 'accounts' && canManage && me.isHrUser && <Accounts search={search} />}
        {view === 'departments' && canManage && me.isHrUser && <Departments search={search} />}
        {view === 'timeoffConfig' && me.isAdmin && <TimeoffConfig />}
        {view === 'onboarding-config' && (me.isHrManager || me.isAdmin) && <OnboardingConfig />}
        {view === 'recruitment-config' && me.isAdmin && <RecruitmentConfig />}
        {view === 'profile' && <Profile />}
      </div>
    </div>
  );
}
