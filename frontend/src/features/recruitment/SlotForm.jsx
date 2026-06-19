/* Form thêm lịch rảnh phỏng vấn (theo tuần) — Owner: Việt.
   Tạo nhiều slot trong một lần cho 1 người phỏng vấn. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createInterviewSlots } from '../../api/recruitment';

const inp = {
  width: '100%', padding: '8px 10px', borderRadius: 9,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

/* 09:00 → 17:00 mỗi 30 phút */
export const HOUR_OPTIONS = (() => {
  const out = [];
  for (let h = 9; h <= 17; h += 0.5) {
    const hh = Math.floor(h);
    const mm = h % 1 ? '30' : '00';
    out.push([h, `${String(hh).padStart(2, '0')}:${mm}`]);
  }
  return out;
})();

export default function SlotForm({ interviewers, meId, weekDates, defaultDate, onClose, onSaved }) {
  const [userId, setUserId] = useState(meId);
  const [lines, setLines] = useState([{ date: defaultDate || weekDates[0], startHour: 9, endHour: 10 }]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const setLine = (i, k, v) => setLines((p) => p.map((l, idx) => (idx === i ? { ...l, [k]: v } : l)));
  const addLine = () => setLines((p) => [...p, { date: defaultDate || weekDates[0], startHour: 9, endHour: 10 }]);
  const delLine = (i) => setLines((p) => p.filter((_, idx) => idx !== i));

  const submit = async () => {
    for (const l of lines) {
      if (Number(l.endHour) <= Number(l.startHour)) { setErr('Giờ kết thúc phải sau giờ bắt đầu.'); return; }
    }
    setBusy(true); setErr(null);
    try {
      await createInterviewSlots(Number(userId), lines.map((l) => ({
        date: l.date, startHour: Number(l.startHour), endHour: Number(l.endHour),
      })));
      onSaved();
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="calendar" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>Thêm lịch rảnh phỏng vấn</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Khai báo khung giờ rảnh để xếp lịch PV</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        <label style={{ display: 'block', marginBottom: 16 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', display: 'block', marginBottom: 5 }}>Người phỏng vấn</span>
          <select style={inp} value={userId} onChange={(e) => setUserId(e.target.value)}>
            {!interviewers.some((u) => u.id === meId) && <option value={meId}>Tôi</option>}
            {interviewers.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
        </label>

        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 8 }}>Khung giờ rảnh</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {lines.map((l, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr auto', gap: 8, alignItems: 'center' }}>
              <input type="date" style={inp} value={l.date} onChange={(e) => setLine(i, 'date', e.target.value)} />
              <select style={inp} value={l.startHour} onChange={(e) => setLine(i, 'startHour', e.target.value)}>
                {HOUR_OPTIONS.map(([v, lbl]) => <option key={v} value={v}>{lbl}</option>)}
              </select>
              <select style={inp} value={l.endHour} onChange={(e) => setLine(i, 'endHour', e.target.value)}>
                {HOUR_OPTIONS.map(([v, lbl]) => <option key={v} value={v}>{lbl}</option>)}
              </select>
              <button className="icon-btn" title="Xoá dòng" onClick={() => delLine(i)} disabled={lines.length === 1}>
                <Icon name="trash" size={16} className="faint" /></button>
            </div>
          ))}
        </div>
        <button className="btn btn-soft btn-sm" style={{ marginTop: 10 }} onClick={addLine}>
          <Icon name="plus" size={14} />Thêm khung giờ</button>

        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : `Tạo ${lines.length} slot`}
        </button>
      </div>
    </Modal>
  );
}
