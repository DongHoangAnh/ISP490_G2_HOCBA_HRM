/* ============================================================
   HỌC BÁ — Module Tuyển dụng / Shell Components
   ============================================================ */
const { useState, useEffect, useRef, useMemo } = React;

/* ── Icon set ── */
function Icon({ name, size = 20, stroke = 1.8, className = '' }) {
  const P = {
    grid:       <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></>,
    users:      <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13A4 4 0 0 1 16 11"/></>,
    user:       <><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/></>,
    briefcase:  <><rect x="2.5" y="7" width="19" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M2.5 12h19"/></>,
    calendar:   <><rect x="3" y="4.5" width="18" height="17" rx="2"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/></>,
    clock:      <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    filter:     <><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3Z"/></>,
    search:     <><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></>,
    bell:       <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></>,
    plus:       <><path d="M12 5v14M5 12h14"/></>,
    x:          <><path d="M18 6 6 18M6 6l12 12"/></>,
    check:      <><path d="M20 6 9 17l-5-5"/></>,
    checkCircle:<><circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 5-5"/></>,
    chevR:      <><path d="m9 18 6-6-6-6"/></>,
    chevD:      <><path d="m6 9 6 6 6-6"/></>,
    chevL:      <><path d="m15 18-6-6 6-6"/></>,
    mail:       <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></>,
    phone:      <><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z"/></>,
    download:   <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/></>,
    arrowUp:    <><path d="M12 19V5M5 12l7-7 7 7"/></>,
    arrowDown:  <><path d="M12 5v14M19 12l-7 7-7-7"/></>,
    arrowR:     <><path d="M5 12h14M12 5l7 7-7 7"/></>,
    chart:      <><path d="M3 3v18h18"/><path d="M7 15l3-4 3 3 4-6"/></>,
    chart2:     <><rect x="3" y="3" width="4" height="18"/><rect x="10" y="8" width="4" height="13"/><rect x="17" y="13" width="4" height="8"/></>,
    file:       <><path d="M14 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5L14 2.5Z"/><path d="M14 2.5V9h5"/></>,
    settings:   <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H2a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 3.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H8a1.65 1.65 0 0 0 1-1.51V2a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V8a1.65 1.65 0 0 0 1.51 1H22a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/></>,
    target:     <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/></>,
    star:       <><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z"/></>,
    mic:        <><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 19v3M9 22h6"/></>,
    inbox:      <><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/></>,
    logout:     <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/></>,
    building:   <><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/></>,
    award:      <><circle cx="12" cy="9" r="6"/><path d="M9 14.5 8 22l4-2.5L16 22l-1-7.5"/></>,
    dots:       <><circle cx="12" cy="5" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="19" r="1.4" fill="currentColor" stroke="none"/></>,
    edit:       <><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5Z"/></>,
    pin:        <><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></>,
    link:       <><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></>,
  };
  return (
    <svg className={'ico ' + className} width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth={stroke}
      strokeLinecap="round" strokeLinejoin="round">
      {P[name] || null}
    </svg>
  );
}

/* ── Badge ── */
function Badge({ kind, children, dot }) {
  return (
    <span className={'badge badge-' + kind}>
      {dot && <span className="bdot"></span>}
      {children}
    </span>
  );
}

/* ── Avatar ── */
function Avatar({ emp, size = 34 }) {
  return (
    <div className={'av ' + (emp.avatar || 'av-a')}
      style={{ width: size, height: size, fontSize: size * 0.36 }}>
      {emp.initials}
    </div>
  );
}

/* ── Stars ── */
function Stars({ n, size = 12 }) {
  return (
    <div style={{ display: 'flex', gap: 1 }}>
      {[0, 1, 2, 3, 4].map(i => (
        <svg key={i} width={size} height={size} viewBox="0 0 24 24"
          fill={i < n ? 'var(--gold-500)' : 'none'}
          stroke={i < n ? 'var(--gold-500)' : '#D8D2C9'}
          strokeWidth="1.6" strokeLinejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z"/>
        </svg>
      ))}
    </div>
  );
}

/* ── Modal ── */
function Modal({ children, onClose, lg }) {
  useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);
  return (
    <div className="overlay" onClick={onClose}>
      <div className={'modal' + (lg ? ' modal-lg' : '')} onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

/* ── Donut chart (pure SVG) ── */
function Donut({ data, total, label = 'mục' }) {
  const sum = data.reduce((s, d) => s + d.val, 0);
  let acc = 0;
  const R = 54, C = 2 * Math.PI * R;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
      <svg width="140" height="140" viewBox="0 0 140 140" style={{ flexShrink: 0 }}>
        <circle cx="70" cy="70" r={R} fill="none" stroke="#EEEAE4" strokeWidth="16"/>
        {data.map((d, i) => {
          const frac = d.val / sum;
          const dash = frac * C;
          const el = (
            <circle key={i} cx="70" cy="70" r={R} fill="none"
              stroke={d.color} strokeWidth="16"
              strokeDasharray={`${dash} ${C - dash}`}
              strokeDashoffset={-acc * C}
              transform="rotate(-90 70 70)" strokeLinecap="butt"/>
          );
          acc += frac;
          return el;
        })}
        <text x="70" y="66" textAnchor="middle" fontSize="28" fontWeight="800" fill="var(--ink)">{total}</text>
        <text x="70" y="84" textAnchor="middle" fontSize="10.5" fill="var(--muted)" fontWeight="600">{label}</text>
      </svg>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 11 }}>
        {data.map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <span style={{ width: 10, height: 10, borderRadius: 3, background: d.color, flexShrink: 0 }}></span>
            <span style={{ fontSize: 12.5, fontWeight: 500, flex: 1 }}>{d.label}</span>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{d.val}</span>
            <span style={{ fontSize: 11, color: 'var(--faint)', width: 34, textAlign: 'right' }}>
              {Math.round(d.val / sum * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Sidebar navigation ── */
const REC_NAV = [
  { sec: 'Tổng quan', items: [
    { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
  ]},
  { sec: 'Quy trình tuyển dụng', items: [
    { id: 'kanban',     label: 'Pipeline Kanban',     icon: 'briefcase' },
    { id: 'jobs',       label: 'Vị trí tuyển dụng',  icon: 'building' },
    { id: 'applicants', label: 'Danh sách ứng viên', icon: 'users' },
    { id: 'interviews', label: 'Lịch phỏng vấn',     icon: 'calendar' },
  ]},
  { sec: 'Phân tích & Báo cáo', items: [
    { id: 'analytics', label: 'Phân tích nguồn',  icon: 'chart', soon: true },
    { id: 'reports',   label: 'Báo cáo tuyển dụng', icon: 'file', soon: true },
  ]},
];

function RecSidebar({ view, setView }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">HB</div>
        <div>
          <div className="brand-name">Học Bá <span style={{ color: 'var(--gold-500)' }}>Tuyển dụng</span></div>
          <div className="brand-sub">Hệ thống Tuyển dụng</div>
        </div>
      </div>
      <nav className="nav">
        {REC_NAV.map(grp => (
          <div key={grp.sec}>
            <div className="nav-label">{grp.sec}</div>
            {grp.items.map(it => {
              const badge = it.id === 'kanban' ? String(APPLICANTS.length)
                : it.id === 'jobs' ? String(REC_JOBS.length)
                : it.id === 'interviews' ? String(REC_STATS.interviewsThisWeek)
                : null;
              return (
                <button key={it.id}
                  className={'nav-item' + (view === it.id ? ' active' : '')}
                  onClick={() => !it.soon && setView(it.id)}
                  style={it.soon ? { opacity: .5, cursor: 'default' } : null}>
                  <Icon name={it.icon} size={19} className="ico"/>
                  <span>{it.label}</span>
                  {badge && !it.soon && <span className="nav-badge">{badge}</span>}
                  {it.soon && (
                    <span style={{ marginLeft:'auto', fontSize:'9.5px', fontWeight:700,
                      letterSpacing:'.5px', color:'rgba(255,255,255,.4)', textTransform:'uppercase' }}>
                      Sắp có
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
          <div style={{ flex: 1 }}>
            <div className="t">Học Bá Education</div>
            <div className="s">Odoo 19 · Tuyển dụng v1.0</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

/* ── Topbar ── */
const REC_PAGE_META = {
  dashboard:  { t: 'Dashboard Tuyển dụng', c: 'Tổng quan' },
  kanban:     { t: 'Pipeline Kanban', c: 'Quy trình tuyển dụng' },
  jobs:       { t: 'Vị trí tuyển dụng', c: 'Quy trình tuyển dụng' },
  applicants: { t: 'Danh sách ứng viên', c: 'Quy trình tuyển dụng' },
  interviews: { t: 'Lịch phỏng vấn', c: 'Quy trình tuyển dụng' },
};

function RecTopbar({ view, onSearch }) {
  const m = REC_PAGE_META[view] || { t: '', c: '' };
  return (
    <header className="topbar">
      <div>
        <div className="page-title">{m.t}</div>
        <div className="page-crumb">{m.c}</div>
      </div>
      <label className="search">
        <Icon name="search" size={17}/>
        <input placeholder="Tìm ứng viên, vị trí, mã UV…" onChange={e => onSearch && onSearch(e.target.value)}/>
      </label>
      <button className="icon-btn" title="Thông báo">
        <Icon name="bell" size={20}/>
        <span className="dot"></span>
      </button>
      <button className="icon-btn" title="Cài đặt">
        <Icon name="settings" size={20}/>
      </button>
      <div style={{ width: 1, height: 30, background: 'var(--border)' }}></div>
      <div className="user-chip">
        <div className="avatar" style={{ fontSize: 13 }}>NA</div>
        <div>
          <div className="nm">Hoàng Thị Ngọc Anh</div>
          <div className="rl">HCNS · HB.75</div>
        </div>
      </div>
    </header>
  );
}

Object.assign(window, {
  Icon, Badge, Avatar, Stars, Modal, Donut,
  RecSidebar, RecTopbar, REC_PAGE_META, REC_NAV,
});
