/* Cấu hình lương — CRUD quy tắc lương + kéo thứ tự + danh sách ngân hàng. Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import {
  fetchSalaryRules, deleteSalaryRule, reorderSalaryRules,
  fetchBankFormats, deleteBankFormat,
} from '../../api/payroll';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import SalaryRuleForm from './SalaryRuleForm';
import BankFormatForm from './BankFormatForm';

const TYPE_LABEL = { fixed: 'Số cố định', formula: 'Công thức' };
const SUB_TABS = [['rules', 'Quy tắc lương'], ['banks', 'Ngân hàng']];

const segWrap = {
  display: 'inline-flex', gap: 0, background: 'var(--gray-100)',
  borderRadius: 8, padding: 3, marginBottom: 16,
};
const segBtn = (active) => ({
  padding: '7px 18px', borderRadius: 6, fontSize: 13, fontWeight: 600,
  border: 'none', cursor: 'pointer', transition: 'all .15s',
  background: active ? '#fff' : 'transparent',
  color: active ? 'var(--ink)' : 'var(--muted)',
  boxShadow: active ? '0 1px 3px rgba(0,0,0,.1)' : 'none',
});

export default function ConfigView() {
  const [tab, setTab] = useState('rules');

  const [rules, setRules] = useState(null);
  const [ruleForm, setRuleForm] = useState(null);
  const [ruleBusy, setRuleBusy] = useState(null);
  const [err, setErr] = useState(null);

  /* bank format state */
  const [banks, setBanks] = useState(null);
  const [bankForm, setBankForm] = useState(null);
  const [bankBusy, setBankBusy] = useState(null);

  /* drag state */
  const dragIdx = useRef(null);
  const [dragOver, setDragOver] = useState(null);

  const loadRules = () => {
    fetchSalaryRules({}).then(setRules).catch((e) => setErr(e.message));
  };
  const loadBanks = () => {
    fetchBankFormats().then(setBanks).catch((e) => setErr(e.message));
  };
  useEffect(() => { loadRules(); loadBanks(); }, []);

  const delRule = async (r) => {
    if (!confirm(`Xoá rule "${r.name}" (${r.code})?`)) return;
    setRuleBusy(r.id);
    try { await deleteSalaryRule(r.id); loadRules(); }
    catch (e) { alert('Xoá thất bại: ' + e.message); }
    finally { setRuleBusy(null); }
  };

  const delBank = async (b) => {
    if (!confirm(`Xoá ngân hàng "${b.name}" (${b.code})?`)) return;
    setBankBusy(b.id);
    try { await deleteBankFormat(b.id); loadBanks(); }
    catch (e) { alert('Xoá thất bại: ' + e.message); }
    finally { setBankBusy(null); }
  };

  /* ── Move up / down ── */
  const move = async (idx, dir) => {
    const next = [...rules];
    const target = idx + dir;
    if (target < 0 || target >= next.length) return;
    [next[idx], next[target]] = [next[target], next[idx]];
    setRules(next);
    try {
      await reorderSalaryRules(next.map((r) => r.id));
    } catch (e) {
      loadRules(); // rollback
    }
  };

  /* ── Drag & drop ── */
  const onDragStart = (idx) => { dragIdx.current = idx; };
  const onDragOver = (e, idx) => { e.preventDefault(); setDragOver(idx); };
  const onDragEnd = () => { setDragOver(null); dragIdx.current = null; };
  const onDrop = async (idx) => {
    const from = dragIdx.current;
    setDragOver(null);
    dragIdx.current = null;
    if (from === null || from === idx) return;
    const next = [...rules];
    const [moved] = next.splice(from, 1);
    next.splice(idx, 0, moved);
    setRules(next);
    try {
      await reorderSalaryRules(next.map((r) => r.id));
    } catch (e) {
      loadRules();
    }
  };

  if (err) return <ErrorState message={err} onRetry={() => { setErr(null); loadRules(); loadBanks(); }} />;
  if (!rules || !banks) return <LoadingState label="Đang tải cấu hình..." />;

  return (
    <>
      {/* ── Segment toggle ── */}
      <div style={segWrap}>
        {SUB_TABS.map(([id, l]) => (
          <button key={id} style={segBtn(tab === id)} onClick={() => setTab(id)}>{l}</button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════
          TAB: QUY TẮC LƯƠNG
          ════════════════════════════════════════════════════════ */}
      {tab === 'rules' && (
        <div className="card">
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Quy tắc lương (Salary Rules)</h3>
              <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Kéo hoặc dùng mũi tên để sắp xếp thứ tự tính lương</div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setRuleForm('new')}>
              <Icon name="plus" size={14} />Thêm rule
            </button>
          </div>
          {rules.length === 0 ? (
            <div style={{ padding: 28, textAlign: 'center' }}><EmptyState>Chưa có quy tắc lương.</EmptyState></div>
          ) : (
            <div className="tbl-wrap">
              <table className="tbl">
                <thead>
                  <tr>
                    <th style={{ width: 70 }}>Thứ tự</th>
                    <th>Mã</th>
                    <th>Tên</th>
                    <th>Loại tính</th>
                    <th>Giá trị / Công thức</th>
                    <th style={{ width: 120 }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((r, i) => (
                    <tr
                      key={r.id}
                      draggable
                      onDragStart={() => onDragStart(i)}
                      onDragOver={(e) => onDragOver(e, i)}
                      onDragEnd={onDragEnd}
                      onDrop={() => onDrop(i)}
                      style={{
                        cursor: 'grab',
                        background: dragOver === i ? 'var(--blue-50)' : undefined,
                        borderTop: dragOver === i ? '2px solid var(--blue-400)' : undefined,
                      }}
                    >
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <button
                            className="icon-btn"
                            title="Lên"
                            onClick={() => move(i, -1)}
                            disabled={i === 0}
                            style={{ padding: 2 }}
                          >
                            <Icon name="arrowUp" size={14} />
                          </button>
                          <button
                            className="icon-btn"
                            title="Xuống"
                            onClick={() => move(i, 1)}
                            disabled={i === rules.length - 1}
                            style={{ padding: 2 }}
                          >
                            <Icon name="arrowDown" size={14} />
                          </button>
                          <span className="muted" style={{ fontSize: 12, marginLeft: 4 }}>{i + 1}</span>
                        </div>
                      </td>
                      <td><code style={{ fontSize: 12.5 }}>{r.code}</code></td>
                      <td style={{ fontWeight: 600 }}>{r.name}</td>
                      <td>
                        <span style={{
                          display: 'inline-block', padding: '2px 8px', borderRadius: 4,
                          fontSize: 12, fontWeight: 600,
                          background: r.amount_type === 'formula' ? 'var(--blue-50)' : 'var(--green-50)',
                          color: r.amount_type === 'formula' ? 'var(--blue-600)' : 'var(--green-700)',
                        }}>
                          {TYPE_LABEL[r.amount_type] || r.amount_type}
                        </span>
                      </td>
                      <td className="muted" style={{ fontSize: 12.5, fontFamily: 'monospace', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {r.amount_type === 'fixed' ? (r.amount_fixed ? Number(r.amount_fixed).toLocaleString('vi') + ' ₫' : '—')
                          : r.amount_type === 'formula' ? (r.amount_formula || '—')
                          : '—'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button className="icon-btn" title="Sửa" onClick={() => setRuleForm(r)}>
                            <Icon name="edit" size={15} />
                          </button>
                          <button className="icon-btn" title="Xoá" onClick={() => delRule(r)} disabled={ruleBusy === r.id}>
                            <Icon name="trash" size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAB: NGÂN HÀNG
          ════════════════════════════════════════════════════════ */}
      {tab === 'banks' && (
        <div className="card">
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Ngân hàng (Bank Formats)</h3>
              <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Danh sách ngân hàng để chọn khi tạo lương</div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setBankForm('new')}>
              <Icon name="plus" size={14} />Thêm ngân hàng
            </button>
          </div>
          {banks.length === 0 ? (
            <div style={{ padding: 28, textAlign: 'center' }}><EmptyState>Chưa có ngân hàng nào.</EmptyState></div>
          ) : (
            <div className="tbl-wrap">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Mã</th>
                    <th>Tên ngân hàng</th>
                    <th style={{ width: 120 }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {banks.map((b) => (
                    <tr key={b.id}>
                      <td><code style={{ fontSize: 12.5 }}>{b.code}</code></td>
                      <td style={{ fontWeight: 600 }}>{b.name}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button className="icon-btn" title="Sửa" onClick={() => setBankForm(b)}>
                            <Icon name="edit" size={15} />
                          </button>
                          <button className="icon-btn" title="Xoá" onClick={() => delBank(b)} disabled={bankBusy === b.id}>
                            <Icon name="trash" size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Modals ── */}
      {ruleForm && (
        <SalaryRuleForm
          item={ruleForm === 'new' ? null : ruleForm}
          structureId={null}
          nextSequence={rules ? Math.max(...rules.map((r) => r.sequence || 0), 0) + 10 : 10}
          onClose={() => setRuleForm(null)}
          onSaved={() => { setRuleForm(null); loadRules(); }}
        />
      )}
      {bankForm && (
        <BankFormatForm
          item={bankForm === 'new' ? null : bankForm}
          onClose={() => setBankForm(null)}
          onSaved={() => { setBankForm(null); loadBanks(); }}
        />
      )}
    </>
  );
}
