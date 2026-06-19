/* Form tạo file chuyển khoản — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { generateBankFile, fetchBankFormats } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

export default function BankFileForm({ batches, onClose, onSaved }) {
  const [formats, setFormats] = useState([]);
  const [form, setForm] = useState({ batch_id: '', bank_format_id: '', payment_date: '' });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchBankFormats().then(setFormats).catch(() => {}); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await generateBankFile({
        batch_id: Number(form.batch_id),
        bank_format_id: Number(form.bank_format_id),
        payment_date: form.payment_date,
      });
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Tạo file thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Tạo file chuyển khoản</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Sinh file thanh toán cho ngân hàng</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Đợt lương</label>
          <select className="sel" style={{ width: '100%' }} value={form.batch_id} onChange={(e) => set('batch_id', e.target.value)} required>
            <option value="">Chọn đợt lương</option>
            {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Định dạng ngân hàng</label>
          <select className="sel" style={{ width: '100%' }} value={form.bank_format_id} onChange={(e) => set('bank_format_id', e.target.value)} required>
            <option value="">Chọn định dạng</option>
            {formats.map((f) => <option key={f.id} value={f.id}>{f.name} ({f.code})</option>)}
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Ngày thanh toán</label>
          <input type="date" style={inp} value={form.payment_date} onChange={(e) => set('payment_date', e.target.value)} required />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang tạo...' : 'Tạo file'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
