/* ============================================================
   Màn Nghỉ phép — self-service + duyệt đơn (mẫu chuẩn: màn Nhân viên).
   Owner: Nhật Anh. Spec: docs/SPEC_API_TIMEOFF.md
   ============================================================ */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchOverview, cancelRequest } from '../../api/timeoff';
import SortBar, { sortRows } from './SortBar';
import LeaveForm from './LeaveForm';
import ApprovalPanel from './ApprovalPanel';
import ApprovedPanel from './ApprovedPanel';
import BalancesPanel from './BalancesPanel';
import DashboardPanel from './DashboardPanel';
import CalendarPanel from './CalendarPanel';
import SummaryPanel from './SummaryPanel';
import WorkScheduleModal from './WorkScheduleModal';

export default function TimeOff({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(null);
  const [creating, setCreating] = useState(false);
  const [schedOpen, setSchedOpen] = useState(false); // modal lịch làm việc (HR)
  const [busy, setBusy] = useState(null); // id đơn đang hủy

  const load = () => {
    setErr(null); setData(null);
    fetchOverview().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nghỉ phép…" />;

  const onCancel = (id) => {
    if (!window.confirm('Hủy đơn nghỉ này?')) return;
    setBusy(id);
    cancelRequest(id)
      .then(setData)
      .catch((e) => alert('Không hủy được đơn: ' + e.message))
      .finally(() => setBusy(null));
  };

  // Tách luồng cá nhân / quản lý theo phân quyền:
  //  - Quản lý (officer): "Tổng quan" + "Lịch" + "Chờ duyệt" + "Đơn đã duyệt".
  //    KHÔNG có tab "Của tôi" (luồng quản lý thuần).
  //  - Nhân viên: "Tổng hợp" (báo cáo cá nhân) + "Của tôi" + "Lịch".
  const tabs = [];
  if (data.isOfficer) {
    tabs.push(['overview', 'Tổng quan'], ['calendar', 'Lịch'],
              ['approvals', 'Chờ duyệt'], ['approved', 'Đơn đã duyệt'],
              ['balances', 'Quỹ phép']);
  } else {
    tabs.push(['summary', 'Tổng hợp'], ['me', 'Của tôi'], ['calendar', 'Lịch']);
  }

  const activeTab = tab || tabs[0][0];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nghỉ phép</h1>
          <p>Số dư phép, đơn nghỉ &amp; phê duyệt · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          {data.isHrManager && (
            <button className="btn btn-ghost" onClick={() => setSchedOpen(true)}>
              <Icon name="calendar" size={16} />Thêm lịch làm việc</button>
          )}
          {/* Chỉ tài khoản nhân viên thường mới được tạo đơn nghỉ; vai trò quản lý
              (Admin/HR/Giáo vụ/Trưởng phòng) chỉ duyệt/theo dõi. */}
          {data.isEmployee && data.employee && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Tạo đơn nghỉ</button>
          )}
        </div>
      </div>

      <div className="tabs">
        {tabs.map(([id, l]) => (
          <button key={id} className={'tab' + (activeTab === id ? ' active' : '')}
            onClick={() => setTab(id)}>{l}</button>
        ))}
      </div>

      {activeTab === 'overview' && data.isOfficer && <DashboardPanel />}
      {activeTab === 'summary' && !data.isOfficer && <SummaryPanel />}
      {activeTab === 'me' && !data.isOfficer && (
        <MyTimeOff data={data} search={search} busy={busy} onCancel={onCancel} />
      )}
      {activeTab === 'calendar' && <CalendarPanel isOfficer={data.isOfficer} />}
      {activeTab === 'approvals' && data.isOfficer && (
        <ApprovalPanel isHrManager={data.isHrManager} />
      )}
      {activeTab === 'approved' && data.isOfficer && <ApprovedPanel search={search} />}
      {activeTab === 'balances' && data.isOfficer && <BalancesPanel search={search} />}

      {creating && (
        <LeaveForm
          leaveTypes={data.leaveTypes}
          onClose={() => setCreating(false)}
          onSaved={(payload) => { setCreating(false); setData(payload); }} />
      )}

      {schedOpen && <WorkScheduleModal onClose={() => setSchedOpen(false)} />}
    </div>
  );
}

/* ---- Tab "Của tôi": số dư phép + danh sách đơn ---- */
const MY_SORT_FIELDS = [
  { key: 'leaveType', label: 'Loại nghỉ', type: 'text' },
  { key: 'from', label: 'Từ ngày', type: 'date' },
  { key: 'to', label: 'Đến ngày', type: 'date' },
  { key: 'days', label: 'Số ngày', type: 'num' },
  { key: 'stateLabel', label: 'Trạng thái', type: 'text' },
];

function MyTimeOff({ data, search, busy, onCancel }) {
  const [sort, setSort] = useState({ key: 'from', dir: 'desc' });
  if (!data.employee) {
    return <EmptyState>Tài khoản chưa gắn với hồ sơ nhân viên — chưa có dữ liệu nghỉ phép.</EmptyState>;
  }

  const q = (search || '').toLowerCase();
  const requests = sortRows(
    data.requests.filter((r) =>
      !q || (r.leaveType || '').toLowerCase().includes(q)
          || (r.reason || '').toLowerCase().includes(q)),
    MY_SORT_FIELDS, sort);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Số dư phép */}
      {data.balances.length > 0 && (
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))' }}>
          {data.balances.map((b) => (
            <div key={b.leaveTypeId} className="card" style={{ padding: 18 }}>
              <div className="muted" style={{ fontSize: 12.5, fontWeight: 600 }}>{b.leaveType}</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, margin: '8px 0 4px' }}>
                <span style={{ fontSize: 28, fontWeight: 800 }}>{b.remaining}</span>
                <span className="muted" style={{ fontSize: 13 }}>/ {b.allocated} ngày còn lại</span>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <Badge kind={b.kind}>Còn {b.remaining}</Badge>
                <span className="muted" style={{ fontSize: 12 }}>đã dùng {b.taken}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Đơn nghỉ của tôi */}
      <div className="card">
        <div className="card-head">
          <h3>Đơn nghỉ của tôi</h3>
          <div className="actions"><SortBar fields={MY_SORT_FIELDS} sort={sort} onChange={setSort} /></div>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Loại nghỉ</th><th>Từ ngày</th><th>Đến ngày</th><th className="tbl-num">Số ngày</th>
              <th>Lý do</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span style={{ fontWeight: 600 }}>{r.leaveType}</span>
                    {r.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
                    {r.scheduleConflict && <Badge kind="amber">Xung đột lịch</Badge>}
                  </td>
                  <td className="mono muted">{fmtDate(r.from)}</td>
                  <td className="mono muted">{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 600 }}>{r.days}</td>
                  <td className="muted">{r.reason || '—'}</td>
                  <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                  <td>
                    {r.canCancel && (
                      <button className="btn btn-ghost btn-sm" disabled={busy === r.id}
                        onClick={() => onCancel(r.id)}>
                        {busy === r.id ? 'Đang hủy…' : 'Hủy'}</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {requests.length === 0 && <EmptyState>Chưa có đơn nghỉ nào.</EmptyState>}
      </div>
    </div>
  );
}
