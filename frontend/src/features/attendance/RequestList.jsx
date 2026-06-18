/* Danh sách đơn chấm công (Gói 3).
   - canReview=false (user): xem trạng thái + ghi chú duyệt (read-only).
   - canReview=true (manager): chỉnh giờ đề xuất + Duyệt / Từ chối. */
import { useState } from 'react';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { approveRequest, rejectRequest } from '../../api/attendance';

const STATE_LABEL = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối' };
const STATE_KIND = { pending: 'amber', approved: 'green', rejected: 'red' };

export default function RequestList({ rows, loading, error, onReload, canReview }) {
  if (loading) return <LoadingState label="Đang tải đơn…" />;
  if (error) return <ErrorState message={error} onRetry={onReload} />;
  if (!rows || rows.length === 0)
    return <div className="muted" style={{ padding: 16, fontSize: 13 }}>Chưa có đơn nào.</div>;
  return (
    <div className="card">
      <div className="card-head"><h3>{canReview ? 'Đơn chấm công chờ duyệt' : 'Đơn của tôi'}</h3></div>
      <div style={{ padding: '4px 12px 8px' }}>
        {rows.map((r) => (
          <RequestRow key={r.id} r={r} canReview={canReview} onReload={onReload} />
        ))}
      </div>
    </div>
  );
}

function RequestRow({ r, canReview, onReload }) {
  const [ci, setCi] = useState(r.checkIn ? r.checkIn.slice(0, 16) : '');
  const [co, setCo] = useState(r.checkOut ? r.checkOut.slice(0, 16) : '');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function act(approve) {
    setBusy(true); setErr(null);
    try {
      const body = approve
        ? { checkIn: ci || null, checkOut: co || null, reviewNote: note }
        : { reviewNote: note };
      await (approve ? approveRequest(r.id, body) : rejectRequest(r.id, body));
      onReload && onReload();
    } catch (e) {
      setErr('Thao tác thất bại (' + e.message + ').');
      onReload && onReload();   // đơn có thể đã đổi trạng thái (vd already_decided) -> đồng bộ lại
    } finally { setBusy(false); }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '12px 4px', borderBottom: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Avatar emp={{ id: r.empId, name: r.empName, hasImg: false }} size={40} />
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.empName}</div>
          <div className="muted" style={{ fontSize: 12 }}>{r.code} · {r.depName}</div>
        </div>
        <div style={{ flex: 1 }}>
          <span className="mono" style={{ fontWeight: 600, fontSize: 13 }}>
            {fmtDate(r.requestDate)}
          </span>
          <span className="muted" style={{ fontSize: 12.5, marginLeft: 8 }}>
            {r.attendanceId ? 'Sửa bản ghi' : 'Ngày thiếu'} · vào {fmtTime(r.checkIn)} / ra {fmtTime(r.checkOut)}
          </span>
          <div className="muted" style={{ fontSize: 12.5 }}>"{r.reason}"</div>
        </div>
        <Badge kind={STATE_KIND[r.state]} dot>{STATE_LABEL[r.state]}</Badge>
      </div>

      {!canReview && r.state !== 'pending' && r.reviewNote && (
        <div className="muted" style={{ fontSize: 12.5, paddingLeft: 54 }}>
          Ghi chú duyệt: {r.reviewNote}
        </div>
      )}

      {canReview && r.state === 'pending' && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end', paddingLeft: 54 }}>
          <label style={{ fontSize: 12 }}>Giờ vào
            <input type="datetime-local" className="sel" value={ci} onChange={(e) => setCi(e.target.value)} />
          </label>
          <label style={{ fontSize: 12 }}>Giờ ra
            <input type="datetime-local" className="sel" value={co} onChange={(e) => setCo(e.target.value)} />
          </label>
          <label style={{ fontSize: 12, flex: 1, minWidth: 140 }}>Ghi chú
            <input className="sel" value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => act(true)}>Duyệt</button>
          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={() => act(false)}>Từ chối</button>
        </div>
      )}
      {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5, paddingLeft: 54 }}>{err}</div>}
    </div>
  );
}
