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
import { USE_MOCK, FORGOT_REQUESTS, OT_LOG } from './mock';

export default function Attendance({ search }) {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState('me');

  const load = () => {
    setErr(null); setMe(null);
    fetchMyAttendance().then(setMe).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!me) return <LoadingState label="Đang tải dữ liệu chấm công…" />;

  const isStaff = me.isHr || me.isHrManager;
  const hasEmp = me.hasEmployee !== false;
  const tabs = [];
  if (hasEmp) tabs.push(['me', 'Chấm công của tôi']);
  if (isStaff) tabs.push(['day', 'Bảng chấm công'], ['forgot', 'Đơn quên chấm công'], ['ot', 'Tăng ca (OT)']);
  const ids = tabs.map((t) => t[0]);
  const cur = ids.includes(tab) ? tab : (ids[0] || 'me');

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Chấm công</h1>
          <p>Tự điểm danh bằng khuôn mặt &amp; vị trí · dữ liệu trực tiếp từ Odoo</p>
        </div>
      </div>

      {!hasEmp && (
        <div style={{ padding: '9px 13px', background: 'var(--amber-bg)', color: 'var(--amber)', borderRadius: 9, fontSize: 12.5, marginBottom: 14, fontWeight: 600 }}>
          Tài khoản này chưa gắn hồ sơ nhân viên — chỉ xem bảng chấm công quản lý, không tự điểm danh được.
        </div>
      )}

      <div className="tabs">
        {tabs.map(([id, l]) => (
          <button key={id} className={'tab' + (cur === id ? ' active' : '')} onClick={() => setTab(id)}>{l}</button>
        ))}
      </div>

      {cur === 'me' && hasEmp && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <CheckInPanel me={me} onChanged={load} />
          <MyHistory />
        </div>
      )}
      {cur === 'day' && <AttendanceTable search={search} />}
      {cur === 'forgot' && <ForgotMock />}
      {cur === 'ot' && <OtMock />}
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

function ForgotMock() {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn quên chấm công</h3></div>
      <div style={{ padding: '8px 12px' }}>
        <MockBanner />
        {FORGOT_REQUESTS.map((f) => (
          <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 4px', borderBottom: '1px solid var(--border)' }}>
            <Avatar emp={{ id: f.id, name: f.name, hasImg: false }} size={40} />
            <div style={{ minWidth: 200 }}>
              <div style={{ fontWeight: 600, fontSize: 13.5 }}>{f.name}</div>
              <div className="muted" style={{ fontSize: 12 }}>{f.code} · {f.depName}</div>
            </div>
            <div style={{ flex: 1 }}>
              <Badge kind="red">{f.missType}</Badge>
              <span className="mono" style={{ fontWeight: 600, fontSize: 13, marginLeft: 8 }}>{fmtDate(f.date)} · {f.proposed}</span>
              <div className="muted" style={{ fontSize: 12.5 }}>"{f.reason}"</div>
            </div>
            <Badge kind="amber" dot>{f.state}</Badge>
          </div>
        ))}
      </div>
    </div>
  );
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
