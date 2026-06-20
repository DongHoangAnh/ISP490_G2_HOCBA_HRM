/* Tạo đợt lương mới — Owner: Hùng. */
import { useState } from 'react';
import { createBatch } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { defaultBatchName, firstOfMonth, lastOfMonth, currentMonth, currentYear } from './util';

export default function BatchForm({ onClose, onSaved }) {
  const m = currentMonth(), y = currentYear();
  const [form, setForm] = useState({
    name: defaultBatchName(m, y),
    date_start: firstOfMonth(m, y),
    date_end: lastOfMonth(m, y),
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => {
    const next = { ...form, [k]: v };
    if (k === 'date_start' && v) {
      const [yy, mm] = v.split('-');
      next.name = defaultBatchName(mm, yy);
      next.date_end = lastOfMonth(mm, yy);
    }
    setForm(next);
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await createBatch(form);
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Tạo đợt lương thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Tạo đợt lương</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Tạo kỳ lương mới cho nhân viên</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tên kỳ lương</label>
          <input style={inp} value={form.name} onChange={(e) => set('name', e.target.value)} required />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Từ ngày</label>
            <input type="date" style={inp} value={form.date_start} onChange={(e) => set('date_start', e.target.value)} required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Đến ngày</label>
            <input type="date" style={inp} value={form.date_end} onChange={(e) => set('date_end', e.target.value)} required />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang tạo...' : 'Tạo đợt lương'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
