/* Cấu hình lương — CRUD quy tắc lương + kéo thứ tự + danh sách ngân hàng + mẫu email. Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import {
  fetchSalaryRules, deleteSalaryRule, reorderSalaryRules,
  fetchBankFormats, createBankFormat, updateBankFormat, deleteBankFormat,
  fetchEmailjsConfig, saveEmailjsConfig,
  fetchConfirmConfig, saveConfirmConfig,
} from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import SalaryRuleForm from './SalaryRuleForm';
import TblWrap from '../../components/TblWrap';

const TYPE_LABEL = { fixed: 'Số tiền cố định', formula: 'Công thức tính toán', lookup: 'Tra bảng biểu / Định mức' };
const SUB_TABS = [['rules', 'Thành phần lương'], ['banks', 'Mẫu file Bank'], ['confirm', 'Quy trình chốt lương'], ['mail', 'Mẫu Email gửi phiếu lương']];

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

  /* unified bank list state */
  const [banks, setBanks] = useState(null);
  const [bankSearch, setBankSearch] = useState('');
  const [bankEditing, setBankEditing] = useState(null);   // id or 'new'
  const [bankEditForm, setBankEditForm] = useState({ code: '', name: '', transfer_type: 'normal' });
  const [bankBusy, setBankBusy] = useState(null);

  /* emailjs config state */
  const [ejsServiceId, setEjsServiceId] = useState('');
  const [ejsTemplateId, setEjsTemplateId] = useState('');
  const [ejsPublicKey, setEjsPublicKey] = useState('');
  const [ejsSaving, setEjsSaving] = useState(false);
  const [ejsMsg, setEjsMsg] = useState('');

  /* confirm config state */
  const [cfmDays, setCfmDays] = useState(3);
  const [cfmAutoMail, setCfmAutoMail] = useState(false);
  const [cfmSaving, setCfmSaving] = useState(false);
  const [cfmMsg, setCfmMsg] = useState('');

  /* drag state */
  const dragIdx = useRef(null);
  const [dragOver, setDragOver] = useState(null);

  const loadRules = () => {
    fetchSalaryRules({}).then(setRules).catch((e) => setErr(e.message));
  };
  const loadBanks = () => {
    fetchBankFormats().then(setBanks).catch((e) => setErr(e.message));
  };
  const loadEjsCfg = () => {
    fetchEmailjsConfig().then((d) => {
      setEjsServiceId(d.service_id || '');
      setEjsTemplateId(d.template_id || '');
      setEjsPublicKey(d.public_key || '');
    }).catch(() => {});
  };
  const loadCfmCfg = () => {
    fetchConfirmConfig().then((d) => {
      setCfmDays(d.confirm_period_days || 3);
      setCfmAutoMail(!!d.auto_send_mail);
    }).catch(() => {});
  };
  useEffect(() => { loadRules(); loadBanks(); loadEjsCfg(); loadCfmCfg(); }, []);

  const delRule = async (r) => {
    if (!confirm(`Xoá rule "${r.name}" (${r.code})?`)) return;
    setRuleBusy(r.id);
    try { await deleteSalaryRule(r.id); loadRules(); }
    catch (e) { alert('Xoá thất bại: ' + e.message); }
    finally { setRuleBusy(null); }
  };

  /* ── Bank handlers (unified) ── */
  const startBankEdit = (entry) => {
    setBankEditing(entry.id);
    setBankEditForm({ code: entry.code || '', name: entry.name, transfer_type: entry.transfer_type || 'normal' });
  };
  const startBankAdd = () => {
    setBankEditing('new');
    setBankEditForm({ code: '', name: '', transfer_type: 'normal' });
  };
  const cancelBankEdit = () => { setBankEditing(null); };
  const saveBankEntry = async () => {
    if (!bankEditForm.name.trim()) return;
    setBankBusy(bankEditing);
    try {
      if (bankEditing === 'new') {
        await createBankFormat(bankEditForm);
      } else {
        await updateBankFormat(bankEditing, bankEditForm);
      }
      setBankEditing(null);
      loadBanks();
    } catch (e) { alert('Lưu thất bại: ' + e.message); }
    finally { setBankBusy(null); }
  };
  const delBank = async (entry) => {
    if (!confirm(`Xoá "${entry.name}"?`)) return;
    setBankBusy(entry.id);
    try { await deleteBankFormat(entry.id); loadBanks(); }
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

  /* filtered bank list */
  const filteredBanks = banks.filter((b) =>
    !bankSearch
    || (b.name || '').toLowerCase().includes(bankSearch.toLowerCase())
    || (b.code || '').toLowerCase().includes(bankSearch.toLowerCase())
  );

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
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Thành phần lương (Pay Components)</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>Kéo hoặc dùng mũi tên để sắp xếp thứ tự tính các thành phần lương</div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setRuleForm('new')}>
              <Icon name="plus" size={14} />Thêm thành phần
            </button>
          </div>
          {rules.length === 0 ? (
            <div style={{ padding: 28, textAlign: 'center' }}><EmptyState>Chưa có thành phần lương.</EmptyState></div>
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
                            background: r.amount_type === 'formula' ? 'var(--blue-50)'
                              : r.amount_type === 'lookup' ? '#fef3c7'
                              : 'var(--green-50)',
                            color: r.amount_type === 'formula' ? 'var(--blue-600)'
                              : r.amount_type === 'lookup' ? '#92400e'
                              : 'var(--green-700)',
                          }}>
                            {TYPE_LABEL[r.amount_type] || r.amount_type}
                          </span>
                        </td>
                        <td style={{ fontSize: 12.5, fontFamily: 'monospace', color: '#6b7280' }}>
                          {r.amount_type === 'fixed' ? (r.amount_fixed ? Number(r.amount_fixed).toLocaleString('vi') + ' ₫' : '—')
                            : r.amount_type === 'formula' ? (r.amount_formula || '—')
                            : r.amount_type === 'lookup' ? `${r.lookup_source || '?'}.${r.lookup_field || '?'}`
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
          TAB: NGÂN HÀNG (unified)
          ════════════════════════════════════════════════════════ */}
      {tab === 'banks' && (
        <div style={{
          flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
          border: '1px solid #e5e7eb', borderRadius: 10,
          background: '#fff', overflow: 'hidden',
        }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Danh sách mẫu file Bank</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>
                Mẫu file ngân hàng dùng cho chi trả lương
                <span style={{ marginLeft: 6, fontWeight: 600 }}>({banks.length} ngân hàng)</span>
              </div>
            </div>
            <input
              type="text"
              className="inp"
              placeholder="Tìm ngân hàng..."
              value={bankSearch}
              onChange={(e) => setBankSearch(e.target.value)}
              style={{ width: 220, padding: '6px 10px', fontSize: 13 }}
            />
            <button className="btn btn-primary btn-sm" onClick={startBankAdd}>
              <Icon name="plus" size={14} />Thêm
            </button>
          </div>
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
            <TblWrap id="cfg-banks">
              <table className="tbl">
                <thead>
                  <tr>
                    <th style={{ width: 120 }}>Mã</th>
                    <th>Tên ngân hàng</th>
                    <th style={{ width: 280 }}>Hình thức chuyển</th>
                    <th style={{ width: 100 }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Inline add row */}
                  {bankEditing === 'new' && (
                    <tr style={{ background: '#f0fdf4' }}>
                      <td>
                        <input type="text" className="inp" value={bankEditForm.code}
                          onChange={(e) => setBankEditForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                          placeholder="VD: ACB"
                          style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                          autoFocus
                        />
                      </td>
                      <td>
                        <input type="text" className="inp" value={bankEditForm.name}
                          onChange={(e) => setBankEditForm((f) => ({ ...f, name: e.target.value }))}
                          placeholder="VD: ACB - Ngan hang TMCP A Chau"
                          style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                        />
                      </td>
                      <td>
                        <select className="sel" value={bankEditForm.transfer_type}
                          onChange={(e) => setBankEditForm((f) => ({ ...f, transfer_type: e.target.value }))}
                          style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                        >
                          <option value="normal">CK THƯỜNG</option>
                          <option value="fast_247">CK NHANH 24/7</option>
                        </select>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button className="icon-btn" title="Lưu" onClick={saveBankEntry} disabled={bankBusy === 'new'}>
                            <Icon name="check" size={15} style={{ color: 'var(--green-600)' }} />
                          </button>
                          <button className="icon-btn" title="Huỷ" onClick={cancelBankEdit}>
                            <Icon name="x" size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                  {filteredBanks.map((entry) => (
                    bankEditing === entry.id ? (
                      /* Inline edit row */
                      <tr key={entry.id} style={{ background: '#eff6ff' }}>
                        <td>
                          <input type="text" className="inp" value={bankEditForm.code}
                            onChange={(e) => setBankEditForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                            style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                            autoFocus
                          />
                        </td>
                        <td>
                          <input type="text" className="inp" value={bankEditForm.name}
                            onChange={(e) => setBankEditForm((f) => ({ ...f, name: e.target.value }))}
                            style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                          />
                        </td>
                        <td>
                          <select className="sel" value={bankEditForm.transfer_type}
                            onChange={(e) => setBankEditForm((f) => ({ ...f, transfer_type: e.target.value }))}
                            style={{ width: '100%', padding: '5px 8px', fontSize: 13 }}
                          >
                            <option value="normal">CK THƯỜNG</option>
                            <option value="fast_247">CK NHANH 24/7</option>
                          </select>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            <button className="icon-btn" title="Lưu" onClick={saveBankEntry} disabled={bankBusy === entry.id}>
                              <Icon name="check" size={15} style={{ color: 'var(--green-600)' }} />
                            </button>
                            <button className="icon-btn" title="Huỷ" onClick={cancelBankEdit}>
                              <Icon name="x" size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      /* Display row */
                      <tr key={entry.id}
                        style={{ background: '#fff' }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; }}
                      >
                        <td style={{ fontSize: 12.5, fontFamily: 'monospace' }}>{entry.code || ''}</td>
                        <td style={{ fontSize: 13 }}>{entry.name}</td>
                        <td>
                          <span style={{
                            display: 'inline-block', padding: '2px 8px', borderRadius: 4,
                            fontSize: 12, fontWeight: 600,
                            background: entry.transfer_type === 'fast_247' ? '#dbeafe' : '#f3f4f6',
                            color: entry.transfer_type === 'fast_247' ? '#1d4ed8' : '#374151',
                          }}>
                            {entry.transfer_type === 'fast_247' ? 'CK NHANH 24/7' : 'CK THƯỜNG'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            <button className="icon-btn" title="Sửa" onClick={() => startBankEdit(entry)}>
                              <Icon name="edit" size={15} />
                            </button>
                            <button className="icon-btn" title="Xoá" onClick={() => delBank(entry)} disabled={bankBusy === entry.id}>
                              <Icon name="trash" size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  ))}
                </tbody>
              </table>
            </TblWrap>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAB: XÁC NHẬN LƯƠNG
          ════════════════════════════════════════════════════════ */}
      {tab === 'confirm' && (
        <div style={{
          display: 'flex', flexDirection: 'column', gap: 16,
        }}>
          {/* ── Card chính ── */}
          <div style={{
            border: '1px solid #e5e7eb', borderRadius: 12,
            background: '#fff', overflow: 'hidden',
          }}>
            {/* Header */}
            <div style={{
              padding: '16px 22px', borderBottom: '1px solid #e5e7eb',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Quy trình chốt & Phản hồi phiếu lương</h3>
                <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 3 }}>
                  Cấu hình khoảng thời gian nhân viên phản hồi và chốt bảng lương
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  className="btn btn-primary btn-sm"
                  disabled={cfmSaving}
                  onClick={async () => {
                    setCfmSaving(true); setCfmMsg('');
                    try {
                      await saveConfirmConfig({
                        confirm_period_days: cfmDays,
                        auto_send_mail: cfmAutoMail,
                      });
                      setCfmMsg('Đã lưu!');
                    } catch (e) {
                      setCfmMsg('Lỗi: ' + e.message);
                    } finally { setCfmSaving(false); }
                  }}
                >
                  {cfmSaving ? 'Đang lưu...' : 'Lưu cấu hình'}
                </button>
                {cfmMsg && (
                  <span style={{
                    fontSize: 12.5, fontWeight: 600,
                    color: cfmMsg.startsWith('Lỗi') ? '#dc2626' : '#16a34a',
                  }}>{cfmMsg}</span>
                )}
              </div>
            </div>

            <div style={{ padding: '20px 22px' }}>
              {/* Info banner */}
              <div style={{
                padding: '14px 18px', marginBottom: 20, borderRadius: 10,
                background: 'linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%)',
                border: '1px solid #bfdbfe',
                display: 'flex', gap: 12, alignItems: 'flex-start',
              }}>
                <span style={{ fontSize: 22, lineHeight: 1 }}>💡</span>
                <div style={{ fontSize: 13, color: '#1e40af', lineHeight: 1.6 }}>
                  <strong>Quy trình chốt lương & Phản hồi:</strong>
                  <ul style={{ margin: '6px 0 0 18px', padding: 0 }}>
                    <li>HR chủ động bấm <strong>"Gửi mail"</strong> cho nhân viên sau khi rà soát và tính toán lương xong (không tự động gửi ngay khi tính).</li>
                    <li>Trong khoảng thời hạn phản hồi (Từ ngày gửi mail đến ngày hết hạn), nhân viên được phép truy cập phiếu lương cá nhân và có thể <strong>Xác nhận đồng ý</strong> hoặc <strong>Gửi phản hồi / Khiếu nại</strong> nhiều lần (vô số lần trong khoảng thời hạn).</li>
                    <li>Nếu hết thời hạn mà nhân viên không có phản hồi gì, hệ thống sẽ <strong>tự động coi như nhân viên đồng ý</strong> (Auto-confirmed) để HR tiến hành <strong>Lưu lịch sử lương</strong> và <strong>Tạo file chi lương Ngân hàng</strong>.</li>
                  </ul>
                </div>
              </div>

              {/* Confirm period days */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20,
                padding: '16px 20px', borderRadius: 10,
                background: '#fafafa', border: '1px solid #f3f4f6',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Thời hạn phản hồi phiếu lương</div>
                  <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 3 }}>
                    Số ngày dương lịch (bao gồm T7, CN) nhân viên có quyền gửi/chỉnh sửa phản hồi khiếu nại kể từ khi HR bấm gửi mail
                  </div>
                </div>
                <select
                  className="sel"
                  value={cfmDays}
                  onChange={(e) => { setCfmDays(Number(e.target.value)); setCfmMsg(''); }}
                  style={{
                    width: 150, padding: '8px 12px', fontSize: 14,
                    fontWeight: 700, borderRadius: 8,
                    border: '2px solid #cbd5e1',
                    background: '#fff', color: '#0f172a',
                  }}
                >
                  {[1, 2, 3, 5, 7, 10, 14, 30].map((d) => (
                    <option key={d} value={d}>{d} ngày</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* ── Preview card ── */}
          <div style={{
            border: '1px solid #e5e7eb', borderRadius: 12,
            background: '#fff', overflow: 'hidden',
          }}>
            <div style={{
              padding: '14px 22px', borderBottom: '1px solid #e5e7eb',
            }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#374151' }}>Tóm tắt cấu hình hiện tại</h3>
            </div>
            <div style={{ padding: '16px 22px', display: 'flex', gap: 16 }}>
              <div style={{
                flex: 1, padding: '14px 18px', borderRadius: 10,
                background: 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%)',
                border: '1px solid #bbf7d0',
              }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#16a34a', textTransform: 'uppercase', letterSpacing: 0.5 }}>Thời hạn</div>
                <div style={{ fontSize: 22, fontWeight: 800, color: '#065f46', marginTop: 4 }}>{cfmDays} ngày</div>
                <div style={{ fontSize: 11.5, color: '#15803d', marginTop: 2 }}>sau khi gửi mail</div>
              </div>
              <div style={{
                flex: 1, padding: '14px 18px', borderRadius: 10,
                background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
                border: '1px solid #93c5fd',
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#2563eb', textTransform: 'uppercase', letterSpacing: 0.5 }}>Hình thức gửi mail</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#1d4ed8', marginTop: 4 }}>
                  HR CHỦ ĐỘNG
                </div>
                <div style={{ fontSize: 11.5, color: '#3b82f6', marginTop: 2 }}>
                  Bấm gửi mail sau khi tính & kiểm tra
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAB: MẪU EMAIL
          ════════════════════════════════════════════════════════ */}
      {tab === 'mail' && (
        <div style={{
          display: 'flex', flexDirection: 'column',
          border: '1px solid #e5e7eb', borderRadius: 10,
          background: '#fff', overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 20px', borderBottom: '1px solid #e5e7eb', flexShrink: 0,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Cấu hình EmailJS (dịch vụ gửi mail)</h3>
              <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>
                Thay thế SMTP — gửi qua tài khoản Gmail/Outlook của bạn
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button
                className="btn btn-primary btn-sm"
                disabled={ejsSaving}
                onClick={async () => {
                  setEjsSaving(true); setEjsMsg('');
                  try {
                    await saveEmailjsConfig({
                      service_id: ejsServiceId,
                      template_id: ejsTemplateId,
                      public_key: ejsPublicKey,
                    });
                    setEjsMsg('Đã lưu!');
                  } catch (e) {
                    setEjsMsg('Lỗi: ' + e.message);
                  } finally { setEjsSaving(false); }
                }}
              >
                {ejsSaving ? 'Đang lưu...' : 'Lưu EmailJS'}
              </button>
              {ejsMsg && (
                <span style={{ fontSize: 12.5, fontWeight: 600, color: ejsMsg.startsWith('Lỗi') ? '#dc2626' : '#16a34a' }}>
                  {ejsMsg}
                </span>
              )}
            </div>
          </div>

          <div style={{ padding: '16px 20px' }}>
            {/* EmailJS guide */}
            <div style={{
              padding: '10px 14px', marginBottom: 14, borderRadius: 8,
              background: '#fefce8', border: '1px solid #fde68a', fontSize: 12.5, color: '#92400e',
            }}>
              <strong>Cách lấy thông tin:</strong> Đăng nhập{' '}
              <strong>emailjs.com</strong> → Email Services (lấy Service ID) →
              Email Templates (tạo template, lấy Template ID) →
              Account → API Keys (lấy Public Key).
              <br />
              <strong>Biến trong template EmailJS:</strong>{' '}
              <code>{'{{to_email}}'}</code>, <code>{'{{employee_name}}'}</code>,{' '}
              <code>{'{{month}}'}</code>, <code>{'{{year}}'}</code>,{' '}
              <code>{'{{gross}}'}</code>, <code>{'{{net}}'}</code>,{' '}
              <code>{'{{view_url}}'}</code>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ fontSize: 12.5, fontWeight: 600, color: '#374151', width: 100, flexShrink: 0 }}>
                  Service ID
                </label>
                <input className="inp" value={ejsServiceId}
                  onChange={(e) => { setEjsServiceId(e.target.value); setEjsMsg(''); }}
                  placeholder="service_xxxxxxx" style={{ flex: 1 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ fontSize: 12.5, fontWeight: 600, color: '#374151', width: 100, flexShrink: 0 }}>
                  Template ID
                </label>
                <input className="inp" value={ejsTemplateId}
                  onChange={(e) => { setEjsTemplateId(e.target.value); setEjsMsg(''); }}
                  placeholder="template_xxxxxxx" style={{ flex: 1 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ fontSize: 12.5, fontWeight: 600, color: '#374151', width: 100, flexShrink: 0 }}>
                  Public Key
                </label>
                <input className="inp" value={ejsPublicKey}
                  onChange={(e) => { setEjsPublicKey(e.target.value); setEjsMsg(''); }}
                  placeholder="xxxxxxxxxxxxxxxxxxxx" style={{ flex: 1 }} />
              </div>
            </div>
          </div>
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
    </div>
  );
}
