/* ============================================================
   Form tạo phiếu thu/chi (nháp). Owner: Tài chính.
   ctx = { funds, categories:{income,expense} } lấy từ /api/finance/context.
   ============================================================ */
import { useState, useMemo } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createVoucher } from '../../api/finance';

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

const today = () => new Date().toISOString().slice(0, 10);

export default function VoucherForm({ ctx, onClose, onDone }) {
  const [type, setType] = useState('income');
  const [amount, setAmount] = useState('');
  const [dateV, setDateV] = useState(today());
  const [fundId, setFundId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [partnerName, setPartnerName] = useState('');
  const [memo, setMemo] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const cats = useMemo(
    () => (type === 'income' ? ctx.categories.income : ctx.categories.expense),
    [type, ctx]);

  const submit = async () => {
    setErr(null);
    if (!fundId) return setErr('Vui lòng chọn quỹ.');
    if (!categoryId) return setErr('Vui lòng chọn mục.');
    if (!(Number(amount) > 0)) return setErr('Số tiền phải lớn hơn 0.');
    setBusy(true);
    try {
      const res = await createVoucher({
        voucherType: type,
        amount: Number(amount),
        date: dateV,
        fundId: Number(fundId),
        categoryId: Number(categoryId),
        partnerName, memo,
      });
      onDone(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: type === 'income' ? 'var(--green-600,#16a34a)' : 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={type === 'income' ? 'arrowDown' : 'arrowUp'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Tạo phiếu {type === 'income' ? 'thu' : 'chi'}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Phiếu tạo ở trạng thái Nháp, chờ Kế toán duyệt.</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Loại phiếu *">
            <select style={inp} value={type}
              onChange={(e) => { setType(e.target.value); setCategoryId(''); }}>
              <option value="income">Phiếu thu</option>
              <option value="expense">Phiếu chi</option>
            </select>
          </Field>
          <Field label="Ngày *">
            <input type="date" style={inp} value={dateV} onChange={(e) => setDateV(e.target.value)} />
          </Field>
          <Field label="Số tiền (VND) *">
            <input type="number" min="0" step="1000" style={inp} value={amount}
              onChange={(e) => setAmount(e.target.value)} placeholder="0" autoComplete="off" />
          </Field>
          <Field label="Quỹ *">
            <select style={inp} value={fundId} onChange={(e) => setFundId(e.target.value)}>
              <option value="">— Chọn quỹ —</option>
              {ctx.funds.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}{f.departmentName ? ` · ${f.departmentName}` : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Mục *" full>
            <select style={inp} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">— Chọn mục —</option>
              {cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Người nộp / nhận" full>
            <input style={inp} value={partnerName} onChange={(e) => setPartnerName(e.target.value)}
              placeholder="VD: Nguyễn Văn A" autoComplete="off" />
          </Field>
          <Field label="Diễn giải" full>
            <input style={inp} value={memo} onChange={(e) => setMemo(e.target.value)}
              placeholder="Nội dung phiếu" autoComplete="off" />
          </Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : 'Tạo phiếu'}
        </button>
      </div>
    </Modal>
  );
}
