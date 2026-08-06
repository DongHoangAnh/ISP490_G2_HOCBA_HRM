/* Form tạo/sửa salary rule — Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import { createSalaryRule, updateSalaryRule, fetchLookupSources } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

const AMOUNT_TYPES = [
  ['fixed', 'Số tiền cố định'],
  ['formula', 'Công thức tính toán'],
  ['lookup', 'Tra bảng biểu / Định mức'],
];

/* Vietnamese diacritics → ASCII slug */
const toSlug = (str) => {
  const map = {
    'à':'a','á':'a','ả':'a','ã':'a','ạ':'a',
    'ă':'a','ắ':'a','ằ':'a','ẳ':'a','ẵ':'a','ặ':'a',
    'â':'a','ấ':'a','ầ':'a','ẩ':'a','ẫ':'a','ậ':'a',
    'đ':'d',
    'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e',
    'ê':'e','ế':'e','ề':'e','ể':'e','ễ':'e','ệ':'e',
    'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
    'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o',
    'ô':'o','ố':'o','ồ':'o','ổ':'o','ỗ':'o','ộ':'o',
    'ơ':'o','ớ':'o','ờ':'o','ở':'o','ỡ':'o','ợ':'o',
    'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u',
    'ư':'u','ứ':'u','ừ':'u','ử':'u','ữ':'u','ự':'u',
    'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y',
  };
  return str
    .toLowerCase()
    .split('')
    .map((c) => map[c] || c)
    .join('')
    .replace(/[^a-z0-9\s_]/g, '')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
};

export default function SalaryRuleForm({ item, structureId, nextSequence = 10, onClose, onSaved }) {
  const isEdit = !!item;
  const [form, setForm] = useState({
    code: item?.code || '',
    name: item?.name || '',
    sequence: item?.sequence ?? nextSequence,
    amount_type: item?.amount_type || 'fixed',
    amount_fixed: item?.amount_fixed ?? '',
    amount_formula: item?.amount_formula || '',
    lookup_source: item?.lookup_source || '',
    lookup_field: item?.lookup_field || '',
    note: item?.note || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [lookupSources, setLookupSources] = useState(null);

  useEffect(() => {
    fetchLookupSources().then(setLookupSources).catch(() => setLookupSources({}));
  }, []);

  const set = (k, v) => {
    setForm((f) => {
      const next = { ...f, [k]: v };
      /* Auto-gen slug from name */
      if (k === 'name' && !isEdit) {
        next.code = toSlug(v);
      }
      return next;
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const payload = {
        ...form,
        sequence: Number(form.sequence),
        amount_fixed: Number(form.amount_fixed || 0),
      };
      if (isEdit) {
        await updateSalaryRule(item.id, payload);
      } else {
        await createSalaryRule(payload);
      }
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Lưu thất bại.');
    } finally {
      setBusy(false);
    }
  };

  const inp = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14 };
  const ta = { ...inp, minHeight: 80, fontFamily: 'monospace', fontSize: 13 };
  const hint = { fontSize: 12, color: 'var(--muted)', marginTop: 4 };

  const taRef = useRef(null);

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{isEdit ? 'Sửa thành phần lương' : 'Thêm thành phần lương'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? `Đang sửa: ${item.name}` : 'Thêm thành phần lương mới vào cấu trúc'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px', maxHeight: '70vh', overflowY: 'auto' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tên</label>
          <input type="text" style={inp} value={form.name} onChange={(e) => set('name', e.target.value)}
            placeholder="VD: Lương thời gian" required />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Mã (tự sinh từ tên)</label>
          <input type="text" style={{ ...inp, background: 'var(--gray-50)', color: 'var(--muted)' }}
            value={form.code} readOnly />
          <div style={hint}>Tự động tạo slug từ tên: không dấu, viết thường, dấu cách → _</div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Loại tính</label>
          <select className="sel" style={{ width: '100%' }} value={form.amount_type} onChange={(e) => set('amount_type', e.target.value)}>
            {AMOUNT_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>

        {form.amount_type === 'fixed' && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Số tiền cố định (VNĐ)</label>
            <input type="number" style={inp} value={form.amount_fixed} onChange={(e) => set('amount_fixed', e.target.value)} />
          </div>
        )}

        {form.amount_type === 'formula' && (
          <FormulaSection form={form} set={set} ta={ta} hint={hint} taRef={taRef} />
        )}

        {form.amount_type === 'lookup' && lookupSources && (
          <LookupSection form={form} set={set} lookupSources={lookupSources} />
        )}

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Ghi chú</label>
          <input type="text" style={inp} value={form.note} onChange={(e) => set('note', e.target.value)}
            placeholder="Mô tả ngắn (tuỳ chọn)" />
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

/* ── Formula helper data ─────────────────────────────────── */
const FUNC_BUTTONS = [
  { label: 'IF( , , )',   snippet: 'IF( , , )' },
  { label: 'SUM( , )',    snippet: 'SUM( , )' },
  { label: 'MAX( , )',    snippet: 'MAX( , )' },
  { label: 'MIN( , )',    snippet: 'MIN( , )' },
  { label: 'ABS( )',      snippet: 'ABS( )' },
  { label: 'ROUND( , )',   snippet: 'ROUND( , )' },
];

const FUNC_HELP = [
  { name: 'Mã rule',              desc: 'Ghi trực tiếp mã slug của rule để lấy giá trị đã tính.',                          example: 'luong_thoi_gian * 0.08' },
  { name: 'IF(đk, đúng, sai)',    desc: 'Nếu điều kiện đúng trả về giá trị đúng, ngược lại trả về giá trị sai.',          example: 'IF(tong_thu_nhap > 0, tong_thu_nhap - khau_tru_nv, 0)' },
  { name: 'SUM(a, b)',            desc: 'Cộng tất cả rule từ mã a đến mã b theo thứ tự (bao gồm cả a và b).',             example: 'SUM(luong_thoi_gian, thuong_khac)' },
  { name: 'MAX(a, b)',            desc: 'Trả về giá trị lớn nhất trong các tham số.',                                       example: 'MAX(tong_thu_nhap - khau_tru_nv, 0)' },
  { name: 'MIN(a, b)',            desc: 'Trả về giá trị nhỏ nhất trong các tham số.',                                       example: 'MIN(luong_thoi_gian, 5000000)' },
  { name: 'ABS(x)',               desc: 'Trả về giá trị tuyệt đối (bỏ dấu âm).',                                           example: 'ABS(bhxh_8_nv)' },
  { name: 'ROUND(x, y)',           desc: 'Làm tròn số. y = 1: làm tròn lên, y = 0: làm tròn xuống.',                          example: 'ROUND(luong_thoi_gian * 0.08, 1)' },
];

/* ── FormulaSection component ─────────────────────────────── */
function FormulaSection({ form, set, ta, hint, taRef }) {
  const [showHelp, setShowHelp] = useState(false);

  const insertSnippet = (snippet) => {
    const el = taRef.current;
    if (!el) {
      set('amount_formula', ((form.amount_formula || '') + ' ' + snippet).trim());
      return;
    }
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const cur = form.amount_formula || '';
    const next = cur.substring(0, start) + snippet + cur.substring(end);
    set('amount_formula', next);
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + snippet.length;
      el.setSelectionRange(pos, pos);
    });
  };

  const btnStyle = {
    padding: '3px 10px', borderRadius: 6,
    border: '1px solid var(--border)', background: 'var(--gray-50)',
    fontSize: 12, fontFamily: 'monospace', cursor: 'pointer',
    color: 'var(--text)', lineHeight: 1.6,
  };

  const helpBtnStyle = {
    background: 'none', border: 'none', color: 'var(--blue-600)',
    fontSize: 12, cursor: 'pointer', padding: '2px 0',
    display: 'flex', alignItems: 'center', gap: 4,
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Công thức</label>
      <textarea
        ref={taRef}
        style={ta}
        value={form.amount_formula}
        onChange={(e) => set('amount_formula', e.target.value)}
        placeholder="VD: SUM(luong_thoi_gian, thuong_khac) hoặc luong_thoi_gian * 0.08"
      />
      <div style={hint}>
        VD: <code>IF(tong_thu_nhap {'>'} 0, tong_thu_nhap - SUM(bhxh_8_nv, bhtn_1_nv), 0)</code>
      </div>

      {/* Quick-insert buttons */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
        {FUNC_BUTTONS.map((f) => (
          <button key={f.label} type="button" style={btnStyle} onClick={() => insertSnippet(f.snippet)}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Help toggle */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 6 }}>
        <button type="button" style={helpBtnStyle} onClick={() => setShowHelp((v) => !v)}>
          <Icon name="help-circle" size={14} />
          {showHelp ? 'Ẩn hướng dẫn' : 'Hướng dẫn hàm'}
        </button>
      </div>

      {/* Help table */}
      {showHelp && (
        <div style={{
          marginTop: 6, border: '1px solid var(--border)', borderRadius: 8,
          overflow: 'hidden', fontSize: 12.5,
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--gray-50)' }}>
                <th style={thStyle}>Hàm</th>
                <th style={thStyle}>Mô tả &amp; cách dùng</th>
              </tr>
            </thead>
            <tbody>
              {FUNC_HELP.map((h) => (
                <tr key={h.name}>
                  <td style={{ ...tdStyle, fontWeight: 600, whiteSpace: 'nowrap', fontFamily: 'monospace' }}>{h.name}</td>
                  <td style={tdStyle}>
                    {h.desc}
                    <br />
                    <code style={{ color: 'var(--blue-700)', fontSize: 11.5 }}>{h.example}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '6px 10px', fontSize: 11.5, color: 'var(--muted)', borderTop: '1px solid var(--border)' }}>
            Toán tử hỗ trợ: <code>+ - * / {'>'} {'<'} {'>'}= {'<'}= == !=</code>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── SearchSelect: dropdown có ô tìm kiếm ────────────────── */
function SearchSelect({ value, options, onChange, placeholder, disabled }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const boxRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const h = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [open]);

  const current = options.find(([v]) => v === value);
  const ql = q.trim().toLowerCase();
  const filtered = ql
    ? options.filter(([v, l]) => (l + ' ' + v).toLowerCase().includes(ql))
    : options;

  const box = {
    width: '100%', padding: '9px 12px', borderRadius: 8,
    border: '1px solid var(--border)', fontSize: 14, background: disabled ? 'var(--gray-50)' : '#fff',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
    cursor: disabled ? 'not-allowed' : 'pointer', color: current ? 'var(--text)' : 'var(--muted)',
  };

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      <div style={box} onClick={() => { if (!disabled) { setOpen((o) => !o); setQ(''); } }}>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {current ? current[1] : (placeholder || '-- Chọn --')}
        </span>
        <span style={{ fontSize: 10, color: 'var(--muted)' }}>▾</span>
      </div>
      {open && !disabled && (
        <div style={{
          position: 'absolute', top: '105%', left: 0, right: 0, zIndex: 60,
          background: '#fff', border: '1px solid var(--border)', borderRadius: 8,
          boxShadow: '0 8px 24px rgba(0,0,0,.12)', overflow: 'hidden',
        }}>
          <div style={{ padding: 8, borderBottom: '1px solid var(--border)' }}>
            <input autoFocus value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Tìm nhanh..."
              style={{ width: '100%', padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13 }} />
          </div>
          <div style={{ maxHeight: 240, overflowY: 'auto' }}>
            {filtered.length === 0 && (
              <div style={{ padding: '10px 12px', fontSize: 13, color: 'var(--muted)' }}>Không có kết quả</div>
            )}
            {filtered.map(([v, l]) => (
              <div key={v} onClick={() => { onChange(v); setOpen(false); }}
                style={{
                  display: 'flex', alignItems: 'baseline', gap: 8,
                  padding: '8px 12px', fontSize: 13.5, cursor: 'pointer',
                  background: v === value ? 'var(--red-50,#fef2f2)' : '#fff',
                  fontWeight: v === value ? 600 : 400,
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#f3f4f6'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = v === value ? 'var(--red-50,#fef2f2)' : '#fff'; }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l}</span>
                <span style={{ marginLeft: 'auto', flexShrink: 0, color: 'var(--muted)', fontSize: 11, fontFamily: 'monospace' }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── LookupSection component ─────────────────────────────── */
function LookupSection({ form, set, lookupSources }) {
  const sourceOptions = lookupSources
    ? Object.entries(lookupSources).map(([key, src]) => [key, src.label])
    : [];

  const fieldOptions = (form.lookup_source && lookupSources && lookupSources[form.lookup_source])
    ? Object.entries(lookupSources[form.lookup_source].fields).map(
        ([key, f]) => [key, f.label]
      )
    : [];

  const handleSourceChange = (val) => {
    set('lookup_source', val);
    set('lookup_field', '');
  };

  const hint = { fontSize: 12, color: 'var(--muted)', marginTop: 4 };

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>
          Nguồn dữ liệu
        </label>
        <SearchSelect value={form.lookup_source} options={sourceOptions}
          onChange={handleSourceChange} placeholder="-- Chọn nguồn --" />
        <div style={hint}>Chọn module/bảng dữ liệu để tra cứu — gõ để tìm nhanh.</div>
      </div>

      {form.lookup_source && (
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>
            Trường tra cứu
          </label>
          <SearchSelect value={form.lookup_field} options={fieldOptions}
            onChange={(v) => set('lookup_field', v)} placeholder="-- Chọn trường --" />
          <div style={hint}>
            Trường số của model đã chọn — gõ để tìm nhanh. Nguồn theo kỳ (có ngày) sẽ
            tổng hợp trong kỳ lương; nguồn không có ngày lấy giá trị hiện tại.
          </div>
        </div>
      )}

      {form.lookup_source && form.lookup_field && (
        <div style={{
          padding: '10px 14px', borderRadius: 8,
          background: '#eff6ff', border: '1px solid #bfdbfe',
          fontSize: 12.5, color: '#1e40af',
        }}>
          <strong>Gợi ý:</strong> Giá trị lookup sẽ được lưu vào{' '}
          <code>rules['{form.code || 'ma_rule'}']</code>.
          Các rule tiếp theo có thể tham chiếu bằng mã rule này trong công thức.
          <br />
          VD: <code>{form.code || 'so_cong'} * don_gia_gio</code>
        </div>
      )}
    </div>
  );
}

const thStyle = { textAlign: 'left', padding: '8px 10px', borderBottom: '1px solid var(--border)' };
const tdStyle = { padding: '7px 10px', borderBottom: '1px solid var(--border)', verticalAlign: 'top' };
