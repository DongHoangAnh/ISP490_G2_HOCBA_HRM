/* Tab "Tổng quan" — dashboard Nghỉ phép, tự đổi view Manager/Nhân viên
   theo quyền (tái hiện OWL dashboard hr_holidays_modern). Owner: Nhật Anh.
   Spec §3.6. */
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
import { fmtDate } from '../../utils/format';
import { fetchDashboard } from '../../api/timeoff';
import Kpi from './Kpi';

export default function DashboardPanel({ year, onYearChange, dept, onDeptChange }) {
  const { data, err, loading, reload } = useFetch(
    () => fetchDashboard(year, dept || undefined), [year, dept],
    `timeoff:dashboard:${year}:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const nav = <YearNav year={year} onChange={onYearChange} />;

  return data.isManager
    ? <ManagerView data={data} year={year} dept={dept} onDeptChange={onDeptChange} nav={nav} />
    : <EmployeeView data={data} nav={nav} />;
}

function BarList({ rows, unit = 'ngày', onEmpty = 'Chưa có dữ liệu.' }) {
  if (!rows.length) return <EmptyState>{onEmpty}</EmptyState>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 13, padding: '4px 2px' }}>
      {rows.map((r) => (
        <div key={r.id || r.name}>
          <div className="between" style={{ marginBottom: 5 }}>
            <span style={{ fontSize: 13, fontWeight: 600, display: 'inline-flex', gap: 8, alignItems: 'center' }}>
              <span style={{ width: 9, height: 9, borderRadius: 3, background: r.color }}></span>{r.name}
            </span>
            <span className="muted mono" style={{ fontSize: 12 }}>{r.days} {unit} · {r.count} đơn</span>
          </div>
          <div className="bar"><span style={{ width: r.pct + '%', background: r.color }}></span></div>
        </div>
      ))}
    </div>
  );
}

/* ---------- View Manager ---------- */
function ManagerView({ data, dept, onDeptChange, nav }) {
  const k = data.kpi;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="filterbar">
        {nav}
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={onDeptChange} departments={data.departments} />
        </div>
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))' }}>
        {/* Thứ tự theo vòng đời đơn: tổng → chờ → duyệt → từ chối → quá hạn →
            đang nghỉ. "Đã từ chối" thay ô "Tuổi đơn cũ nhất" (BE vẫn trả
            oldestAgeDays/avgAgeDays, chỉ không hiện ở đây). */}
        <Kpi label="Tổng đơn (năm)" value={k.total} />
        <Kpi label="Chờ duyệt" value={k.pending} color="var(--amber)" sub="cần xử lý" />
        <Kpi label="Đã duyệt" value={k.approved} color="var(--green)"
          sub={`${k.approvedDays} ngày phép đã duyệt`} />
        <Kpi label="Đã từ chối" value={k.refused} color="var(--red-600)"
          sub="trong năm" />
        <Kpi label={`Đơn quá hạn (> ${k.slaDays} ngày)`} value={k.overdue}
          color={k.overdue > 0 ? 'var(--red-600)' : 'var(--ink)'}
          sub={k.overdue > 0 ? 'cần xử lý gấp' : 'trong SLA'} />
        <Kpi label="Đang nghỉ hôm nay" value={k.onLeaveToday} color="var(--blue)" />
      </div>

      {data.overdueRequests && data.overdueRequests.length > 0 && (
        <div className="card">
          <div className="card-head">
            <h3>Đơn quá hạn duyệt</h3>
            <span className="sub">{data.overdueRequests.length} đơn vượt SLA {k.slaDays} ngày làm việc</span>
          </div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Nhân viên</th><th>Phòng ban</th><th>Loại</th>
                <th>Ngày tạo</th><th>Từ</th><th>Đến</th>
                <th className="tbl-num">Ngày</th><th className="tbl-num">Tuổi đơn</th>
                <th>Trạng thái</th>
              </tr></thead>
              <tbody>
                {data.overdueRequests.map((r) => (
                  <tr key={r.requestId} style={{
                    background: r.ageDays > k.slaDays * 2
                      ? 'var(--red-50)' : 'var(--amber-bg,#fff7ed)',
                  }}>
                    <td style={{ fontWeight: 600 }}>{r.employee}
                      {r.isEmergency && <Badge kind="red">Khẩn</Badge>}</td>
                    <td className="muted">{r.department}</td>
                    <td>{r.leaveType}</td>
                    <td className="mono muted">{fmtDate(r.submittedAt)}</td>
                    <td className="mono muted">{fmtDate(r.from)}</td>
                    <td className="mono muted">{fmtDate(r.to)}</td>
                    <td className="tbl-num mono">{r.days}</td>
                    <td className="tbl-num mono" style={{
                      fontWeight: 700,
                      color: r.ageDays > k.slaDays * 2 ? 'var(--red-700)' : 'var(--amber-700,#b45309)',
                    }}>{r.ageDays} ngày</td>
                    <td><Badge kind="amber" dot>{r.stateLabel}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-head"><h3>Theo loại nghỉ</h3></div>
          <div style={{ padding: 16 }}><BarList rows={data.byType} /></div>
        </div>
        <div className="card">
          <div className="card-head"><h3>Theo phòng ban</h3></div>
          <div style={{ padding: 16 }}><BarList rows={data.byDept} /></div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: 16 }}>
        <div className="card">
          <div className="card-head"><h3>Top nhân viên nghỉ nhiều</h3></div>
          <div style={{ padding: 16 }}><BarList rows={data.topEmployees} /></div>
        </div>
        <div className="card">
          <div className="card-head">
            <h3>Đơn chờ duyệt</h3><span className="sub">{data.pending.length} đơn mới nhất</span>
          </div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Nhân viên</th><th>Loại</th><th>Từ</th><th>Đến</th><th className="tbl-num">Ngày</th></tr></thead>
              <tbody>
                {data.pending.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600 }}>{p.employee}{p.isEmergency && <Badge kind="red">Khẩn</Badge>}</td>
                    <td>{p.leaveType}</td>
                    <td className="mono muted">{fmtDate(p.from)}</td>
                    <td className="mono muted">{fmtDate(p.to)}</td>
                    <td className="tbl-num mono">{p.days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.pending.length === 0 && <EmptyState>Không có đơn chờ duyệt.</EmptyState>}
        </div>
      </div>
    </div>
  );
}

/* ---------- View Nhân viên ---------- */
function EmployeeView({ data, nav }) {
  if (data.empMissing) {
    return <EmptyState>Tài khoản chưa gắn hồ sơ nhân viên — chưa có dữ liệu nghỉ phép.</EmptyState>;
  }
  const k = data.empKpi;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="filterbar">{nav}</div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Tổng phép còn lại" value={data.totalRemaining} color="var(--red-600)" sub="ngày" />
        <Kpi label="Đơn chờ duyệt" value={k.pending} color="var(--amber)" />
        <Kpi label="Đơn đã duyệt (năm)" value={k.approved} color="var(--green)" />
        <Kpi label="Ngày phép đã dùng" value={k.approvedDays} sub="trong năm" />
      </div>

      <div className="card">
        <div className="card-head"><h3>Số dư phép theo loại</h3></div>
        <div style={{ padding: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: 14 }}>
          {data.balances.map((b) => (
            <div key={b.id} className="card" style={{ padding: 16, boxShadow: 'none', border: '1px solid var(--border)' }}>
              <div className="between">
                <span style={{ fontWeight: 700, fontSize: 13, display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ width: 9, height: 9, borderRadius: 3, background: b.color }}></span>{b.name}
                </span>
                {b.low && <Badge kind="amber">Sắp hết</Badge>}
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, margin: '8px 0 6px' }}>
                <span style={{ fontSize: 24, fontWeight: 800 }}>{b.remaining}</span>
                <span className="muted" style={{ fontSize: 12 }}>/ {b.allocated} còn lại</span>
              </div>
              <div className="bar"><span style={{ width: b.pct + '%', background: b.low ? 'var(--amber)' : b.color }}></span></div>
              <div className="muted" style={{ fontSize: 11.5, marginTop: 5 }}>đã dùng {b.taken} ngày</div>
            </div>
          ))}
          {data.balances.length === 0 && <EmptyState>Chưa có phân bổ phép nào.</EmptyState>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-head"><h3>Đơn nghỉ gần đây</h3></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Loại</th><th>Từ</th><th>Đến</th><th className="tbl-num">Ngày</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {data.myRequests.map((r) => (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 600 }}>{r.leaveType}</td>
                    <td className="mono muted">{fmtDate(r.from)}</td>
                    <td className="mono muted">{fmtDate(r.to)}</td>
                    <td className="tbl-num mono">{r.days}</td>
                    <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.myRequests.length === 0 && <EmptyState>Chưa có đơn nghỉ nào.</EmptyState>}
        </div>

        <div className="card">
          <div className="card-head"><h3>Nghỉ sắp tới</h3></div>
          <div style={{ padding: '8px 12px' }}>
            {data.upcoming.map((u) => (
              <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '10px 8px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ width: 34, height: 34, borderRadius: 9, background: 'var(--red-50)', color: 'var(--red-600)', display: 'grid', placeItems: 'center' }}>
                  <Icon name="calendar" size={16} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{u.leaveType}</div>
                  <div className="muted" style={{ fontSize: 11.5 }}>{fmtDate(u.from)} → {fmtDate(u.to)}</div>
                </div>
                <span className="mono muted" style={{ fontSize: 12 }}>{u.days} ngày</span>
              </div>
            ))}
            {data.upcoming.length === 0 && <EmptyState>Không có lịch nghỉ sắp tới.</EmptyState>}
          </div>
        </div>
      </div>
    </div>
  );
}
