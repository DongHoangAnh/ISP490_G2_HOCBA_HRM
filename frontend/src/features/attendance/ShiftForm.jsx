/* Form đăng ký ca làm việc (Gói 4A). User chọn giờ vào/ra (datetime-local),
   loại ca (CTV/OT), lý do. Manager: chọn NV theo mã/tên để thêm ca hộ. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createShift, searchEmployees } from '../../api/attendance';

export default function ShiftForm({ canManage, onClose, onSaved }) {
  const [form, setForm] = useState({ start: '', end: '', shiftType: 'ot', otLevel: '100', reason: '' });
  const [emp, setEmp] = useState(null);          // {id, code, name}
  const [q, setQ] = useState('');
  const [opts, setOpts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function doSearch(text) {
    setQ(text); setEmp(null);
    if (!text.trim()) { setOpts([]); return; }
    try { const d = await searchEmployees(text); setOpts(d.rows || []); }
    catch { setOpts([]); }
  }

  async function submit() {
    if (canManage && !emp) { setErr('Vui lòng chọn nhân viên.'); return; }
    if (!form.start || !form.end) { setErr('Vui lòng chọn giờ bắt đầu và kết thúc.'); return; }
    setBusy(true); setErr(null);
    try {
      await createShift({
        empId: canManage && emp ? emp.id : undefined,
        start: form.start, end: form.end,
        shiftType: form.shiftType, otLevel: form.otLevel,
        reason: form.reason.trim(),
      });
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Đăng ký ca thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>
          {canManage ? 'Thêm ca cho nhân viên' : 'Đăng ký ca làm việc'}
        </h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {canManage && (
          <label style={{ fontSize: 12.5 }}>Nhân viên (mã hoặc tên)
            {emp ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                <span style={{ fontWeight: 600 }}>{emp.name}</span>
                <span className="muted" style={{ fontSize: 12 }}>{emp.code}</span>
                <button className="btn btn-ghost btn-sm" onClick={() => { setEmp(null); setQ(''); }}>Đổi</button>
              </div>
            ) : (
              <>
                <input className="sel" value={q} placeholder="VD: EMP-001 hoặc Nguyễn…"
                  onChange={(e) => doSearch(e.target.value)} />
                {opts.length > 0 && (
                  <div style={{ border: '1px solid var(--border)', borderRadius: 8, marginTop: 4, maxHeight: 160, overflowY: 'auto' }}>
                    {opts.map((o) => (
                      <button key={o.id} onClick={() => { setEmp(o); setOpts([]); }}
                        style={{ display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', background: 'none', border: 'none', cursor: 'pointer' }}>
                        <span style={{ fontWeight: 600 }}>{o.name}</span>
                        <span className="muted" style={{ fontSize: 12, marginLeft: 6 }}>{o.code}</span>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </label>
        )}
        <label style={{ fontSize: 12.5 }}>Loại ca
          <select className="sel" value={form.shiftType}
            onChange={(e) => setForm({ ...form, shiftType: e.target.value,
              otLevel: e.target.value === 'ctv' ? '100' : form.otLevel })}>
            <option value="ot">Tăng ca (OT)</option>
            <option value="ctv">CTV</option>
          </select>
        </label>
        {form.shiftType === 'ot' && (
          <label style={{ fontSize: 12.5 }}>Mức hệ số
            <select className="sel" value={form.otLevel}
              onChange={(e) => setForm({ ...form, otLevel: e.target.value })}>
              <option value="100">100%</option>
              <option value="150">150%</option>
              <option value="300">300%</option>
            </select>
          </label>
        )}
        <label style={{ fontSize: 12.5 }}>Bắt đầu
          <input type="datetime-local" className="sel" value={form.start}
            onChange={(e) => setForm({ ...form, start: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Kết thúc
          <input type="datetime-local" className="sel" value={form.end}
            onChange={(e) => setForm({ ...form, end: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Lý do
          <textarea className="sel" rows={2} value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}>
            {canManage ? 'Thêm ca' : 'Đăng ký ca'}
          </button>
          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={onClose}>Hủy</button>
        </div>
      </div>
    </Modal>
  );
}
