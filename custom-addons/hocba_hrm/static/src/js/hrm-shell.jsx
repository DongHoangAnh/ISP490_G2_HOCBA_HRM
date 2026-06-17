/* ============================================================
   HOC BA HRM — Shell: Icons, Sidebar, Topbar
   ============================================================ */
const { useState, useEffect, useRef, useMemo } = React;

/* ---------- Line icon set (stroke, 22px) ---------- */
function Icon({ name, size=20, stroke=1.8, className='' }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13A4 4 0 0 1 16 11"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    wallet: <><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2"/><path d="M21 7H7a2 2 0 0 0 0 8h14v-8Z"/><circle cx="16" cy="11" r="1.2" fill="currentColor" stroke="none"/></>,
    briefcase: <><rect x="2.5" y="7" width="19" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M2.5 12h19"/></>,
    calendar: <><rect x="3" y="4.5" width="18" height="17" rx="2"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/></>,
    award: <><circle cx="12" cy="9" r="6"/><path d="M9 14.5 8 22l4-2.5L16 22l-1-7.5"/></>,
    file: <><path d="M14 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5L14 2.5Z"/><path d="M14 2.5V9h5"/></>,
    chart: <><path d="M3 3v18h18"/><path d="M7 15l3-4 3 3 4-6"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H2a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 3.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H8a1.65 1.65 0 0 0 1-1.51V2a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V8a1.65 1.65 0 0 0 1.51 1H22a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    x: <><path d="M18 6 6 18M6 6l12 12"/></>,
    chevR: <><path d="m9 18 6-6-6-6"/></>,
    chevD: <><path d="m6 9 6 6 6-6"/></>,
    filter: <><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3Z"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/></>,
    mail: <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></>,
    phone: <><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z"/></>,
    pin: <><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></>,
    check: <><path d="M20 6 9 17l-5-5"/></>,
    checkCircle: <><circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 5-5"/></>,
    edit: <><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5Z"/></>,
    arrowUp: <><path d="M12 19V5M5 12l7-7 7 7"/></>,
    arrowDown: <><path d="M12 5v14M19 12l-7 7-7-7"/></>,
    star: <><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z"/></>,
    dots: <><circle cx="12" cy="5" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="19" r="1.4" fill="currentColor" stroke="none"/></>,
    logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/></>,
    building: <><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/></>,
    trend: <><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></>,
    coins: <><circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18M7 6h1v4M16.71 13.88l.7.71-2.82 2.82"/></>,
    target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/></>,
    book: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></>,
    home: <><path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V9.5Z"/></>,
    cake: <><path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8M4 16s.5-1 2-1 2.5 1 4 1 2.5-1 4-1 2.5 1 4 1 2-1 2-1M12 4a1 1 0 1 0 .01 0M12 7V4.5"/></>,
    sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M5 5l1.5 1.5M17.5 17.5 19 19M2 12h2M20 12h2M5 19l1.5-1.5M17.5 6.5 19 5"/></>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/></>,
    idcard: <><rect x="2.5" y="5" width="19" height="14" rx="2"/><circle cx="8" cy="11" r="2.2"/><path d="M4.8 16.2a3.2 3.2 0 0 1 6.4 0M14 9.5h4M14 13h3"/></>,
    shield: <><path d="M12 2 4 5v6c0 5 3.5 8 8 11 4.5-3 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/></>,
    graduation: <><path d="M22 9 12 5 2 9l10 4 10-4Z"/><path d="M6 10.5V16c0 1 2.5 3 6 3s6-2 6-3v-5.5"/></>,
  };
  return (
    <svg className={'ico '+className} width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {paths[name] || null}
    </svg>
  );
}

/* ---------- Sidebar ---------- */
const NAV = [
  { sec:'Tổng quan', items:[
    { id:'dashboard', label:'Dashboard', icon:'grid' },
  ]},
  { sec:'Quản lý nhân sự', items:[
    { id:'employees', label:'Nhân viên', icon:'users', badge:'53' },
    { id:'onboarding', label:'Nhận việc', icon:'checkCircle', badge:'7' },
    { id:'attendance', label:'Chấm công', icon:'clock', badge:'5' },
    { id:'timeoff', label:'Nghỉ phép', icon:'calendar', badge:'7' },
    { id:'payroll', label:'Bảng lương', icon:'wallet' },
    { id:'contracts', label:'Hợp đồng', icon:'file', badge:'4' },
    { id:'recruitment', label:'Tuyển dụng', icon:'briefcase', badge:'6' },
  ]},
  { sec:'Phát triển & Báo cáo', items:[
    { id:'appraisal', label:'Đánh giá', icon:'award' },
    { id:'reports', label:'Báo cáo', icon:'chart' },
  ]},
  { sec:'Cá nhân', items:[
    { id:'profile', label:'Hồ sơ của tôi', icon:'user' },
  ]},
];

function Sidebar({ view, setView }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">HB</div>
        <div>
          <div className="brand-name">Học Bá <span style={{color:'var(--gold-500)'}}>HRM</span></div>
          <div className="brand-sub">Hệ thống Nhân sự</div>
        </div>
      </div>
      <nav className="nav">
        {NAV.map(grp=>(
          <div key={grp.sec}>
            <div className="nav-label">{grp.sec}</div>
            {grp.items.map(it=>(
              <button key={it.id}
                className={'nav-item'+(view===it.id?' active':'')}
                onClick={()=> it.soon ? null : setView(it.id)}
                style={it.soon?{opacity:.5,cursor:'default'}:null}>
                <Icon name={it.icon} size={19} className="ico" />
                <span>{it.label}</span>
                {it.badge && !it.soon && <span className="nav-badge">{it.badge}</span>}
                {it.soon && <span style={{marginLeft:'auto',fontSize:'9.5px',fontWeight:700,letterSpacing:'.5px',color:'rgba(255,255,255,.4)',textTransform:'uppercase'}}>Sắp có</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className="org-card">
          <div className="dot"></div>
          <div style={{flex:1}}>
            <div className="t">Học Bá Education</div>
            <div className="s">Odoo 19 · 360 Giải Phóng</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

/* ---------- Topbar ---------- */
const PAGE_META = {
  dashboard: { t:'Dashboard nhân sự', c:'Tổng quan' },
  employees: { t:'Nhân viên', c:'Quản lý nhân sự / Hồ sơ' },
  onboarding:{ t:'Nhận việc', c:'Quản lý nhân sự / Onboarding' },
  attendance:{ t:'Chấm công', c:'Quản lý nhân sự / Attendance' },
  timeoff:   { t:'Nghỉ phép & Làm online', c:'Quản lý nhân sự / Time Off' },
  payroll:   { t:'Bảng lương', c:'Quản lý nhân sự / Payroll' },
  contracts: { t:'Hợp đồng lao động', c:'Quản lý nhân sự / Contracts' },
  recruitment:{ t:'Tuyển dụng', c:'Quản lý nhân sự / Recruitment' },
  appraisal: { t:'Đánh giá nhân sự', c:'Phát triển / Appraisals' },
  reports:   { t:'Báo cáo nhân sự', c:'Phát triển / Reporting' },
  profile:   { t:'Hồ sơ của tôi', c:'Cá nhân / Self-service' },
};

function Topbar({ view, onSearch, onProfile }) {
  const m = PAGE_META[view] || {t:'',c:''};
  return (
    <header className="topbar">
      <div>
        <div className="page-title">{m.t}</div>
        <div className="page-crumb">{m.c}</div>
      </div>
      <label className="search">
        <Icon name="search" size={17} />
        <input placeholder="Tìm nhân viên, mã HB, phòng ban…" onChange={e=>onSearch&&onSearch(e.target.value)} />
      </label>
      <button className="icon-btn" title="Thông báo"><Icon name="bell" size={20} /><span className="dot"></span></button>
      <button className="icon-btn" title="Cài đặt"><Icon name="settings" size={20} /></button>
      <div style={{width:1,height:30,background:'var(--border)'}}></div>
      <button className="user-chip" onClick={onProfile} title="Hồ sơ của tôi">
        <div className="avatar">NA</div>
        <div>
          <div className="nm">Hoàng Thị Ngọc Anh</div>
          <div className="rl">Hành chính nhân sự · HB.75</div>
        </div>
        <Icon name="chevD" size={16} className="faint" />
      </button>
    </header>
  );
}

/* ---------- Helper components ---------- */
function Badge({ kind, children, dot }) {
  return <span className={'badge badge-'+kind}>{dot && <span className="bdot"></span>}{children}</span>;
}
function statusBadge(status){
  const map = {
    'Chính thức':'green','Thử việc':'amber','Nghỉ việc':'gray','Online':'blue','Offline':'gray','CTV':'violet',
    'Đúng giờ':'green','Đi trễ':'amber','Làm online':'blue','Nghỉ phép':'violet','Chưa chấm':'red',
    'Đã duyệt':'green','Nháp':'gray','Chờ duyệt':'amber',
  };
  return map[status]||'gray';
}
function typeBadge(t){ return {Offline:'teal',Online:'blue',CTV:'violet'}[t]||'gray'; }

function Avatar({ emp, size=34 }) {
  return <div className={'av '+emp.avatar} style={{width:size,height:size,fontSize:size*0.36}}>{emp.initials}</div>;
}

function EmpCell({ emp }) {
  return (
    <div className="cell-emp">
      <Avatar emp={emp} />
      <div>
        <div className="nm">{emp.name}</div>
        <div className="id">{emp.code} · {emp.jobTitle}</div>
      </div>
    </div>
  );
}

function Modal({ children, onClose, lg }) {
  useEffect(()=>{
    const h = e=>{ if(e.key==='Escape') onClose(); };
    window.addEventListener('keydown',h); return ()=>window.removeEventListener('keydown',h);
  },[]);
  return (
    <div className="overlay" onClick={onClose}>
      <div className={'modal'+(lg?' modal-lg':'')} onClick={e=>e.stopPropagation()}>{children}</div>
    </div>
  );
}

Object.assign(window, { Icon, Sidebar, Topbar, Badge, Avatar, EmpCell, Modal, statusBadge, typeBadge, PAGE_META });
