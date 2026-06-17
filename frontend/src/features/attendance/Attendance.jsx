/* Màn Chấm công — điều phối tab theo quyền (mẫu chuẩn: màn Nhân viên).
   Owner: Hoàng Anh. Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchMyAttendance } from '../../api/attendance';
import CheckInPanel from './CheckInPanel';
import MyHistory from './MyHistory';
import AttendanceTable from './AttendanceTable';
import { USE_MOCK, OT_LOG } from './mock';
import { fetchMyRequests, fetchPendingRequests } from '../../api/attendance';
import RequestForm from './RequestForm';
import RequestList from './RequestList';

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
  const tabs = isManager
    ? [['day', 'Bảng chấm công'], ['requests', 'Đơn chấm công'], ['ot', 'Tăng ca (OT)']]
    : [['me', 'Chấm công của tôi'], ['requests', 'Đơn của tôi']];
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
      {activeTab === 'ot' && <OtMock />}

      {showForm && (
        <RequestForm onClose={() => setShowForm(false)} onSaved={() => loadReqs(false)} />
      )}
    </div>
  );
}

function MockBanner() {
  return USE_MOCK ? (
    <div style={{ padding: '8px 12px', background: 'var(--amber-bg)', color: 'var(--amber)', borderRadius: 9, fontSize: 12.5, marginBottom: 12, fontWeight: 600 }}>
      Dữ liệu mẫu — chờ backend
    </div>
  ) : null;
}

function OtMock() {
  return (
    <div className="card">
      <div className="card-head"><h3>Đăng ký tăng ca</h3></div>
      <div style={{ padding: '0 12px 8px' }}><MockBanner /></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr><th>Nhân viên</th><th>Ngày</th><th className="tbl-num">Số giờ</th><th>Hệ số</th><th>Lý do</th></tr></thead>
          <tbody>
            {OT_LOG.map((o) => (
              <tr key={o.id} style={{ cursor: 'default' }}>
                <td><div className="cell-emp"><Avatar emp={{ id: o.id, name: o.name, hasImg: false }} /><div><div className="nm">{o.name}</div><div className="id">{o.code}</div></div></div></td>
                <td className="mono muted">{fmtDate(o.date)}</td>
                <td className="tbl-num mono" style={{ fontWeight: 600 }}>{o.hours} giờ</td>
                <td><Badge kind={o.rate === 300 ? 'red' : o.rate === 150 ? 'amber' : 'gray'}>{o.rate}%</Badge></td>
                <td className="muted">{o.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
