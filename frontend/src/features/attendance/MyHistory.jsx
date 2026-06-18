/* Lịch sử chấm công của chính mình theo tháng (read-only). */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMyHistory } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus, currentMonth, fmtCredit } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Sum({ val, lbl, col }) {
  return (
    <div className="stat" style={{ padding: '14px 16px' }}>
      <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: col || 'inherit' }}>{val}</div>
      <div className="stat-lbl" style={{ marginTop: 4 }}>{lbl}</div>
    </div>
  );
}

export default function MyHistory() {
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchMyHistory(month).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month]);

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="between" style={{ marginBottom: 14 }}>
        <h3 style={{ margin: 0 }}>Lịch sử chấm công của tôi</h3>
        <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải lịch sử…" />}

      {data && (
        <>
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(6,1fr)', marginBottom: 16 }}>
            <Sum val={data.summary.daysPresent} lbl="Ngày có mặt" />
            <Sum val={data.summary.totalCredit} lbl="Tổng công" />
            <Sum val={data.summary.deficitCredit} lbl="Công thiếu" col={data.summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
            <Sum val={data.summary.netCredit} lbl="Công thực" col="var(--green)" />
            <Sum val={data.summary.otHours} lbl="Giờ OT" />
            <Sum val={data.summary.otCreditHours} lbl="Công OT quy đổi" col="var(--green)" />
          </div>

          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th>
                <th className="tbl-num">Về sớm</th><th className="tbl-num">Thiếu</th>
                <th className="tbl-num">Ngày công</th><th>Trạng thái</th><th></th>
              </tr></thead>
              <tbody>
                {data.rows.map((r) => {
                  const [lbl, kind] = attStatus(r.statusKey);
                  return (
                    <tr key={r.id} onClick={() => setSel(r)}>
                      <td className="mono">{fmtDate(r.date)}</td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                      <td className="tbl-num mono">{r.workingHours || '—'}</td>
                      <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono">{r.earlyLeaveMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>-{r.earlyLeaveMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono">{r.missingMinutes > 0 ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono" style={{ fontWeight: 600 }}>{fmtCredit(r.workCredit)}</td>
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
          {data.rows.length === 0 && <EmptyState>Chưa có bản ghi chấm công trong tháng này.</EmptyState>}
        </>
      )}

      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
    </div>
  );
}
