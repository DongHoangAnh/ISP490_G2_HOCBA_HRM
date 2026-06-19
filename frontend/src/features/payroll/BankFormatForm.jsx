/* Form tạo/sửa bank format — Owner: Hùng. */
import { useState } from 'react';
import { createBankFormat, updateBankFormat } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

export default function BankFormatForm({ item, onClose, onSaved }) {
  const isEdit = !!item;
  const [form, setForm] = useState({
    name: item?.name || '',
    code: item?.code || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      if (isEdit) {
        await updateBankFormat(item.id, form);
      } else {
        await createBankFormat(form);
      }
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Lưu thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };
  const hint = { fontSize: 12, color: 'var(--muted)', marginTop: 4 };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--blue-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{isEdit ? 'Sửa ngân hàng' : 'Thêm ngân hàng'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? `Đang sửa: ${item.name}` : 'Thêm ngân hàng để chọn khi tạo lương'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tên ngân hàng</label>
          <input type="text" style={inp} value={form.name} onChange={(e) => set('name', e.target.value)}
            placeholder="VD: Vietcombank" required />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Mã ngắn</label>
          <input type="text" style={inp} value={form.code} onChange={(e) => set('code', e.target.value.toUpperCase())}
            placeholder="VD: VCB" required />
          <div style={hint}>Viết hoa, duy nhất</div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang lưu...' : (isEdit ? 'Cập nhật' : 'Thêm mới')}
          </button>
        </div>
      </form>
    </Modal>
  );
}
