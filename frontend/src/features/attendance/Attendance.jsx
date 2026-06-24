/* Màn Chấm công — điều phối tab theo quyền (mẫu chuẩn: màn Nhân viên).
   Owner: Hoàng Anh. Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMyAttendance, fetchMyRequests, fetchPendingRequests } from '../../api/attendance';
import { fetchRoles } from '../../api/employees';
import CheckInPanel from './CheckInPanel';
import AttendanceTable from './AttendanceTable';
import ManagerAttendanceBoard from './ManagerAttendanceBoard';
import ShiftCalendar from './ShiftCalendar';
import RequestList from './RequestList';
import ShiftAttendance from './ShiftAttendance';
import AttendanceHistory from './AttendanceHistory';
import TeachingSchedule from './TeachingSchedule';
import TeachingCalendar from './TeachingCalendar';

export default function Attendance({ search }) {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(null);
  const [reqs, setReqs] = useState({ rows: null, loading: false, error: null });

  const loadReqs = (manager) => {
    setReqs({ rows: null, loading: true, error: null });
    const fn = manager ? fetchPendingRequests : fetchMyRequests;
    fn().then((d) => setReqs({ rows: d.rows, loading: false, error: null }))
      .catch((e) => setReqs({ rows: null, loading: false, error: e.message }));
  };

  const load = () => {
    setErr(null); setMe(null);
    // Tài khoản vai trò (HR/Admin/Giáo vụ) có thể KHÔNG gắn hồ sơ NV (tách tài khoản
    // quản lý ↔ cá nhân — họp #2). /api/attendance/me trả 400 'no_employee' cho các
    // tài khoản này, nên đọc cờ vai trò trước và chỉ gọi endpoint cá nhân khi có hồ sơ NV.
    fetchRoles().then((roles) => {
      if (roles.hasEmployee) return fetchMyAttendance().then(setMe);
      setMe({ canManage: roles.canManage, hasEmployee: false, isOfficial: false });
    }).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!me) return <LoadingState label="Đang tải dữ liệu chấm công…" />;
  // Không có hồ sơ NV và cũng không phải tài khoản quản lý → không có dữ liệu chấm công
  // cá nhân để hiển thị (tránh rơi vào tab cá nhân vốn cần employeeId).
  if (me.hasEmployee === false && !me.canManage)
    return <EmptyState>Tài khoản này chưa gắn hồ sơ nhân viên nên không có dữ liệu chấm công.</EmptyState>;

  const isManager = me.canManage;
  const isTeacher = !isManager && !!me.isTeacher;
  const isCtv = !isManager && !me.isOfficial && !isTeacher;
  const tabs = isManager
    ? [['mgr', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Ca làm việc (CTV/OT)']]
    : isTeacher
      ? [['teaching', 'Chấm công hôm nay'], ['cal', 'Lịch tuần'], ['history', 'Lịch sử chấm công'], ['requests', 'Đơn của tôi']]
      : isCtv
        ? [['shift', 'Chấm công của tôi'], ['history', 'Lịch sử chấm công'], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']]
        : [['me', 'Chấm công của tôi'], ['history', 'Lịch sử chấm công'], ['shift', 'Chấm công OT'], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
  const activeTab = tab || (isManager ? 'mgr' : isTeacher ? 'teaching' : isCtv ? 'shift' : 'me');

  const goTab = (id) => {
    setTab(id);
    if (id === 'requests') loadReqs(isManager);
  };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Chấm công</h1>
          <p>Tự điểm danh bằng khuôn mặt &amp; vị trí · dữ liệu trực tiếp từ Odoo</p>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(([id, l]) => (
          <button key={id} className={'tab' + (activeTab === id ? ' active' : '')} onClick={() => goTab(id)}>{l}</button>
        ))}
      </div>

      {activeTab === 'me' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <CheckInPanel me={me} onChanged={load} />
        </div>
      )}
      {activeTab === 'history' && <AttendanceHistory me={me} />}
      {activeTab === 'shift' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <ShiftAttendance me={me} onChanged={load} />
        </div>
      )}
      {activeTab === 'mgr' && <ManagerAttendanceBoard search={search} />}
      {activeTab === 'day' && <AttendanceTable search={search} />}
      {activeTab === 'requests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!isManager && (
            <div className="muted" style={{ fontSize: 12.5 }}>
              Để gửi đơn sửa/quên chấm công, mở một bản ghi trong "Lịch sử chấm công" rồi bấm "Gửi đơn sửa".
            </div>
          )}
          <RequestList rows={reqs.rows} loading={reqs.loading} error={reqs.error}
            onReload={() => loadReqs(isManager)} canReview={isManager} />
        </div>
      )}
      {activeTab === 'ot' && <ShiftCalendar canManage={isManager} />}
      {activeTab === 'teaching' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <TeachingSchedule me={me} onChanged={load} />
        </div>
      )}
      {activeTab === 'cal' && <TeachingCalendar />}

    </div>
  );
}

