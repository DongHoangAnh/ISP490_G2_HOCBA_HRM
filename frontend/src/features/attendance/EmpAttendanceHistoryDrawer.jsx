/* Lịch sử chấm công đầy đủ 1 NV cho manager: thường + OT + CTV theo tháng.
   Manager sửa trực tiếp từng bản ghi (trừ tên). */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchEmpHistory } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus, fmtCredit } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Sum({ val, lbl, col }) {
  return (
    <div className="stat" style={{ padding: '12px 14px' }}>
      <div style={{ fontSize: 20, fontWeight: 800, lineHeight: 1, color: col || 'inherit' }}>{val}</div>
      <div className="stat-lbl" style={{ marginTop: 3 }}>{lbl}</div>
    </div>
  );
}

const ROW_TYPE_LABEL = { regular: 'Thường', ot: 'OT', ctv: 'CTV' };
const ROW_TYPE_COLOR = { regular: 'gray', ot: 'amber', ctv: 'blue' };

const FILTERS = [
  ['all', 'Tất cả'],
  ['regular', 'Thường'],
  ['ot', 'OT'],
  ['ctv', 'CTV'],
];

export default function EmpAttendanceHistoryDrawer({ emp, month, onClose, onChanged }) {
  const [filter, setFilter] = useState('all');
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchEmpHistory(emp.empId, month, filter).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [emp.empId, month, filter]);

  return (
    <Modal onClose={onClose} lg>
      {/* Header */}
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{emp.empName}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
            {emp.code} · {emp.depName} · Tháng {month}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '16px 20px', maxHeight: '72vh', overflowY: 'auto' }}>
        {/* Filter tabs */}
        <div className="tabs" style={{ marginBottom: 14 }}>
          {FILTERS.map(([id, lbl]) => (
            <button key={id} className={'tab' + (filter === id ? ' active' : '')}
              onClick={() => setFilter(id)}>{lbl}</button>
          ))}
        </div>

        {err && <ErrorState message={err} onRetry={load} />}
        {!data && !err && <LoadingState label="Đang tải lịch sử…" />}

        {data && (
          <>
            {/* Summary */}
            {filter === 'all' && (
              <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 14 }}>
                <Sum val={data.summary.totalCredit} lbl="Tổng công thường" />
                <Sum val={data.summary.congOt} lbl="Công OT" col="var(--amber)" />
                <Sum val={data.summary.congCtv} lbl="Công CTV" col="#1D4ED8" />
                <Sum val={data.summary.deficitCredit} lbl="Công thiếu"
                  col={data.summary.deficitCredit > 0 ? 'var(--red-600)' : undefined} />
              </div>
            )}
            {filter === 'regular' && (
              <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 14 }}>
                <Sum val={data.summary.totalCredit} lbl="Tổng công" />
                <Sum val={data.summary.deficitCredit} lbl="Công thiếu"
                  col={data.summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
                <Sum val={data.summary.netCredit} lbl="Công thực" col="var(--green)" />
              </div>
            )}
            {filter === 'ot' && (
              <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 14 }}>
                <Sum val={data.summary.otHours} lbl="Giờ OT" />
                <Sum val={data.summary.congOt} lbl="Công OT" col="var(--amber)" />
              </div>
            )}
            {filter === 'ctv' && (
              <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 14 }}>
                <Sum val={data.summary.ctvHours} lbl="Giờ CTV" />
                <Sum val={data.summary.congCtv} lbl="Công CTV" col="#1D4ED8" />
              </div>
            )}

            {/* Table */}
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr>
                  <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                  <th className="tbl-num">Giờ công</th>
                  <th className="tbl-num">Đi trễ</th>
                  <th className="tbl-num">Thiếu</th>
                  <th className="tbl-num">Ngày công</th>
                  <th>Trạng thái</th>
                  <th></th>
                </tr></thead>
                <tbody>
                  {data.rows.map((r) => {
                    const [stLbl, stKind] = attStatus(r.statusKey);
                    const showTypeBadge = filter === 'all' && r.rowType !== 'regular';
                    return (
                      <tr key={r.rowType + '-' + r.id} style={{ cursor: 'pointer' }}
                        onClick={() => setSel(r)}>
                        <td className="mono">
                          <span title={r.shiftLabel || undefined}>{fmtDate(r.date)}</span>
                          {showTypeBadge && (
                            <Badge kind={ROW_TYPE_COLOR[r.rowType] || 'gray'}
                              style={{ marginLeft: 6, fontSize: 10 }}>
                              {ROW_TYPE_LABEL[r.rowType]}
                            </Badge>
                          )}
                        </td>
                        <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                        <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                        <td className="tbl-num mono">{r.workingHours || '—'}</td>
                        <td className="tbl-num mono">
                          {r.lateMinutes > 0
                            ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span>
                            : <span className="faint">—</span>}
                        </td>
                        <td className="tbl-num mono">
                          {r.missingMinutes > 0
                            ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span>
                            : <span className="faint">—</span>}
                        </td>
                        <td className="tbl-num mono" style={{ fontWeight: 600 }}>
                          {fmtCredit(r.workCredit)}
                        </td>
                        <td>
                          <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                            <Badge kind={stKind} dot>{stLbl}</Badge>
                            {r.needsReview && <Badge kind="amber">!</Badge>}
                          </span>
                        </td>
                        <td>
                          <button className="icon-btn"
                            onClick={(e) => { e.stopPropagation(); setSel(r); }}>
                            <Icon name="chevR" size={18} className="faint" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {data.rows.length === 0 && <EmptyState>Chưa có bản ghi trong tháng này.</EmptyState>}
          </>
        )}
      </div>

      {/* Chi tiết / sửa 1 bản ghi — dùng lại AttendanceDrawer, canManage=true */}
      {sel && (
        <AttendanceDrawer
          rec={{ ...sel, name: emp.empName }}
          canManage
          onClose={() => setSel(null)}
          onChanged={() => { setSel(null); load(); if (onChanged) onChanged(); }}
        />
      )}
    </Modal>
  );
}
