/* Shell: Sidebar + Topbar — file CHUNG, sửa phải qua review (quy ước §2) */
import Icon from '../components/Icon';
import NotificationBell from '../components/NotificationBell';

/* Nav theo vai trò (họp #2 — tách tài khoản quản lý ↔ cá nhân).
   need 'manage' = chỉ Admin/HR/Quản lý/Giáo vụ; không gắn need = mọi nhân viên.
   need 'self'   = ẩn với MỌI tài khoản vai trò quản lý (Admin/HR/Giáo vụ/Trưởng phòng)
   — phần cá nhân của họ đi theo luồng nhân viên ở tài khoản riêng; chỉ nhân viên
   thường mới thấy "Hồ sơ của tôi". */
const NAV = [
  { sec: 'Tổng quan', items: [
    { id: 'dashboard', label: 'Dashboard', icon: 'grid', need: 'manage' },
  ]},
  { sec: 'Quản lý nhân sự', need: 'manage', items: [
    { id: 'employees', label: 'Nhân viên', icon: 'users', need: 'manage' },
    { id: 'onboarding', label: 'Nhận việc', icon: 'checkCircle', need: 'manage' },
    { id: 'attendance', label: 'Chấm công', icon: 'clock', need: 'manage' },
    { id: 'timeoff', label: 'Nghỉ phép', icon: 'calendar', need: 'manage' },
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'manage' },
    { id: 'payroll', label: 'Bảng lương', icon: 'wallet', need: 'manage' },
    { id: 'recruitment', label: 'Tuyển dụng', icon: 'briefcase', need: 'manage' },
    { id: 'accounts', label: 'Tài khoản', icon: 'idcard', need: 'hr' },
    { id: 'departments', label: 'Phòng ban', icon: 'building', need: 'hr' },
    // Cấu hình quy trình nhận việc bước động — chỉ HR Manager/Admin
    { id: 'onboarding-config', label: 'Cấu hình nhận việc', icon: 'settings', need: 'hrm' },
  ]},
  { sec: 'Tài chính', need: 'finance', items: [
    { id: 'finance', label: 'Dòng tiền', icon: 'wallet', need: 'finance' },
  ]},
  { sec: 'Hệ thống', need: 'admin', items: [
    { id: 'timeoffConfig', label: 'Cấu hình nghỉ phép', icon: 'settings', need: 'admin' },
  ]},
  { sec: 'Cá nhân', need: 'self', items: [
    { id: 'attendance', label: 'Chấm công', icon: 'clock', need: 'self' },
    // Nghỉ phép cá nhân của nhân viên/Trưởng phòng. Tài khoản vai trò thuần
    // (Admin/HR/Giáo vụ) thấy Nghỉ phép ở mục Quản lý nhân sự (need:manage);
    // component TimeOff tự bổ sung tab Chờ duyệt/Đơn đã duyệt theo data.isOfficer.
    { id: 'timeoff', label: 'Nghỉ phép', icon: 'calendar', need: 'self' },
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'self' },
    { id: 'profile', label: 'Hồ sơ của tôi', icon: 'user', need: 'self' },
  ]},
];

/* Tài khoản vai trò quản lý (không gắn với cá nhân): Admin/HR/Giáo vụ/Trưởng phòng
   → ẩn 'Hồ sơ của tôi' (họp #2: HR cấp phòng ban cũng phải tách, dùng tài khoản
   cá nhân riêng). */
const isRoleAccount = (me) => !!(me && (me.isAdmin || me.isHrManager || me.isHrUser || me.isGiaovu || me.isManager));

const allow = (need, me) => {
  if (need === 'manage') return !!(me && me.canManage);
  if (need === 'hr') return !!(me && (me.isHrUser || me.isHrManager || me.isAdmin));
  if (need === 'admin') return !!(me && me.isAdmin);
  if (need === 'hrm') return !!(me && (me.isHrManager || me.isAdmin));
  if (need === 'finance') return !!(me && me.isFinance);
  if (need === 'self') return !isRoleAccount(me);
  return true;
};

/* Danh sách section/item user được thấy theo vai trò. */
export function visibleNav(me) {
  return NAV
    .filter((g) => allow(g.need, me))
    .map((g) => ({ ...g, items: g.items.filter((it) => allow(it.need, me)) }))
    .filter((g) => g.items.length);
}

/* Tập id view hợp lệ với vai trò hiện tại (để chặn truy cập view quản lý). */
export function allowedViews(me) {
  return new Set(visibleNav(me).flatMap((g) => g.items.map((it) => it.id)));
}

/* View mặc định: quản lý → dashboard; nhân viên thường → hồ sơ của tôi. */
export const defaultView = (me) => (me && me.canManage ? 'dashboard' : 'profile');

export const PAGE_META = {
  dashboard: { t: 'Dashboard nhân sự', c: 'Tổng quan' },
  employees: { t: 'Nhân viên', c: 'Quản lý nhân sự / Hồ sơ' },
  onboarding: { t: 'Nhận việc', c: 'Quản lý nhân sự / Onboarding' },
  attendance: { t: 'Chấm công', c: 'Quản lý nhân sự / Attendance' },
  timeoff: { t: 'Nghỉ phép', c: 'Cá nhân / Nghỉ phép' },
  offboarding: { t: 'Nghỉ việc', c: 'Nhân sự / Offboarding' },
  payroll: { t: 'Bảng lương', c: 'Quản lý nhân sự / Payroll' },
  finance: { t: 'Tài chính — Dòng tiền', c: 'Tài chính / Quản lý dòng tiền' },
  recruitment: { t: 'Tuyển dụng', c: 'Quản lý nhân sự / Recruitment' },
  accounts: { t: 'Tài khoản', c: 'Quản lý nhân sự / Tài khoản' },
  departments: { t: 'Phòng ban', c: 'Quản lý nhân sự / Phòng ban' },
  'onboarding-config': { t: 'Cấu hình nhận việc', c: 'Quản lý nhân sự / Cấu hình quy trình' },
  profile: { t: 'Hồ sơ của tôi', c: 'Cá nhân / Self-service' },
  timeoffConfig: { t: 'Cấu hình nghỉ phép', c: 'Hệ thống / Time Off' },
};

export function Sidebar({ view, setView, me }) {
  const groups = visibleNav(me);
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">HB</div>
        <div>
          <div className="brand-name">Học Bá <span style={{ color: 'var(--gold-500)' }}>HRM</span></div>
          <div className="brand-sub">Hệ thống Nhân sự</div>
        </div>
      </div>
      <nav className="nav">
        {groups.map((grp) => (
          <div key={grp.sec}>
            <div className="nav-label">{grp.sec}</div>
            {grp.items.map((it) => (
              <button key={it.id}
                className={'nav-item' + (view === it.id ? ' active' : '')}
                onClick={() => setView(it.id)}>
                <Icon name={it.icon} size={19} className="ico" />
                <span>{it.label}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className="org-card">
          <div className="dot"></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="t" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {me ? me.name : 'Học Bá Education'}
            </div>
            <div className="s">{me ? me.roleLabel : '360 Giải Phóng'}</div>
          </div>
          <button className="icon-btn" title="Đăng xuất"
            onClick={() => { window.location.href = '/web/session/logout?redirect=/hocba-hrm'; }}>
            <Icon name="logout" size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}

export function Topbar({ view, onSearch, onOpenNotification }) {
  const m = PAGE_META[view] || { t: '', c: '' };
  return (
    <header className="topbar">
      <div>
        <div className="page-title">{m.t}</div>
        <div className="page-crumb">{m.c}</div>
      </div>
      <label className="search">
        <Icon name="search" size={17} />
        <input placeholder="Tìm nhân viên, mã HB, phòng ban…"
          onChange={(e) => onSearch && onSearch(e.target.value)} />
      </label>
      <NotificationBell onOpenNotification={onOpenNotification} />
      <button className="icon-btn" title="Mở Odoo backend"
        onClick={() => window.open('/odoo', '_blank')}>
        <Icon name="settings" size={20} />
      </button>
    </header>
  );
}
