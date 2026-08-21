/* Shell: Sidebar + Topbar — file CHUNG, sửa phải qua review (quy ước §2) */
import { useState } from 'react';
import Icon from '../components/Icon';
import NotificationBell from '../components/NotificationBell';
import ChangePasswordForm from '../components/ChangePasswordForm';
import brandLogo from '../assets/logo1.jpg';

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
    // Hộp thư yêu cầu/góp ý của nhân viên (HR + Trưởng phòng xử lý).
    { id: 'service', label: 'Yêu cầu dịch vụ', icon: 'mail', need: 'manage' },
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'manage' },
    { id: 'payroll', label: 'Bảng lương', icon: 'wallet', need: 'manage' },
    // Đánh giá định kỳ (giảng viên / văn phòng) — HR, trưởng phòng, giáo vụ
    { id: 'reviews', label: 'Đánh giá', icon: 'star', need: 'manage' },
    // Trang lịch sử từng người (họp 2026-08-07): thăng tiến + đánh giá +
    // nhận xét thử việc + vinh danh gộp trong một dòng thời gian.
    { id: 'career', label: 'Lộ trình sự nghiệp', icon: 'trend', need: 'manage' },
    { id: 'recruitment', label: 'Tuyển dụng', icon: 'briefcase', need: 'manage' },
    { id: 'accounts', label: 'Tài khoản', icon: 'idcard', need: 'hr' },
    { id: 'departments', label: 'Phòng ban', icon: 'building', need: 'hr' },
  ]},
  { sec: 'Tài chính', need: 'finance', items: [
    { id: 'finance', label: 'Dòng tiền', icon: 'wallet', need: 'finance' },
  ]},
  // Mọi màn cấu hình quy trình gom về đây (need section 'hrm' để HR Manager vẫn
  // thấy Cấu hình nhận việc; từng item tự chặn theo vai trò).
  { sec: 'Hệ thống', need: 'hrm', items: [
    { id: 'onboarding-config', label: 'Cấu hình nhận việc', icon: 'settings', need: 'hrm' },
    { id: 'recruitment-config', label: 'Cấu hình tuyển dụng', icon: 'settings', need: 'hrm' },
    // Bộ câu hỏi/trọng số/ngưỡng của đánh giá định kỳ — sửa là ảnh hưởng cả
    // trung tâm nên chỉ HR Manager/Admin, trưởng phòng & giáo vụ không thấy.
    { id: 'reviewsConfig', label: 'Cấu hình đánh giá', icon: 'settings', need: 'hrm' },
    { id: 'timeoffConfig', label: 'Cấu hình nghỉ phép', icon: 'settings', need: 'admin' },
    { id: 'attendanceConfig', label: 'Cấu hình chấm công', icon: 'settings', need: 'admin' },
  ]},
  { sec: 'Cá nhân', need: 'self', items: [
    { id: 'attendance', label: 'Chấm công', icon: 'clock', need: 'self' },
    // Nghỉ phép cá nhân của nhân viên/Trưởng phòng. Tài khoản vai trò thuần
    // (Admin/HR/Giáo vụ) thấy Nghỉ phép ở mục Quản lý nhân sự (need:manage);
    // component TimeOff tự bổ sung tab Chờ duyệt/Đơn đã duyệt theo data.isOfficer.
    { id: 'timeoff', label: 'Nghỉ phép', icon: 'calendar', need: 'self' },
    // Gửi yêu cầu/góp ý (kể cả ẩn danh) tới HR hoặc trưởng phòng.
    { id: 'service', label: 'Yêu cầu & Góp ý', icon: 'mail', need: 'self' },
    { id: 'offboarding', label: 'Nghỉ việc', icon: 'logout', need: 'self' },
    { id: 'payroll', label: 'Phiếu lương cá nhân', icon: 'wallet', need: 'self' },
    { id: 'profile', label: 'Hồ sơ của tôi', icon: 'user', need: 'self' },
    // Cùng view 'career', tự ghim vào bản thân — khách muốn nhân viên xem
    // được "họ được đánh giá như thế nào, thăng tiến như thế nào" (08:13).
    { id: 'career', label: 'Lộ trình của tôi', icon: 'trend', need: 'self' },
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
  reviews: { t: 'Đánh giá nhân viên', c: 'Quản lý nhân sự / Đánh giá định kỳ' },
  recruitment: { t: 'Tuyển dụng', c: 'Quản lý nhân sự / Recruitment' },
  accounts: { t: 'Tài khoản', c: 'Quản lý nhân sự / Tài khoản' },
  departments: { t: 'Phòng ban', c: 'Quản lý nhân sự / Phòng ban' },
  'onboarding-config': { t: 'Cấu hình nhận việc', c: 'Hệ thống / Cấu hình quy trình' },
  'recruitment-config': { t: 'Cấu hình tuyển dụng', c: 'Hệ thống / Cấu hình quy trình' },
  profile: { t: 'Hồ sơ của tôi', c: 'Cá nhân / Self-service' },
  // Crumb trung tính: view này ở CẢ 2 mục nav (quản lý + cá nhân).
  career: { t: 'Lộ trình sự nghiệp', c: 'Nhân sự / Thăng tiến & Đánh giá' },
  // Crumb trung tính: view này xuất hiện ở CẢ 2 mục nav (quản lý + cá nhân),
  // PAGE_META lại theo view nên "Cá nhân / Self-service" sẽ sai với HR.
  service: { t: 'Yêu cầu dịch vụ nhân sự', c: 'Nhân sự / Yêu cầu & Góp ý' },
  reviewsConfig: { t: 'Cấu hình đánh giá', c: 'Hệ thống / Đánh giá định kỳ' },
  timeoffConfig: { t: 'Cấu hình nghỉ phép', c: 'Hệ thống / Time Off' },
  attendanceConfig: { t: 'Cấu hình chấm công', c: 'Hệ thống / Attendance' },
};

/* Đăng xuất phiên Odoo rồi quay lại SPA (SPA sẽ hiện màn đăng nhập).
   Dùng chung cho nút ở sidebar và ở topbar. */
function logout() {
  window.location.href = '/web/session/logout?redirect=/hocba-hrm';
}

/* badges: { [viewId]: number } — số việc cần xử lý hiện cạnh tên mục menu
   (vd Nghỉ phép: số đơn chờ duyệt). 0 / thiếu key = không hiện. */
export function Sidebar({ view, setView, me, badges, collapsed }) {
  const groups = visibleNav(me);
  // Đổi mật khẩu đặt ở đây (không phải trong "Hồ sơ của tôi") vì tài khoản vai
  // trò quản lý — HR/Admin/Giáo vụ — không thấy màn hồ sơ cá nhân.
  const [pwOpen, setPwOpen] = useState(false);
  return (
    <>
    <aside className="sidebar">
      <div className="brand">
        {/* Logo mở website trung tâm ở tab mới (rel noopener: chặn tab đích
            đụng vào window.opener). */}
        <a className="brand-mark" href="https://hoc-ba.edu.vn/"
           target="_blank" rel="noopener noreferrer"
           title="Website Học Bá Education">
          <img src={brandLogo} alt="Học Bá" />
        </a>
        <div className="brand-text">
          <div className="brand-name">Học Bá <span style={{ color: 'var(--gold-500)' }}>HRM</span></div>
          <div className="brand-sub">Hệ thống Nhân sự</div>
        </div>
      </div>
      <nav className="nav">
        {groups.map((grp) => (
          <div key={grp.sec}>
            <div className="nav-label">{grp.sec}</div>
            {grp.items.map((it) => {
              const n = (badges && badges[it.id]) || 0;
              return (
                <button key={it.id}
                  className={'nav-item' + (view === it.id ? ' active' : '')}
                  /* Thu gọn thì chữ bị ẩn → dựa vào tooltip để biết mục nào. */
                  title={collapsed ? it.label : undefined}
                  onClick={() => setView(it.id)}>
                  <Icon name={it.icon} size={19} className="ico" />
                  <span>{it.label}</span>
                  {n > 0 && (
                    <span className="nav-badge" title={`${n} việc cần xử lý`}>
                      {n > 99 ? '99+' : n}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className="org-card">
          <div className="dot"></div>
          <div className="org-text" style={{ flex: 1, minWidth: 0 }}>
            <div className="t" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {me ? me.name : 'Học Bá Education'}
            </div>
            <div className="s">{me ? me.roleLabel : '360 Giải Phóng'}</div>
          </div>
          {/* Nút đăng xuất đã dời lên topbar (góc phải) — ở đây chỉ còn thông tin
              tài khoản, tránh 2 nút cùng chức năng. Riêng Đổi mật khẩu vẫn ở
              đây: tài khoản vai trò quản lý không có màn "Hồ sơ của tôi". */}
          <button className="icon-btn" title="Đổi mật khẩu"
            onClick={() => setPwOpen(true)}>
            <Icon name="lock" size={18} />
          </button>
        </div>
      </div>
    </aside>
    {/* Modal PHẢI nằm ngoài <aside>: sidebar là position:sticky nên tạo
        stacking context riêng — để bên trong thì z-index:100 của .overlay chỉ
        có tác dụng trong phạm vi sidebar, và topbar (z:30) cùng nội dung trang
        vẫn đè lên modal. */}
    {pwOpen && <ChangePasswordForm onClose={() => setPwOpen(false)} />}
    </>
  );
}

export function Topbar({ view, onSearch, onOpenNotification, navCollapsed, onToggleNav }) {
  const m = PAGE_META[view] || { t: '', c: '' };
  return (
    <header className="topbar">
      <button className="icon-btn nav-toggle"
        title={navCollapsed ? 'Mở thanh menu' : 'Thu gọn thanh menu'}
        aria-label={navCollapsed ? 'Mở thanh menu' : 'Thu gọn thanh menu'}
        aria-expanded={!navCollapsed}
        onClick={onToggleNav}>
        <Icon name="panel-left" size={20} />
      </button>
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
      {/* Trước đây là nút mở Odoo backend — người dùng nghiệp vụ không dùng
          giao diện Odoo, đổi thành Đăng xuất cho đúng nhu cầu. */}
      <button className="icon-btn" title="Đăng xuất"
        onClick={logout}>
        <Icon name="logout" size={20} />
      </button>
    </header>
  );
}
