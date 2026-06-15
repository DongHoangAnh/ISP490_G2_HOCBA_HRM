/* ============================================================
   Form Thêm/Sửa chứng chỉ (F-008) — inline trong tab Thông tin,
   chỉ HR. cert=null là thêm mới. Loại → Chứng chỉ → Cấp độ (cascade).
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchFormMeta, createCert, updateCert } from '../../api/employees';
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

export default function CertForm({ empId, cert, onClose, onSaved }) {
  const isEdit = !!cert;
  const [types, setTypes] = useState([]);
  const [f, setF] = useState({
    skillTypeId: cert?.skillTypeId || '', skillId: cert?.skillId || '',
    levelId: cert?.levelId || '', certDate: cert?.date || '',
    certExpiry: cert?.expiry || '', verified: cert?.verified || false,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then((m) => setTypes(m.skillTypes || [])).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));
  const curType = types.find((t) => t.id === Number(f.skillTypeId));

  const submit = async () => {
    setErr(null);
    if (!f.skillTypeId) { setErr('Vui lòng chọn loại chứng chỉ.'); return; }
    if (!f.skillId) { setErr('Vui lòng chọn chứng chỉ.'); return; }
    if (!f.levelId) { setErr('Vui lòng chọn cấp độ.'); return; }
    if (f.certDate && f.certExpiry && f.certExpiry <= f.certDate) {
      setErr('Ngày hết hạn phải sau ngày cấp.'); return;
    }
    setBusy(true);
    try {
      const det = isEdit ? await updateCert(cert.id, f) : await createCert(empId, f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--teal,#0F766E)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="award" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{isEdit ? 'Sửa chứng chỉ' : 'Thêm chứng chỉ'}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Ma trận kỹ năng & hạn hiệu lực (F-008)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Loại *">
            <select style={inp} value={f.skillTypeId}
              onChange={(e) => setF((p) => ({ ...p, skillTypeId: e.target.value, skillId: '', levelId: '' }))}>
              <option value="">— Chọn —</option>
              {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select></Field>
          <Field label="Cấp độ *">
            <select style={inp} value={f.levelId} onChange={set('levelId')} disabled={!curType}>
              <option value="">— Chọn —</option>
              {(curType?.levels || []).map((lv) => <option key={lv.id} value={lv.id}>{lv.name}</option>)}
            </select></Field>
          <Field label="Chứng chỉ *" full>
            <select style={inp} value={f.skillId} onChange={set('skillId')} disabled={!curType}>
              <option value="">— Chọn —</option>
              {(curType?.skills || []).map((sk) => <option key={sk.id} value={sk.id}>{sk.name}</option>)}
            </select></Field>
          <Field label="Ngày cấp">
            <input type="date" style={inp} value={f.certDate || ''} onChange={set('certDate')} /></Field>
          <Field label="Ngày hết hạn (nếu có)">
            <input type="date" style={inp} value={f.certExpiry || ''} onChange={set('certExpiry')} /></Field>
          <label style={{ display: 'flex', alignItems: 'center', gap: 9, gridColumn: '1 / -1', cursor: 'pointer', fontSize: 13 }}>
            <input type="checkbox" checked={f.verified}
              onChange={(e) => setF((p) => ({ ...p, verified: e.target.checked }))} />
            Đã xác minh bản gốc (chỉ chứng chỉ đã xác minh mới được cảnh báo hết hạn)
          </label>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : (isEdit ? 'Lưu' : 'Thêm')}
        </button>
      </div>
    </Modal>
  );
}
