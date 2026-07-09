/* Tab "Chờ duyệt" — danh sách đơn chờ + duyệt/từ chối. Owner: Nhật Anh.
   Spec §3.2 / §3.5. */
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ModalHeader from '../../components/ModalHeader';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import { fmtDate } from '../../utils/format';
import { fetchApprovals, decideRequest, decideWithdraw } from '../../api/timeoff';
import SortBar, { sortRows } from './SortBar';

const SORT_FIELDS = [
  { key: 'employee', label: 'Nhân viên', type: 'text' },
  { key: 'department', label: 'Phòng ban', type: 'text' },
  { key: 'leaveType', label: 'Loại nghỉ', type: 'text' },
  { key: 'from', label: 'Từ ngày', type: 'date' },
  { key: 'to', label: 'Đến ngày', type: 'date' },
  { key: 'days', label: 'Số ngày', type: 'num' },
];

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

// Ngưỡng cảnh báo trùng lịch (Phase 4) — khớp OVERLAP_WARN của backend.
const OVERLAP_WARN = 3;

export default function ApprovalPanel({ isHrManager, focusRequestId, onFocusConsumed, onChanged }) {
  const [decision, setDecision] = useState(null); // đơn đang mở modal duyệt
  const [withdrawDecision, setWithdrawDecision] = useState(null); // yêu cầu rút đang xử lý
  const [sort, setSort] = useState({ key: 'from', dir: 'asc' });
  const [dept, setDept] = useState(''); // lọc phòng ban (chỉ role HR, khi sắp xếp theo phòng ban)
  const { data, err, loading, reload, setData } = useFetch(
    () => fetchApprovals(), [], 'timeoff:approvals');

  // Deep-link từ tab "Giám sát duyệt": mở thẳng modal xử lý của đơn được trỏ.
  // Tiêu thụ 1 lần (onFocusConsumed) — user đóng modal thì không tự mở lại;
  // đơn không còn trong danh sách (vừa được xử lý) → chỉ hiện tab, không modal.
  useEffect(() => {
    if (!data || !focusRequestId) return;
    const row = data.requests.find((r) => r.id === focusRequestId);
    if (row) {
      if (row.withdrawState === 'pending') setWithdrawDecision(row);
      else setDecision(row);
    }
    onFocusConsumed && onFocusConsumed();
    // onFocusConsumed cố ý KHÔNG nằm trong deps: arrow inline tạo mới mỗi render, đưa vào sẽ refire effect.
  }, [data, focusRequestId]);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  // Lọc phòng ban chỉ áp dụng khi role HR đang sắp xếp theo phòng ban + đã chọn 1 phòng.
  const deptFilterOn = data.seeAll && sort.key === 'department' && dept;
  const filtered = deptFilterOn
    ? data.requests.filter((r) => String(r.departmentId) === String(dept))
    : data.requests;
  const rows = sortRows(filtered, SORT_FIELDS, sort);

  return (
    <div className="card">
      <div className="card-head">
        <h3>Đơn chờ duyệt</h3>
        <span className="sub">{rows.length} đơn</span>
        <div className="actions">
          <SortBar
            fields={SORT_FIELDS} sort={sort} onChange={setSort}
            departments={data.seeAll ? data.allDepartments : null}
            dept={dept} onDeptChange={setDept}
          />
        </div>
      </div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Nhân viên</th><th>Phòng ban</th><th>Loại nghỉ</th><th>Từ ngày</th><th>Đến ngày</th>
            <th className="tbl-num">Số ngày</th><th>Cảnh báo</th><th>Trạng thái</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td style={{ fontWeight: 600 }}>{r.employee}</td>
                <td className="muted">{r.department}</td>
                <td>{r.leaveType}</td>
                <td className="mono muted">{fmtDate(r.from)}</td>
                <td className="mono muted">{fmtDate(r.to)}</td>
                <td className="tbl-num mono" style={{ fontWeight: 600 }}>{r.days}</td>
                <td>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {r.withdrawState === 'pending' && (
                      <Badge kind="red">Yêu cầu rút</Badge>
                    )}
                    {r.overdue && (
                      <Badge kind="red">Quá hạn {r.ageDays} ngày</Badge>
                    )}
                    {r.lapsed && (
                      <Badge kind="red">
                        Lỡ hạn{r.lapsed.lapsedDays > 0 ? ` ${r.lapsed.lapsedDays} ngày` : ''}
                      </Badge>
                    )}
                    {r.halfDay && <Badge kind="blue">{r.halfDay}</Badge>}
                    {r.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
                    {r.overlapCount >= OVERLAP_WARN && (
                      <Badge kind="amber">Trùng lịch: {r.overlapCount}</Badge>
                    )}
                    {r.supportDocument && (
                      <Badge kind={r.hasMedicalDoc ? 'green' : 'gray'}>
                        {r.hasMedicalDoc ? 'Có chứng từ' : 'Thiếu chứng từ'}</Badge>
                    )}
                  </div>
                </td>
                <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                {/* width:1% + nowrap + overflow visible: ô tự co theo nội dung,
                    không bị quy tắc .tbl td (max-width:0; overflow:hidden) cắt mất nút. */}
                <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                  {r.withdrawState === 'pending' ? (
                    <button className="btn btn-primary btn-sm"
                      onClick={() => setWithdrawDecision(r)}>Xử lý rút</button>
                  ) : (
                    <button className="btn btn-primary btn-sm"
                      onClick={() => setDecision(r)}>Xử lý</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.requests.length === 0 && <EmptyState>Không có đơn nào chờ duyệt.</EmptyState>}

      {decision && (
        <DecisionModal req={decision} isHrManager={isHrManager}
          onClose={() => setDecision(null)}
          onDone={(payload) => {
            setDecision(null); setData(payload);
            // Báo parent số đơn chờ mới để badge tab "Chờ duyệt" cập nhật ngay.
            onChanged && onChanged((payload.requests || []).length);
          }} />
      )}

      {withdrawDecision && (
        <WithdrawDecisionModal req={withdrawDecision}
          onClose={() => setWithdrawDecision(null)}
          onDone={(payload) => {
            setWithdrawDecision(null); setData(payload);
            onChanged && onChanged((payload.requests || []).length);
          }} />
      )}
    </div>
  );
}

/* Phase 7 — modal duyệt/từ chối yêu cầu rút đơn. Duyệt rút = đơn về 'refuse'
   và quỹ phép tự hoàn lại; Từ chối rút = đơn giữ 'validate'. */
function WithdrawDecisionModal({ req, onClose, onDone }) {
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const decide = (approve) => {
    setErr(null); setBusy(true);
    decideWithdraw(req.id, { approve, note: note.trim() })
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="alertCircle" title="Xử lý yêu cầu rút đơn"
        sub={`${req.employee} · ${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />

      <div style={{ padding: '22px 24px', display: 'grid', gap: 14 }}>
        {req.withdrawReason && (
          <div style={{ padding: '10px 13px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 13 }}>
            <b>Lý do nhân viên rút:</b>
            <pre style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{req.withdrawReason}</pre>
          </div>
        )}

        <div className="muted" style={{ fontSize: 12.5 }}>
          <b>Duyệt rút</b>: đơn chuyển sang <i>Từ chối</i> và quỹ phép được hoàn lại đầy đủ.
          {' '}<b>Từ chối rút</b>: đơn giữ nguyên <i>Đã duyệt</i>, quỹ phép không đổi.
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
            Ghi chú (tùy chọn)
          </span>
          <textarea rows={2}
            style={{
              width: '100%', padding: '9px 12px', borderRadius: 10,
              border: '1px solid var(--border-strong)', background: '#fff',
              fontSize: 13.5, color: 'var(--ink)', outline: 'none',
              fontFamily: 'inherit', resize: 'vertical',
            }}
            value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="Ghi chú cho nhân viên (hiển thị ở lịch sử xử lý)…" />
        </label>

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-soft" onClick={() => decide(false)} disabled={busy}>
          <Icon name="x" size={16} />Từ chối rút
        </button>
        <button className="btn btn-primary" onClick={() => decide(true)} disabled={busy}>
          <Icon name="check" size={16} />{busy ? 'Đang xử lý…' : 'Duyệt rút'}
        </button>
      </div>
    </Modal>
  );
}

/* Modal xử lý 1 đơn: duyệt (kèm override chứng từ) hoặc từ chối. */
function DecisionModal({ req, isHrManager, onClose, onDone }) {
  const [override, setOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const missingDoc = req.supportDocument && !req.hasMedicalDoc;    // BR-011

  const decide = (action) => {
    setErr(null);
    setBusy(true);
    decideRequest(req.id, {
      action,
      medicalOverride: override,
      medicalOverrideReason: overrideReason.trim(),
    })
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="checkCircle" title="Xử lý đơn nghỉ"
        sub={`${req.employee} · ${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto', display: 'grid', gap: 14 }}>
        <div className="muted" style={{ fontSize: 13 }}><b>Ngày tạo đơn:</b> {fmtDate(req.createdAt)}</div>

        {req.reason && (
          <div className="muted" style={{ fontSize: 13 }}><b>Lý do:</b> {req.reason}</div>
        )}

        {req.lapsed && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, fontSize: 12.5, color: 'var(--red-700)' }}>
            <b>Đơn lỡ hạn duyệt{req.lapsed.lapsedDays > 0 ? ` ${req.lapsed.lapsedDays} ngày làm việc` : ''}</b>
            {' '}— đã qua ngày bắt đầu nghỉ mà chưa được duyệt.
            <div style={{ marginTop: 6, color: 'var(--ink)' }}>
              {req.lapsed.exempt
                ? 'Nghỉ buổi dạy — không đối chiếu chấm công.'
                : req.lapsed.checkedCount === 0
                  ? 'Chưa có ngày nghỉ nào qua để đối chiếu chấm công.'
                  : `Đối chiếu chấm công: đi làm ${req.lapsed.workedCount}/${req.lapsed.checkedCount} ngày nghỉ đã qua.`}
              {req.lapsed.suggestion === 'approve' && <b> Nhân viên nghỉ thật — đề xuất duyệt trễ.</b>}
              {req.lapsed.suggestion === 'refuse' && <b> Nhân viên vẫn đi làm — đề xuất từ chối (hoàn quỹ).</b>}
            </div>
            {req.lapsed.dayChecks.length > 0 && (
              <div style={{ marginTop: 6, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {req.lapsed.dayChecks.map((d) => (
                  <Badge key={d.date} kind={d.worked ? 'amber' : 'green'}>
                    {fmtDate(d.date)}: {d.worked ? `đi làm (${d.workCredit} công)` : 'nghỉ'}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}

        {req.overlapCount > 0 && (
          <div style={{
            padding: '10px 13px', borderRadius: 10, fontSize: 12.5,
            display: 'flex', alignItems: 'center', gap: 9,
            background: req.overlapCount >= OVERLAP_WARN ? 'var(--amber-bg,#fff7ed)' : 'var(--surface-2)',
            border: '1px solid var(--border)',
            color: req.overlapCount >= OVERLAP_WARN ? 'var(--amber-700,#b45309)' : 'var(--ink)',
          }}>
            <Icon name="users" size={16} />
            <span>Cùng phòng đang nghỉ trùng khoảng ngày này: <b>{req.overlapCount} người</b>
              {req.overlapCount >= OVERLAP_WARN
                ? ' — cân nhắc trước khi duyệt, phòng có thể thiếu người.' : '.'}</span>
          </div>
        )}

        {missingDoc && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, fontSize: 12.5, color: 'var(--red-700)' }}>
            Đơn cần chứng từ y tế nhưng chưa có (BR-011).
            {isHrManager ? (
              <div style={{ marginTop: 8 }}>
                <label style={{ display: 'flex', gap: 7, alignItems: 'center', color: 'var(--ink)' }}>
                  <input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} />
                  Bỏ qua yêu cầu chứng từ (HR Manager)</label>
                {override && (
                  <textarea style={{ ...inp, resize: 'vertical', marginTop: 8 }} rows={2}
                    value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)}
                    placeholder="Lý do bỏ qua chứng từ…" />
                )}
              </div>
            ) : (
              <div style={{ marginTop: 6, color: 'var(--ink)' }}>Chỉ HR Manager mới được bỏ qua yêu cầu này.</div>
            )}
          </div>
        )}

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        {req.lapsed && req.lapsed.suggestion && (
          <button className="btn btn-soft" disabled={busy}
            style={{ marginRight: 'auto', borderColor: 'var(--red-600)', color: 'var(--red-700)' }}
            onClick={() => decide(req.lapsed.suggestion)}>
            <Icon name="alertCircle" size={16} />
            {req.lapsed.suggestion === 'approve' ? 'Duyệt trễ theo đề xuất' : 'Từ chối theo đề xuất'}
          </button>
        )}
        <button className="btn btn-soft" onClick={() => decide('refuse')} disabled={busy}>
          <Icon name="x" size={16} />Từ chối</button>
        <button className="btn btn-primary" onClick={() => decide('approve')} disabled={busy}>
          <Icon name="check" size={16} />{busy ? 'Đang xử lý…' : 'Duyệt'}</button>
      </div>
    </Modal>
  );
}
