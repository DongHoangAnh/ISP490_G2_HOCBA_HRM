/* Tab "Chờ duyệt" — danh sách đơn chờ + duyệt/từ chối. Owner: Nhật Anh.
   Spec §3.2 / §3.5. */
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchApprovals, decideRequest } from '../../api/timeoff';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

export default function ApprovalPanel({ isManager }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [decision, setDecision] = useState(null); // đơn đang mở modal duyệt

  const load = () => {
    setErr(null); setData(null);
    fetchApprovals().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải đơn chờ duyệt…" />;

  return (
    <div className="card">
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Nhân viên</th><th>Phòng ban</th><th>Loại nghỉ</th><th>Từ ngày</th><th>Đến ngày</th>
            <th className="tbl-num">Số ngày</th><th>Cảnh báo</th><th>Trạng thái</th><th></th>
          </tr></thead>
          <tbody>
            {data.requests.map((r) => (
              <tr key={r.id}>
                <td style={{ fontWeight: 600 }}>{r.employee}</td>
                <td className="muted">{r.department}</td>
                <td>{r.leaveType}</td>
                <td className="mono muted">{fmtDate(r.from)}</td>
                <td className="mono muted">{fmtDate(r.to)}</td>
                <td className="tbl-num mono" style={{ fontWeight: 600 }}>{r.days}</td>
                <td>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {r.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
                    {r.scheduleConflict && <Badge kind="amber">Xung đột lịch</Badge>}
                    {r.supportDocument && (
                      <Badge kind={r.hasMedicalDoc ? 'green' : 'gray'}>
                        {r.hasMedicalDoc ? 'Có chứng từ' : 'Thiếu chứng từ'}</Badge>
                    )}
                  </div>
                </td>
                <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                <td>
                  <button className="btn btn-primary btn-sm" onClick={() => setDecision(r)}>Xử lý</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.requests.length === 0 && <EmptyState>Không có đơn nào chờ duyệt.</EmptyState>}

      {decision && (
        <DecisionModal req={decision} isManager={isManager}
          onClose={() => setDecision(null)}
          onDone={(payload) => { setDecision(null); setData(payload); }} />
      )}
    </div>
  );
}

/* Modal xử lý 1 đơn: duyệt (kèm ghi chú thay thế / override chứng từ) hoặc từ chối. */
function DecisionModal({ req, isManager, onClose, onDone }) {
  const [note, setNote] = useState(req.replacementNote || '');
  const [override, setOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const needNote = req.scheduleConflict && !req.isEmergency;       // BR-031
  const missingDoc = req.supportDocument && !req.hasMedicalDoc;    // BR-011

  const decide = (action) => {
    setErr(null);
    setBusy(true);
    decideRequest(req.id, {
      action,
      replacementNote: note.trim(),
      medicalOverride: override,
      medicalOverrideReason: overrideReason.trim(),
    })
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="checkCircle" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>Xử lý đơn nghỉ</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {req.employee} · {req.leaveType} · {fmtDate(req.from)} → {fmtDate(req.to)} ({req.days} ngày)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto', display: 'grid', gap: 14 }}>
        {req.reason && (
          <div className="muted" style={{ fontSize: 13 }}><b>Lý do:</b> {req.reason}</div>
        )}

        {req.scheduleConflict && (
          <div style={{ padding: '10px 13px', background: 'var(--amber-bg,#fff7ed)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 12.5 }}>
            <b>Xung đột lịch dạy:</b>
            <pre style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{req.conflictInfo || '—'}</pre>
          </div>
        )}

        {needNote && (
          <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
              Ghi chú bố trí thay thế *</span>
            <textarea style={{ ...inp, resize: 'vertical' }} rows={2} value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="VD: Cô B dạy thay buổi 18/06…" />
            <span className="muted" style={{ fontSize: 12 }}>Bắt buộc trước khi duyệt khi có xung đột lịch dạy (BR-031).</span>
          </label>
        )}

        {missingDoc && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, fontSize: 12.5, color: 'var(--red-700)' }}>
            Đơn cần chứng từ y tế nhưng chưa có (BR-011).
            {isManager ? (
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
        <button className="btn btn-soft" onClick={() => decide('refuse')} disabled={busy}>
          <Icon name="x" size={16} />Từ chối</button>
        <button className="btn btn-primary" onClick={() => decide('approve')} disabled={busy}>
          <Icon name="check" size={16} />{busy ? 'Đang xử lý…' : 'Duyệt'}</button>
      </div>
    </Modal>
  );
}
