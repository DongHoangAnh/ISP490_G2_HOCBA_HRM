/* Bảng quản lý chấm công OT theo tháng (Gói 4C, manager). Liệt kê ca OT
   approved trong phạm vi; manager đổi mốc hệ số inline. */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchOtTable, setShiftLevel } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, currentMonth, firstDayOfMonth, lastDayOfMonth } from './util';

const LEVELS = ['100', '150', '300'];

export default function OtTable() {
  const [month, setMonth] = useState(currentMonth());
  const [from, setFrom] = useState(firstDayOfMonth());
  const [to, setTo] = useState(lastDayOfMonth());
  const [useRange, setUseRange] = useState(false);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchOtTable(month, useRange ? from : null, useRange ? to : null)
      .then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month, from, to, useRange]);

  async function changeLevel(id, level) {
    setBusyId(id);
    try { await setShiftLevel(id, level); load(); }
    catch (e) { setErr(e.message); }
    finally { setBusyId(null); }
  }

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="between" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 12 }}>
        <h3 style={{ margin: 0 }}>Chấm công OT</h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {useRange ? (
            <>
              <input type="date" className="sel" value={from} onChange={(e) => setFrom(e.target.value)} />
              <span className="muted">→</span>
              <input type="date" className="sel" value={to} onChange={(e) => setTo(e.target.value)} />
            </>
          ) : (
            <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
          )}
          <button className="btn btn-ghost btn-sm" onClick={() => setUseRange(!useRange)}>
            {useRange ? 'Xem theo tháng' : 'Xem theo khoảng ngày'}
          </button>
        </div>
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải dữ liệu OT…" />}

      {data && (
        <>
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 16 }}>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1 }}>{data.totals.otHours}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Tổng giờ OT</div>
            </div>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: 'var(--green)' }}>{data.totals.otCong}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Tổng công ca</div>
            </div>
            <div className="stat" style={{ padding: '14px 16px' }}>
              <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1 }}>{data.totals.countedCount}/{data.totals.count}</div>
              <div className="stat-lbl" style={{ marginTop: 4 }}>Ca đã chấm / tổng</div>
            </div>
          </div>

          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Nhân viên</th><th>Phòng</th><th>Ngày</th><th>Giờ ca</th>
                <th className="tbl-num">Số giờ</th><th>Mức</th>
                <th className="tbl-num">Công</th><th>Đã chấm</th>
              </tr></thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.id} style={{ opacity: r.counted ? 1 : 0.55 }}>
                    <td>{r.empName}<div className="muted" style={{ fontSize: 11 }}>{r.code}</div></td>
                    <td>{r.depName}</td>
                    <td className="mono">{fmtDate(r.date)}</td>
                    <td className="mono">{fmtTime(r.start)}–{fmtTime(r.end)}</td>
                    <td className="tbl-num mono">{r.hours}</td>
                    <td>
                      {data.canManage && r.shiftType === 'ot' ? (
                        <select className="sel" value={r.otLevel} disabled={busyId === r.id}
                          onChange={(e) => changeLevel(r.id, e.target.value)}>
                          {LEVELS.map((l) => <option key={l} value={l}>{l}%</option>)}
                        </select>
                      ) : `${r.otLevel}%`}
                    </td>
                    <td className="tbl-num mono" style={{ fontWeight: 600, color: r.counted ? 'var(--green)' : undefined }}>{r.congCa}</td>
                    <td>{r.counted ? <Badge kind="green" dot>Đã chấm</Badge> : <Badge kind="gray">Chưa</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.rows.length === 0 && <EmptyState>Không có ca OT đã duyệt trong tháng này.</EmptyState>}
        </>
      )}
    </div>
  );
}
