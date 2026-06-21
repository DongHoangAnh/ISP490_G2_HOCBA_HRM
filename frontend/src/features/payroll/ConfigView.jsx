/* Cấu hình lương — CRUD quy tắc lương + kéo thứ tự + danh sách ngân hàng + mẫu email. Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import {
  fetchSalaryRules, deleteSalaryRule, reorderSalaryRules,
  fetchBankFormats, deleteBankFormat,
  fetchMailTemplate, saveMailTemplate,
} from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import SalaryRuleForm from './SalaryRuleForm';
import BankFormatForm from './BankFormatForm';
import TblWrap from '../../components/TblWrap';

const TYPE_LABEL = { fixed: 'Số cố định', formula: 'Công thức' };
const SUB_TABS = [['rules', 'Quy tắc lương'], ['banks', 'Ngân hàng'], ['mail', 'Mẫu email']];

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

  /* mail template state */
  const [mailSubject, setMailSubject] = useState('');
  const [mailBody, setMailBody] = useState('');
  const [mailLoaded, setMailLoaded] = useState(false);
  const [mailSaving, setMailSaving] = useState(false);
  const [mailMsg, setMailMsg] = useState('');
  const [mailPreview, setMailPreview] = useState(false);

  /* drag state */
  const dragIdx = useRef(null);
  const [dragOver, setDragOver] = useState(null);

  const loadRules = () => {
    fetchSalaryRules({}).then(setRules).catch((e) => setErr(e.message));
  };
  const loadBanks = () => {
    fetchBankFormats().then(setBanks).catch((e) => setErr(e.message));
  };
  const loadMailTpl = () => {
    fetchMailTemplate().then((d) => {
      setMailSubject(d.subject || '');
      setMailBody(d.body || '');
      setMailLoaded(true);
    }).catch(() => setMailLoaded(true));
  };
  useEffect(() => { loadRules(); loadBanks(); loadMailTpl(); }, []);

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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* ── Segment toggle ── */}
      <div style={{ ...segWrap, flexShrink: 0 }}>
        {SUB_TABS.map(([id, l]) => (
          <button key={id} style={segBtn(tab === id)} onClick={() => setTab(id)}>{l}</button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════
          TAB: QUY TẮC LƯƠNG
          ════════════════════════════════════════════════════════ */}
      {tab === 'rules' && (
        <div style={{
          flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
          border: '1px solid #e5e7eb', borderRadius: 10,
          background: '#fff', overflow: 'hidden',
        }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Quy tắc lương (Salary Rules)</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>Kéo hoặc dùng mũi tên để sắp xếp thứ tự tính lương</div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setRuleForm('new')}>
              <Icon name="plus" size={14} />Thêm rule
            </button>
          </div>
          {rules.length === 0 ? (
            <div style={{ padding: 28, textAlign: 'center' }}><EmptyState>Chưa có quy tắc lương.</EmptyState></div>
          ) : (
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}>
            <TblWrap id="cfg-rules">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th style={{ width: 70 }}>Thứ tự</th>
                      <th>Mã</th>
                      <th>Tên</th>
                      <th>Loại tính</th>
                      <th>Giá trị / Công thức</th>
                      <th style={{ width: 100 }}>Thao tác</th>
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
                          background: dragOver === i ? 'var(--blue-50)' : '#fff',
                          borderTop: dragOver === i ? '2px solid var(--blue-400)' : undefined,
                        }}
                        onMouseEnter={(e) => { if (dragOver == null) e.currentTarget.style.background = '#f8fafc'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = dragOver === i ? 'var(--blue-50)' : '#fff'; }}
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
                            <span style={{ fontSize: 12, color: '#6b7280', marginLeft: 4 }}>{i + 1}</span>
                          </div>
                        </td>
                        <td style={{ fontSize: 12.5, fontFamily: 'monospace' }}>{r.code}</td>
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
                        <td style={{ fontSize: 12.5, fontFamily: 'monospace', color: '#6b7280' }}>
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
              </TblWrap>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAB: NGÂN HÀNG
          ════════════════════════════════════════════════════════ */}
      {tab === 'banks' && (
        <div style={{
          flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
          border: '1px solid #e5e7eb', borderRadius: 10,
          background: '#fff', overflow: 'hidden',
        }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Ngân hàng (Bank Formats)</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>Danh sách ngân hàng để chọn khi tạo lương</div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setBankForm('new')}>
              <Icon name="plus" size={14} />Thêm ngân hàng
            </button>
          </div>
          {banks.length === 0 ? (
            <div style={{ padding: 28, textAlign: 'center' }}><EmptyState>Chưa có ngân hàng nào.</EmptyState></div>
          ) : (
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}>
            <TblWrap id="cfg-banks">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Mã</th>
                      <th>Tên ngân hàng</th>
                      <th style={{ width: 100 }}>Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {banks.map((b) => (
                      <tr key={b.id}
                        style={{ background: '#fff' }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; }}
                      >
                        <td style={{ fontSize: 12.5, fontFamily: 'monospace' }}>{b.code}</td>
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
              </TblWrap>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAB: MẪU EMAIL
          ════════════════════════════════════════════════════════ */}
      {tab === 'mail' && (
        <div style={{
          flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
          border: '1px solid #e5e7eb', borderRadius: 10,
          background: '#fff', overflow: 'hidden',
        }}>
          {/* Header with buttons */}
          <div style={{
            padding: '14px 20px', borderBottom: '1px solid #e5e7eb', flexShrink: 0,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Mẫu email gửi phiếu lương</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>
                Tuỳ chỉnh nội dung email gửi cho nhân viên khi xác nhận bảng lương
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setMailPreview(true)}>
                <Icon name="eye" size={14} />Xem trước
              </button>
              <button
                className="btn btn-primary btn-sm"
                disabled={mailSaving}
                onClick={async () => {
                  setMailSaving(true);
                  setMailMsg('');
                  try {
                    await saveMailTemplate({ subject: mailSubject, body: mailBody });
                    setMailMsg('Đã lưu thành công!');
                  } catch (e) {
                    setMailMsg('Lỗi: ' + e.message);
                  } finally {
                    setMailSaving(false);
                  }
                }}
              >
                <Icon name="check" size={14} />
                {mailSaving ? 'Đang lưu...' : 'Lưu mẫu email'}
              </button>
              {mailMsg && (
                <span style={{
                  fontSize: 12.5, fontWeight: 600, whiteSpace: 'nowrap',
                  color: mailMsg.startsWith('Lỗi') ? '#dc2626' : '#16a34a',
                }}>{mailMsg}</span>
              )}
            </div>
          </div>

          {!mailLoaded ? (
            <LoadingState label="Đang tải mẫu email..." />
          ) : (
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '16px 20px' }}>
              {/* Placeholders guide */}
              <div style={{
                padding: '10px 14px', marginBottom: 16, borderRadius: 8,
                background: '#eff6ff', border: '1px solid #bfdbfe', fontSize: 12.5, color: '#1e40af',
              }}>
                <strong>Biến có thể dùng:</strong>{' '}
                <code>{'{employee_name}'}</code> — Tên nhân viên, {' '}
                <code>{'{month}'}</code> — Tháng, {' '}
                <code>{'{year}'}</code> — Năm, {' '}
                <code>{'{gross}'}</code> — Tổng thu nhập, {' '}
                <code>{'{net}'}</code> — Thực lĩnh, {' '}
                <code>{'{view_url}'}</code> — Link xem phiếu lương
              </div>

              {/* Subject */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>
                  Tiêu đề email (Subject)
                </label>
                <input
                  type="text"
                  className="inp"
                  value={mailSubject}
                  onChange={(e) => { setMailSubject(e.target.value); setMailMsg(''); }}
                  placeholder="Bảng lương tháng {month}/{year} — {employee_name}"
                  style={{ width: '100%' }}
                />
              </div>

              {/* Body */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>
                  Nội dung email (HTML)
                </label>
                <textarea
                  className="inp"
                  value={mailBody}
                  onChange={(e) => { setMailBody(e.target.value); setMailMsg(''); }}
                  rows={14}
                  style={{
                    width: '100%', fontFamily: 'monospace', fontSize: 12.5,
                    lineHeight: 1.5, resize: 'vertical',
                  }}
                  placeholder="<div>Nội dung email HTML...</div>"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Preview modal ── */}
      {mailPreview && (
        <Modal onClose={() => setMailPreview(false)} lg>
          <div className="modal-head">
            <h3>Xem trước email</h3>
            <button className="modal-x" onClick={() => setMailPreview(false)}>✕</button>
          </div>
          <div style={{ padding: 20 }}>
            <div style={{
              fontSize: 13, color: '#6b7280', marginBottom: 12,
              padding: '8px 12px', background: '#f9fafb', borderRadius: 6,
            }}>
              <strong>Subject:</strong>{' '}
              {mailSubject
                .replace(/\{employee_name\}/g, 'Nguyễn Văn A')
                .replace(/\{month\}/g, '06')
                .replace(/\{year\}/g, '2026')
                .replace(/\{gross\}/g, '15,000,000')
                .replace(/\{net\}/g, '12,500,000')
                .replace(/\{view_url\}/g, '#')}
            </div>
            <div style={{
              border: '1px solid #e5e7eb', borderRadius: 8, padding: 16,
              background: '#fff', minHeight: 120, fontSize: 13,
            }}>
              <div
                dangerouslySetInnerHTML={{
                  __html: mailBody
                    .replace(/\{employee_name\}/g, 'Nguyễn Văn A')
                    .replace(/\{month\}/g, '06')
                    .replace(/\{year\}/g, '2026')
                    .replace(/\{gross\}/g, '15,000,000')
                    .replace(/\{net\}/g, '12,500,000')
                    .replace(/\{view_url\}/g, '#'),
                }}
              />
            </div>
          </div>
        </Modal>
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
    </div>
  );
}
