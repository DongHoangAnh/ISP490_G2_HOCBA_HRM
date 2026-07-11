/* Bảng tổng hợp chấm công tháng cho manager: 1 dòng/NV với tổng công thường,
   OT, CTV, thiếu, tổng tháng. Click hàng → EmpAttendanceHistoryDrawer. */
import { useState, useEffect } from 'react';
import Avatar from '../../components/Avatar';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchManagerSummary } from '../../api/attendance';
import { currentMonth } from './util';
import EmpAttendanceHistoryDrawer from './EmpAttendanceHistoryDrawer';

function CreditCell({ val, col }) {
  if (!val) return <span className="faint">—</span>;
  return <span style={{ fontWeight: 600, color: col }}>{val}</span>;
}

export default function ManagerAttendanceBoard({ search }) {
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [selEmp, setSelEmp] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchManagerSummary(month).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month]);

  const rows = data
    ? data.rows.filter((r) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (r.empName || '').toLowerCase().includes(q)
          || (r.code || '').toLowerCase().includes(q)
          || (r.depName || '').toLowerCase().includes(q);
      })
    : [];

  return (
    <div>
      <div className="filterbar">
        <input type="month" className="sel" value={month}
          onChange={(e) => setMonth(e.target.value)} />
      </div>

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải bảng chấm công…" />}

      {data && (
        <div className="card">
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Nhân viên</th>
                <th>Phòng ban</th>
                <th className="tbl-num">Tổng công thường</th>
                <th className="tbl-num">Tổng công OT</th>
                <th className="tbl-num">Tổng công CTV</th>
                <th className="tbl-num" style={{ color: 'var(--amber)' }}>Tổng công thiếu</th>
                <th className="tbl-num" style={{ color: 'var(--green)' }}>Tổng công tháng</th>
              </tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.empId} style={{ cursor: 'pointer' }}
                    onClick={() => setSelEmp({ emp: r, month })}>
                    <td>
                      <div className="cell-emp">
                        <Avatar emp={{ id: r.empId, name: r.empName, hasImg: false }} />
                        <div>
                          <div className="nm">{r.empName}</div>
                          <div className="id">{r.code}</div>
                        </div>
                      </div>
                    </td>
                    <td className="muted">{r.depName}</td>
                    <td className="tbl-num mono">
                      <CreditCell val={r.totalRegular} />
                    </td>
                    <td className="tbl-num mono">
                      <CreditCell val={r.totalOt} col="var(--amber)" />
                    </td>
                    <td className="tbl-num mono">
                      <CreditCell val={r.totalCtv} col="#1D4ED8" />
                    </td>
                    <td className="tbl-num mono">
                      <CreditCell val={r.totalMissing} col={r.totalMissing > 0 ? 'var(--red-600)' : undefined} />
                    </td>
                    <td className="tbl-num mono">
                      <CreditCell val={r.totalMonth} col="var(--green)" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length === 0 && <EmptyState>Không có nhân viên trong tháng này.</EmptyState>}
        </div>
      )}

      {selEmp && (
        <EmpAttendanceHistoryDrawer
          emp={selEmp.emp}
          month={selEmp.month}
          onClose={() => setSelEmp(null)}
          onChanged={() => { setSelEmp(null); load(); }}
        />
      )}
    </div>
  );
}
