/* Tab "Sức khỏe NV" — cảnh báo burnout (Widget 5-6, BR-040). Chỉ officer
   (HR/Admin mọi phòng, Trưởng phòng phòng mình). Dữ liệu 90 ngày gần nhất.
   Spec: docs/superpowers/specs/2026-07-07-timeoff-burnout-dashboard-lapsed-link-design.md
   Owner: Nhật Anh. */
import Badge from '../../components/Badge';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
import { fetchBurnout } from '../../api/timeoff';
import Kpi from './Kpi';

/* Màu badge theo nhóm lý do (khớp 3 chuỗi risk_reason của SQL view). */
const reasonKind = (reason) => (
  reason.startsWith('Nghỉ ốm') ? 'red'
    : reason.startsWith('Vắng') ? 'amber' : 'gray'
);

export default function BurnoutPanel({ dept, onDeptChange }) {
  const { data, err, loading, reload } = useFetch(
    () => fetchBurnout(dept || undefined), [dept], `timeoff:burnout:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const k = data.kpi;
  const maxDept = Math.max(...data.byDepartment.map((r) => r.count), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {data.seeAll && (
        <div className="filterbar">
          <div style={{ marginLeft: 'auto' }}>
            <DeptSelect value={dept} onChange={onDeptChange} departments={data.allDepartments} />
          </div>
        </div>
      )}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Tổng cảnh báo" value={k.total}
          color={k.total > 0 ? 'var(--red-600)' : 'var(--ink)'}
          sub="nhân viên trong diện theo dõi" />
        <Kpi label="Nghỉ ốm thường xuyên" value={k.sickFreq} color="var(--red-600)"
          sub="≥3 lần / 3 tháng" />
        <Kpi label="Vắng nhiều" value={k.highAbsence} color="var(--amber)"
          sub=">10 ngày / 3 tháng" />
        <Kpi label="Sắp cạn phép" value={k.lowBalance}
          sub="số dư < 2 ngày" />
      </div>

      {data.byDepartment.length > 0 && (
        <div className="card">
          <div className="card-head"><h3>Cảnh báo theo phòng ban</h3></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 13, padding: 16 }}>
            {data.byDepartment.map((r) => (
              <div key={r.id || r.name}>
                <div className="between" style={{ marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</span>
                  <span className="muted mono" style={{ fontSize: 12 }}>{r.count} NV</span>
                </div>
                <div className="bar">
                  <span style={{ width: (r.count / maxDept) * 100 + '%', background: 'var(--red-600)' }}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-head">
          <h3>Nhân viên trong diện cảnh báo</h3>
          <span className="sub">{data.items.length} nhân viên — dữ liệu 90 ngày gần nhất (BR-040)</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th>
              <th className="tbl-num">Nghỉ ốm (3 tháng)</th>
              <th className="tbl-num">Ngày vắng (3 tháng)</th>
              <th className="tbl-num">Số dư phép</th>
              <th>Lý do cảnh báo</th>
            </tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.employeeId}>
                  <td style={{ fontWeight: 600 }}>{r.employee}</td>
                  <td className="muted">{r.department}</td>
                  <td className="tbl-num mono">{r.sickCount3m} lần</td>
                  <td className="tbl-num mono">{r.absenceDays3m} ngày</td>
                  <td className="tbl-num mono">{r.remainingBalance} ngày</td>
                  <td style={{ overflow: 'visible', maxWidth: 'none', whiteSpace: 'nowrap' }}>
                    <Badge kind={reasonKind(r.riskReason)}>{r.riskReason}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.items.length === 0 && (
          <EmptyState>Không có nhân viên nào trong diện cảnh báo. 🎉</EmptyState>
        )}
      </div>
    </div>
  );
}
