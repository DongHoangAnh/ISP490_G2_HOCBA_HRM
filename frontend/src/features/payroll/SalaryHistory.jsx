/* Lịch sử lương — xem lương đã khoá theo tháng/năm (read-only). Owner: Hùng. */
import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchSalaryHistory } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { downloadXlsx, sumFormula } from '../../utils/xlsx';
import { monthOptions, yearOptions, currentMonth, currentYear } from './util';

/* ── localStorage ── */
const LS_KEY = 'hb_history_col';
const LS_WIDTHS = 'hb_history_widths';
const loadCfg = () => { try { return JSON.parse(localStorage.getItem(LS_KEY)) || null; } catch { return null; } };
const saveCfg = (c) => localStorage.setItem(LS_KEY, JSON.stringify(c));
const loadWidths = () => { try { return JSON.parse(localStorage.getItem(LS_WIDTHS)) || {}; } catch { return {}; } };
const saveWidths = (w) => localStorage.setItem(LS_WIDTHS, JSON.stringify(w));

const BASE = [
  { key: 'stt',        label: 'STT',        w: 40  },
  { key: 'code',       label: 'Mã NV',      w: 76  },
  { key: 'name',       label: 'Họ và tên',  w: 150 },
  { key: 'job_title',  label: 'Chức vụ',    w: 110 },
  { key: 'department', label: 'Phòng ban',   w: 115 },
];

/* ── Receipt-style detail modal (read-only) ── */
function HistoryDetail({ emp, columns, onClose }) {
  const lastCode = columns.length > 0 ? columns[columns.length - 1].code : null;
  const NET_CODES = new Set(['thuc_lanh']);
  const netRow = columns.find((c) => NET_CODES.has(c.code));
  const netVal = netRow ? emp.amounts[netRow.code] : null;

  return (
    <Modal onClose={onClose}>
      <div style={{
        display: 'flex', flexDirection: 'column',
        height: 'calc(100vh - 100px)', maxHeight: 720,
        padding: '16px 24px 16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12, flexShrink: 0 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{emp.name}</h2>
            <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 3 }}>
              {[emp.code, emp.job_title, emp.department].filter(Boolean).join(' · ')}
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} style={{ marginTop: -4 }}><Icon name="x" size={18} /></button>
        </div>

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
      </div>
    </Modal>
  );
}

/* Màu mặc định khi bật tick (người dùng đổi được): nền tiêu đề xanh nhạt,
   nền giá trị vàng nhạt — giống mẫu bảng lương in cho sếp. */
const DEF_HEADER_FILL = '#BDD7EE';
const DEF_VALUE_FILL = '#FFF2CC';

/* Ô chọn màu 1 cột: tick bật/tắt + hộp màu. Tắt tick = để trắng bình thường. */
function ColorTick({ on, color, onToggle, onColor, title }) {
  return (
    <span title={title} style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <input type="checkbox" checked={on} onChange={onToggle}
        style={{ width: 14, height: 14, accentColor: '#2563eb', cursor: 'pointer' }} />
      <input type="color" value={color} disabled={!on} onChange={(e) => onColor(e.target.value)}
        style={{
          width: 24, height: 18, padding: 0, border: '1px solid #d1d5db', borderRadius: 4,
          background: on ? undefined : '#fff', opacity: on ? 1 : 0.35,
          cursor: on ? 'pointer' : 'not-allowed',
        }} />
    </span>
  );
}

/* ── Column config modal (hiển thị + thứ tự + màu in) ── */
function CfgModal({ dataCols, baseCols, cfg, onApply, onClose }) {
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
  const [hFill, setHFill] = useState(() => ({ ...(cfg.headerFill || {}) }));
  const [vFill, setVFill] = useState(() => ({ ...(cfg.valueFill || {}) }));
  const allOn = dataCols.length > 0 && dataCols.every((c) => vis[c.code]);
  const flipAll = () => { const on = !allOn; setVis(Object.fromEntries(dataCols.map((c) => [c.code, on]))); };
  const [dragCode, setDragCode] = useState(null);
  const nameOf = {};
  dataCols.forEach((c) => { nameOf[c.code] = c.name; });

  /* Reorder LIVE theo mã cột (không theo index tĩnh → không lệch sau re-render).
     Chèn trước/sau hàng đang hover theo điểm giữa (midpoint) và bù dịch khi bỏ
     phần tử → mượt, không dao động. VD: cột #5 kéo lên #2 thì #2,3,4 → #3,4,5. */
  const reorderOver = (e, overCode) => {
    e.preventDefault();
    if (dragCode == null || dragCode === overCode) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const after = (e.clientY - rect.top) > rect.height / 2;
    setOrd((prev) => {
      const from = prev.indexOf(dragCode);
      let to = prev.indexOf(overCode);
      if (from < 0 || to < 0) return prev;
      if (after) to += 1;      // thả vào nửa dưới → chèn sau hàng hover
      if (from < to) to -= 1;  // bù chỗ trống khi phần tử bị lấy ra ở trên
      if (to === from) return prev;
      const next = [...prev];
      next.splice(from, 1);
      next.splice(to, 0, dragCode);
      return next;
    });
  };

  const toggleFill = (setter, key, def) => setter((m) => {
    const n = { ...m }; if (n[key]) delete n[key]; else n[key] = def; return n;
  });
  const setFill = (setter, key, val) => setter((m) => ({ ...m, [key]: val }));

  /* 2 ô chọn màu (nền tiêu đề + nền giá trị) cho một cột theo khoá `key`. */
  const colorCtl = (key) => (
    <>
      <ColorTick title="Màu nền tiêu đề cột khi in"
        on={!!hFill[key]} color={hFill[key] || DEF_HEADER_FILL}
        onToggle={() => toggleFill(setHFill, key, DEF_HEADER_FILL)}
        onColor={(v) => setFill(setHFill, key, v)} />
      <ColorTick title="Màu nền giá trị (các ô số) khi in"
        on={!!vFill[key]} color={vFill[key] || DEF_VALUE_FILL}
        onToggle={() => toggleFill(setVFill, key, DEF_VALUE_FILL)}
        onColor={(v) => setFill(setVFill, key, v)} />
    </>
  );

  const rowSt = { display: 'flex', alignItems: 'center', gap: 8, padding: '7px 24px', borderBottom: '1px solid #f3f4f6', fontSize: 13 };
  const nameSt = { flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' };

  return (
    <Modal onClose={onClose}>
      <div style={{ padding: '20px 24px 14px', borderBottom: '1px solid var(--border,#e5e7eb)' }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Tuỳ chỉnh cột & màu in</h2>
        <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--muted,#6b7280)' }}>
          Mỗi cột có 2 ô màu: <b>nền tiêu đề</b> và <b>nền giá trị</b> khi xuất/in Excel.
          Bỏ tick = để trắng bình thường.
        </p>
      </div>

      {/* Chú thích 2 cột màu */}
      <div style={{ ...rowSt, background: 'var(--gray-50,#f9fafb)', color: 'var(--muted,#6b7280)', fontSize: 11.5, fontWeight: 600 }}>
        <span style={{ width: 15 }} />
        <span style={nameSt}>Cột</span>
        <span style={{ width: 42, textAlign: 'center' }}>Tiêu đề</span>
        <span style={{ width: 42, textAlign: 'center' }}>Giá trị</span>
        <span style={{ width: 15 }} />
      </div>

      <div style={{ maxHeight: '54vh', overflowY: 'auto' }}>
        {/* Cột cố định (STT, Mã NV, Họ tên, Chức vụ, Phòng ban) — chỉ chỉnh màu */}
        {baseCols.map((b) => (
          <div key={b.key} style={rowSt}>
            <span style={{ width: 15 }} />
            <span style={nameSt}>{b.label}</span>
            {colorCtl(b.key)}
            <span style={{ width: 15 }} />
          </div>
        ))}

        {/* Nhóm cột dữ liệu — bật/tắt hiển thị + kéo thả thứ tự + màu */}
        <label style={{ ...rowSt, cursor: 'pointer', background: 'var(--gray-50,#f9fafb)', fontSize: 13.5 }}>
          <input type="checkbox" checked={allOn} onChange={flipAll} style={{ width: 15, height: 15, accentColor: '#2563eb', cursor: 'pointer' }} />
          <span style={{ ...nameSt, fontWeight: 600 }}>Tất cả cột dữ liệu</span>
          <span style={{ fontSize: 12, color: 'var(--muted)' }}>{dataCols.filter((c) => vis[c.code]).length}/{dataCols.length}</span>
          <span style={{ width: 15 }} />
        </label>
        {ord.map((code) => (
          <div key={code}
            style={{
              ...rowSt,
              opacity: dragCode === code ? 0.45 : 1,
              background: dragCode === code ? 'var(--gray-50,#f9fafb)' : undefined,
              transition: 'background .12s',
            }}
            onDragOver={(e) => reorderOver(e, code)}
            onDrop={(e) => e.preventDefault()}>
            <input type="checkbox" checked={vis[code] !== false} onChange={() => setVis((v) => ({ ...v, [code]: !v[code] }))} style={{ width: 15, height: 15, accentColor: '#2563eb', cursor: 'pointer' }} />
            <span style={nameSt}>{nameOf[code] || code}</span>
            {colorCtl(code)}
            <span
              draggable
              onDragStart={(e) => { setDragCode(code); e.dataTransfer.effectAllowed = 'move'; }}
              onDragEnd={() => setDragCode(null)}
              title="Kéo để đổi thứ tự"
              style={{ cursor: 'grab', color: '#9ca3af', fontSize: 16, userSelect: 'none', width: 18, textAlign: 'center', touchAction: 'none' }}>&#9776;</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Huỷ</button>
        <button className="btn btn-primary" onClick={() => { onApply({ visible: vis, order: ord, headerFill: hFill, valueFill: vFill }); onClose(); }}>Áp dụng</button>
      </div>
    </Modal>
  );
}

/* ── Main ── */
export default function SalaryHistory() {
  const [month, setMonth] = useState(currentMonth());
  const [year, setYear] = useState(currentYear());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [detailEmp, setDetailEmp] = useState(null);
  const [cfgOpen, setCfgOpen] = useState(false);
  const [cfg, setCfg] = useState(() => loadCfg() || {});
  const [colWidths, setColWidths] = useState(() => loadWidths());
  const [localSearch, setLocalSearch] = useState('');
  const [periodOpen, setPeriodOpen] = useState(false);
  const periodRef = useRef(null);

  const applyCfg = useCallback((c) => { setCfg(c); saveCfg(c); }, []);

  /* close period dropdown on outside click */
  useEffect(() => {
    if (!periodOpen) return;
    const h = (e) => { if (periodRef.current && !periodRef.current.contains(e.target)) setPeriodOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [periodOpen]);

  const load = () => {
    setErr(null); setData(null);
    fetchSalaryHistory({ month, year }).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month, year]);

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

  if (err) return <ErrorState message={err} onRetry={load} />;

  const q = localSearch.toLowerCase();
  const emps = data ? data.employees.filter((e) => {
    if (!e.payslip_id) return false; // history only shows employees with payslips
    if (!q) return true;
    return (e.name || '').toLowerCase().includes(q)
      || (e.code || '').toLowerCase().includes(q)
      || (e.department || '').toLowerCase().includes(q)
      || (e.job_title || '').toLowerCase().includes(q);
  }) : [];

  const total = emps.length;

  const allCols = data ? data.columns : [];
  const sorted = (() => {
    const codes = allCols.map((c) => c.code);
    const o = (cfg.order || []).filter((c) => codes.includes(c));
    codes.forEach((c) => { if (!o.includes(c)) o.push(c); });
    return o.map((c) => allCols.find((x) => x.code === c)).filter(Boolean);
  })();
  const visCols = sorted.filter((c) => (cfg.visible || {})[c.code] !== false);

  const fw = BASE.map((b) => getW(b.key, b.w));
  const cumL = fw.map((_, i) => fw.slice(0, i).reduce((a, b) => a + b, 0));

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

  const P = { padding: '10px 14px', fontSize: 13.5, whiteSpace: 'nowrap', lineHeight: '20px', overflow: 'hidden', textOverflow: 'ellipsis' };
  const dataDefW = 110;

  const exportExcel = () => {
    const headers = [...BASE.map((b) => b.label), ...visCols.map((c) => c.name)];
    const body = emps.map((emp, idx) => [
      idx + 1, emp.code || '', emp.name || '', emp.job_title || '', emp.department || '',
      ...visCols.map((c) => (emp.amounts[c.code] != null ? emp.amounts[c.code] : '')),
    ]);
    // Hàng Tổng: dùng công thức SUM để Excel tự cộng (dữ liệu ở các hàng 2..N+1),
    // giúp đối chiếu số trên web với kết quả Excel tính. Cột dữ liệu bắt đầu ở
    // chỉ số 5 (sau 5 cột cố định STT/Mã NV/Họ tên/Chức vụ/Phòng ban).
    const firstRow = 2, lastRow = emps.length + 1;
    const totalRow = ['', '', 'Tổng', '', '',
      ...visCols.map((_, j) => sumFormula(5 + j, firstRow, lastRow))];
    body.push(totalRow);
    // Màu in theo cấu hình từng cột: [...cột cố định, ...cột dữ liệu hiển thị].
    const hf = cfg.headerFill || {}, vf = cfg.valueFill || {};
    const exportKeys = [...BASE.map((b) => b.key), ...visCols.map((c) => c.code)];
    const colStyles = exportKeys.map((k) => ({ headerFill: hf[k] || null, valueFill: vf[k] || null }));
    downloadXlsx(`lich-su-luong-T${month}-${year}.xlsx`, `Lịch sử lương T${month}-${year}`,
      headers, body, { colStyles, lastRowIsTotal: true });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexShrink: 0 }}>

        {/* search bar with period chip */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
          padding: '4px 10px', minWidth: 280, flex: '0 1 380px',
        }}>
          <Icon name="search" size={15} style={{ color: '#9ca3af', flexShrink: 0 }} />

          {/* Period chip — clickable dropdown */}
          <div ref={periodRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setPeriodOpen(!periodOpen)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '3px 10px', borderRadius: 5, fontSize: 12, fontWeight: 600,
                border: 'none', background: '#f3e8ff', color: '#7c3aed', cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              T{month}/{year}
              <span style={{ fontSize: 10, marginLeft: 2 }}>▾</span>
            </button>
            {periodOpen && (
              <div style={{
                position: 'absolute', top: '110%', left: 0, zIndex: 50,
                background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8,
                boxShadow: '0 4px 16px rgba(0,0,0,.12)', padding: 12, minWidth: 200,
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>Chọn kỳ lương</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <select className="sel" value={month} onChange={(e) => { setMonth(e.target.value); setPeriodOpen(false); }} style={{ flex: 1 }}>
                    {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <select className="sel" value={year} onChange={(e) => { setYear(e.target.value); setPeriodOpen(false); }} style={{ flex: 1 }}>
                    {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>
            )}
          </div>

          <input
            type="text"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Tìm tên, mã NV, phòng ban..."
            style={{ flex: 1, border: 'none', outline: 'none', fontSize: 13, background: 'transparent', minWidth: 100 }}
          />
          {localSearch && (
            <button onClick={() => setLocalSearch('')} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 2, color: '#9ca3af', display: 'flex', alignItems: 'center' }}>
              <Icon name="x" size={14} />
            </button>
          )}
        </div>

        {/* metrics */}
        {data && <>
          <div style={{ width: 1, height: 24, background: '#e5e7eb', margin: '0 2px' }} />
          <span style={{ fontSize: 11.5, color: '#6b7280' }}>
            NV: <b style={{ color: '#111827' }}>{total}</b>
          </span>
        </>}

        <div style={{ flex: 1 }} />

        <button onClick={exportExcel} disabled={!data || emps.length === 0}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 10px', borderRadius: 6,
            border: '1px solid var(--border,#d1d5db)', background: '#fff',
            fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
            color: emps.length === 0 ? '#9ca3af' : '#15803d',
            cursor: emps.length === 0 ? 'not-allowed' : 'pointer',
            opacity: emps.length === 0 ? 0.6 : 1,
          }}>
          <Icon name="download" size={13} />
          Xuất Excel
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

      {/* table */}
      <div style={{
        flex: '0 1 auto', minHeight: 0,
        border: '1px solid var(--border,#e5e7eb)', borderRadius: 10,
        background: '#fff', overflow: 'hidden', display: 'flex', flexDirection: 'column',
      }}>
        {!data ? (
          <div style={{ padding: 40 }}><LoadingState label="Đang tải lịch sử lương..." /></div>
        ) : emps.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center' }}><EmptyState>Không có dữ liệu lương tháng {month}/{year}.</EmptyState></div>
        ) : (
          <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
            <table style={{
              width: '100%', borderCollapse: 'separate', borderSpacing: 0,
              tableLayout: 'fixed',
              minWidth: fw.reduce((a, b) => a + b, 0) + visCols.reduce((s, c) => s + getW(c.code, dataDefW), 0) + 40,
            }}>
              <thead>
                <tr>
                  {BASE.map((b, i) => (
                    <th key={b.key} style={{
                      ...sH(i), ...P, position: 'sticky', top: 0,
                      fontSize: 12, fontWeight: 600, color: '#6b7280',
                      textAlign: 'left',
                      borderBottom: '1px solid #e5e7eb', overflow: 'visible',
                      ...(i === BASE.length - 1 ? { boxShadow: '1px 0 0 #e5e7eb' } : {}),
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
                </tr>
              </thead>
              <tbody>
                {emps.map((emp, idx) => (
                  <tr key={emp.id}
                    style={{ background: '#fff' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; }}>
                    {BASE.map((b, i) => (
                      <td key={b.key} style={{
                        ...sD(i), ...P, background: 'inherit', textAlign: 'left',
                        fontWeight: b.key === 'name' ? 600 : 400,
                        borderBottom: '1px solid #e5e7eb',
                        ...(i === BASE.length - 1 ? { borderRight: '1px solid #e5e7eb' } : {}),
                      }}>
                        {b.key === 'name' ? (
                          <span
                            onClick={() => setDetailEmp(emp)}
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
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  {BASE.map((b, i) => (
                    <td key={b.key} style={{
                      ...sF(i), ...P, position: 'sticky', bottom: 0,
                      fontWeight: 700, borderTop: '1px solid #e5e7eb',
                      textAlign: b.key === 'name' ? 'right' : 'left',
                      ...(i === BASE.length - 1 ? { borderRight: '1px solid #e5e7eb' } : {}),
                    }}>
                      {b.key === 'name' ? 'Tổng' : ''}
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
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {cfgOpen && allCols.length > 0 && (
        <CfgModal dataCols={allCols} baseCols={BASE} cfg={cfg} onApply={applyCfg} onClose={() => setCfgOpen(false)} />
      )}
      {detailEmp && <HistoryDetail emp={detailEmp} columns={allCols} onClose={() => setDetailEmp(null)} />}
    </div>
  );
}
