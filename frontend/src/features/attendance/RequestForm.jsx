/* Form gửi đơn chấm công (Gói 3). Dùng 2 trường hợp:
   - Sửa bản ghi có sẵn: truyền attendanceId + requestDate cố định (prefill giờ).
   - Quên cả ngày: không attendanceId, user tự chọn ngày. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createRequest } from '../../api/attendance';

export default function RequestForm({ attendanceId, requestDate, checkIn, checkOut, onClose, onSaved }) {
  const fixedDate = !!attendanceId;
  const [form, setForm] = useState({
    requestDate: requestDate || '',
    checkIn: checkIn ? checkIn.slice(0, 16) : '',
    checkOut: checkOut ? checkOut.slice(0, 16) : '',
    reason: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function submit() {
    if (!form.requestDate) { setErr('Vui lòng chọn ngày.'); return; }
    if (!form.reason.trim()) { setErr('Vui lòng nhập lý do.'); return; }
    setBusy(true); setErr(null);
    try {
      await createRequest({
        attendanceId: attendanceId || undefined,
        requestDate: form.requestDate,
        checkIn: form.checkIn || null,
        checkOut: form.checkOut || null,
        reason: form.reason.trim(),
      });
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Gửi đơn thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>
          {fixedDate ? 'Gửi đơn sửa chấm công' : 'Gửi đơn quên chấm công'}
        </h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <label style={{ fontSize: 12.5 }}>Ngày công
          <input type="date" className="sel" value={form.requestDate} disabled={fixedDate}
            onChange={(e) => setForm({ ...form, requestDate: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Giờ vào đề xuất
          <input type="datetime-local" className="sel" value={form.checkIn}
            onChange={(e) => setForm({ ...form, checkIn: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Giờ ra đề xuất
          <input type="datetime-local" className="sel" value={form.checkOut}
            onChange={(e) => setForm({ ...form, checkOut: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Lý do
          <textarea className="sel" rows={3} value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}>Gửi đơn</button>
          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={onClose}>Hủy</button>
        </div>
      </div>
    </Modal>
  );
}
