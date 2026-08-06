/* ============================================================
   Form tạo phiếu thu/chi (nháp) — chuẩn Mẫu 01-TT / 02-TT
   Thông tư 200/2014/TT-BTC Bộ Tài chính.
   Owner: Tài chính. ctx = { funds, categories } từ /api/finance/context.
   ============================================================ */
import { useState, useMemo } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createVoucher } from '../../api/finance';

/* ── Số tiền → chữ (tiếng Việt) ──────────────────────────────────────
   Chuẩn: viết hoa chữ cái đầu, kết thúc bằng "đồng" (TT200 §01-TT).
   Chỉ VND, không xử lý ngoại tệ. ────────────────────────────────────*/
const DIGITS = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];
const readGroup3 = (a, b, c, showZeroHundred) => {
  const parts = [];
  if (a > 0) { parts.push(DIGITS[a], 'trăm'); }
  else if (showZeroHundred) { parts.push('không', 'trăm'); }
  if (b > 0) {
    parts.push(b === 1 ? 'mười' : DIGITS[b] + ' mươi');
    if (c === 1) parts.push('mốt');
    else if (c === 5) parts.push('lăm');
    else if (c > 0) parts.push(DIGITS[c]);
  } else if (c > 0) {
    if (a > 0 || showZeroHundred) parts.push('lẻ');
    parts.push(DIGITS[c]);
  }
  return parts.join(' ');
};

function amountToWords(n) {
  n = Math.abs(Math.floor(n || 0));
  if (n === 0) return 'Không đồng';
  const units = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ'];
  const groups = [];
  while (n > 0) { groups.push(n % 1000); n = Math.floor(n / 1000); }
  const segs = [];
  for (let i = groups.length - 1; i >= 0; i--) {
    const g = groups[i];
    if (g === 0) continue;
    const a = Math.floor(g / 100), b = Math.floor((g % 100) / 10), c = g % 10;
    segs.push(readGroup3(a, b, c, i < groups.length - 1) + (units[i] ? ' ' + units[i] : ''));
  }
  const raw = segs.join(' ').replace(/\s+/g, ' ').trim();
  return raw.charAt(0).toUpperCase() + raw.slice(1) + ' đồng';
}

/* ── Styles ───────────────────────────────────────────────────────────── */
const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, required, full, children, hint }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
        {label}{required && ' *'}
      </span>
      {children}
      {hint && <span style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>{hint}</span>}
    </label>
  );
}

const today = () => new Date().toISOString().slice(0, 10);

/* ── Format VND display ──────────────────────────────────────────────── */
const fmtVND = (n) =>
  new Intl.NumberFormat('vi-VN').format(n || 0);

export default function VoucherForm({ ctx, onClose, onDone }) {
  const [type, setType] = useState('income');
  const [amount, setAmount] = useState('');
  const [dateV, setDateV] = useState(today());
  const [fundId, setFundId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [partnerName, setPartnerName] = useState('');
  const [partnerAddress, setPartnerAddress] = useState('');
  const [memo, setMemo] = useState('');
  const [attachmentCount, setAttachmentCount] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const cats = useMemo(
    () => (type === 'income' ? ctx.categories.income : ctx.categories.expense),
    [type, ctx]);

  const amountNum = Number(amount) || 0;
  const amountWords = amountNum > 0 ? amountToWords(amountNum) : '';

  const submit = async () => {
    setErr(null);
    if (!fundId) return setErr('Vui lòng chọn quỹ.');
    if (!categoryId) return setErr('Vui lòng chọn mục.');
    if (!(amountNum > 0)) return setErr('Số tiền phải lớn hơn 0.');
    setBusy(true);
    try {
      const res = await createVoucher({
        voucherType: type,
        amount: amountNum,
        date: dateV,
        fundId: Number(fundId),
        categoryId: Number(categoryId),
        partnerName,
        partnerAddress,
        memo,
        attachmentCount: Number(attachmentCount) || 0,
      });
      onDone(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const isIncome = type === 'income';
  const typeLabel = isIncome ? 'thu' : 'chi';
  const typeColor = isIncome ? 'var(--green-600, #16a34a)' : 'var(--red-600)';

  return (
    <Modal onClose={onClose}>
      {/* Header — chuẩn phiếu */}
      <div className="drawer-head" style={{
        background: isIncome
          ? 'linear-gradient(135deg, #dcfce7 0%, #fff 100%)'
          : 'linear-gradient(135deg, var(--red-50) 0%, #fff 100%)',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 12,
          background: typeColor, color: '#fff',
          display: 'grid', placeItems: 'center', flexShrink: 0,
          boxShadow: `0 4px 12px ${isIncome ? 'rgba(22,163,74,.25)' : 'rgba(220,38,38,.25)'}`,
        }}>
          <Icon name={isIncome ? 'arrowDown' : 'arrowUp'} size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>
            Tạo phiếu {typeLabel}
          </h2>
          <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
            Theo Mẫu {isIncome ? '01' : '02'}-TT · Thông tư 200/2014/TT-BTC
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {/* Body — layout 2 cột chuẩn chứng từ */}
      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          {/* Row 1: Loại + Ngày */}
          <Field label="Loại phiếu" required>
            <select style={inp} value={type}
              onChange={(e) => { setType(e.target.value); setCategoryId(''); }}>
              <option value="income">Phiếu thu</option>
              <option value="expense">Phiếu chi</option>
            </select>
          </Field>
          <Field label="Ngày" required hint="Ngày tiền thực chạy">
            <input type="date" style={inp} value={dateV} onChange={(e) => setDateV(e.target.value)} />
          </Field>

          {/* Row 2: Quỹ + Mục */}
          <Field label="Quỹ" required>
            <select style={inp} value={fundId} onChange={(e) => setFundId(e.target.value)}>
              <option value="">— Chọn quỹ —</option>
              {ctx.funds.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}{f.departmentName ? ` · ${f.departmentName}` : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Mục" required>
            <select style={inp} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">— Chọn mục —</option>
              {cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>

          {/* Row 3: Số tiền + Số tiền bằng chữ */}
          <Field label={`Số tiền (VND)`} required>
            <input type="number" min="0" step="1000" style={inp} value={amount}
              onChange={(e) => setAmount(e.target.value)} placeholder="0" autoComplete="off" />
            {amountNum > 0 && (
              <span style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                = {fmtVND(amountNum)} ₫
              </span>
            )}
          </Field>
          <Field label="Số tiền bằng chữ" hint="Tự động · chuẩn TT200">
            <div style={{
              ...inp, background: '#f9fafb', color: 'var(--ink)',
              fontStyle: amountWords ? 'normal' : 'italic',
              minHeight: 38, display: 'flex', alignItems: 'center',
              border: '1px dashed var(--border-strong)',
            }}>
              {amountWords || 'Nhập số tiền để hiển thị'}
            </div>
          </Field>

          {/* Row 4: Họ tên + Địa chỉ */}
          <Field label={`Họ tên người ${isIncome ? 'nộp' : 'nhận'} tiền`} full={false}>
            <input style={inp} value={partnerName} onChange={(e) => setPartnerName(e.target.value)}
              placeholder="VD: Nguyễn Văn A" autoComplete="off" />
          </Field>
          <Field label="Địa chỉ">
            <input style={inp} value={partnerAddress} onChange={(e) => setPartnerAddress(e.target.value)}
              placeholder="VD: 123 Nguyễn Trãi, Q.5, TP.HCM" autoComplete="off" />
          </Field>

          {/* Row 5: Lý do nộp/chi (full width) */}
          <Field label={`Lý do ${typeLabel}`} required full>
            <textarea style={{ ...inp, minHeight: 56, resize: 'vertical' }} value={memo}
              onChange={(e) => setMemo(e.target.value)}
              placeholder={isIncome ? 'VD: Thu học phí khóa HSK4 tháng 8/2026' : 'VD: Thanh toán hóa đơn điện nước tháng 7/2026'} />
          </Field>

          {/* Row 6: Kèm theo chứng từ gốc */}
          <Field label="Kèm theo chứng từ gốc" hint="Số lượng chứng từ đính kèm (hóa đơn, quyết định…)">
            <input type="number" min="0" style={inp} value={attachmentCount}
              onChange={(e) => setAttachmentCount(e.target.value)} placeholder="0" />
          </Field>
        </div>

        {/* Error */}
        {err && (
          <div style={{
            marginTop: 14, padding: '10px 13px',
            background: 'var(--red-50)', border: '1px solid var(--red-100)',
            borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5,
          }}>{err}</div>
        )}
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : 'Tạo phiếu'}
        </button>
      </div>
    </Modal>
  );
}
