/* Tab "Tổng hợp" — tổng hợp đơn nghỉ (mọi trạng thái) theo phòng ban.
   Gồm phần Tổng quan + danh sách đơn nhóm theo phòng ban. Chỉ officer.
   Owner: Nhật Anh. Spec §3.8. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchSummary } from '../../api/timeoff';

const THIS_YEAR = new Date().getFullYear();

export default function SummaryPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0);
  const [open, setOpen] = useState({}); // phòng ban đang mở (id -> bool)

  useEffect(() => {
    setErr(null); setData(null);
    fetchSummary(year, dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [year, dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải tổng hợp đơn nghỉ…" />;

  const o = data.overview;
  const toggle = (id) => setOpen((p) => ({ ...p, [id]: !p[id] }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Thanh điều khiển */}
      <div className="filterbar">
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="icon-btn" onClick={() => setYear((y) => y - 1)}>
            <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
          <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
          <button className="icon-btn" onClick={() => setYear((y) => y + 1)}><Icon name="chevR" size={16} /></button>
          <button className="btn btn-ghost btn-sm" onClick={() => setYear(THIS_YEAR)}>Năm nay</button>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <select className="sel" value={dept} onChange={(e) => setDept(e.target.value)}>
            <option value="">Mọi phòng ban</option>
            {data.allDepartments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
      </div>

      {/* Phần 1: Tổng quan */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))' }}>
        <Kpi label="Tổng đơn" value={o.total} />
        <Kpi label="Chờ duyệt" value={o.pending} color="var(--amber)" />
        <Kpi label="Đã duyệt" value={o.approved} color="var(--green)" />
        <Kpi label="Từ chối" value={o.refused} color="var(--red-600)" />
        <Kpi label="Ngày phép đã duyệt" value={o.approvedDays} sub="tổng số ngày" />
      </div>

      <div className="card">
        <div className="card-head"><h3>Đơn theo loại nghỉ</h3><span className="sub">{o.byType.length} loại</span></div>
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {o.byType.length === 0 && <EmptyState>Chưa có đơn nào trong năm.</EmptyState>}
          {o.byType.map((t) => (
            <div key={t.id}>
              <div className="between" style={{ marginBottom: 5 }}>
                <span style={{ fontSize: 13, fontWeight: 600, display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ width: 9, height: 9, borderRadius: 3, background: t.color }}></span>{t.name}
                </span>
                <span className="muted mono" style={{ fontSize: 12 }}>{t.count} đơn</span>
              </div>
              <div className="bar"><span style={{ width: t.pct + '%', background: t.color }}></span></div>
            </div>
          ))}
        </div>
      </div>

      {/* Phần 2: Danh sách theo phòng ban */}
      <div>
        <h3 style={{ margin: '4px 2px 12px', fontSize: 15 }}>Đơn nghỉ theo phòng ban</h3>
        {data.departments.length === 0 && <EmptyState>Không có đơn nghỉ nào trong năm.</EmptyState>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {data.departments.map((d) => {
            const key = d.id || 'none';
            const isOpen = open[key] !== false; // mặc định mở
            return (
              <div key={key} className="card">
                <div className="card-head" style={{ cursor: 'pointer' }} onClick={() => toggle(key)}>
                  <h3 style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ display: 'inline-flex', transform: isOpen ? 'none' : 'rotate(-90deg)', transition: 'transform .15s' }}>
                      <Icon name="chevD" size={16} /></span>
                    {d.name}
                  </h3>
                  <div className="actions">
                    <Badge kind="gray">{d.total} đơn</Badge>
                    {d.pending > 0 && <Badge kind="amber" dot>{d.pending} chờ</Badge>}
                    {d.approved > 0 && <Badge kind="green" dot>{d.approved} duyệt</Badge>}
                    <span className="muted mono" style={{ fontSize: 12 }}>{d.days} ngày</span>
                  </div>
                </div>
                {isOpen && (
                  <div className="tbl-wrap">
                    <table className="tbl">
                      <thead><tr>
                        <th>Nhân viên</th><th>Loại nghỉ</th><th>Từ ngày</th><th>Đến ngày</th>
                        <th className="tbl-num">Số ngày</th><th>Trạng thái</th>
                      </tr></thead>
                      <tbody>
                        {d.requests.map((r) => (
                          <tr key={r.id}>
                            <td style={{ fontWeight: 600 }}>
                              {r.employee}{r.isEmergency && <Badge kind="red">Khẩn</Badge>}</td>
                            <td>{r.leaveType}</td>
                            <td className="mono muted">{fmtDate(r.from)}</td>
                            <td className="mono muted">{fmtDate(r.to)}</td>
                            <td className="tbl-num mono">{r.days}</td>
                            <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px', color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}
