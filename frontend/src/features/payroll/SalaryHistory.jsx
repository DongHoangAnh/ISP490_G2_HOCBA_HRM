/* Lịch sử lương — xem lương tất cả nhân viên theo tháng/năm. Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import { fetchPayslips } from '../../api/payroll';
import Icon from '../../components/Icon';
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
  const [localSearch, setLocalSearch] = useState('');
  const [periodOpen, setPeriodOpen] = useState(false);
  const periodRef = useRef(null);

  /* close period dropdown on outside click */
  useEffect(() => {
    if (!periodOpen) return;
    const h = (e) => { if (periodRef.current && !periodRef.current.contains(e.target)) setPeriodOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [periodOpen]);

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

  /* filter by local search */
  const q = localSearch.toLowerCase();
  const filtered = data ? data.filter((p) => {
    if (!q) return true;
    return (p.employee_name || '').toLowerCase().includes(q)
      || (p.number || '').toLowerCase().includes(q)
      || (p.structure_code || '').toLowerCase().includes(q);
  }) : [];

  const totalGross = filtered.reduce((s, p) => s + (p.gross_amount || 0), 0);
  const totalNet = filtered.reduce((s, p) => s + (p.net_amount || 0), 0);

  if (err) return <ErrorState message={err} onRetry={load} />;

  return (
    <>
      {/* toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>

        {/* Odoo-style search bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
          padding: '4px 10px', minWidth: 280, flex: '0 1 380px',
        }}>
          <Icon name="search" size={15} style={{ color: '#9ca3af', flexShrink: 0 }} />

          {/* Period chip */}
          <div ref={periodRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setPeriodOpen(!periodOpen)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '3px 10px', borderRadius: 5, fontSize: 12, fontWeight: 600,
                border: 'none', background: '#eff6ff', color: '#1d4ed8', cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              T{month}/{year}
              <span style={{ fontSize: 10, marginLeft: 2 }}>▾</span>
            </button>
            {periodOpen && (
              <div style={{
                position: 'absolute', top: '110%', left: 0, zIndex: 50,
                background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8,
                boxShadow: '0 4px 16px rgba(0,0,0,.12)', padding: 12, minWidth: 200,
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>Chọn kỳ lương</div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <select className="sel" value={month} onChange={(e) => { setMonth(e.target.value); setPeriodOpen(false); }} style={{ flex: 1 }}>
                    {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <select className="sel" value={year} onChange={(e) => { setYear(e.target.value); setPeriodOpen(false); }} style={{ flex: 1 }}>
                    {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Search input */}
          <input
            type="text"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Tìm tên, mã NV, cấu trúc..."
            style={{
              flex: 1, border: 'none', outline: 'none', fontSize: 13,
              background: 'transparent', minWidth: 100,
            }}
          />
          {localSearch && (
            <button onClick={() => setLocalSearch('')} style={{
              border: 'none', background: 'none', cursor: 'pointer', padding: 2, color: '#9ca3af',
              display: 'flex', alignItems: 'center',
            }}>
              <Icon name="x" size={14} />
            </button>
          )}
        </div>

        {/* metrics */}
        {data && <>
          <div style={{ width: 1, height: 24, background: '#e5e7eb', margin: '0 2px' }} />
          <span style={{ fontSize: 11.5, color: '#6b7280' }}>
            Phiếu: <b style={{ color: '#111827' }}>{filtered.length}</b>
          </span>
        </>}

        <div style={{ flex: 1 }} />
      </div>

      <div className="card">
        {!data ? (
          <div style={{ padding: 36 }}>
            <LoadingState label="Đang tải lịch sử lương..." />
          </div>
        ) : filtered.length === 0 ? (
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
                {filtered.map((p) => {
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
