/* ============================================================
   CRUD Quỹ & Mục thu/chi — Tab "Cấu hình" trong Finance.
   Chỉ hiển thị với role Kế toán / BGĐ.
   ============================================================ */
import { useState, useCallback } from 'react';
import Icon from '../../components/Icon';
import {
  createFund, updateFund, deleteFund,
  createCategory, updateCategory, deleteCategory,
} from '../../api/finance';

/* ── Styles ───────────────────────────────────────────────────────────── */
const inp = {
  width: '100%', padding: '8px 12px', borderRadius: 8,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const sel = { ...inp, cursor: 'pointer' };
const cellPad = { padding: '10px 14px', verticalAlign: 'middle' };
const monoR = { ...cellPad, textAlign: 'right', fontFamily: 'var(--mono)', fontWeight: 600 };

/* ── Utility: format VND compact ─────────────────────────────────────── */
const fmtVND = (n) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(n || 0);

/* ══════════════════════════════════════════════════════════════════════ */
export default function FundCategoryManager({ ctx, onReloadCtx }) {
  const [sub, setSub] = useState('funds'); // 'funds' | 'categories'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 8 }}>
        <SubTab active={sub === 'funds'} onClick={() => setSub('funds')}>
          <Icon name="wallet" size={15} /> Quỹ tiền
        </SubTab>
        <SubTab active={sub === 'categories'} onClick={() => setSub('categories')}>
          <Icon name="list" size={15} /> Mục thu/chi
        </SubTab>
      </div>

      {sub === 'funds'
        ? <FundsSection ctx={ctx} onReload={onReloadCtx} />
        : <CategoriesSection ctx={ctx} onReload={onReloadCtx} />}
    </div>
  );
}

function SubTab({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: '8px 18px', borderRadius: 10, fontSize: 13, fontWeight: 600,
      fontFamily: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
      border: active ? '2px solid var(--primary)' : '1px solid var(--border)',
      background: active ? 'var(--primary-50, #eff6ff)' : '#fff',
      color: active ? 'var(--primary)' : 'var(--muted)',
    }}>
      {children}
    </button>
  );
}

/* ══════════════════════════════════════════════════════════════════════ */
/* ── FUNDS SECTION ──────────────────────────────────────────────────── */
/* ══════════════════════════════════════════════════════════════════════ */

function FundsSection({ ctx, onReload }) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  // form state
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [fundType, setFundType] = useState('cash');
  const [deptId, setDeptId] = useState('');
  const [opening, setOpening] = useState('');

  const resetForm = () => {
    setName(''); setCode(''); setFundType('cash'); setDeptId(''); setOpening('');
    setEditId(null); setShowForm(false); setErr(null);
  };

  const startEdit = (f) => {
    setName(f.name); setCode(f.code); setFundType(f.fundType);
    setDeptId(f.departmentId || ''); setOpening(String(f.openingBalance || 0));
    setEditId(f.id); setShowForm(true); setErr(null);
  };

  const submit = async () => {
    setErr(null);
    if (!name.trim()) return setErr('Tên quỹ không được để trống.');
    if (!code.trim()) return setErr('Mã quỹ không được để trống.');
    setBusy(true);
    try {
      const payload = {
        name: name.trim(), code: code.trim(), fundType,
        departmentId: deptId ? Number(deptId) : null,
        openingBalance: Number(opening) || 0,
      };
      if (editId) {
        await updateFund(editId, payload);
      } else {
        await createFund(payload);
      }
      resetForm();
      onReload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async (f) => {
    if (!window.confirm(`Ẩn quỹ "${f.name}"? Quỹ sẽ không hiển thị nữa nhưng dữ liệu vẫn giữ.`)) return;
    try {
      await deleteFund(f.id);
      onReload();
    } catch (e) {
      window.alert(e.message);
    }
  };

  return (
    <div className="card">
      <div className="card-head" style={{ gap: 10 }}>
        <h3 style={{ marginRight: 'auto' }}>Danh sách Quỹ tiền</h3>
        <button className="btn btn-primary btn-sm" onClick={() => { resetForm(); setShowForm(true); }}>
          <Icon name="plus" size={15} /> Thêm quỹ
        </button>
      </div>

      {/* Inline form */}
      {showForm && (
        <div style={{ padding: '16px 20px', background: 'var(--bg-subtle, #fafbfc)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px 14px' }}>
            <label style={lbl}>
              Tên quỹ *
              <input style={inp} value={name} onChange={e => setName(e.target.value)}
                placeholder="VD: Quỹ tiền mặt — MKT" />
            </label>
            <label style={lbl}>
              Mã quỹ *
              <input style={inp} value={code} onChange={e => setCode(e.target.value)}
                placeholder="VD: MKT_CASH" />
            </label>
            <label style={lbl}>
              Loại quỹ
              <select style={sel} value={fundType} onChange={e => setFundType(e.target.value)}>
                <option value="cash">Tiền mặt</option>
                <option value="bank">Ngân hàng</option>
              </select>
            </label>
            <label style={lbl}>
              Phòng ban
              <select style={sel} value={deptId} onChange={e => setDeptId(e.target.value)}>
                <option value="">— Quỹ tổng công ty —</option>
                {ctx.departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </label>
            <label style={lbl}>
              Số dư đầu kỳ (VND)
              <input type="number" style={inp} value={opening} onChange={e => setOpening(e.target.value)}
                placeholder="0" />
            </label>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={submit} disabled={busy}>
                <Icon name="checkCircle" size={14} /> {editId ? 'Cập nhật' : 'Tạo mới'}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={resetForm} disabled={busy}>Huỷ</button>
            </div>
          </div>
          {err && <div style={errBox}>{err}</div>}
        </div>
      )}

      {/* Table */}
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th style={cellPad}>Tên quỹ</th>
            <th style={cellPad}>Mã</th>
            <th style={cellPad}>Loại</th>
            <th style={cellPad}>Phòng ban</th>
            <th style={{ ...cellPad, textAlign: 'right' }}>Số dư đầu</th>
            <th style={{ ...cellPad, textAlign: 'right' }}>Số dư hiện tại</th>
            <th style={{ ...cellPad, textAlign: 'right', width: 100 }}>Thao tác</th>
          </tr></thead>
          <tbody>
            {ctx.funds.map(f => (
              <tr key={f.id}>
                <td style={cellPad}><strong>{f.name}</strong></td>
                <td style={cellPad}><code style={{ fontSize: 12, color: 'var(--muted)' }}>{f.code}</code></td>
                <td style={cellPad}>{f.fundType === 'cash' ? '💵 Tiền mặt' : '🏦 Ngân hàng'}</td>
                <td style={cellPad} className="muted">{f.departmentName || 'Tổng công ty'}</td>
                <td style={monoR}>{fmtVND(f.openingBalance)}</td>
                <td style={{ ...monoR, color: f.currentBalance < 0 ? 'var(--red-600)' : 'var(--green-600, #16a34a)' }}>
                  {fmtVND(f.currentBalance)}
                </td>
                <td style={{ ...cellPad, textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                    <button className="btn btn-ghost btn-sm" title="Sửa" onClick={() => startEdit(f)}
                      style={{ padding: '5px 7px', lineHeight: 0 }}>
                      <Icon name="edit" size={14} />
                    </button>
                    <button className="btn btn-ghost btn-sm" title="Ẩn" onClick={() => doDelete(f)}
                      style={{ padding: '5px 7px', lineHeight: 0, color: 'var(--red-600)' }}>
                      <Icon name="trash" size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {ctx.funds.length === 0 && (
        <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
          Chưa có quỹ nào. Nhấn "Thêm quỹ" để bắt đầu.
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════ */
/* ── CATEGORIES SECTION ─────────────────────────────────────────────── */
/* ══════════════════════════════════════════════════════════════════════ */

function CategoriesSection({ ctx, onReload }) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [filterType, setFilterType] = useState('');

  // form state
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [catType, setCatType] = useState('income');

  const allCats = [...(ctx.categories.income || []), ...(ctx.categories.expense || [])];
  const displayed = filterType
    ? allCats.filter(c => {
        if (filterType === 'income') return ctx.categories.income.some(x => x.id === c.id);
        return ctx.categories.expense.some(x => x.id === c.id);
      })
    : allCats;

  const resetForm = () => {
    setName(''); setCode(''); setCatType('income');
    setEditId(null); setShowForm(false); setErr(null);
  };

  const startEdit = (c) => {
    setName(c.name); setCode(c.code);
    setCatType(ctx.categories.income.some(x => x.id === c.id) ? 'income' : 'expense');
    setEditId(c.id); setShowForm(true); setErr(null);
  };

  const submit = async () => {
    setErr(null);
    if (!name.trim()) return setErr('Tên mục không được để trống.');
    if (!code.trim()) return setErr('Mã mục không được để trống.');
    setBusy(true);
    try {
      const payload = { name: name.trim(), code: code.trim(), categoryType: catType };
      if (editId) {
        await updateCategory(editId, payload);
      } else {
        await createCategory(payload);
      }
      resetForm();
      onReload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async (c) => {
    if (!window.confirm(`Ẩn mục "${c.name}"? Mục sẽ không hiển thị trong form tạo phiếu nữa.`)) return;
    try {
      await deleteCategory(c.id);
      onReload();
    } catch (e) {
      window.alert(e.message);
    }
  };

  return (
    <div className="card">
      <div className="card-head" style={{ gap: 10, flexWrap: 'wrap' }}>
        <h3 style={{ marginRight: 'auto' }}>Danh sách Mục thu/chi</h3>
        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border-strong)', fontFamily: 'inherit', fontSize: 12.5 }}>
          <option value="">Tất cả loại</option>
          <option value="income">Thu</option>
          <option value="expense">Chi</option>
        </select>
        <button className="btn btn-primary btn-sm" onClick={() => { resetForm(); setShowForm(true); }}>
          <Icon name="plus" size={15} /> Thêm mục
        </button>
      </div>

      {/* Inline form */}
      {showForm && (
        <div style={{ padding: '16px 20px', background: 'var(--bg-subtle, #fafbfc)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '12px 14px', alignItems: 'end' }}>
            <label style={lbl}>
              Tên mục *
              <input style={inp} value={name} onChange={e => setName(e.target.value)}
                placeholder="VD: Chạy ads" />
            </label>
            <label style={lbl}>
              Mã mục *
              <input style={inp} value={code} onChange={e => setCode(e.target.value)}
                placeholder="VD: ADS" />
            </label>
            <label style={lbl}>
              Loại
              <select style={sel} value={catType} onChange={e => setCatType(e.target.value)}>
                <option value="income">Thu</option>
                <option value="expense">Chi</option>
              </select>
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={submit} disabled={busy}>
                <Icon name="checkCircle" size={14} /> {editId ? 'Cập nhật' : 'Tạo mới'}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={resetForm} disabled={busy}>Huỷ</button>
            </div>
          </div>
          {err && <div style={errBox}>{err}</div>}
        </div>
      )}

      {/* Table */}
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th style={cellPad}>Tên mục</th>
            <th style={cellPad}>Mã</th>
            <th style={cellPad}>Loại</th>
            <th style={{ ...cellPad, textAlign: 'right', width: 100 }}>Thao tác</th>
          </tr></thead>
          <tbody>
            {displayed.map(c => {
              const isIncome = ctx.categories.income.some(x => x.id === c.id);
              return (
                <tr key={c.id}>
                  <td style={cellPad}><strong>{c.name}</strong></td>
                  <td style={cellPad}><code style={{ fontSize: 12, color: 'var(--muted)' }}>{c.code}</code></td>
                  <td style={cellPad}>
                    <span style={{
                      display: 'inline-block', padding: '3px 10px', borderRadius: 6, fontSize: 11.5, fontWeight: 700,
                      background: isIncome ? '#dcfce7' : 'var(--red-50)',
                      color: isIncome ? '#16a34a' : 'var(--red-600)',
                    }}>
                      {isIncome ? 'Thu' : 'Chi'}
                    </span>
                  </td>
                  <td style={{ ...cellPad, textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                      <button className="btn btn-ghost btn-sm" title="Sửa" onClick={() => startEdit(c)}
                        style={{ padding: '5px 7px', lineHeight: 0 }}>
                        <Icon name="edit" size={14} />
                      </button>
                      <button className="btn btn-ghost btn-sm" title="Ẩn" onClick={() => doDelete(c)}
                        style={{ padding: '5px 7px', lineHeight: 0, color: 'var(--red-600)' }}>
                        <Icon name="trash" size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {displayed.length === 0 && (
        <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
          Chưa có mục nào{filterType ? ` loại "${filterType === 'income' ? 'Thu' : 'Chi'}"` : ''}. Nhấn "Thêm mục" để tạo.
        </div>
      )}
    </div>
  );
}

/* ── Shared styles ──────────────────────────────────────────────────── */
const lbl = { display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11.5, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' };
const errBox = { marginTop: 10, padding: '8px 12px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 8, color: 'var(--red-700)', fontSize: 12.5 };
