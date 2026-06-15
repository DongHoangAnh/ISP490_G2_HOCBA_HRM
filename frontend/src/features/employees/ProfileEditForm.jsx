/* ============================================================
   Form "Cập nhật thông tin của tôi" — self-service: nhân viên tự sửa
   LIÊN HỆ + ĐỊA CHỈ của chính mình (thay "Sửa trong Odoo"). Các trường
   nhạy cảm (lương/trạng thái/pháp lý) do HR quản, không sửa ở đây. Owner: Tân.
   ============================================================ */
import { useState } from 'react';
import { updateMe } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

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

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 12.5, fontWeight: 800, marginBottom: 12, paddingBottom: 7, borderBottom: '1px solid var(--border)', color: 'var(--red-700)' }}>{title}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>{children}</div>
    </div>
  );
}

export default function ProfileEditForm({ det, onClose, onSaved }) {
  const ed = det.editable || {};
  const provinces = det.provinces || [];
  const [f, setF] = useState({
    phone: ed.phone || '', permStreet: ed.permStreet || '', permWard: ed.permWard || '',
    permState: ed.permState || '', currentSame: ed.currentSame !== false,
    currStreet: ed.currStreet || '', currWard: ed.currWard || '', currState: ed.currState || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));
  const provSelect = (k) => (
    <select style={inp} value={f[k] || ''} onChange={set(k)}>
      <option value="">— Chọn tỉnh/thành —</option>
      {provinces.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
    </select>
  );

  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      const d = await updateMe(f);
      onSaved(d);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="edit" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>Cập nhật thông tin của tôi</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Liên hệ &amp; địa chỉ · các thông tin khác do Nhân sự quản lý</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        <Section title="Liên hệ">
          <Field label="Điện thoại" full>
            <input style={inp} value={f.phone} onChange={set('phone')} placeholder="09xxxxxxxx" /></Field>
        </Section>

        <Section title="Địa chỉ thường trú">
          <Field label="Số nhà / Đường" full>
            <input style={inp} value={f.permStreet} onChange={set('permStreet')} placeholder="Số 10, ngõ 25 phố ..." /></Field>
          <Field label="Phường / Xã">
            <input style={inp} value={f.permWard} onChange={set('permWard')} /></Field>
          <Field label="Tỉnh / Thành">{provSelect('permState')}</Field>
        </Section>

        <label style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 13.5, fontWeight: 600, cursor: 'pointer', marginBottom: f.currentSame ? 4 : 16 }}>
          <input type="checkbox" checked={f.currentSame}
            onChange={(e) => setF((p) => ({ ...p, currentSame: e.target.checked }))}
            style={{ width: 16, height: 16, accentColor: 'var(--red-600)' }} />
          Tạm trú giống thường trú
        </label>

        {!f.currentSame && (
          <Section title="Địa chỉ tạm trú">
            <Field label="Số nhà / Đường" full>
              <input style={inp} value={f.currStreet} onChange={set('currStreet')} /></Field>
            <Field label="Phường / Xã">
              <input style={inp} value={f.currWard} onChange={set('currWard')} /></Field>
            <Field label="Tỉnh / Thành">{provSelect('currState')}</Field>
          </Section>
        )}

        {err && (
          <div style={{ marginTop: 4, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : 'Lưu thay đổi'}
        </button>
      </div>
    </Modal>
  );
}
