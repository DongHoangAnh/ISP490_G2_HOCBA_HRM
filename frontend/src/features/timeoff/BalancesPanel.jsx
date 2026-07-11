/* Trang "Quỹ phép" — số dư phép của toàn bộ nhân viên trong phạm vi quản lý.
   HR/Admin xem mọi phòng ban; Trưởng phòng chỉ phòng ban mình quản lý (gồm
   phòng con). Lọc theo năm + phòng ban, sắp xếp, xuất Excel. Owner: Nhật Anh.
   Phase 1 — spec docs/superpowers/specs/2026-06-21-timeoff-hr-quota-management-design.md */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { LoadingState, ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
import { downloadXlsx } from '../../utils/xlsx';
import { fetchBalances, adjustQuota, fetchAdjustHistory } from '../../api/timeoff';
import SortBar, { sortRows } from './SortBar';
import Kpi from './Kpi';

/* Datetime ISO (UTC từ Odoo) → "dd/mm/yyyy HH:MM". */
function fmtDateTime(s) {
  if (!s) return '—';
  const [datePart, timePart] = String(s).split('T');
  const [y, m, d] = datePart.split('-');
  const hm = (timePart || '').slice(0, 5);
  return `${d}/${m}/${y}${hm ? ' ' + hm : ''}`;
}

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

const SORT_FIELDS = [
  { key: 'employee', label: 'Nhân viên', type: 'text' },
  { key: 'department', label: 'Phòng ban', type: 'text' },
  { key: 'totalAllocated', label: 'Tổng được cấp', type: 'num' },
  { key: 'totalTaken', label: 'Tổng đã dùng', type: 'num' },
  { key: 'totalRemaining', label: 'Tổng còn lại', type: 'num' },
];

export default function BalancesPanel({ search, year, onYearChange, dept, onDeptChange }) {
  const [sort, setSort] = useState({ key: 'totalRemaining', dir: 'asc' });
  const [adjust, setAdjust] = useState(null);   // dòng đang điều chỉnh
  const [history, setHistory] = useState(null); // dòng đang xem lịch sử
  const [expiring, setExpiring] = useState(false); // lọc "sắp mất phép"
  const { data, err, loading, reload } = useFetch(
    () => fetchBalances(year, dept || undefined, undefined, expiring ? 'expiring' : undefined),
    [year, dept, expiring], `timeoff:balances:${year}:${dept}:${expiring ? 1 : 0}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const types = data.leaveTypes || [];
  const k = data.kpi || {};
  const q = (search || '').toLowerCase();
  const rows = sortRows(
    (data.rows || []).filter((r) =>
      !q || (r.employee || '').toLowerCase().includes(q)
         || (r.department || '').toLowerCase().includes(q)),
    SORT_FIELDS, sort);

  // Tra cứu số dư của 1 NV theo leaveTypeId (rows trả balances theo cùng tập loại).
  const balOf = (row, typeId) =>
    (row.balances || []).find((b) => b.leaveTypeId === typeId);

  const exportExcel = () => {
    const headers = ['Nhân viên', 'Phòng ban'];
    types.forEach((t) => {
      headers.push(`${t.name} — Được cấp`, `${t.name} — Đã dùng`, `${t.name} — Còn lại`);
    });
    headers.push('Tổng còn lại');
    const body = rows.map((r) => {
      const cells = [r.employee || '', r.department || ''];
      types.forEach((t) => {
        const b = balOf(r, t.id);
        cells.push(b ? Number(b.allocated) : 0, b ? Number(b.taken) : 0,
          b ? Number(b.remaining) : 0);
      });
      cells.push(Number(r.totalRemaining) || 0);
      return cells;
    });
    const deptName = dept
      ? (data.allDepartments.find((d) => String(d.id) === String(dept))?.name || '')
      : '';
    const fn = `quy-phep-${year}${deptName ? '-' + deptName.replace(/\s+/g, '_') : ''}.xlsx`;
    downloadXlsx(fn, `Quỹ phép ${year}`, headers, body);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Thanh điều khiển */}
      <div className="filterbar">
        <YearNav year={year} onChange={onYearChange} />
        <button className={'btn btn-sm ' + (expiring ? 'btn-primary' : 'btn-soft')}
          onClick={() => setExpiring((v) => !v)} title={`Còn ≥ ${data.atRiskDays ?? 5} ngày phép năm chưa dùng`}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginLeft: 12 }}>
          <Icon name="bell" size={15} />Sắp mất phép{(k.atRisk ?? 0) > 0 ? ` (${k.atRisk})` : ''}
        </button>
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={onDeptChange} departments={data.allDepartments} />
        </div>
      </div>

      {/* KPI */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Nhân viên" value={k.employees ?? 0} sub="trong phạm vi" />
        <Kpi label="Tổng ngày còn lại" value={k.totalRemaining ?? 0} sub="cộng dồn toàn đội" />
        <Kpi label="Sắp hết phép" value={k.lowBalance ?? 0} sub="còn ≤ 2 ngày" color="var(--amber-600,#d97706)" />
        <Kpi label="Sắp mất phép" value={k.atRisk ?? 0}
          sub={`còn ≥ ${data.atRiskDays ?? 5} ngày phép năm`} color="var(--red-600)" />
      </div>

      {/* Bảng số dư */}
      <div className="card">
        <div className="card-head">
          <h3>Quỹ phép theo nhân viên</h3>
          <span className="sub">{rows.length} nhân viên</span>
          <div className="actions">
            <SortBar fields={SORT_FIELDS} sort={sort} onChange={setSort} />
            <button className="btn btn-soft btn-sm" onClick={exportExcel} disabled={rows.length === 0}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Icon name="download" size={15} />Xuất Excel</button>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th>
              {types.map((t) => (
                <th key={t.id} className="tbl-num">{t.name}<br />
                  <span className="muted" style={{ fontWeight: 400, fontSize: 11 }}>còn / cấp</span></th>
              ))}
              <th className="tbl-num">Tổng còn lại</th>
              <th></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.employeeId} style={r.atRisk ? { background: 'var(--amber-bg,#fff7ed)' } : undefined}>
                  <td style={{ fontWeight: 600 }}>
                    {r.employee}
                    {r.atRisk && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2,
                        fontWeight: 500, fontSize: 11.5, color: '#b45309' }}>
                        <Icon name="bell" size={12} />Hết hạn {fmtDateTime(r.expireDate)}</span>
                    )}
                  </td>
                  <td className="muted">{r.department}</td>
                  {types.map((t) => {
                    const b = balOf(r, t.id);
                    return (
                      <td key={t.id} className="tbl-num mono">
                        {b ? (
                          <span>
                            <Badge kind={b.kind}>{b.remaining}</Badge>
                            <span className="muted" style={{ marginLeft: 4 }}>/ {b.allocated}</span>
                          </span>
                        ) : <span className="muted">—</span>}
                      </td>
                    );
                  })}
                  <td className="tbl-num mono" style={{ fontWeight: 700 }}>
                    <Badge kind={r.totalRemaining <= 0 ? 'red' : (r.totalRemaining <= 2 ? 'amber' : 'teal')}>
                      {r.totalRemaining}</Badge>
                  </td>
                  {/* width:1% + nowrap + overflow visible: ô tự co theo nội dung,
                      không bị quy tắc .tbl td (max-width:0; overflow:hidden) cắt
                      mất nút "Điều chỉnh" bên trái. */}
                  <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                      {data.isHrManager && (
                        <button className="btn btn-primary btn-sm" onClick={() => setAdjust(r)}>
                          Điều chỉnh</button>
                      )}
                      <button className="btn btn-ghost btn-sm" onClick={() => setHistory(r)}>
                        Lịch sử</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Không có nhân viên nào trong phạm vi.</EmptyState>}
      </div>

      {adjust && (
        <AdjustQuotaModal row={adjust} leaveTypes={types}
          onClose={() => setAdjust(null)}
          onDone={() => { setAdjust(null); reload(); }} />
      )}
      {history && (
        <HistoryModal row={history} onClose={() => setHistory(null)} />
      )}
    </div>
  );
}

/* Modal điều chỉnh quỹ (chỉ HR Manager): chọn loại nghỉ, nhập +/- ngày, lý do. */
function AdjustQuotaModal({ row, leaveTypes, onClose, onDone }) {
  const [leaveTypeId, setLeaveTypeId] = useState(leaveTypes[0]?.id || '');
  const [delta, setDelta] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const cur = (row.balances || []).find((b) => b.leaveTypeId === Number(leaveTypeId));
  const deltaNum = parseFloat(delta);
  const valid = leaveTypeId && !Number.isNaN(deltaNum) && deltaNum !== 0 && reason.trim();

  const submit = () => {
    setErr(null); setBusy(true);
    adjustQuota({ employeeId: row.employeeId, leaveTypeId: Number(leaveTypeId),
      deltaDays: deltaNum, reason: reason.trim() })
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="calendar" title="Điều chỉnh quỹ phép"
        sub={`${row.employee} · ${row.department}`} onClose={onClose} />

      <div style={{ padding: '22px 24px', display: 'grid', gap: 14 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Loại nghỉ</span>
          <select style={inp} value={leaveTypeId} onChange={(e) => setLeaveTypeId(e.target.value)}>
            {leaveTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          {cur && <span className="muted" style={{ fontSize: 12 }}>Hiện còn {cur.remaining} / {cur.allocated} ngày.</span>}
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Số ngày (+ cấp thêm / − trừ bớt)</span>
          <input style={inp} type="number" step="0.5" value={delta}
            onChange={(e) => setDelta(e.target.value)} placeholder="VD: 3 hoặc -2" />
          {cur && !Number.isNaN(deltaNum) && deltaNum !== 0 && (
            <span className="muted" style={{ fontSize: 12 }}>
              Sau điều chỉnh: còn {Math.round((cur.remaining + deltaNum) * 100) / 100} ngày.</span>
          )}
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Lý do *</span>
          <textarea style={{ ...inp, resize: 'vertical' }} rows={2} value={reason}
            onChange={(e) => setReason(e.target.value)} placeholder="VD: Thưởng thâm niên / sửa nhầm phân bổ…" />
        </label>

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={submit} disabled={!valid || busy}>
          {busy ? 'Đang lưu…' : 'Lưu điều chỉnh'}</button>
      </div>
    </Modal>
  );
}

/* Modal nhật ký điều chỉnh quỹ của 1 nhân viên. */
function HistoryModal({ row, onClose }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setErr(null); setData(null);
    fetchAdjustHistory(row.employeeId).then(setData).catch((e) => setErr(e.message));
  }, [row.employeeId]);

  const list = data?.history || [];
  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="file" title="Lịch sử điều chỉnh"
        sub={`${row.employee} · ${row.department}`} onClose={onClose} />

      <div style={{ padding: '16px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        {err && <ErrorState message={err} />}
        {!err && !data && <LoadingState label="Đang tải lịch sử…" />}
        {data && list.length === 0 && <EmptyState>Chưa có điều chỉnh nào cho nhân viên này.</EmptyState>}
        {data && list.length > 0 && (
          <table className="tbl">
            <thead><tr>
              <th>Thời điểm</th><th>Loại nghỉ</th><th className="tbl-num">Thay đổi</th>
              <th>Lý do</th><th>Người chỉnh</th>
            </tr></thead>
            <tbody>
              {list.map((h) => (
                <tr key={h.id}>
                  <td className="mono muted">{fmtDateTime(h.appliedDate)}</td>
                  <td>{h.leaveType}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 700 }}>
                    <Badge kind={h.deltaDays >= 0 ? 'green' : 'red'}>
                      {h.deltaDays > 0 ? '+' : ''}{h.deltaDays}</Badge>
                  </td>
                  <td className="muted">{h.reason}</td>
                  <td className="muted">{h.appliedBy || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
