/* Danh sách đợt lương — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchBatches } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate, hbVND } from '../../utils/format';
import { batchState, yearOptions } from './util';
import BatchDrawer from './BatchDrawer';
import BatchForm from './BatchForm';

const CHIPS = [
  ['all', 'Tất cả'],
  ['draft', 'Nháp'],
  ['computed', 'Đã tính'],
  ['paid', 'Đã trả'],
];

export default function BatchList({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);
  const [creating, setCreating] = useState(false);
  const [stFilter, setStFilter] = useState('all');
  const [yrFilter, setYrFilter] = useState(String(new Date().getFullYear()));

  const load = () => {
    setErr(null); setData(null);
    fetchBatches().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải danh sách bảng lương..." />;

  const filtered = data.filter((b) => {
    if (stFilter !== 'all' && b.state !== stFilter) return false;
    if (yrFilter && b.date_start && !b.date_start.startsWith(yrFilter)) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!(b.name || '').toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const counts = {};
  data.forEach((b) => { counts[b.state] = (counts[b.state] || 0) + 1; });

  return (
    <>
      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 18 }}>
        {[
          ['Tổng kỳ', data.length, 'calendar'],
          ['Nháp', counts.draft || 0, 'file-text'],
          ['Đã tính', counts.computed || 0, 'calculator'],
          ['Đã trả', counts.paid || 0, 'check-circle'],
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

      {/* Filters */}
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={yrFilter} onChange={(e) => setYrFilter(e.target.value)}>
          {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div className="chips">
          {CHIPS.map(([val, label]) => (
            <button key={val} className={'chip' + (stFilter === val ? ' active' : '')}
              onClick={() => setStFilter(val)}>
              {label}{val !== 'all' && counts[val] ? ` (${counts[val]})` : ''}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={16} />Tạo đợt lương
        </button>
      </div>

      {/* Table */}
      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Kỳ lương</th>
                <th>Từ ngày</th>
                <th>Đến ngày</th>
                <th style={{ textAlign: 'right' }}>Số phiếu</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: 32 }} className="muted">Không có dữ liệu</td></tr>
              )}
              {filtered.map((b) => {
                const [stLabel, stKind] = batchState(b.state);
                return (
                  <tr key={b.id} onClick={() => setSel(b)} style={{ cursor: 'pointer' }}>
                    <td style={{ fontWeight: 600 }}>{b.name}</td>
                    <td>{fmtDate(b.date_start)}</td>
                    <td>{fmtDate(b.date_end)}</td>
                    <td style={{ textAlign: 'right' }}>{b.payslip_count}</td>
                    <td><Badge kind={stKind}>{stLabel}</Badge></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {sel && <BatchDrawer batch={sel} onClose={() => setSel(null)} onChanged={() => { setSel(null); load(); }} />}
      {creating && <BatchForm onClose={() => setCreating(false)} onSaved={() => { setCreating(false); load(); }} />}
    </>
  );
}
