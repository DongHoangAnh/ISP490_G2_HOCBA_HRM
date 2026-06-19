/* Form tạo đơn nghỉ (modal). Owner: Nhật Anh. Spec §3.3.
   Theo idiom form chuẩn của màn Nhân viên (style `inp` inline, drawer-head). */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createRequest } from '../../api/timeoff';

const ALLOWED_MIME = ['application/pdf', 'image/jpeg', 'image/png'];
const MAX_SIZE = 5 * 1024 * 1024;

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

/* File → base64 (bỏ tiền tố data:...;base64,). */
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(',')[1] || '');
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

export default function LeaveForm({ leaveTypes, onClose, onSaved }) {
  const [typeId, setTypeId] = useState(leaveTypes[0]?.id || '');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [reason, setReason] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const type = leaveTypes.find((t) => t.id === Number(typeId));
  const needDoc = !!type?.supportDocument;

  const submit = async () => {
    setErr(null);
    if (!typeId || !from || !to) { setErr('Vui lòng chọn loại nghỉ và khoảng ngày.'); return; }
    if (to < from) { setErr('Ngày kết thúc phải sau ngày bắt đầu.'); return; }

    let attachment = null;
    if (file) {
      if (!ALLOWED_MIME.includes(file.type)) { setErr('Chứng từ chỉ chấp nhận PDF, JPG, PNG.'); return; }
      if (file.size > MAX_SIZE) { setErr('Chứng từ tối đa 5 MB.'); return; }
      attachment = { filename: file.name, mimetype: file.type, data: await fileToBase64(file) };
    }

    setBusy(true);
    try {
      const payload = await createRequest({
        leaveTypeId: Number(typeId), dateFrom: from, dateTo: to,
        reason: reason.trim(), attachment,
      });
      onSaved(payload);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="calendar" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>Tạo đơn nghỉ</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Gửi đơn xin nghỉ để quản lý phê duyệt</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto', display: 'grid', gap: 14 }}>
        <Field label="Loại nghỉ *" full>
          <select style={inp} value={typeId} onChange={(e) => setTypeId(e.target.value)}>
            {leaveTypes.map((t) => (
              <option key={t.id} value={t.id}>{t.name}{t.isEmergency ? ' (khẩn cấp)' : ''}</option>
            ))}
          </select>
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <Field label="Từ ngày *">
            <input type="date" style={inp} value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
          <Field label="Đến ngày *">
            <input type="date" style={inp} value={to} onChange={(e) => setTo(e.target.value)} /></Field>
        </div>

        <Field label="Lý do" full>
          <textarea style={{ ...inp, resize: 'vertical' }} rows={3} value={reason}
            onChange={(e) => setReason(e.target.value)} placeholder="Nhập lý do nghỉ…" /></Field>

        {needDoc && (
          <Field label="Chứng từ y tế (PDF/JPG/PNG, ≤ 5 MB)" full>
            <input type="file" style={inp} accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setFile(e.target.files[0] || null)} />
            <span className="muted" style={{ fontSize: 12, marginTop: 4 }}>
              Đơn nghỉ ốm cần chứng từ để được duyệt (BR-011).</span>
          </Field>
        )}

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang gửi…' : 'Gửi đơn'}</button>
      </div>
    </Modal>
  );
}
