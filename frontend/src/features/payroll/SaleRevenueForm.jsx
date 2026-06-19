/* Form tạo/sửa doanh thu sale — Owner: Hùng. */
import { useState } from 'react';
import { createSaleRevenue, updateSaleRevenue } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import EmployeePicker from '../../components/EmployeePicker';
import { monthOptions, yearOptions, currentMonth, currentYear } from './util';

export default function SaleRevenueForm({ rev, onClose, onSaved }) {
  const isEdit = !!rev;
  const [form, setForm] = useState({
    employee_id: rev?.employee_id || '',
    period_month: rev?.period_month || currentMonth(),
    period_year: rev?.period_year || currentYear(),
    revenue: rev?.revenue || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const payload = {
        ...form,
        employee_id: Number(form.employee_id),
        revenue: Number(form.revenue),
      };
      if (isEdit) {
        await updateSaleRevenue(rev.id, { revenue: payload.revenue, period_month: payload.period_month, period_year: payload.period_year });
      } else {
        await createSaleRevenue(payload);
      }
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Lưu thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{isEdit ? 'Sửa doanh thu' : 'Thêm doanh thu sale'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? rev.employee_name : 'Nhập doanh thu bán hàng cho nhân viên'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        {!isEdit && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Nhân viên</label>
            <EmployeePicker
              value={form.employee_id}
              onChange={(id) => set('employee_id', id)}
            />
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tháng</label>
            <select className="sel" style={{ width: '100%' }} value={form.period_month} onChange={(e) => set('period_month', e.target.value)}>
              {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Năm</label>
            <select className="sel" style={{ width: '100%' }} value={form.period_year} onChange={(e) => set('period_year', e.target.value)}>
              {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Doanh thu (VNĐ)</label>
          <input type="number" style={inp} value={form.revenue} onChange={(e) => set('revenue', e.target.value)}
            placeholder="0" min="0" required />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang lưu...' : (isEdit ? 'Cập nhật' : 'Thêm mới')}
          </button>
        </div>
      </form>
    </Modal>
  );
}
