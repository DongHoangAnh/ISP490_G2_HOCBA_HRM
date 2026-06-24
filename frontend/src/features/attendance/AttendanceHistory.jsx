/* Lịch sử chấm công đầy đủ — tab riêng với filter Thường / OT / Tất cả (chính thức)
   hoặc Công CTV (CTV). Spec: docs/superpowers/specs/2026-06-19-attendance-history-screen-design.md */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMyHistoryFull } from '../../api/attendance';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus, currentMonth, fmtCredit } from './util';
import AttendanceDrawer from './AttendanceDrawer';

function Sum({ val, lbl, col }) {
  return (
    <div className="stat" style={{ padding: '14px 16px' }}>
      <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1, color: col || 'inherit' }}>{val}</div>
      <div className="stat-lbl" style={{ marginTop: 4 }}>{lbl}</div>
    </div>
  );
}

function SummaryBar({ summary, filter, isTeacher }) {
  if (filter === 'regular') return (
    <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 16 }}>
      <Sum val={summary.daysPresent} lbl="Ngày có mặt" />
      <Sum val={summary.totalCredit} lbl="Tổng công" />
      <Sum val={summary.deficitCredit} lbl="Công thiếu" col={summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
      <Sum val={summary.netCredit} lbl="Công thực" col="var(--green)" />
    </div>
  );
  if (filter === 'ot') return (
    <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 16 }}>
      <Sum val={summary.otHours} lbl="Giờ OT" />
      <Sum val={summary.congOt} lbl="Công OT" col="var(--green)" />
    </div>
  );
  if (filter === 'ctv') return (
    <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginBottom: 16 }}>
      <Sum val={summary.ctvHours} lbl={isTeacher ? 'Giờ' : 'Giờ CTV'} />
      <Sum val={summary.congCtv} lbl={isTeacher ? 'Công' : 'Công CTV'} col="var(--green)" />
    </div>
  );
  // all
  return (
    <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(6,1fr)', marginBottom: 16 }}>
      <Sum val={summary.daysPresent} lbl="Ngày có mặt" />
      <Sum val={summary.totalCredit} lbl="Tổng công thường" />
      <Sum val={summary.deficitCredit} lbl="Công thiếu" col={summary.deficitCredit > 0 ? 'var(--amber)' : undefined} />
      <Sum val={summary.netCredit} lbl="Công thực" col="var(--green)" />
      <Sum val={summary.otHours} lbl="Giờ OT" />
      <Sum val={summary.congOt} lbl="Công OT" col="var(--green)" />
    </div>
  );
}

const ROW_TYPE_LABEL = { regular: 'Thường', ot: 'OT', ctv: 'CTV' };
const ROW_TYPE_COLOR = { regular: 'gray', ot: 'amber', ctv: 'blue' };

export default function AttendanceHistory({ me }) {
  const isTeacher = me && !!me.isTeacher;
  const isCtv = me && !me.isOfficial;

  // filter: 'all' | 'regular' | 'ot' (chính thức) | 'ctv' (CTV)
  const defaultFilter = isCtv ? 'ctv' : 'all';
  const [filter, setFilter] = useState(defaultFilter);
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchMyHistoryFull(month, filter).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [month, filter]);

  const FILTERS = isCtv
    ? [['ctv', 'Công CTV']]
    : [['all', 'Tất cả'], ['regular', 'Thường'], ['ot', 'OT']];

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="between" style={{ marginBottom: 14 }}>
        <h3 style={{ margin: 0 }}>Lịch sử chấm công của tôi</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="month" className="sel" value={month} onChange={(e) => setMonth(e.target.value)} />
        </div>
      </div>

      {/* Filter tabs */}
      {FILTERS.length > 1 && (
        <div className="tabs" style={{ marginBottom: 14 }}>
          {FILTERS.map(([id, lbl]) => (
            <button key={id} className={'tab' + (filter === id ? ' active' : '')} onClick={() => setFilter(id)}>{lbl}</button>
          ))}
        </div>
      )}

      {err && <ErrorState message={err} onRetry={load} />}
      {!data && !err && <LoadingState label="Đang tải lịch sử…" />}

      {data && (
        <>
          <SummaryBar summary={data.summary} filter={filter} isTeacher={isTeacher} />

          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Ngày</th><th>Check-in</th><th>Check-out</th>
                <th className="tbl-num">Giờ công</th><th className="tbl-num">Đi trễ</th>
                <th className="tbl-num">Về sớm</th><th className="tbl-num">Thiếu</th>
                <th className="tbl-num">Ngày công</th><th>Trạng thái</th><th></th>
              </tr></thead>
              <tbody>
                {data.rows.map((r) => {
                  const [lbl, kind] = attStatus(r.statusKey);
                  const showTypeBadge = filter === 'all' && r.rowType !== 'regular';
                  return (
                    <tr key={r.rowType + '-' + r.id} onClick={() => setSel(r)}>
                      <td className="mono">
                        <span title={r.shiftLabel || undefined}>{fmtDate(r.date)}</span>
                        {showTypeBadge && (
                          <Badge kind={ROW_TYPE_COLOR[r.rowType] || 'gray'} style={{ marginLeft: 6, fontSize: 10 }}>
                            {ROW_TYPE_LABEL[r.rowType]}
                          </Badge>
                        )}
                      </td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkIn)}</td>
                      <td className="mono" style={{ fontWeight: 600 }}>{fmtTime(r.checkOut)}</td>
                      <td className="tbl-num mono">{r.workingHours || '—'}</td>
                      <td className="tbl-num mono">{r.lateMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>+{r.lateMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono">{r.earlyLeaveMinutes > 0 ? <span style={{ color: 'var(--amber)', fontWeight: 600 }}>-{r.earlyLeaveMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono">{r.missingMinutes > 0 ? <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>{r.missingMinutes}'</span> : <span className="faint">—</span>}</td>
                      <td className="tbl-num mono" style={{ fontWeight: 600 }}>{fmtCredit(r.workCredit)}</td>
                      <td><span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                        <Badge kind={kind} dot>{lbl}</Badge>
                        {r.needsReview && <Badge kind="amber">!</Badge>}
                      </span></td>
                      <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {data.rows.length === 0 && <EmptyState>Chưa có bản ghi trong tháng này.</EmptyState>}
        </>
      )}

      {sel && <AttendanceDrawer rec={sel} onClose={() => setSel(null)} />}
    </div>
  );
}
