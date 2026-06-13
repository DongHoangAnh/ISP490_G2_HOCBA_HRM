/* Bảng chấm công theo ngày cho HR/manager. */
import { useState, useEffect } from 'react';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchAttendanceDay } from '../../api/attendance';
import { fmtTime, attStatus, today as todayStr } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Metric({ ico, col, bg, val, lbl }) {
  return (
    <div className="stat" style={{ padding: '15px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{ width: 38, height: 38, borderRadius: 11, background: bg, color: col, display: 'grid', placeItems: 'center' }}>
          <Icon name={ico} size={19} /></div>
        <div>
          <div style={{ fontSize: 24, fontWeight: 800, lineHeight: 1 }}>{val}</div>
          <div className="stat-lbl" style={{ marginTop: 3 }}>{lbl}</div>
        </div>
      </div>
    </div>
  );
}

export default function AttendanceTable({ search }) {
  const [date, setDate] = useState(todayStr());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchAttendanceDay(date).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [date]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải bảng chấm công…" />;

  const rows = data.rows.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (r.name || '').toLowerCase().includes(q) || (r.code || '').toLowerCase().includes(q);
  });

  return (
    <div>
      <div className="filterbar">
        <input type="date" className="sel" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
        <Metric ico="checkCircle" col="var(--green)" bg="var(--green-bg)" val={data.counts.onTime} lbl="Đúng giờ" />
        <Metric ico="clock" col="var(--amber)" bg="var(--amber-bg)" val={data.counts.late} lbl="Đi muộn" />
        <Metric ico="shield" col="var(--red-600)" bg="var(--red-50)" val={data.counts.needsReview} lbl="Cần xem lại" />
        <Metric ico="x" col="var(--text-3)" bg="var(--surface-2)" val={data.counts.missing} lbl="Chưa chấm" />
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Check-in</th><th>Check-out</th>
              <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => {
                const [lbl, kind] = attStatus(r.statusKey);
                return (
                  <tr key={r.id} onClick={() => setSel(r)}>
                    <td><div className="cell-emp">
                      <Avatar emp={{ id: r.empId, name: r.name, hasImg: false }} />
                      <div><div className="nm">{r.name}</div><div className="id">{r.code}</div></div>
                    </div></td>
                    <td className="muted">{r.depName}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                    <td className="tbl-num mono">{r.workingHours || '—'}</td>
                    <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
                    <td><span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                      <Badge kind={kind} dot>{lbl}</Badge>
                      {r.needsReview && <Badge kind="amber">!</Badge>}
                    </span></td>
                    <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Không có bản ghi chấm công cho ngày này.</EmptyState>}
      </div>

      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
    </div>
  );
}
