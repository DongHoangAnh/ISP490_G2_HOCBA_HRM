import { useState, useEffect } from 'react';
import { Sidebar, Topbar, allowedViews, defaultView } from './Shell';
import { fetchRoles } from '../api/employees';
import { fetchPendingCount } from '../api/timeoff';
import { fetchOnbPendingCount } from '../api/onboarding';
import { fetchOffbPendingCount } from '../api/offboarding';
import { fetchAttendancePendingCount } from '../api/attendance';
import { fetchIncompleteCount } from '../api/employees';
import { fetchRequestPendingCount } from '../api/recruitment';
import Dashboard from '../features/dashboard/Dashboard';
import Employees from '../features/employees/Employees';
import Onboarding from '../features/employees/Onboarding';
import Profile from '../features/employees/Profile';
import Career from '../features/employees/Career';
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
import AttendanceConfig from '../features/attendance-config/AttendanceConfig';
import ReviewsConfig from '../features/reviews-config/ReviewsConfig';
import { LoadingState, ErrorState, AccessDeniedState } from '../components/states';
import Login from '../features/auth/Login';

export default function App() {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [unauthenticated, setUnauthenticated] = useState(false);
  const [view, setView] = useState(() => localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');
  // Thu gọn thanh menu trái (chỉ còn icon). Nhớ lựa chọn giữa các lần vào app.
  const [navCollapsed, setNavCollapsed] = useState(
    () => localStorage.getItem('hocba_nav_collapsed') === '1'
  );
  const toggleNav = () => setNavCollapsed((v) => {
    localStorage.setItem('hocba_nav_collapsed', v ? '0' : '1');
    return !v;
  });
  // Đơn cần mở khi bấm 1 thông báo ở chuông (Phase 5). nonce để re-trigger dù trùng id.
  const [focus, setFocus] = useState(null);
  // NV cần mở trên trang Lộ trình sự nghiệp (0 = chính mình). Đặt khi bấm
  // "Mở trang đầy đủ" từ drawer hồ sơ.
  const [careerEmp, setCareerEmp] = useState(0);

  /* Đổi view do người dùng tự bấm (menu trái, Dashboard, nút điều hướng trong
     màn) → xoá focus deep-link còn treo. Không có bước này thì focus của thông
     báo (vd đơn nghỉ id 123) vẫn nằm nguyên và màn kế tiếp — Yêu cầu dịch vụ,
     Tuyển dụng… — lại lấy đúng id đó đi mở chi tiết, ra "404 not_found". */
  const goView = (v) => { setFocus(null); setView(v); };

  /* Focus chỉ dành cho ĐÚNG view mà thông báo trỏ tới; các màn khác nhận null
     dù state focus vẫn còn (chặn lớp 2, phòng khi view đổi mà không qua goView). */
  const focusFor = (v) => (focus && focus.view === v ? focus : null);

  const openCareer = (empId) => { setCareerEmp(empId || 0); goView('career'); };

  /* Badge "việc cần xử lý" cạnh tên mục menu: Nghỉ phép (đơn chờ duyệt),
     Nhận việc (bước đang chờ), Nghỉ việc (đơn chờ duyệt/hoàn tất).
     Key trùng view id nên Sidebar đọc thẳng badges[it.id]. */
  const [navBadges, setNavBadges] = useState({});
  const setBadge = (key) => (n) => setNavBadges((b) => ({ ...b, [key]: n }));
  const setTimeoffBadge = setBadge('timeoff');
  const setAttendanceBadge = setBadge('attendance');

  // Sau mỗi thao tác, hỏi lại server thay vì tự trừ ở client: phạm vi đếm là
  // quyền duyệt phía server, đoán ở FE sẽ lệch với số nút bấm được.
  const reloadOnbBadge = () => fetchOnbPendingCount()
    .then((d) => setBadge('onboarding')(d.count || 0)).catch(() => {});
  const reloadOffbBadge = () => fetchOffbPendingCount()
    .then((d) => setBadge('offboarding')(d.count || 0)).catch(() => {});
  const reloadAttendanceBadge = () => fetchAttendancePendingCount()
    .then((d) => setAttendanceBadge(d.count || 0)).catch(() => {});
  // Hồ sơ thiếu giấy tờ pháp lý (CCCD/MST/BHXH) — chủ yếu là nhân sự cũ nhập
  // từ Excel. Route trả 0 cho người không có quyền nên badge tự ẩn.
  const reloadIncompleteBadge = () => fetchIncompleteCount()
    .then((d) => setBadge('employees')(d.count || 0)).catch(() => {});
  // Phiếu yêu cầu tuyển dụng chờ duyệt. Chuông vẫn giữ nguyên — badge là lớp
  // thêm, để việc tồn đọng không trôi mất theo chuông.
  const reloadRecruitBadge = () => fetchRequestPendingCount()
    .then((d) => setBadge('recruitment')(d.count || 0)).catch(() => {});

  /* Bấm 1 thông báo ở chuông → nhảy tới view đích; timeoff cần focus để mở
     đúng đơn/tab (kind giữ semantic cũ: sub_request → tab dạy thay).
     Chỉ điều hướng khi vai trò được thấy view đích (vd NV thường nhận nhắc hạn
     trỏ 'employees' → bỏ qua, tránh content trống + breadcrumb sai). */
  const openNotification = (n) => {
    const view = n.targetView || 'timeoff';
    if (!allowedViews(me).has(view)) return;
    setView(view);
    // timeoff + service + recruitment + employees + attendance đều cần focus để mở đúng
    // đơn/ứng viên/hồ sơ/tab. targetTab: service chọn tab người gửi / người xử lý;
    // recruitment chọn tab 'cv' rồi mở drawer ứng viên quá hạn; employees mở
    // drawer hồ sơ (vd nhắc "cần hoàn thiện hồ sơ" sau khi Onboard);
    // attendance chọn tab 'requests' hoặc 'ot'.
    if (view === 'timeoff' || view === 'service' || view === 'recruitment'
        || view === 'employees' || view === 'attendance') {
      setFocus({
        view, requestId: n.targetRef, kind: n.kind,
        targetTab: n.targetTab, nonce: Date.now(),
      });
    } else {
      // Thông báo trỏ tới view không dùng focus → dọn focus cũ, tránh treo.
      setFocus(null);
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

  // Số việc chờ cho badge sidebar: nạp 1 lần sau khi biết vai trò. Người
  // không có quyền duyệt vẫn nhận count 0 → badge tự ẩn. Từng màn sẽ đẩy
  // số mới về (onPendingCount) mỗi khi duyệt/từ chối, khỏi phải F5.
  useEffect(() => {
    if (!me) return;
    fetchPendingCount()
      .then((d) => setTimeoffBadge(d.count || 0))
      .catch(() => {});
    reloadOnbBadge();
    reloadOffbBadge();
    reloadAttendanceBadge();
    reloadIncompleteBadge();
    reloadRecruitBadge();
  }, [me]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payslip_id')) {
      setView('payroll');
    }
  }, []);

  // Tách tài khoản: nhân viên thường không được mở các view quản lý.
  useEffect(() => {
    if (me) {
      const params = new URLSearchParams(window.location.search);
      if (params.get('payslip_id') && allowedViews(me).has('payroll')) {
        setView('payroll');
      } else if (!allowedViews(me).has(view) && view !== 'payroll') {
        setView(defaultView(me));
      }
    }
  }, [me]); // eslint-disable-line react-hooks/exhaustive-deps

  if (unauthenticated) return <Login onSuccess={loadRoles} />;
  if (err) return <ErrorState message={err} onRetry={loadRoles} />;
  if (!me) return <LoadingState label="Đang tải tài khoản…" />;

  const canManage = me.canManage;
  const navViews = allowedViews(me);
  return (
    <div className={'app' + (navCollapsed ? ' nav-collapsed' : '')}>
      <Sidebar view={view} setView={goView} me={me} badges={navBadges} collapsed={navCollapsed} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} me={me} onOpenNotification={openNotification}
          navCollapsed={navCollapsed} onToggleNav={toggleNav} />
        {view === 'dashboard' && canManage && <Dashboard setView={goView} />}
        {view === 'employees' && canManage && <Employees search={search} focus={focusFor('employees')} onOpenCareer={openCareer} />}
        {view === 'career' && (
          <Career canManage={canManage} focusEmpId={careerEmp}
            onBack={canManage ? () => goView('employees') : null} />
        )}
        {view === 'onboarding' && canManage && (
          <Onboarding search={search} onQueueChanged={reloadOnbBadge} />
        )}
        {view === 'attendance' && <Attendance search={search} onNavigate={goView} onPendingCount={setAttendanceBadge} focus={focusFor('attendance')} />}
        {view === 'timeoff' && (
          <TimeOff search={search} focus={focusFor('timeoff')} onPendingCount={setTimeoffBadge} />
        )}
        {view === 'service' && <Service search={search} focus={focusFor('service')} />}
        {view === 'offboarding' && (
          <Offboarding search={search} onQueueChanged={reloadOffbBadge} />
        )}
        {view === 'payroll' && (
          navViews.has('payroll')
            ? <Payroll search={search} me={me} />
            : <AccessDeniedState />
        )}
        {view === 'finance' && me.isFinance && <Finance search={search} />}
        {view === 'reviews' && canManage && (
          <Reviews search={search} canPromote={me.isHrManager} />
        )}
        {view === 'recruitment' && canManage && <Recruitment search={search} focus={focusFor('recruitment')}
          onPendingCount={setBadge('recruitment')} />}
        {/* Điều kiện render PHẢI trùng điều kiện bày menu (Shell: need 'hr' =
            HR | HR Mgr | Admin), nên lấy thẳng từ allowedViews thay vì chép tay:
            trước đây chỉ xét me.isHrUser, mà tài khoản Admin "thuần"
            (base.group_system, không kèm nhóm HR) lại không có cờ đó → bấm vào
            menu Phòng ban / Tài khoản chỉ thấy vùng nội dung trắng trơn. */}
        {view === 'accounts' && navViews.has('accounts') && <Accounts search={search} />}
        {view === 'departments' && navViews.has('departments') && <Departments search={search} />}
        {view === 'timeoffConfig' && me.isAdmin && <TimeoffConfig />}
        {view === 'attendanceConfig' && me.isAdmin && <AttendanceConfig search={search} />}
        {view === 'reviewsConfig' && (me.isHrManager || me.isAdmin) && <ReviewsConfig />}
        {view === 'onboarding-config' && (me.isHrManager || me.isAdmin) && <OnboardingConfig />}
        {view === 'recruitment-config' && (me.isHrManager || me.isAdmin) && <RecruitmentConfig />}
        {view === 'profile' && <Profile />}
      </div>
    </div>
  );
}
