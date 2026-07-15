/* ============================================================
   Form Thêm/Sửa người phụ thuộc (F-003) — inline trong tab Thông tin,
   chỉ HR. dep=null là thêm mới. Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchDependentMeta, createDependent, updateDependent } from '../../api/employees';
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

export default function DependentForm({ empId, dep, onClose, onSaved }) {
  const isEdit = !!dep;
  const [rels, setRels] = useState([]);
  const [f, setF] = useState({
    name: dep?.name || '', relationship: dep?.relationshipKey || '',
    birthday: dep?.birthday || '', nationalId: dep?.nationalId || '',
    dateStart: dep?.from || '', dateEnd: dep?.to || '', notes: dep?.notes || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchDependentMeta().then((m) => setRels(m.relationship || [])).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập họ tên NPT.'); return; }
    if (!f.relationship) { setErr('Vui lòng chọn quan hệ.'); return; }
    if (!f.birthday || !f.dateStart) { setErr('Cần ngày sinh và ngày bắt đầu giảm trừ.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateDependent(dep.id, f) : await createDependent(empId, f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={isEdit ? 'edit' : 'plus'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{isEdit ? 'Sửa người phụ thuộc' : 'Thêm người phụ thuộc'}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Giảm trừ gia cảnh (F-003)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Họ tên NPT *" full>
            <input style={inp} value={f.name} onChange={set('name')} placeholder="Nguyễn Văn B" /></Field>
          <Field label="Quan hệ *">
            <select style={inp} value={f.relationship} onChange={set('relationship')}>
              <option value="">— Chọn —</option>
              {rels.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Ngày sinh *">
            <input type="date" style={inp} value={f.birthday || ''} onChange={set('birthday')} /></Field>
          <Field label="Số CCCD/Hộ chiếu">
            <input style={inp} value={f.nationalId} onChange={set('nationalId')} /></Field>
          <Field label="Bắt đầu giảm trừ *">
            <input type="date" style={inp} value={f.dateStart || ''} onChange={set('dateStart')} /></Field>
          <Field label="Kết thúc (nếu có)">
            <input type="date" style={inp} value={f.dateEnd || ''} onChange={set('dateEnd')} /></Field>
          <Field label="Ghi chú" full>
            <input style={inp} value={f.notes} onChange={set('notes')} /></Field>
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
