/* Lịch sử lương — xem lương tất cả nhân viên theo tháng/năm. Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchPayslips } from '../../api/payroll';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { slipState, monthOptions, yearOptions, currentMonth, currentYear } from './util';
import PayslipDrawer from './PayslipDrawer';
import TblWrap from '../../components/TblWrap';

export default function SalaryHistory() {
  const [month, setMonth] = useState(currentMonth());
  const [year, setYear] = useState(currentYear());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    const params = { limit: 500 };
    if (year) params.year = year;
    if (month) params.month = month;
    fetchPayslips(params)
      .then(setData)
      .catch((e) => setErr(e.message));
  };
  useEffect(load, [month, year]);

  const totalGross = data ? data.reduce((s, p) => s + (p.gross_amount || 0), 0) : 0;
  const totalNet = data ? data.reduce((s, p) => s + (p.net_amount || 0), 0) : 0;

  if (err) return <ErrorState message={err} onRetry={load} />;

  return (
    <>
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={month} onChange={(e) => setMonth(e.target.value)}>
          <option value="">Tất cả tháng</option>
          {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="sel" value={year} onChange={(e) => { setYear(e.target.value); if (!e.target.value) setMonth(''); }}>
          <option value="">Tất cả năm</option>
          {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        {data && (
          <div style={{ fontSize: 13.5, color: 'var(--muted)' }}>
            {data.length} phiếu lương
          </div>
        )}
      </div>

      <div className="card">
        {!data ? (
          <div style={{ padding: 36 }}>
            <LoadingState label="Đang tải lịch sử lương..." />
          </div>
        ) : data.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Không có phiếu lương{month && year ? ` tháng ${month}/${year}` : year ? ` năm ${year}` : ''}.</EmptyState>
          </div>
        ) : (
          <TblWrap id="salary-history">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Mã NV</th>
                  <th>Nhân viên</th>
                  <th>Cấu trúc</th>
                  <th style={{ textAlign: 'right' }}>Gross</th>
                  <th style={{ textAlign: 'right' }}>Net</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {data.map((p) => {
                  const [sl, sk] = slipState(p.state);
                  return (
                    <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => setSel(p)}>
                      <td><code style={{ fontSize: 12.5 }}>{p.number || '—'}</code></td>
                      <td style={{ fontWeight: 600, color: 'var(--red-600)' }}>{p.employee_name}</td>
                      <td>{p.structure_code || '—'}</td>
                      <td style={{ textAlign: 'right' }}>{hbVND(p.gross_amount)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--green-700)' }}>{hbVND(p.net_amount)}</td>
                      <td><Badge kind={sk}>{sl}</Badge></td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr style={{ background: 'var(--gray-50)', fontWeight: 700 }}>
                  <td colSpan={3} style={{ textAlign: 'right', fontSize: 14 }}>Tổng cộng</td>
                  <td style={{ textAlign: 'right', fontSize: 14 }}>{hbVND(totalGross)}</td>
                  <td style={{ textAlign: 'right', fontSize: 14, color: 'var(--green-700)' }}>{hbVND(totalNet)}</td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </TblWrap>
        )}
      </div>

      {sel && (
        <PayslipDrawer
          slip={sel}
          onClose={() => setSel(null)}
          onChanged={load}
        />
      )}
    </>
  );
}
