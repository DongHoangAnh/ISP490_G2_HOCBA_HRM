/* Bang luong nhan vien theo thang — Owner: Hung. */
import { useState, useEffect, useCallback } from 'react';
import { fetchEmployeePayroll, sendPayslipMail, markPayslipsSent, closeBatchByPeriod, computeAllPayslips, fetchEmailjsConfig, resetPayslipConfirm } from '../../api/payroll';
import emailjs from '@emailjs/browser';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { currentMonth, currentYear } from './util';

/* ── localStorage v2 ── */
const LS_KEY = 'hb_payroll_col_v2';
const LS_WIDTHS = 'hb_payroll_widths';
const loadCfg = () => {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || null; } catch { return null; }
};
const saveCfg = (c) => localStorage.setItem(LS_KEY, JSON.stringify(c));
const loadWidths = () => {
  try { return JSON.parse(localStorage.getItem(LS_WIDTHS)) || {}; } catch { return {}; }
};
const saveWidths = (w) => localStorage.setItem(LS_WIDTHS, JSON.stringify(w));

/* 5 cot co ban */
const BASE = [
  { key: 'stt',        label: 'STT',        w: 40  },
  { key: 'code',       label: 'Ma NV',      w: 76  },
  { key: 'name',       label: 'Ho va ten',  w: 150 },
  { key: 'job_title',  label: 'Chuc vu',    w: 110 },
  { key: 'department', label: 'Phong ban',   w: 115 },
];

/* ── Column-config Modal ── */
function CfgModal({ dataCols, cfg, onApply, onClose }) {
  const [frozen, setFrozen] = useState(() => {
    const s = cfg.frozen || {};
    return Object.fromEntries(BASE.map((b) => [b.key, s[b.key] !== false]));
  });
  const [vis, setVis] = useState(() => {
    const s = cfg.visible || {};
    return Object.fromEntries(dataCols.map((c) => [c.code, s[c.code] !== false]));
  });
  const [ord, setOrd] = useState(() => {
    const saved = cfg.order || [];
    const all = dataCols.map((c) => c.code);
    const merged = saved.filter((c) => all.includes(c));
    all.forEach((c) => { if (!merged.includes(c)) merged.push(c); });
    return merged;
  });

  const allOn = dataCols.length > 0 && dataCols.every((c) => vis[c.code]);
  const flipAll = () => {
    const on = !allOn;
    setVis(Object.fromEntries(dataCols.map((c) => [c.code, on])));
  };

  const [dragCode, setDragCode] = useState(null);
  const nameOf = {};
  dataCols.forEach((c) => { nameOf[c.code] = c.name; });

  /* Reorder LIVE theo mã cột (không theo index tĩnh → không lệch sau re-render).
     Chèn trước/sau hàng hover theo điểm giữa (midpoint) + bù dịch khi bỏ phần tử
     → mượt, không dao động. VD: cột #5 kéo lên #2 thì #2,3,4 → #3,4,5. */
  const reorderOver = (e, overCode) => {
    e.preventDefault();
    if (dragCode == null || dragCode === overCode) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const after = (e.clientY - rect.top) > rect.height / 2;
    setOrd((prev) => {
      const from = prev.indexOf(dragCode);
      let to = prev.indexOf(overCode);
      if (from < 0 || to < 0) return prev;
      if (after) to += 1;
      if (from < to) to -= 1;
      if (to === from) return prev;
      const next = [...prev];
      next.splice(from, 1);
      next.splice(to, 0, dragCode);
      return next;
    });
  };

  return (
    <Modal onClose={onClose}>
      <div style={{ padding: '20px 24px 14px', borderBottom: '1px solid var(--border,#e5e7eb)' }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Tuy chinh cot hien thi</h2>
        <p style={{ margin: '4px 0 0', fontSize: 12.5, color: 'var(--muted,#888)' }}>
          Chon cot va thu tu hien thi tren bang luong. Cau hinh duoc luu tren trinh duyet.
        </p>
      </div>
      <div style={{ maxHeight: '58vh', overflowY: 'auto' }}>
        <label style={MS.allRow}>
          <input type="checkbox" checked={allOn} onChange={flipAll} style={MS.chk} />
          <span style={{ fontWeight: 600 }}>Tat ca cot du lieu</span>
          <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--muted)' }}>
            {dataCols.filter((c) => vis[c.code]).length}/{dataCols.length}
          </span>
        </label>
        <div style={MS.section}>Co dinh (Freeze)</div>
        {BASE.map((b) => (
          <label key={b.key} style={MS.row}>
            <input type="checkbox" checked={frozen[b.key]} style={MS.chk}
              onChange={() => setFrozen((f) => ({ ...f, [b.key]: !f[b.key] }))} />
            <Icon name="lock" size={13} />
            <span>{b.label}</span>
          </label>
        ))}
        <div style={MS.section}>Cot du lieu</div>
        {ord.map((code) => (
          <div key={code}
            style={{
              ...MS.row, cursor: 'default',
              opacity: dragCode === code ? 0.45 : 1,
              background: dragCode === code ? 'var(--gray-50,#f9fafb)' : undefined,
              transition: 'background .12s',
            }}
            onDragOver={(e) => reorderOver(e, code)}
            onDrop={(e) => e.preventDefault()}>
            <input type="checkbox" checked={vis[code] !== false} style={MS.chk}
              onChange={() => setVis((v) => ({ ...v, [code]: !v[code] }))} />
            <span style={{ flex: 1, fontSize: 13 }}>{nameOf[code] || code}</span>
            <span
              draggable
              onDragStart={(e) => { setDragCode(code); e.dataTransfer.effectAllowed = 'move'; }}
              onDragEnd={() => setDragCode(null)}
              title="Kéo để đổi thứ tự"
              style={{ cursor: 'grab', color: '#9ca3af', fontSize: 16, userSelect: 'none', width: 18, textAlign: 'center', touchAction: 'none' }}>&#9776;</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 24px', borderTop: '1px solid var(--border,#e5e7eb)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Huy</button>
        <button className="btn btn-primary" onClick={() => { onApply({ frozen, visible: vis, order: ord }); onClose(); }}>
          Ap dung
        </button>
      </div>
    </Modal>
  );
}
const MS = {
  chk: { width: 15, height: 15, accentColor: '#2563eb', cursor: 'pointer', flexShrink: 0 },
  allRow: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 24px',
    borderBottom: '1px solid var(--border,#e5e7eb)', cursor: 'pointer',
    background: 'var(--gray-50,#f9fafb)', fontSize: 13.5,
  },
  row: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '7px 24px',
    borderBottom: '1px solid #f3f4f6', fontSize: 13, cursor: 'pointer',
  },
  section: {
    padding: '10px 24px 4px', fontSize: 11, fontWeight: 700,
    color: '#9ca3af', textTransform: 'uppercase', letterSpacing: .6,
  },
};

/* ── Salary Detail — receipt-style, flex to screen ── */
const CONFIRM_STYLE = {
  pending:   { label: 'Chờ xác nhận', bg: '#fef3c7', color: '#92400e', icon: 'clock' },
  confirmed: { label: 'Đã xác nhận',  bg: '#d1fae5', color: '#065f46', icon: 'checkCircle' },
  rejected:  { label: 'Từ chối',      bg: '#fee2e2', color: '#991b1b', icon: 'xCircle' },
};

function SalaryDetail({ emp, columns, onClose, onChanged }) {
  const lastCode = columns.length > 0 ? columns[columns.length - 1].code : null;
  const NET_CODES = new Set(['thuc_lanh']);
  const netRow = columns.find((c) => NET_CODES.has(c.code));
  const netVal = netRow ? emp.amounts[netRow.code] : null;

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [localStatus, setLocalStatus] = useState(emp.employee_confirm || 'pending');

  const cs = CONFIRM_STYLE[localStatus] || CONFIRM_STYLE.pending;
  const canReset = emp.payslip_id && localStatus !== 'pending';

  const handleReset = async () => {
    if (!confirm('Bỏ xác nhận để tính lại lương cho nhân viên này?')) return;
    setBusy(true); setErr(null);
    try {
      await resetPayslipConfirm(emp.payslip_id);
      setLocalStatus('pending');
      if (onChanged) onChanged();
    } catch (e) {
      setErr(e.message || 'Reset thất bại');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div style={{
        display: 'flex', flexDirection: 'column',
        height: 'calc(100vh - 100px)', maxHeight: 720,
        padding: '16px 24px 16px',
      }}>
        {/* ─ header ─ */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12, flexShrink: 0 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{emp.name}</h2>
              {emp.payslip_id && (
                <span style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                  padding: '3px 10px', borderRadius: 20,
                  fontSize: 11.5, fontWeight: 600,
                  background: cs.bg, color: cs.color,
                }}>
                  <Icon name={cs.icon} size={13} />
                  {cs.label}
                </span>
              )}
            </div>
            <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 3 }}>
              {[emp.code, emp.job_title, emp.department].filter(Boolean).join(' · ')}
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} style={{ marginTop: -4 }}><Icon name="x" size={18} /></button>
        </div>

        {/* ─ rows — flex fill ─ */}
        <div style={{
          flex: 1, minHeight: 0,
          border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
        }}>
          {columns.map((col, i) => {
            const val = emp.amounts[col.code];
            const isNet = NET_CODES.has(col.code) || col.code === lastCode;
            return (
              <div key={col.code} style={{
                flex: 1, minHeight: 0,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0 16px',
                borderBottom: i < columns.length - 1 ? '1px solid #f3f4f6' : 'none',
                background: isNet ? '#f0fdf4' : '#fff',
                fontSize: 13,
              }}>
                <span style={{
                  color: isNet ? '#15803d' : '#374151',
                  fontWeight: isNet ? 700 : 400,
                }}>{col.name}</span>
                <span style={{
                  fontVariantNumeric: 'tabular-nums',
                  fontWeight: isNet ? 800 : 500,
                  color: isNet ? '#15803d' : val < 0 ? '#dc2626' : '#111827',
                  fontSize: isNet ? 14.5 : 13,
                }}>
                  {val != null ? hbVND(val) : '—'}
                </span>
              </div>
            );
          })}
        </div>

        {/* ─ total bar ─ */}
        {netVal != null && (
          <div style={{
            marginTop: 10, padding: '10px 16px', borderRadius: 8, flexShrink: 0,
            background: 'linear-gradient(135deg, #065f46, #047857)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ color: '#d1fae5', fontSize: 13, fontWeight: 600 }}>Thực lĩnh</span>
            <span style={{ color: '#fff', fontSize: 18, fontWeight: 800, fontVariantNumeric: 'tabular-nums' }}>
              {hbVND(netVal)}
            </span>
          </div>
        )}

        {/* ─ rejected feedback ─ */}
        {localStatus === 'rejected' && emp.employee_feedback && (
          <div style={{
            marginTop: 10, padding: '10px 16px', borderRadius: 8, flexShrink: 0,
            background: '#fef2f2', border: '1px solid #fecaca',
            fontSize: 12.5, color: '#991b1b',
          }}>
            <span style={{ fontWeight: 600 }}>Lý do từ chối:</span> {emp.employee_feedback}
          </div>
        )}

        {/* ─ status + HR reset action ─ */}
        {err && (
          <div style={{ color: '#dc2626', fontSize: 12.5, marginTop: 10, padding: '6px 10px', background: '#fef2f2', borderRadius: 6 }}>
            {err}
          </div>
        )}

        {localStatus === 'confirmed' && (
          <div style={{
            marginTop: 10, padding: '10px 16px', borderRadius: 8, flexShrink: 0,
            background: '#f0fdf4', border: '1px solid #bbf7d0',
            display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 13, color: '#065f46', fontWeight: 600,
          }}>
            <Icon name="checkCircle" size={16} />
            Nhân viên đã xác nhận phiếu lương
          </div>
        )}

        {canReset && (
          <button
            onClick={handleReset}
            disabled={busy}
            style={{
              marginTop: 10, padding: '10px 0', borderRadius: 8, flexShrink: 0,
              border: '1px solid #d1d5db', background: '#fff',
              fontSize: 13, fontWeight: 600, color: '#374151',
              cursor: busy ? 'not-allowed' : 'pointer',
              opacity: busy ? 0.5 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
          >
            <Icon name="refresh" size={15} />
            {busy ? 'Đang xử lý...' : 'Bỏ xác nhận — tính lại lương'}
          </button>
        )}
      </div>
    </Modal>
  );
}

/* checkbox col width */
const CHK_W = 40;

/* NV xac nhan badge styles */
const CONFIRM_MAP = {
  pending:   { label: 'Chờ',     bg: '#fef3c7', color: '#92400e' },
  confirmed: { label: 'Đã XN',   bg: '#d1fae5', color: '#065f46' },
  rejected:  { label: 'Từ chối', bg: '#fee2e2', color: '#991b1b' },
};

/* ── Main ── */
export default function BatchList({ search }) {
  const month = currentMonth();
  const year  = currentYear();
  const [data, setData]   = useState(null);
  const [err, setErr]     = useState(null);
  const [detailEmp, setDetailEmp] = useState(null);
  const [cfgOpen, setCfgOpen] = useState(false);
  const [cfg, setCfg] = useState(() => loadCfg() || {});
  const [colWidths, setColWidths] = useState(() => loadWidths());
  const [checked, setChecked] = useState({});
  const [computing, setComputing] = useState(false);
  const [sending, setSending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [localSearch, setLocalSearch] = useState('');
  const [confirmFilter, setConfirmFilter] = useState('');
  const load = () => { setErr(null); setData(null); setChecked({}); fetchEmployeePayroll({ month, year }).then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, [month, year]);
  const applyCfg = useCallback((c) => { setCfg(c); saveCfg(c); }, []);

  /* ── column resize (mượt) ──
     Trong lúc kéo CHỈ ghi thẳng width vào <th> qua DOM (rAF-throttle) → không
     setState → KHÔNG re-render cả bảng → không giật. table-layout:fixed nên chỉ
     cần set <th> là cả cột giãn theo. Commit vào React state 1 LẦN khi thả. */
  const startResize = useCallback((colKey, initW, e) => {
    e.preventDefault();
    const handle = e.currentTarget;
    const th = handle.closest('th');
    handle.classList.add('rh-active');
    const startX = e.clientX;
    let latestW = initW;
    let rafId = 0;
    const apply = () => {
      rafId = 0;
      if (th) { const w = latestW + 'px'; th.style.width = w; th.style.minWidth = w; th.style.maxWidth = w; }
    };
    const onMove = (ev) => {
      latestW = Math.max(40, initW + (ev.clientX - startX));
      if (!rafId) rafId = requestAnimationFrame(apply);
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      if (rafId) cancelAnimationFrame(rafId);
      handle.classList.remove('rh-active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      setColWidths((prev) => { const next = { ...prev, [colKey]: latestW }; saveWidths(next); return next; });
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }, []);

  const getW = useCallback((key, def) => colWidths[key] || def, [colWidths]);

  /* ── checkbox helpers (uses filtered emps list via ref) ── */
  const allEmpsWithSlip = (data ? data.employees : []).filter((e) => e.payslip_id);
  const checkedIds = Object.keys(checked).filter((k) => checked[k]).map(Number);
  const checkedCount = checkedIds.length;
  const toggleOne = (pid) => setChecked((p) => ({ ...p, [pid]: !p[pid] }));

  /* ── compute all ── */
  const handleComputeAll = async () => {
    if (computing) return;
    setComputing(true);
    try {
      const res = await computeAllPayslips(Number(month), Number(year));
      const msg = `Đã tính lương cho ${res.computed} nhân viên`
        + (res.created ? `, tạo mới ${res.created} phiếu` : '')
        + (res.errors?.length ? `\nLỗi: ${res.errors.join('; ')}` : '');
      alert(msg);
      load();
    } catch (e) {
      alert('Lỗi tính lương: ' + e.message);
    } finally {
      setComputing(false);
    }
  };

  /* ── send mail via EmailJS ── */
  const handleSendMail = async () => {
    if (checkedCount === 0 || sending) return;
    setSending(true);
    try {
      // 1. Load EmailJS config
      const cfg = await fetchEmailjsConfig();
      if (!cfg.service_id || !cfg.template_id || !cfg.public_key) {
        alert('Chưa cấu hình EmailJS.\nVào tab Cấu hình → Mẫu email → phần "Cấu hình EmailJS" để nhập Service ID, Template ID, Public Key.');
        return;
      }

      // 2. Find employee rows for checked payslip IDs
      const allEmps = data ? data.employees : [];
      const checkedSet = new Set(checkedIds);
      const targets = allEmps.filter((e) => e.payslip_id && checkedSet.has(e.payslip_id));

      const baseUrl = window.location.origin;
      const sentIds = [];
      const errors = [];

      for (const emp of targets) {
        if (!emp.work_email) {
          errors.push(`${emp.name}: không có work_email`);
          continue;
        }
        const gross = emp.gross_amount ? emp.gross_amount.toLocaleString('vi-VN') : '0';
        const net = emp.net_amount ? emp.net_amount.toLocaleString('vi-VN') : '0';
        const viewUrl = emp.access_token
          ? `${baseUrl}/payslip/view/${emp.access_token}`
          : baseUrl;
        try {
          await emailjs.send(
            cfg.service_id,
            cfg.template_id,
            {
              to_email: emp.work_email,
              employee_name: emp.name,
              month: String(month).padStart(2, '0'),
              year: String(year),
              gross,
              net,
              view_url: viewUrl,
            },
            { publicKey: cfg.public_key },
          );
          sentIds.push(emp.payslip_id);
        } catch (e) {
          errors.push(`${emp.name}: ${e?.text || e?.message || JSON.stringify(e)}`);
        }
      }

      // 3. Mark as sent on backend
      if (sentIds.length > 0) {
        await markPayslipsSent(sentIds);
      }

      const msg = `Đã gửi ${sentIds.length} email`
        + (errors.length ? `\nLỗi (${errors.length}):\n${errors.join('\n')}` : '');
      alert(msg);
      setChecked({});
      load();
    } catch (e) {
      alert('Lỗi gửi mail: ' + e.message);
    } finally {
      setSending(false);
    }
  };

  /* ── save to history ── */
  const allConfirmed = allEmpsWithSlip.length > 0 &&
    allEmpsWithSlip.every((e) => e.employee_confirm === 'confirmed');

  const handleSaveHistory = async () => {
    if (!allConfirmed || saving) return;
    if (!confirm(`Lưu lịch sử lương tháng ${month}/${year}? Sau khi lưu sẽ không thể chỉnh sửa.`)) return;
    setSaving(true);
    try {
      await closeBatchByPeriod(Number(month), Number(year));
      alert(`Đã lưu lịch sử lương tháng ${month}/${year} thành công!`);
      load();
    } catch (e) {
      alert('Lỗi: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;

  const q = (search || localSearch || '').toLowerCase();
  const emps = data ? data.employees.filter((e) => {
    if (confirmFilter && (e.employee_confirm || 'pending') !== confirmFilter) return false;
    if (!q) return true;
    return (e.name || '').toLowerCase().includes(q)
      || (e.code || '').toLowerCase().includes(q)
      || (e.department || '').toLowerCase().includes(q)
      || (e.job_title || '').toLowerCase().includes(q);
  }) : [];

  /* toggleAll / allChecked work on the FILTERED list */
  const visibleWithSlip = emps.filter((e) => e.payslip_id);
  const allChecked = visibleWithSlip.length > 0 && visibleWithSlip.every((e) => checked[e.payslip_id]);
  const toggleAll = () => {
    if (allChecked) setChecked({});
    else setChecked(Object.fromEntries(visibleWithSlip.map((e) => [e.payslip_id, true])));
  };

  const allCols = data ? data.columns : [];
  const sorted = (() => {
    const codes = allCols.map((c) => c.code);
    const o = (cfg.order || []).filter((c) => codes.includes(c));
    codes.forEach((c) => { if (!o.includes(c)) o.push(c); });
    return o.map((c) => allCols.find((x) => x.code === c)).filter(Boolean);
  })();
  const visCols = sorted.filter((c) => (cfg.visible || {})[c.code] !== false);

  const fr = cfg.frozen || {};
  const frozenBase = BASE.filter((b) => fr[b.key] !== false);
  const fw = frozenBase.map((b) => getW(b.key, b.w));
  /* offset by CHK_W for checkbox column */
  const cumL = fw.map((_, i) => CHK_W + fw.slice(0, i).reduce((a, b) => a + b, 0));

  const sH = (i) => ({ position: 'sticky', left: cumL[i], zIndex: 5, background: '#fafbfd', width: fw[i], minWidth: fw[i], maxWidth: fw[i] });
  const sD = (i) => ({ position: 'sticky', left: cumL[i], zIndex: 2, background: 'inherit', width: fw[i], minWidth: fw[i], maxWidth: fw[i] });
  const sF = (i) => ({ position: 'sticky', left: cumL[i], zIndex: 5, background: '#f8f9fb', width: fw[i], minWidth: fw[i], maxWidth: fw[i] });

  const cellVal = (e, key, idx) => {
    if (key === 'stt') return idx + 1;
    if (key === 'code') return e.code || '—';
    if (key === 'name') return e.name;
    if (key === 'job_title') return e.job_title || '—';
    if (key === 'department') return e.department || '—';
    return '—';
  };

  const total = emps.length;
  const withSlip = emps.filter((e) => e.payslip_id).length;

  const P = { padding: '10px 14px', fontSize: 13.5, whiteSpace: 'nowrap', lineHeight: '20px', overflow: 'hidden', textOverflow: 'ellipsis' };
  const dataDefW = 110;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexShrink: 0 }}>

        {/* Odoo-style search bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
          padding: '4px 10px', minWidth: 280, flex: '0 1 380px',
        }}>
          <Icon name="search" size={15} style={{ color: '#9ca3af', flexShrink: 0 }} />

          {/* Period label (fixed to current month) */}
          <span style={{
            display: 'inline-flex', alignItems: 'center',
            padding: '3px 10px', borderRadius: 5, fontSize: 12, fontWeight: 600,
            background: '#eff6ff', color: '#1d4ed8', whiteSpace: 'nowrap',
          }}>
            T{month}/{year}
          </span>

          {/* Search input */}
          <input
            type="text"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Tìm tên, mã NV, phòng ban..."
            style={{
              flex: 1, border: 'none', outline: 'none', fontSize: 13,
              background: 'transparent', minWidth: 100,
            }}
          />
          {localSearch && (
            <button onClick={() => setLocalSearch('')} style={{
              border: 'none', background: 'none', cursor: 'pointer', padding: 2, color: '#9ca3af',
              display: 'flex', alignItems: 'center',
            }}>
              <Icon name="x" size={14} />
            </button>
          )}
        </div>

        {/* Status filter */}
        <select
          value={confirmFilter}
          onChange={(e) => { setConfirmFilter(e.target.value); setChecked({}); }}
          style={{
            padding: '5px 10px', borderRadius: 7, fontSize: 12.5, fontWeight: 600,
            border: '1px solid #d1d5db', background: confirmFilter === 'rejected' ? '#fee2e2' : '#fff',
            color: confirmFilter === 'rejected' ? '#991b1b' : '#374151',
            cursor: 'pointer',
          }}
        >
          <option value="">Tất cả trạng thái</option>
          <option value="pending">Chờ xác nhận</option>
          <option value="confirmed">Đã xác nhận</option>
          <option value="rejected">Từ chối</option>
        </select>

        {/* metrics inline */}
        {data && <>
          <div style={{ width: 1, height: 24, background: '#e5e7eb', margin: '0 2px' }} />
          {[
            ['NV:', total], ['Phiếu:', withSlip],
          ].map(([l, v]) => (
            <span key={l} style={{ fontSize: 11.5, color: '#6b7280' }}>
              {l} <b style={{ color: '#111827' }}>{v}</b>
            </span>
          ))}
        </>}

        <div style={{ flex: 1 }} />

        <button onClick={handleComputeAll} disabled={computing}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', borderRadius: 6,
            border: 'none', background: '#f59e0b', color: '#fff',
            fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
            cursor: computing ? 'not-allowed' : 'pointer',
            opacity: computing ? .5 : 1,
          }}>
          <Icon name="zap" size={13} />
          {computing ? 'Đang tính...' : 'Tính lương'}
        </button>

        <button onClick={handleSendMail} disabled={sending || checkedCount === 0}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', borderRadius: 6,
            border: 'none', background: '#2563eb', color: '#fff',
            fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
            cursor: (sending || checkedCount === 0) ? 'not-allowed' : 'pointer',
            opacity: (sending || checkedCount === 0) ? .5 : 1,
          }}>
          <Icon name="mail" size={13} />
          {sending ? 'Đang gửi...' : checkedCount > 0 ? `Gửi mail (${checkedCount})` : 'Gửi mail'}
        </button>

        <button onClick={handleSaveHistory} disabled={saving || !allConfirmed}
          title={allConfirmed ? 'Lưu vào lịch sử lương' : 'Tất cả nhân viên phải xác nhận trước khi lưu'}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', borderRadius: 6,
            border: 'none', background: allConfirmed ? '#16a34a' : '#9ca3af', color: '#fff',
            fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
            cursor: (saving || !allConfirmed) ? 'not-allowed' : 'pointer',
            opacity: (saving || !allConfirmed) ? .6 : 1,
          }}>
          <Icon name="check" size={13} />
          {saving ? 'Đang lưu...' : 'Lưu lịch sử'}
        </button>

        <button onClick={() => setCfgOpen(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', borderRadius: 6,
            border: '1px solid var(--border,#d1d5db)', background: '#fff',
            fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
            color: '#374151', cursor: 'pointer',
          }}>
          <Icon name="settings" size={13} />
          Cột&nbsp;<b>{visCols.length}/{allCols.length}</b>
        </button>
      </div>

      {/* table — shrink-wrap content, cap at available screen */}
      <div style={{
        flex: '0 1 auto', minHeight: 0,
        border: '1px solid var(--border,#e5e7eb)', borderRadius: 10,
        background: '#fff', overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {!data ? (
          <div style={{ padding: 40 }}><LoadingState label="Dang tai bang luong..." /></div>
        ) : emps.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center' }}><EmptyState>Khong co du lieu thang {month}/{year}.</EmptyState></div>
        ) : (
          <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
            <table style={{
              width: '100%', borderCollapse: 'separate', borderSpacing: 0,
              tableLayout: 'fixed',
              minWidth: CHK_W + fw.reduce((a, b) => a + b, 0) + visCols.reduce((s, c) => s + getW(c.code, dataDefW), 0) + 100,
            }}>
              <thead>
                <tr>
                  {/* checkbox header */}
                  <th style={{
                    ...P, position: 'sticky', left: 0, top: 0, zIndex: 6,
                    width: CHK_W, minWidth: CHK_W, maxWidth: CHK_W,
                    background: '#fafbfd', borderBottom: '1px solid #e5e7eb',
                    textAlign: 'center', padding: '10px 0',
                  }}>
                    <input type="checkbox" checked={allChecked} onChange={toggleAll}
                      style={{ width: 15, height: 15, accentColor: '#2563eb', cursor: 'pointer' }} />
                  </th>
                  {frozenBase.map((b, i) => (
                    <th key={b.key} style={{
                      ...sH(i), ...P, position: 'sticky', top: 0,
                      fontSize: 12, fontWeight: 600, color: '#6b7280',
                      textAlign: 'left',
                      borderBottom: '1px solid #e5e7eb', overflow: 'visible',
                      ...(i === frozenBase.length - 1 ? { boxShadow: '1px 0 0 #e5e7eb' } : {}),
                    }}>
                      {b.label}
                      <div data-rh="1" onMouseDown={(e) => startResize(b.key, fw[i], e)} />
                    </th>
                  ))}
                  {visCols.map((c) => {
                    const w = getW(c.code, dataDefW);
                    return (
                      <th key={c.code} style={{
                        ...P, position: 'sticky', top: 0, zIndex: 3,
                        fontSize: 12, fontWeight: 600, color: '#6b7280',
                        textAlign: 'left', background: '#fafbfd',
                        borderBottom: '1px solid #e5e7eb', width: w, minWidth: w, maxWidth: w,
                        overflow: 'visible',
                      }}>
                        {c.name}
                        <div data-rh="1" onMouseDown={(e) => startResize(c.code, w, e)} />
                      </th>
                    );
                  })}
                  {/* NV xac nhan header */}
                  <th style={{
                    ...P, position: 'sticky', top: 0, zIndex: 3,
                    fontSize: 12, fontWeight: 600, color: '#6b7280',
                    textAlign: 'center', background: '#fafbfd',
                    borderBottom: '1px solid #e5e7eb', width: 100, minWidth: 100, maxWidth: 100,
                  }}>
                    NV xác nhận
                  </th>
                </tr>
              </thead>
              <tbody>
                {emps.map((emp, idx) => {
                  const cs = CONFIRM_MAP[emp.employee_confirm] || CONFIRM_MAP.pending;
                  const rowBg = emp.employee_confirm === 'confirmed' ? '#f0fdf4'
                    : emp.employee_confirm === 'rejected' ? '#fef2f2' : '#fff';
                  const rowHover = emp.employee_confirm === 'confirmed' ? '#dcfce7'
                    : emp.employee_confirm === 'rejected' ? '#fee2e2' : '#f8fafc';
                  return (
                  <tr key={emp.id}
                    style={{
                      background: rowBg,
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = rowHover; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = rowBg; }}>
                    {/* checkbox cell */}
                    <td style={{
                      ...P, position: 'sticky', left: 0, zIndex: 2,
                      width: CHK_W, minWidth: CHK_W, maxWidth: CHK_W,
                      background: 'inherit', textAlign: 'center', padding: '10px 0',
                      borderBottom: '1px solid #e5e7eb',
                    }}>
                      {emp.payslip_id && (
                        <input type="checkbox" checked={!!checked[emp.payslip_id]}
                          onChange={(e) => { e.stopPropagation(); toggleOne(emp.payslip_id); }}
                          onClick={(e) => e.stopPropagation()}
                          style={{ width: 15, height: 15, accentColor: '#2563eb', cursor: 'pointer' }} />
                      )}
                    </td>
                    {frozenBase.map((b, i) => (
                      <td key={b.key} style={{
                        ...sD(i), ...P,
                        background: 'inherit',
                        textAlign: 'left',
                        fontWeight: b.key === 'name' ? 600 : 400,
                        borderBottom: '1px solid #e5e7eb',
                        ...(i === frozenBase.length - 1 ? { borderRight: '1px solid #e5e7eb' } : {}),
                      }}>
                        {b.key === 'name' ? (
                          <span
                            onClick={(e) => { e.stopPropagation(); setDetailEmp(emp); }}
                            style={{ color: '#2563eb', cursor: 'pointer' }}
                            onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
                          >{emp.name}</span>
                        ) : cellVal(emp, b.key, idx)}
                      </td>
                    ))}
                    {visCols.map((c) => {
                      const w = getW(c.code, dataDefW);
                      return (
                        <td key={c.code} style={{
                          ...P, textAlign: 'right', borderBottom: '1px solid #e5e7eb',
                          fontVariantNumeric: 'tabular-nums',
                          width: w, minWidth: w, maxWidth: w,
                        }}>
                          {emp.amounts[c.code] != null ? hbVND(emp.amounts[c.code]) : ''}
                        </td>
                      );
                    })}
                    {/* NV xac nhan cell */}
                    <td style={{
                      ...P, textAlign: 'center', borderBottom: '1px solid #e5e7eb',
                      width: 100, minWidth: 100, maxWidth: 100,
                    }}>
                      {emp.payslip_id && (
                        <span style={{
                          display: 'inline-block', padding: '3px 10px', borderRadius: 20,
                          fontSize: 11.5, fontWeight: 600,
                          background: cs.bg, color: cs.color,
                        }} title={emp.employee_feedback || ''}>
                          {cs.label}
                          {emp.email_sent && <span style={{ marginLeft: 4, fontSize: 10 }}>✉</span>}
                        </span>
                      )}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr>
                  {/* checkbox footer */}
                  <td style={{
                    ...P, position: 'sticky', left: 0, bottom: 0, zIndex: 5,
                    width: CHK_W, minWidth: CHK_W, maxWidth: CHK_W,
                    background: '#f8f9fb', borderTop: '1px solid #e5e7eb',
                  }} />
                  {frozenBase.map((b, i) => (
                    <td key={b.key} style={{
                      ...sF(i), ...P, position: 'sticky', bottom: 0,
                      fontWeight: 700, borderTop: '1px solid #e5e7eb',
                      textAlign: b.key === 'name' ? 'right' : 'left',
                      ...(i === frozenBase.length - 1 ? { borderRight: '1px solid #e5e7eb' } : {}),
                    }}>
                      {b.key === 'name' ? 'Tong' : ''}
                    </td>
                  ))}
                  {visCols.map((c) => {
                    const sum = emps.reduce((s, e) => s + (e.amounts[c.code] || 0), 0);
                    const w = getW(c.code, dataDefW);
                    return (
                      <td key={c.code} style={{
                        ...P, position: 'sticky', bottom: 0, zIndex: 3,
                        textAlign: 'right', fontWeight: 700,
                        background: '#f8f9fb', borderTop: '1px solid #e5e7eb',
                        fontVariantNumeric: 'tabular-nums',
                        width: w, minWidth: w, maxWidth: w,
                      }}>
                        {sum ? hbVND(sum) : ''}
                      </td>
                    );
                  })}
                  {/* NV xac nhan footer */}
                  <td style={{
                    ...P, position: 'sticky', bottom: 0, zIndex: 3,
                    background: '#f8f9fb', borderTop: '1px solid #e5e7eb',
                    width: 100, minWidth: 100, maxWidth: 100,
                  }} />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {cfgOpen && allCols.length > 0 && (
        <CfgModal dataCols={allCols} cfg={cfg} onApply={applyCfg} onClose={() => setCfgOpen(false)} />
      )}
      {detailEmp && <SalaryDetail emp={detailEmp} columns={allCols} onClose={() => setDetailEmp(null)} onChanged={load} />}
    </div>
  );
}
