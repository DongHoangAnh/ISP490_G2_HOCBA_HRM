/* ============================================================
   Form Cấp phát tài sản (F-006 rút gọn) — inline trong tab Tài sản,
   chỉ HR. Không còn thu hồi/chuyển giao: gỡ tài sản = xoá dòng.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchFormMeta, createAsset } from '../../api/employees';
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

const TODAY = new Date().toISOString().slice(0, 10);

export default function AssetForm({ empId, onClose, onSaved }) {
  const [meta, setMeta] = useState(null);
  const [f, setF] = useState({
    assetTypeId: '', assetCode: '', grantDate: TODAY, conditionIn: 'good',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then(setMeta).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    setErr(null);
    if (!f.assetTypeId) { setErr('Vui lòng chọn loại tài sản.'); return; }
    if (!f.assetCode.trim()) { setErr('Vui lòng nhập mã tài sản.'); return; }
    try {
      setBusy(true);
      onSaved(await createAsset(empId, f));
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="plus" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Cấp phát tài sản</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Ghi nhận thiết bị nhân viên đang giữ</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Loại tài sản *">
            <select style={inp} value={f.assetTypeId} onChange={set('assetTypeId')}>
              <option value="">— Chọn —</option>
              {(meta?.assetTypes || []).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select></Field>
          <Field label="Mã tài sản *">
            <input style={inp} value={f.assetCode} onChange={set('assetCode')} placeholder="VD: LAP-007" /></Field>
          <Field label="Ngày cấp phát">
            <input type="date" style={inp} value={f.grantDate} onChange={set('grantDate')} /></Field>
          <Field label="Tình trạng khi cấp">
            <select style={inp} value={f.conditionIn} onChange={set('conditionIn')}>
              {(meta?.assetCondition || []).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !meta}>
          <Icon name="checkCircle" size={16} />
          {busy ? 'Đang lưu…' : 'Cấp phát'}
        </button>
      </div>
    </Modal>
  );
}
