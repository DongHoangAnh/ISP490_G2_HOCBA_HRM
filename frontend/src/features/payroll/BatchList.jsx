/* Danh sach nhan vien kem bang luong theo thang — Owner: Hung. */
import { useState, useEffect } from 'react';
import { fetchEmployeePayroll } from '../../api/payroll';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { monthOptions, yearOptions, currentMonth, currentYear } from './util';
import PayslipDrawer from './PayslipDrawer';

/* Sticky helpers — giu 5 cot trai co dinh khi cuon ngang */
const COL_W = [50, 90, 180, 120, 130]; // STT, Ma, Ten, ChucVu, PhongBan
const cumLeft = COL_W.map((_, i) => COL_W.slice(0, i).reduce((a, b) => a + b, 0));
const stickyTh = (i) => ({
  position: 'sticky', left: cumLeft[i], zIndex: 3,
  background: 'var(--surface-2, #f8f9fa)', minWidth: COL_W[i],
});
const stickyTd = (i) => ({
  position: 'sticky', left: cumLeft[i], zIndex: 1,
  background: '#fff', minWidth: COL_W[i],
});
const stickyFt = (i) => ({
  position: 'sticky', left: cumLeft[i], zIndex: 1,
  background: 'var(--gray-50, #f9fafb)', minWidth: COL_W[i],
});

export default function BatchList({ search }) {
  const [month, setMonth] = useState(currentMonth());
  const [year, setYear] = useState(currentYear());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchEmployeePayroll({ month, year })
      .then(setData)
      .catch((e) => setErr(e.message));
  };
  useEffect(load, [month, year]);

  if (err) return <ErrorState message={err} onRetry={load} />;

  /* Filter theo search */
  const employees = data ? data.employees.filter((e) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (e.name || '').toLowerCase().includes(q)
      || (e.code || '').toLowerCase().includes(q);
  }) : [];

  const columns = data ? data.columns : [];

  /* Metrics */
  const total = employees.length;
  const withSlip = employees.filter((e) => e.payslip_id).length;
  const netCode = columns.find((c) => c.code === 'thuc_lanh')?.code;
  const totalNet = netCode
    ? employees.reduce((s, e) => s + (e.amounts[netCode] || 0), 0) : 0;
  const avgNet = withSlip > 0 ? Math.round(totalNet / withSlip) : 0;

  return (
    <>
      {/* Filter bar */}
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={month} onChange={(e) => setMonth(e.target.value)}>
          {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="sel" value={year} onChange={(e) => setYear(e.target.value)}>
          {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        {data && (
          <div style={{ fontSize: 13.5, color: 'var(--muted)' }}>
            {total} nhan vien
          </div>
        )}
      </div>

      {/* Metrics */}
      {data && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 18 }}>
          {[
            ['Tong NV', total, 'users'],
            ['Co phieu luong', withSlip, 'file-text'],
            ['Tong thuc linh', hbVND(totalNet), 'dollar-sign'],
            ['Binh quan', hbVND(avgNet), 'trending-up'],
          ].map(([label, val, icon]) => (
            <div key={label} className="card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
              <Icon name={icon} size={22} />
              <div>
                <div style={{ fontSize: 22, fontWeight: 800 }}>{val}</div>
                <div className="muted" style={{ fontSize: 12.5 }}>{label}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="card">
        {!data ? (
          <div style={{ padding: 36 }}>
            <LoadingState label="Dang tai bang luong..." />
          </div>
        ) : employees.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Khong co du lieu thang {month}/{year}.</EmptyState>
          </div>
        ) : (
          <div className="tbl-wrap" style={{ overflowX: 'auto' }}>
            <table className="tbl" style={{ minWidth: cumLeft[4] + COL_W[4] + columns.length * 120 }}>
              <thead>
                <tr>
                  <th style={stickyTh(0)}>STT</th>
                  <th style={stickyTh(1)}>Ma NV</th>
                  <th style={stickyTh(2)}>Ho Ten</th>
                  <th style={stickyTh(3)}>Chuc Vu</th>
                  <th style={{ ...stickyTh(4), borderRight: '2px solid var(--border, #dee2e6)' }}>Phong ban</th>
                  {columns.map((c) => (
                    <th key={c.code} style={{ textAlign: 'right', whiteSpace: 'nowrap', minWidth: 110 }}>
                      {c.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {employees.map((emp, idx) => (
                  <tr
                    key={emp.id}
                    style={{ cursor: emp.payslip_id ? 'pointer' : 'default' }}
                    onClick={() => emp.payslip_id && setSel(emp)}
                  >
                    <td style={stickyTd(0)}>{idx + 1}</td>
                    <td style={stickyTd(1)}>
                      <code style={{ fontSize: 12.5 }}>{emp.code || '—'}</code>
                    </td>
                    <td style={{ ...stickyTd(2), fontWeight: 600 }}>{emp.name}</td>
                    <td style={stickyTd(3)}>{emp.job_title || '—'}</td>
                    <td style={{ ...stickyTd(4), borderRight: '2px solid var(--border, #dee2e6)' }}>
                      {emp.department || '—'}
                    </td>
                    {columns.map((c) => (
                      <td key={c.code} style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        {emp.amounts[c.code] != null ? hbVND(emp.amounts[c.code]) : ''}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ background: 'var(--gray-50)', fontWeight: 700 }}>
                  <td style={stickyFt(0)} />
                  <td style={stickyFt(1)} />
                  <td style={{ ...stickyFt(2), textAlign: 'right', fontSize: 14 }} colSpan={1}>
                    Tong cong
                  </td>
                  <td style={stickyFt(3)} />
                  <td style={{ ...stickyFt(4), borderRight: '2px solid var(--border, #dee2e6)' }} />
                  {columns.map((c) => {
                    const sum = employees.reduce((s, e) => s + (e.amounts[c.code] || 0), 0);
                    return (
                      <td key={c.code} style={{ textAlign: 'right', fontSize: 14, whiteSpace: 'nowrap' }}>
                        {sum ? hbVND(sum) : ''}
                      </td>
                    );
                  })}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {sel && (
        <PayslipDrawer
          slip={{ id: sel.payslip_id }}
          onClose={() => setSel(null)}
          onChanged={load}
        />
      )}
    </>
  );
}
