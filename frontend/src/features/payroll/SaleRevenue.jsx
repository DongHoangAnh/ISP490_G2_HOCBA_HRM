/* Doanh thu sale — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchSaleRevenues, deleteSaleRevenue } from '../../api/payroll';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { monthOptions, yearOptions, currentMonth, currentYear } from './util';
import SaleRevenueForm from './SaleRevenueForm';

export default function SaleRevenue() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [form, setForm] = useState(null);        // null | 'new' | {rev object}
  const [mFilter, setMFilter] = useState('');
  const [yFilter, setYFilter] = useState(currentYear());
  const [deleting, setDeleting] = useState(null); // id being deleted

  const load = () => {
    setErr(null); setData(null);
    const params = {};
    if (mFilter) params.period_month = mFilter;
    if (yFilter) params.period_year = yFilter;
    fetchSaleRevenues(params).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [mFilter, yFilter]);

  const handleDelete = async (id) => {
    if (!window.confirm('Xoá bản ghi doanh thu này?')) return;
    setDeleting(id);
    try {
      await deleteSaleRevenue(id);
      load();
    } catch (e) {
      alert('Xoá thất bại: ' + e.message);
    } finally {
      setDeleting(null);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải doanh thu sale..." />;

  return (
    <>
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={mFilter} onChange={(e) => setMFilter(e.target.value)}>
          <option value="">Tất cả tháng</option>
          {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="sel" value={yFilter} onChange={(e) => setYFilter(e.target.value)}>
          {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setForm('new')}>
          <Icon name="plus" size={16} />Thêm doanh thu
        </button>
      </div>

      <div className="card">
        {data.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Chưa có dữ liệu doanh thu.</EmptyState>
          </div>
        ) : (
          <div className="tbl-wrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Nhân viên</th>
                  <th style={{ textAlign: 'center' }}>Tháng</th>
                  <th style={{ textAlign: 'center' }}>Năm</th>
                  <th style={{ textAlign: 'right' }}>Doanh thu</th>
                  <th>Bậc</th>
                  <th style={{ textAlign: 'right' }}>Hoa hồng</th>
                  <th style={{ textAlign: 'right' }}>Lương sale</th>
                  <th style={{ width: 80 }}></th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 600 }}>{r.employee_name}</td>
                    <td style={{ textAlign: 'center' }}>{r.period_month}</td>
                    <td style={{ textAlign: 'center' }}>{r.period_year}</td>
                    <td style={{ textAlign: 'right' }} className="mono">{hbVND(r.revenue)}</td>
                    <td>{r.level || '—'}</td>
                    <td style={{ textAlign: 'right' }} className="mono">{hbVND(r.commission)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }} className="mono">{hbVND(r.sale_wage)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => setForm(r)} title="Sửa">
                        <Icon name="edit" size={14} />
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(r.id)}
                        disabled={deleting === r.id} title="Xoá" style={{ color: 'var(--red-600)' }}>
                        <Icon name="trash" size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {form && (
        <SaleRevenueForm
          rev={form === 'new' ? null : form}
          onClose={() => setForm(null)}
          onSaved={() => { setForm(null); load(); }}
        />
      )}
    </>
  );
}
