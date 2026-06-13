/* Dashboard — KPI nhân sự THẬT từ /api/employees (domain Employees).
   Các domain khác (chấm công/lương/nghỉ phép…) sẽ bổ sung widget ở G4
   khi API của họ sẵn sàng. File [CHUNG] — sửa qua review. */
import { useState, useEffect } from 'react';
import { fetchEmployees } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate, hbStatusKind } from '../../utils/format';

const COMING = [
  ['attendance', 'Chấm công', 'clock', 'Hoàng Anh'],
  ['timeoff', 'Nghỉ phép', 'calendar', 'Nhật Anh'],
  ['payroll', 'Bảng lương', 'wallet', 'Hùng'],
  ['recruitment', 'Tuyển dụng', 'briefcase', 'Việt'],
];

export default function Dashboard({ setView }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchEmployees().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tổng quan nhân sự…" />;

  const emps = data.employees, deps = data.departments;
  const official = deps.reduce((s, d) => s + (d.official || 0), 0);
  const probation = deps.reduce((s, d) => s + (d.probation || 0), 0);
  const online = emps.filter((e) => e.type === 'Online').length;
  const maxDep = Math.max(1, ...deps.map((d) => d.total));
  const recent = [...emps]
    .filter((e) => e.start)
    .sort((a, b) => (a.start < b.start ? 1 : -1))
    .slice(0, 5);

  const stats = [
    { ico: 'users', col: 'var(--red-600)', bg: 'var(--red-50)', val: emps.length, lbl: 'Tổng nhân sự', sub: `${deps.length} phòng ban` },
    { ico: 'checkCircle', col: 'var(--green)', bg: 'var(--green-bg)', val: official, lbl: 'Chính thức', sub: `${Math.round(official / emps.length * 100)}% tổng nhân sự` },
    { ico: 'clock', col: 'var(--amber)', bg: 'var(--amber-bg)', val: probation, lbl: 'Đang thử việc', sub: 'cần theo dõi 2 cổng' },
    { ico: 'pin', col: 'var(--blue)', bg: 'var(--blue-bg)', val: online, lbl: 'Làm online', sub: `${emps.length - online} offline` },
  ];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tổng quan nhân sự</h1>
          <p>Học Bá Education · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={() => setView('employees')}>
            <Icon name="users" size={16} />Xem nhân viên</button>
        </div>
      </div>

      {/* KPI thật */}
      <div className="stat-grid">
        {stats.map((s, i) => (
          <div className="stat" key={i}>
            <div className="stat-ico" style={{ background: s.bg, color: s.col }}><Icon name={s.ico} size={22} /></div>
            <div className="stat-val">{s.val}</div>
            <div className="stat-lbl">{s.lbl}</div>
            <div className="stat-trend muted" style={{ color: 'var(--muted)' }}>{s.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Phân bổ theo phòng ban */}
        <div className="card">
          <div className="card-head">
            <h3>Phân bổ theo phòng ban</h3>
            <span className="sub">{deps.length} phòng ban</span>
          </div>
          <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {deps.map((d) => (
              <div key={d.id} onClick={() => setView('employees')} style={{ cursor: 'pointer' }}>
                <div className="between" style={{ marginBottom: 6 }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600 }}>
                    <span style={{ width: 9, height: 9, borderRadius: 3, background: d.color || 'var(--border-strong)' }}></span>
                    {d.name}
                  </span>
                  <span className="muted mono" style={{ fontSize: 12.5 }}>
                    {d.total} · <span style={{ color: 'var(--green)' }}>{d.official} CT</span>
                    {d.probation > 0 && <span style={{ color: 'var(--amber)' }}> · {d.probation} TV</span>}
                  </span>
                </div>
                <div className="bar"><span style={{ width: (d.total / maxDep * 100) + '%', background: d.color || 'var(--red-600)' }}></span></div>
              </div>
            ))}
          </div>
        </div>

        {/* Mới vào gần đây */}
        <div className="card">
          <div className="card-head"><h3>Mới vào gần đây</h3></div>
          <div style={{ padding: '8px 12px' }}>
            {recent.map((e) => (
              <div key={e.id} onClick={() => setView('employees')}
                style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '9px 8px', cursor: 'pointer', borderRadius: 10 }}>
                <Avatar emp={e} size={36} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{e.name}</div>
                  <div className="muted" style={{ fontSize: 11.5 }}>{e.depName} · {fmtDate(e.start)}</div>
                </div>
                <Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge>
              </div>
            ))}
            {recent.length === 0 && <div className="empty">Chưa có dữ liệu.</div>}
          </div>
        </div>
      </div>

      {/* Lối vào domain khác — chờ API từng owner (G3) */}
      <div className="card">
        <div className="card-head">
          <h3>Phân hệ khác</h3>
          <span className="sub">đang chờ API — Giai đoạn 3</span>
        </div>
        <div style={{ padding: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: 12 }}>
          {COMING.map(([id, label, icon, owner]) => (
            <div key={id} className="card" style={{ padding: 16, cursor: 'pointer', boxShadow: 'none' }} onClick={() => setView(id)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--surface-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
                  <Icon name={icon} size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13.5 }}>{label}</div>
                  <div className="muted" style={{ fontSize: 11.5 }}>Chờ API · {owner}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
