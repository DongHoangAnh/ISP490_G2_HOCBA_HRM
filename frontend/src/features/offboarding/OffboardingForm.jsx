/* Modal nộp đơn nghỉ việc (self-service). Đơn qua 2 cấp duyệt: quản lý → HR. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { submitOffboarding } from '../../api/offboarding';

const REASONS = [
  ['voluntary', 'Tự nguyện'],
  ['contract_end', 'Hết hạn hợp đồng'],
  ['other', 'Khác'],
];

const plus30 = () => {
  const d = new Date(); d.setDate(d.getDate() + 30);
  return d.toISOString().slice(0, 10);
};

const inputStyle = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function L({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

export default function OffboardingForm({ onClose, onSaved }) {
  const [reasonType, setReasonType] = useState('voluntary');
  const [reason, setReason] = useState('');
  const [leaveDate, setLeaveDate] = useState(plus30);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = () => {
    const r = reason.trim();
    if (!r) { setErr('Vui lòng nhập lý do chi tiết.'); return; }
    if (!leaveDate) { setErr('Vui lòng chọn ngày nghỉ dự kiến.'); return; }
    setBusy(true); setErr(null);
    submitOffboarding({ reasonType, reason: r, expectedLeaveDate: leaveDate })
      .then(onSaved)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="logout" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Nộp đơn nghỉ việc</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            Đơn sẽ qua 2 cấp duyệt: quản lý trực tiếp → HR
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <L label="Loại lý do *">
          <select style={inputStyle} value={reasonType}
            onChange={(e) => setReasonType(e.target.value)}>
            {REASONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </L>
        <L label="Lý do chi tiết *">
          <textarea rows={3} style={{ ...inputStyle, resize: 'vertical' }}
            value={reason} onChange={(e) => setReason(e.target.value)}
            placeholder="VD: Chuyển nơi ở, định hướng nghề nghiệp mới…" />
        </L>
        <L label="Ngày nghỉ dự kiến *">
          <input type="date" style={inputStyle} value={leaveDate}
            onChange={(e) => setLeaveDate(e.target.value)} />
        </L>
        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Đang gửi…' : 'Nộp đơn'}
        </button>
      </div>
    </Modal>
  );
}
