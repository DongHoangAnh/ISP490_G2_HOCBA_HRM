/* ============================================================
   Form Tài sản (F-006) — inline trong tab Tài sản, chỉ HR.
   mode: 'new' (cấp phát) | 'return' (thu hồi) | 'transfer' (chuyển giao).
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import {
  fetchFormMeta, createAsset, returnAsset, transferAsset,
} from '../../api/employees';
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

const TITLES = {
  new: ['Cấp phát tài sản', 'Cấp thiết bị cho nhân viên (F-006)', 'plus'],
  return: ['Thu hồi tài sản', 'Ghi nhận thu hồi thiết bị', 'check'],
  transfer: ['Chuyển giao tài sản', 'Chuyển thiết bị cho nhân viên khác', 'users'],
};

export default function AssetForm({ empId, asset, mode, onClose, onSaved }) {
  const [meta, setMeta] = useState(null);
  const [f, setF] = useState({
    assetTypeId: '', assetCode: '', grantDate: TODAY, conditionIn: 'good',
    returnDate: TODAY, note: '', transferTo: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then(setMeta).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    setErr(null);
    try {
      if (mode === 'new') {
        if (!f.assetTypeId) { setErr('Vui lòng chọn loại tài sản.'); return; }
        if (!f.assetCode.trim()) { setErr('Vui lòng nhập mã tài sản.'); return; }
      }
      if (mode === 'transfer' && !f.transferTo) {
        setErr('Vui lòng chọn nhân viên nhận.'); return;
      }
      setBusy(true);
      let det;
      if (mode === 'new') det = await createAsset(empId, f);
      else if (mode === 'return') det = await returnAsset(asset.id, f);
      else det = await transferAsset(asset.id, f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  const [title, sub, ico] = TITLES[mode];
  // ứng viên nhận chuyển giao: loại trừ chính người đang giữ
  const candidates = meta ? meta.employees.filter((em) => em.id !== empId) : [];

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={ico} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{title}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{sub}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        {mode !== 'new' && asset && (
          <div style={{ marginBottom: 16, padding: '10px 13px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 12.5 }}>
            <b className="mono">{asset.code}</b> · {asset.type}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          {mode === 'new' && (
            <>
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
            </>
          )}
          {mode === 'transfer' && (
            <Field label="Chuyển giao cho *" full>
              <select style={inp} value={f.transferTo} onChange={set('transferTo')}>
                <option value="">— Chọn nhân viên —</option>
                {candidates.map((em) => <option key={em.id} value={em.id}>{em.name}</option>)}
              </select></Field>
          )}
          {mode !== 'new' && (
            <Field label={mode === 'transfer' ? 'Ngày chuyển giao' : 'Ngày thu hồi'}>
              <input type="date" style={inp} value={f.returnDate} onChange={set('returnDate')} /></Field>
          )}
          {mode === 'return' && (
            <Field label="Ghi chú tình trạng" full>
              <input style={inp} value={f.note} onChange={set('note')} placeholder="VD: còn tốt, đủ phụ kiện" /></Field>
          )}
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !meta}>
          <Icon name="checkCircle" size={16} />
          {busy ? 'Đang lưu…' : mode === 'new' ? 'Cấp phát' : mode === 'transfer' ? 'Chuyển giao' : 'Thu hồi'}
        </button>
      </div>
    </Modal>
  );
}
