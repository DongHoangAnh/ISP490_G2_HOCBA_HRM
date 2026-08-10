/* Form đăng ký ca làm việc (Gói 4A). User chọn giờ vào/ra (datetime-local),
   loại ca (CTV/OT), lý do. Manager: chọn NV theo mã/tên để thêm ca hộ. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { createShift, searchEmployees } from '../../api/attendance';

export default function ShiftForm({ canManage, me, onClose, onSaved }) {
  const isCtvUser = me && !me.canManage && !me.isOfficial && !me.isTeacher;
  const [form, setForm] = useState({
    start: '', end: '',
    shiftType: canManage ? 'ot' : (isCtvUser ? 'ctv' : 'ot'),
    otLevel: '100', reason: ''
  });
  const [isMulti, setIsMulti] = useState(false);
  const [multi, setMulti] = useState({ startTime: '08:00', endTime: '12:00', dates: [] });
  const [newDate, setNewDate] = useState('');
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

    const payloads = [];
    if (isMulti) {
      if (multi.dates.length === 0) { setErr('Vui lòng chọn ít nhất một ngày.'); return; }
      if (!multi.startTime || !multi.endTime) { setErr('Vui lòng chọn giờ vào/ra.'); return; }
      multi.dates.forEach(d => {
        payloads.push({
          empId: canManage && emp ? emp.id : undefined,
          start: `${d}T${multi.startTime}`,
          end: `${d}T${multi.endTime}`,
          shiftType: form.shiftType, otLevel: form.otLevel,
          reason: form.reason.trim(),
        });
      });
    } else {
      if (!form.start || !form.end) { setErr('Vui lòng chọn giờ bắt đầu và kết thúc.'); return; }
      payloads.push({
        empId: canManage && emp ? emp.id : undefined,
        start: form.start, end: form.end,
        shiftType: form.shiftType, otLevel: form.otLevel,
        reason: form.reason.trim(),
      });
    }

    setBusy(true); setErr(null);
    try {
      await Promise.all(payloads.map(p => createShift(p)));
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Đăng ký ca thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  const addMultiDate = () => {
    if (!newDate) return;
    if (multi.dates.includes(newDate)) return;
    setMulti({ ...multi, dates: [...multi.dates, newDate].sort() });
    setNewDate('');
  };
  const removeMultiDate = (d) => {
    setMulti({ ...multi, dates: multi.dates.filter(x => x !== d) });
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>
          {canManage ? 'Thêm ca cho nhân viên' : 'Đăng ký ca làm việc'}
        </h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12, maxHeight: '80vh', overflowY: 'auto' }}>
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
            disabled={!canManage}
            onChange={(e) => setForm({ ...form, shiftType: e.target.value,
              otLevel: e.target.value === 'ctv' ? '100' : form.otLevel })}>
            {canManage ? (
              <>
                <option value="ot">Tăng ca (OT)</option>
                <option value="ctv">CTV</option>
              </>
            ) : me?.isOfficial ? (
              <option value="ot">Tăng ca (OT)</option>
            ) : (
              <option value="ctv">CTV</option>
            )}
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
        <label style={{ fontSize: 12.5, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: '4px 0' }}>
          <input type="checkbox" checked={isMulti} onChange={(e) => setIsMulti(e.target.checked)} />
          <b>Đăng ký cho nhiều ngày</b>
        </label>

        {!isMulti ? (
          <>
            <label style={{ fontSize: 12.5 }}>Bắt đầu
              <input type="datetime-local" className="sel" value={form.start}
                onChange={(e) => setForm({ ...form, start: e.target.value })} />
            </label>
            <label style={{ fontSize: 12.5 }}>Kết thúc
              <input type="datetime-local" className="sel" value={form.end}
                onChange={(e) => setForm({ ...form, end: e.target.value })} />
            </label>
          </>
        ) : (
          <div style={{ background: 'var(--surface-2)', padding: 12, borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', gap: 10 }}>
              <label style={{ fontSize: 12, flex: 1 }}>Giờ vào
                <input type="time" className="sel" value={multi.startTime}
                  onChange={(e) => setMulti({ ...multi, startTime: e.target.value })} />
              </label>
              <label style={{ fontSize: 12, flex: 1 }}>Giờ ra
                <input type="time" className="sel" value={multi.endTime}
                  onChange={(e) => setMulti({ ...multi, endTime: e.target.value })} />
              </label>
            </div>
            <label style={{ fontSize: 12 }}>Chọn các ngày
              <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                <input type="date" className="sel" value={newDate} onChange={(e) => setNewDate(e.target.value)} />
                <button className="btn btn-ghost btn-sm" onClick={addMultiDate}>Thêm</button>
              </div>
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {multi.dates.map(d => (
                <Badge key={d} kind="gray" style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }}>
                  {d.split('-').reverse().join('/')}
                  <Icon name="x" size={12} style={{ cursor: 'pointer' }} onClick={() => removeMultiDate(d)} />
                </Badge>
              ))}
            </div>
          </div>
        )}
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
