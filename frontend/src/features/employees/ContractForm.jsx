/* Form hợp đồng lao động — dùng cho cả Thêm mới, Sửa và Tái ký.
   Trường bám sheet "2.5. Theo dõi ký hợp đồng" + khối lương của sheet 2.2.
   Owner: Việt. */
import { useState } from 'react';
import { createContract, saveContract } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, hint, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
      {hint && <span className="muted" style={{ fontSize: 11.5 }}>{hint}</span>}
    </label>
  );
}

const TODAY = new Date().toISOString().slice(0, 10);

/* Ngày hết hạn gợi ý theo loại hợp đồng — HR vẫn sửa đè được. */
const MONTHS_BY_TYPE = { probation: 2, fixed_6m: 6, fixed_12m: 12, teaching: 6 };
const addMonths = (iso, months) => {
  if (!iso || !months) return '';
  const d = new Date(iso);
  d.setMonth(d.getMonth() + months);
  return d.toISOString().slice(0, 10);
};

/* mode: 'create' | 'edit' | 'renew'. Tái ký = tạo mới nhưng bê sẵn điều khoản
   của hợp đồng cũ, vì thực tế HR chỉ đổi ngày và (đôi khi) mức lương. */
export default function ContractForm({ empId, contract, mode = 'create',
  options, onClose, onSaved }) {
  const src = contract || {};
  const renew = mode === 'renew';
  const [f, setF] = useState({
    name: renew ? '' : (src.name || ''),
    typeKey: src.typeKey || 'fixed_12m',
    dateSigned: renew ? TODAY : (src.dateSigned || TODAY),
    dateStart: renew ? (src.dateEnd || TODAY) : (src.dateStart || TODAY),
    dateEnd: renew ? '' : (src.dateEnd || ''),
    wage: src.wage || '',
    insuranceBase: src.insuranceBase || '',
    state: renew ? 'open' : (src.state || 'open'),
    structureId: src.structureId || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  /* Đổi loại HĐ → gợi ý lại ngày hết hạn nếu ô đang trống hoặc đang là gợi ý cũ. */
  const setType = (e) => {
    const typeKey = e.target.value;
    setF((p) => {
      const suggested = addMonths(p.dateStart, MONTHS_BY_TYPE[typeKey]);
      const keep = p.dateEnd && p.dateEnd !== addMonths(p.dateStart, MONTHS_BY_TYPE[p.typeKey]);
      return { ...p, typeKey, dateEnd: keep ? p.dateEnd : suggested };
    });
  };

  const submit = async () => {
    setErr(null);
    if (!f.dateStart) { setErr('Vui lòng nhập ngày bắt đầu hiệu lực.'); return; }
    if (f.dateEnd && f.dateEnd < f.dateStart) {
      setErr('Ngày hết hạn phải sau ngày bắt đầu hiệu lực.'); return;
    }
    try {
      setBusy(true);
      const payload = { ...f, wage: Number(f.wage || 0),
        insuranceBase: Number(f.insuranceBase || 0) };
      onSaved(mode === 'edit'
        ? await saveContract(contract.id, payload)
        : await createContract(empId, payload));
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  const title = mode === 'edit' ? 'Sửa hợp đồng'
    : renew ? 'Tái ký hợp đồng' : 'Thêm hợp đồng';

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={mode === 'edit' ? 'edit' : 'file'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{title}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            {renew
              ? 'Bê sẵn điều khoản hợp đồng cũ — chỉnh ngày và mức lương nếu có thay đổi'
              : 'Hợp đồng đang hiệu lực là căn cứ để nhân viên có mặt trên bảng lương'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px', maxHeight: '62vh', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Loại hợp đồng">
            <select style={inp} value={f.typeKey} onChange={setType}>
              <option value="">— Chưa phân loại —</option>
              {(options?.types || []).map((t) => (
                <option key={t.key} value={t.key}>{t.label}</option>
              ))}
            </select></Field>
          <Field label="Trạng thái"
            hint={f.state !== 'open' ? 'Chỉ hợp đồng "Đang hiệu lực" mới lên bảng lương' : null}>
            <select style={inp} value={f.state} onChange={set('state')}>
              {(options?.states || []).map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select></Field>

          <Field label="Ngày ký" hint="Ngày hai bên ký giấy">
            <input type="date" style={inp} value={f.dateSigned} onChange={set('dateSigned')} /></Field>
          <Field label="Hiệu lực từ *" hint="Mốc quyết định kỳ lương nào có người này">
            <input type="date" style={inp} value={f.dateStart} onChange={set('dateStart')} /></Field>
          <Field label="Hết hạn" hint="Bỏ trống = hợp đồng không xác định thời hạn">
            <input type="date" style={inp} value={f.dateEnd} onChange={set('dateEnd')} /></Field>
          <Field label="Cấu trúc lương">
            <select style={inp} value={f.structureId} onChange={set('structureId')}>
              <option value="">— Theo mặc định —</option>
              {(options?.structures || []).map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select></Field>

          <Field label="Lương cơ bản (₫)">
            <input type="number" min="0" step="100000" style={inp}
              value={f.wage} onChange={set('wage')} placeholder="0" /></Field>
          <Field label="Lương đóng BHXH (₫)" hint="Bỏ trống/0 = tính theo lương cơ bản">
            <input type="number" min="0" step="100000" style={inp}
              value={f.insuranceBase} onChange={set('insuranceBase')} placeholder="0" /></Field>

          <Field label="Tên hợp đồng" full hint="Bỏ trống thì hệ thống tự đặt theo mã và tên nhân viên">
            <input style={inp} value={f.name} onChange={set('name')}
              placeholder="VD: HĐLĐ HB.03 - Trần Quốc Việt" /></Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />
          {busy ? 'Đang lưu…' : 'Lưu hợp đồng'}
        </button>
      </div>
    </Modal>
  );
}
