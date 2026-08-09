/* ============================================================
   Màn Nghỉ phép — self-service + duyệt đơn (mẫu chuẩn: màn Nhân viên).
   Owner: Nhật Anh. Spec: docs/SPEC_API_TIMEOFF.md
   ============================================================ */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchOverview, cancelRequest, fetchApprovals, withdrawRequest, fetchSubstitutions } from '../../api/timeoff';
import SortBar, { sortRows } from './SortBar';
import LeaveForm from './LeaveForm';
import SubstitutionsPanel from './SubstitutionsPanel';
import ApprovalPanel from './ApprovalPanel';
import LapsedPanel from './LapsedPanel';
import BurnoutPanel from './BurnoutPanel';
import ApprovedPanel from './ApprovedPanel';
import BalancesPanel from './BalancesPanel';
import DashboardPanel from './DashboardPanel';
import CalendarPanel from './CalendarPanel';
import SummaryPanel from './SummaryPanel';
import WorkScheduleModal from './WorkScheduleModal';
import HistoryTimeline from './HistoryTimeline';

export default function TimeOff({ search, focus, onPendingCount }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(null);
  const [creating, setCreating] = useState(false);
  const [schedOpen, setSchedOpen] = useState(false); // modal lịch làm việc (HR)
  const [cancelling, setCancelling] = useState(null); // đơn đang chờ xác nhận hủy
  const [pendingCount, setPendingCount] = useState(0); // badge tab "Đơn chờ duyệt"
  const [subCount, setSubCount] = useState(0); // badge tab "Yêu cầu dạy thay"
  const [historyReq, setHistoryReq] = useState(null); // đơn xem lịch sử (từ chuông)
  const [approvalFocus, setApprovalFocus] = useState(null); // requestId từ tab Kiểm duyệt phát sinh → mở modal ở tab Đơn chờ duyệt
  const [year, setYear] = useState(new Date().getFullYear()); // filter chung xuyên tab
  const [dept, setDept] = useState('');                        // '' = mọi phòng ban

  const load = () => {
    setErr(null); setData(null);
    fetchOverview().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  // Badge "Đơn chờ duyệt": cập nhật cả tab lẫn mục "Nghỉ phép" ở thanh menu.
  const updatePending = (n) => {
    setPendingCount(n);
    if (onPendingCount) onPendingCount(n);
  };

  // Officer: lấy số đơn đang chờ để hiện badge trên tab "Chờ duyệt".
  useEffect(() => {
    if (data && data.isOfficer) {
      fetchApprovals().then((d) => updatePending((d.requests || []).length)).catch(() => {});
    }
  }, [data]);

  // Giáo viên: đếm yêu cầu dạy thay đang chờ để hiện badge trên tab.
  const refreshSubCount = () => fetchSubstitutions()
    .then((d) => setSubCount((d.items || []).filter((r) => r.state === 'pending').length))
    .catch(() => {});
  useEffect(() => {
    if (data && data.employee && data.employee.isTeacher) refreshSubCount();
  }, [data]);

  // Bấm 1 thông báo ở chuông → tới đúng nơi xử lý:
  //  - yêu cầu/hủy dạy thay (sub_request, sub_cancelled) → tab "Yêu cầu dạy thay";
  //  - còn lại → mở modal "Lịch sử xử lý" của đơn.
  useEffect(() => {
    if (!focus) return;
    if (focus.kind === 'sub_request' || focus.kind === 'sub_cancelled') setTab('substitutions');
    else if (focus.requestId) setHistoryReq(focus.requestId);
  }, [focus]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nghỉ phép…" />;

  // Tách luồng cá nhân / quản lý theo phân quyền:
  //  - Quản lý (officer): Tổng quan · Đơn chờ duyệt · Đơn đã duyệt · Lịch ·
  //    Kiểm duyệt phát sinh · Theo dõi nghỉ phép · Quỹ phép.
  //    KHÔNG có tab "Đơn của tôi" (luồng quản lý thuần).
  //  - Nhân viên: "Tổng hợp" (báo cáo cá nhân) + "Đơn của tôi" + "Lịch".
  const tabs = [];
  if (data.isOfficer) {
    tabs.push(['overview', 'Tổng quan'],
              ['approvals', 'Đơn chờ duyệt'],
              ['approved', 'Đơn đã duyệt'],
              ['calendar', 'Lịch'],
              ['lapsed', 'Kiểm duyệt phát sinh'],
              ['health', 'Theo dõi nghỉ phép'],
              ['balances', 'Quỹ phép']);
  } else {
    tabs.push(['summary', 'Tổng hợp'], ['me', 'Đơn của tôi'], ['calendar', 'Lịch']);
  }
  // Giáo viên (mọi vai trò) có thêm tab xử lý yêu cầu dạy thay gửi tới mình.
  if (data.employee && data.employee.isTeacher) {
    tabs.push(['substitutions', 'Yêu cầu dạy thay']);
  }

  const activeTab = tab || tabs[0][0];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nghỉ phép</h1>
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
            onClick={() => { setTab(id); setApprovalFocus(null); /* bấm tab tay → hủy focus deep-link còn treo */ }}>
            {l}
            {id === 'approvals' && pendingCount > 0 && (
              <span style={{ marginLeft: 6 }}><Badge kind="amber">{pendingCount}</Badge></span>
            )}
            {id === 'substitutions' && subCount > 0 && (
              <span style={{ marginLeft: 6 }}><Badge kind="amber">{subCount}</Badge></span>
            )}
          </button>
        ))}
      </div>

      {search && !SEARCHABLE_TABS.has(activeTab) && (
        <div className="muted" style={{ fontSize: 12.5, margin: '-8px 0 4px' }}>
          Tìm kiếm không áp dụng cho tab này.
        </div>
      )}

      {activeTab === 'overview' && data.isOfficer && (
        <DashboardPanel year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'summary' && !data.isOfficer && (
        <SummaryPanel year={year} onYearChange={setYear} />
      )}
      {activeTab === 'me' && !data.isOfficer && (
        <MyTimeOff data={data} search={search} onCancel={setCancelling} onUpdated={setData} />
      )}
      {activeTab === 'calendar' && (
        <CalendarPanel isOfficer={data.isOfficer} seeAll={data.seeAll}
          isTeacher={!!(data.employee && data.employee.isTeacher)}
          year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'approvals' && data.isOfficer && (
        <ApprovalPanel isHrManager={data.isHrManager}
          focusRequestId={approvalFocus}
          onFocusConsumed={() => setApprovalFocus(null)}
          onChanged={updatePending} />
      )}
      {/* Lapsed/Burnout chỉ hiện DeptSelect khi seeAll → chặn dept chọn ở tab khác
          leak vào thành filter ẩn (trưởng phòng nhiều phòng ban không thấy/xóa được). */}
      {activeTab === 'lapsed' && data.isOfficer && (
        <LapsedPanel dept={data.seeAll ? dept : ''} onDeptChange={setDept}
          onOpenApproval={(id) => { setApprovalFocus(id); setTab('approvals'); }} />
      )}
      {activeTab === 'health' && data.isOfficer && (
        <BurnoutPanel dept={data.seeAll ? dept : ''} onDeptChange={setDept} />
      )}
      {activeTab === 'approved' && data.isOfficer && (
        <ApprovedPanel search={search} year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'balances' && data.isOfficer && (
        <BalancesPanel search={search} year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'substitutions' && data.employee && data.employee.isTeacher && (
        <SubstitutionsPanel onChanged={refreshSubCount} />
      )}

      {creating && (
        <LeaveForm
          leaveTypes={data.leaveTypes}
          isTeacher={!!(data.employee && data.employee.isTeacher)}
          onClose={() => setCreating(false)}
          onSaved={(payload) => { setCreating(false); setData(payload); }} />
      )}

      {schedOpen && <WorkScheduleModal onClose={() => setSchedOpen(false)} />}

      {cancelling && (
        <ConfirmModal title="Hủy đơn nghỉ" confirmLabel="Hủy đơn"
          message={`Hủy đơn "${cancelling.leaveType}" (${fmtDate(cancelling.from)} → ${fmtDate(cancelling.to)})? Hành động không hoàn tác được.`}
          onClose={() => setCancelling(null)}
          onConfirm={() => cancelRequest(cancelling.id).then((payload) => {
            setData(payload); setCancelling(null);
          })} />
      )}

      {historyReq && (
        <Modal onClose={() => setHistoryReq(null)}>
          <ModalHeader icon="clock" title="Lịch sử xử lý đơn"
            sub="Dòng thời gian thao tác của đơn nghỉ" onClose={() => setHistoryReq(null)} />
          <div style={{ padding: '18px 24px' }}>
            <HistoryTimeline requestId={historyReq} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost" onClick={() => setHistoryReq(null)}>Đóng</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

/* ---- Tab "Đơn của tôi": số dư phép + danh sách đơn ---- */
const MY_SORT_FIELDS = [
  { key: 'leaveType', label: 'Loại nghỉ', type: 'text' },
  { key: 'createdAt', label: 'Ngày tạo', type: 'date' },
  { key: 'from', label: 'Từ ngày', type: 'date' },
  { key: 'to', label: 'Đến ngày', type: 'date' },
  { key: 'days', label: 'Số ngày', type: 'num' },
  { key: 'stateLabel', label: 'Trạng thái', type: 'text' },
];

const SEARCHABLE_TABS = new Set(['me', 'approved', 'balances']);

function MyTimeOff({ data, search, onCancel, onUpdated }) {
  const [sort, setSort] = useState({ key: 'from', dir: 'desc' });
  const [withdrawing, setWithdrawing] = useState(null); // đơn đang mở modal rút
  const [detail, setDetail] = useState(null); // đơn đang xem chi tiết (modal)
  if (!data.employee) {
    return <EmptyState>Tài khoản chưa gắn với hồ sơ nhân viên — chưa có dữ liệu nghỉ phép.</EmptyState>;
  }

  // Cột "GV dạy thay" chỉ có nghĩa với đơn nghỉ theo buổi dạy → nhân viên
  // thường luôn thấy một cột toàn dấu "—", ẩn đi cho gọn bảng.
  const isTeacher = !!data.employee.isTeacher;
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
              {/* width:1% + nowrap cho các cột ngày/số/trạng thái/thao tác → co sát nội dung,
                  dồn khoảng trống cho cột Loại nghỉ & GV dạy thay; nút thao tác không bị
                  đẩy khỏi khung và cột Số ngày nằm sát cột Đến ngày. */}
              <th>Loại nghỉ</th><th>Ngày tạo</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Từ ngày</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Đến ngày</th>
              <th className="tbl-num" style={{ width: '1%', whiteSpace: 'nowrap' }}>Số ngày</th>
              {isTeacher && <th>GV dạy thay</th>}
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
            </tr></thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} tabIndex={0} onClick={() => setDetail(r)}
                  onKeyDown={(e) => {
                    if (e.target !== e.currentTarget) return;
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDetail(r); }
                  }}
                  style={{ cursor: 'pointer' }}>
                  <td>
                    <span style={{ fontWeight: 600 }}>{r.leaveType}</span>
                    {r.halfDay && <Badge kind="blue">{r.halfDay}</Badge>}
                    {r.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
                    {r.withdrawState === 'pending' && (
                      <Badge kind="amber">Chờ duyệt rút</Badge>
                    )}
                  </td>
                  <td className="mono muted">{fmtDate(r.createdAt)}</td>
                  <td className="mono muted" style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>{fmtDate(r.from)}</td>
                  <td className="mono muted" style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 600, width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>
                    {r.isTeachingOff ? `${r.sessionCount} buổi` : r.days}</td>
                  {isTeacher && (
                    <td className="muted">
                      {r.isTeachingOff ? (r.substituteNames || '—') : '—'}</td>
                  )}
                  <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>
                    {r.canCancel && (
                      <button className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); onCancel(r); }}>Hủy</button>
                    )}
                    {r.canWithdraw && (
                      <button className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); setWithdrawing(r); }}>Rút đơn</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {requests.length === 0 && <EmptyState>Chưa có đơn nghỉ nào.</EmptyState>}
      </div>

      {detail && (
        <LeaveDetailModal req={detail} onClose={() => setDetail(null)} />
      )}

      {withdrawing && (
        <WithdrawModal req={withdrawing}
          onClose={() => setWithdrawing(null)}
          onDone={(payload) => { setWithdrawing(null); onUpdated && onUpdated(payload); }} />
      )}
    </div>
  );
}

/* Modal chi tiết 1 đơn nghỉ (mở khi bấm vào dòng ở tab "Đơn của tôi").
   GV xem được đơn xin nghỉ những buổi dạy nào + cách xử lý từng buổi. */
const RES_STATE_LABEL = {
  pending: 'Chờ GV thay đồng ý', accepted: 'Đã chốt',
  declined: 'GV thay từ chối', returned: 'GV thay đã trả lại',
};

function DetailField({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      <span style={{ fontSize: 13.5, color: 'var(--ink)', whiteSpace: 'pre-wrap' }}>{value}</span>
    </div>
  );
}

function LeaveDetailModal({ req, onClose }) {
  const sessions = req.sessionResolutions || [];
  return (
    <Modal onClose={onClose}>
      <ModalHeader icon="calendar" title={req.leaveType} sub="Chi tiết đơn nghỉ" onClose={onClose}>
        {req.halfDay && <Badge kind="blue">{req.halfDay}</Badge>}
        {req.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
      </ModalHeader>

      <div style={{ padding: '18px 24px', display: 'grid', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span className="muted" style={{ fontSize: 12.5 }}>Trạng thái</span>
          <Badge kind={req.stateKind} dot>{req.stateLabel}</Badge>
          {req.withdrawState === 'pending' && <Badge kind="amber">Chờ duyệt rút</Badge>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
          <DetailField label="Ngày tạo" value={fmtDate(req.createdAt)} />
          <DetailField label={req.isTeachingOff ? 'Số buổi' : 'Số ngày'}
            value={req.isTeachingOff ? `${req.sessionCount} buổi` : `${req.days} ngày`} />
          <DetailField label="Từ ngày" value={fmtDate(req.from)} />
          <DetailField label="Đến ngày" value={fmtDate(req.to)} />
        </div>

        <DetailField label="Lý do" value={req.reason || '—'} />

        {req.isTeachingOff && sessions.length > 0 && (
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 8 }}>
              Các buổi xin nghỉ ({sessions.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {sessions.map((s, i) => (
                <div key={i} className="card" style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <span className="mono" style={{ fontWeight: 700, fontSize: 12.5 }}>{fmtDate(s.date)}</span>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{s.className || '—'}</span>
                  <span style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
                    {s.kind === 'class_off'
                      ? <Badge kind="gray">Cả lớp nghỉ</Badge>
                      : <Badge kind="blue">Dạy thay: {s.substituteName || '—'}</Badge>}
                    {s.kind === 'substitute' && s.state && (
                      <span className="muted" style={{ fontSize: 11.5 }}>{RES_STATE_LABEL[s.state] || s.state}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {req.withdrawState === 'pending' && req.withdrawReason && (
          <DetailField label="Lý do rút đơn" value={req.withdrawReason} />
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}

/* Modal nhập lý do rút đơn (Phase 7). */
function WithdrawModal({ req, onClose, onDone }) {
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = () => {
    const r = reason.trim();
    if (!r) { setErr('Vui lòng nhập lý do rút đơn.'); return; }
    setBusy(true); setErr(null);
    withdrawRequest(req.id, r)
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader icon="alertCircle" title="Rút đơn nghỉ đã duyệt"
        sub={`${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />

      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <div className="muted" style={{ fontSize: 13 }}>
          Yêu cầu rút sẽ được gửi tới người duyệt ban đầu (HR/Trưởng phòng).
          Khi được duyệt rút, đơn sẽ chuyển sang <b>"Từ chối"</b> và quỹ phép
          được hoàn lại đầy đủ.
        </div>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
            Lý do rút đơn *
          </span>
          <textarea rows={3}
            style={{
              width: '100%', padding: '9px 12px', borderRadius: 10,
              border: '1px solid var(--border-strong)', background: '#fff',
              fontSize: 13.5, color: 'var(--ink)', outline: 'none',
              fontFamily: 'inherit', resize: 'vertical',
            }}
            value={reason} onChange={(e) => setReason(e.target.value)}
            placeholder="VD: Đổi kế hoạch, không cần nghỉ nữa…" />
        </label>
        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Đang gửi…' : 'Gửi yêu cầu rút'}
        </button>
      </div>
    </Modal>
  );
}
