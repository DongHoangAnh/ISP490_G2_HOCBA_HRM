/* Panel "Yêu cầu dạy thay" — giáo viên xem các yêu cầu dạy thay gửi tới mình
   và Đồng ý / Từ chối (kèm lý do). Owner: Nhật Anh. Spec §8. */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchSubstitutions, decideSubstitution, returnSubstitution } from '../../api/timeoff';

const STATE_META = {
  pending: { kind: 'amber', label: 'Chờ phản hồi' },
  accepted: { kind: 'green', label: 'Đã đồng ý' },
  declined: { kind: 'red', label: 'Đã từ chối' },
  returned: { kind: 'gray', label: 'Đã trả lại' },
};

export default function SubstitutionsPanel({ onChanged }) {
  const [items, setItems] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(null); // id đang đồng ý
  const [actionErr, setActionErr] = useState(null); // lỗi khi Đồng ý (hiện banner trong card)
  const [declining, setDeclining] = useState(null); // yêu cầu đang mở modal từ chối
  const [returning, setReturning] = useState(null); // yêu cầu đang chờ xác nhận trả buổi

  const load = useCallback(() => {
    setErr(null);
    fetchSubstitutions()
      .then((d) => setItems(d.items || []))
      .catch((e) => setErr(e.message));
  }, []);
  useEffect(() => { load(); }, [load]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!items) return <LoadingState label="Đang tải yêu cầu dạy thay…" />;

  const accept = (id) => {
    setBusy(id); setActionErr(null);
    decideSubstitution(id, true, '')
      .then((d) => { setItems(d.items || []); onChanged && onChanged(); })
      .catch((e) => setActionErr('Không xử lý được: ' + e.message))
      .finally(() => setBusy(null));
  };

  const pending = items.filter((r) => r.state === 'pending');

  return (
    <div className="card">
      <div className="card-head">
        <h3>Yêu cầu dạy thay
          {pending.length > 0 && (
            <span style={{ marginLeft: 8 }}><Badge kind="amber">{pending.length} chờ</Badge></span>
          )}
        </h3>
      </div>
      {actionErr && (
        <div style={{ margin: '0 16px 12px', padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
          {actionErr}
        </div>
      )}
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Giáo viên nhờ</th><th>Lớp</th><th>Ngày</th><th>Giờ</th>
            <th>Trạng thái</th><th></th>
          </tr></thead>
          <tbody>
            {items.map((r) => {
              const m = STATE_META[r.state] || { kind: 'gray', label: r.state };
              return (
                <tr key={r.id}>
                  <td style={{ fontWeight: 600 }}>{r.requester}</td>
                  <td>{r.className || '—'}</td>
                  <td className="mono muted">{fmtDate(r.date)}</td>
                  <td className="mono muted">{r.startTime}{r.endTime ? `–${r.endTime}` : ''}</td>
                  <td><Badge kind={m.kind} dot>{m.label}</Badge></td>
                  <td>
                    {r.state === 'pending' && (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-primary btn-sm" disabled={busy === r.id}
                          onClick={() => accept(r.id)}>
                          <Icon name="checkCircle" size={14} />{busy === r.id ? '…' : 'Đồng ý'}</button>
                        <button className="btn btn-ghost btn-sm" disabled={busy === r.id}
                          onClick={() => setDeclining(r)}>Từ chối</button>
                      </div>
                    )}
                    {r.canReturn && (
                      <button className="btn btn-ghost btn-sm" disabled={busy === r.id}
                        onClick={() => setReturning(r)}>
                        <Icon name="rotateCcw" size={14} />Trả buổi</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {items.length === 0 && <EmptyState>Chưa có yêu cầu dạy thay nào.</EmptyState>}

      {declining && (
        <DeclineModal req={declining}
          onClose={() => setDeclining(null)}
          onDone={(d) => { setDeclining(null); setItems(d.items || []); onChanged && onChanged(); }} />
      )}

      {returning && (
        <ConfirmModal title="Trả lại buổi dạy thay" confirmLabel="Trả buổi" icon="rotateCcw"
          message={`Trả lại buổi ${returning.className || '—'} ngày ${fmtDate(returning.date)}? Buổi sẽ về lại giáo viên đã nhờ bạn.`}
          onClose={() => setReturning(null)}
          onConfirm={() => returnSubstitution(returning.id).then((d) => {
            setReturning(null); setItems(d.items || []); onChanged && onChanged();
          })} />
      )}
    </div>
  );
}

/* Modal nhập lý do từ chối dạy thay. */
function DeclineModal({ req, onClose, onDone }) {
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = () => {
    const r = reason.trim();
    if (!r) { setErr('Vui lòng nhập lý do từ chối.'); return; }
    setBusy(true); setErr(null);
    decideSubstitution(req.id, false, r)
      .then(onDone)
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader icon="alertCircle" title="Từ chối dạy thay"
        sub={`${req.requester} · ${req.className} · ${fmtDate(req.date)} ${req.startTime}`}
        onClose={onClose} />

      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <div className="muted" style={{ fontSize: 13 }}>
          Giáo viên xin nghỉ sẽ nhận thông báo và phải chọn cách xử lý khác cho buổi này.
        </div>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
            Lý do từ chối *
          </span>
          <textarea rows={3}
            style={{
              width: '100%', padding: '9px 12px', borderRadius: 10,
              border: '1px solid var(--border-strong)', background: '#fff',
              fontSize: 13.5, color: 'var(--ink)', outline: 'none',
              fontFamily: 'inherit', resize: 'vertical',
            }}
            value={reason} onChange={(e) => setReason(e.target.value)}
            placeholder="VD: Trùng lịch dạy, bận việc cá nhân…" />
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
          {busy ? 'Đang gửi…' : 'Gửi từ chối'}
        </button>
      </div>
    </Modal>
  );
}
