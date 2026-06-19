/* Form tạo nhân viên nhanh — dùng BE employee có sẵn. Owner: Hùng. */
import { useState } from 'react';
import { createEmployee } from '../api/employees';
import Icon from './Icon';
import Modal from './Modal';

export default function EmployeeQuickForm({ meta, onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', code: '', depId: '', jobId: '' });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const emp = await createEmployee({
        name: form.name.trim(),
        code: form.code.trim(),
        depId: Number(form.depId),
        jobId: Number(form.jobId),
      });
      onCreated({ id: emp.id, name: emp.name });
    } catch (ex) {
      setErr(ex.message || 'Tạo nhân viên thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };

  const departments = meta?.departments || [];
  const jobs = meta?.jobs || [];

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Tạo nhân viên mới</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Thêm nhân viên nhanh vào hệ thống</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Họ tên</label>
            <input type="text" style={inp} value={form.name} onChange={(e) => set('name', e.target.value)}
              placeholder="Nguyễn Văn A" required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Mã NV</label>
            <input type="text" style={inp} value={form.code} onChange={(e) => set('code', e.target.value)}
              placeholder="NV001" required />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Phòng ban</label>
            <select className="sel" style={{ width: '100%' }} value={form.depId} onChange={(e) => set('depId', e.target.value)} required>
              <option value="">Chọn phòng ban</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Chức vụ</label>
            <select className="sel" style={{ width: '100%' }} value={form.jobId} onChange={(e) => set('jobId', e.target.value)} required>
              <option value="">Chọn chức vụ</option>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang tạo...' : 'Tạo nhân viên'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
