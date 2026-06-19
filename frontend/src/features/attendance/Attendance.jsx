/* Màn Chấm công — điều phối tab theo quyền (mẫu chuẩn: màn Nhân viên).
   Owner: Hoàng Anh. Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState } from '../../components/states';
import { fetchMyAttendance, fetchMyRequests, fetchPendingRequests } from '../../api/attendance';
import CheckInPanel from './CheckInPanel';
import MyHistory from './MyHistory';
import AttendanceTable from './AttendanceTable';
import ShiftCalendar from './ShiftCalendar';
import OtTable from './OtTable';
import RequestForm from './RequestForm';
import RequestList from './RequestList';
import ShiftAttendance from './ShiftAttendance';

export default function Attendance({ search }) {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(null);
  const [reqs, setReqs] = useState({ rows: null, loading: false, error: null });
  const [showForm, setShowForm] = useState(false);

  const loadReqs = (manager) => {
    setReqs({ rows: null, loading: true, error: null });
    const fn = manager ? fetchPendingRequests : fetchMyRequests;
    fn().then((d) => setReqs({ rows: d.rows, loading: false, error: null }))
      .catch((e) => setReqs({ rows: null, loading: false, error: e.message }));
  };

  const load = () => {
    setErr(null); setMe(null);
    fetchMyAttendance().then(setMe).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!me) return <LoadingState label="Đang tải dữ liệu chấm công…" />;

  const isManager = me.canManage;
  const shiftTabLabel = me.isOfficial ? 'Chấm công OT' : 'Chấm công';
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Ca làm việc (CTV/OT)'], ['otpay', 'Chấm công OT']]
    : [['me', 'Chấm công của tôi'], ['shift', shiftTabLabel], ['requests', 'Đơn của tôi'], ['ot', 'Ca làm việc (CTV/OT)']];
  const activeTab = tab || (isManager ? 'day' : 'me');

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
          <MyHistory />
        </div>
      )}
      {activeTab === 'shift' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <ShiftAttendance me={me} onChanged={load} />
        </div>
      )}
      {activeTab === 'day' && <AttendanceTable search={search} />}
      {activeTab === 'requests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!isManager && (
            <div>
              <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
                Gửi đơn quên chấm công
              </button>
            </div>
          )}
          <RequestList rows={reqs.rows} loading={reqs.loading} error={reqs.error}
            onReload={() => loadReqs(isManager)} canReview={isManager} />
        </div>
      )}
      {activeTab === 'ot' && <ShiftCalendar canManage={isManager} />}
      {activeTab === 'otpay' && <OtTable />}

      {showForm && (
        <RequestForm onClose={() => setShowForm(false)} onSaved={() => loadReqs(false)} />
      )}
    </div>
  );
}

