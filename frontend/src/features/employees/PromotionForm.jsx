/* ============================================================
   Form Thêm thăng tiến (F-007) — inline trong tab Thăng tiến,
   chỉ HR Manager. Tạo bản ghi sẽ tự cập nhật chức vụ/phòng ban NV.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchFormMeta, createPromotion } from '../../api/employees';
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

/* reviewId: phiếu đánh giá làm căn cứ (mở từ màn Đánh giá). Phiếu vừa là
   căn cứ vừa là BẰNG CHỨNG đổi lương — thiếu nó thì _check_rules đòi
   x_evidence_url mà form này không có ô nhập. */
export default function PromotionForm({ det, reviewId, reasonHint, onClose, onSaved }) {
  const [meta, setMeta] = useState(null);
  const [f, setF] = useState({
    dateEffective: TODAY, toDepartmentId: det?.dep || '', toJobId: '',
    toWage: '', decisionRef: '', allowanceNote: '', reason: reasonHint || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then(setMeta).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    setErr(null);
    if (!f.toJobId) { setErr('Vui lòng chọn chức vụ mới.'); return; }
    if (!f.toWage || Number(f.toWage) <= 0) { setErr('Vui lòng nhập mức lương mới (> 0).'); return; }
    setBusy(true);
    try {
      onSaved(await createPromotion(det.id, reviewId ? { ...f, reviewId } : f));
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  // chức vụ lọc theo phòng ban đã chọn (rỗng = hiện tất cả)
  const jobs = meta ? meta.jobs.filter((j) => !f.toDepartmentId || j.dep === Number(f.toDepartmentId)) : [];

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--gold-600,#B45309)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="arrowUp" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Thêm mốc thăng tiến</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            {det.jobTitle} → … · sẽ cập nhật chức vụ hiện tại của NV (F-007)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Ngày hiệu lực">
            <input type="date" style={inp} value={f.dateEffective} onChange={set('dateEffective')} /></Field>
          <Field label="Số quyết định">
            <input style={inp} value={f.decisionRef} onChange={set('decisionRef')} placeholder="VD: QĐ-2026/07" /></Field>
          <Field label="Phòng ban mới">
            <select style={inp} value={f.toDepartmentId}
              onChange={(e) => setF((p) => ({ ...p, toDepartmentId: e.target.value, toJobId: '' }))}>
              <option value="">— Giữ nguyên —</option>
              {(meta?.departments || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></Field>
          <Field label="Chức vụ mới *">
            <select style={inp} value={f.toJobId} onChange={set('toJobId')}>
              <option value="">— Chọn —</option>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
            </select></Field>
          <Field label="Lương mới (₫) *">
            <input type="number" style={inp} value={f.toWage} onChange={set('toWage')} placeholder="0" /></Field>
          <Field label="Phụ cấp (tóm tắt)">
            <input style={inp} value={f.allowanceNote} onChange={set('allowanceNote')} /></Field>
          <Field label="Lý do / Căn cứ" full>
            <input style={inp} value={f.reason} onChange={set('reason')} placeholder="Bắt buộc khi đổi mức lương" /></Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !meta}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : 'Thêm mốc'}
        </button>
      </div>
    </Modal>
  );
}
