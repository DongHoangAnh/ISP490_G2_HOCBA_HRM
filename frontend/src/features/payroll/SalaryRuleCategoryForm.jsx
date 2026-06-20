/* Form tạo/sửa danh mục salary rule — Owner: Hùng. */
import { useState } from 'react';
import { createRuleCategory, updateRuleCategory } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

export default function SalaryRuleCategoryForm({ item, onClose, onSaved }) {
  const isEdit = !!item;
  const [form, setForm] = useState({
    code: item?.code || '',
    name: item?.name || '',
    sequence: item?.sequence ?? 10,
    note: item?.note || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const payload = { ...form, sequence: Number(form.sequence) };
      if (isEdit) {
        await updateRuleCategory(item.id, payload);
      } else {
        await createRuleCategory(payload);
      }
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Lưu thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{isEdit ? 'Sửa danh mục' : 'Thêm danh mục'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? `Đang sửa: ${item.name}` : 'Thêm danh mục quy tắc lương'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Mã</label>
            <input type="text" style={inp} value={form.code} onChange={(e) => set('code', e.target.value)}
              placeholder="VD: GROSS" required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tên</label>
            <input type="text" style={inp} value={form.name} onChange={(e) => set('name', e.target.value)}
              placeholder="VD: Tổng thu nhập" required />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Thứ tự</label>
            <input type="number" style={inp} value={form.sequence} onChange={(e) => set('sequence', e.target.value)}
              min="1" required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Ghi chú</label>
            <input type="text" style={inp} value={form.note} onChange={(e) => set('note', e.target.value)}
              placeholder="Mô tả ngắn (tuỳ chọn)" />
          </div>
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
