/* Chi tiết 1 ca (Gói 4A). Manager + ca pending: override giờ/loại/hệ số +
   Duyệt/Từ chối. Owner + ca pending: nút Hủy. Còn lại: xem trạng thái. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { approveShift, rejectShift, cancelShift } from '../../api/attendance';

const STATE_LABEL = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối' };
const STATE_KIND = { pending: 'amber', approved: 'green', rejected: 'red' };

export default function ShiftDrawer({ shift, canManage, onClose, onChanged }) {
  const isPending = shift.state === 'pending';
  const [start, setStart] = useState(shift.start ? shift.start.slice(0, 16) : '');
  const [end, setEnd] = useState(shift.end ? shift.end.slice(0, 16) : '');
  const [stype, setStype] = useState(shift.shiftType);
  const [rate, setRate] = useState(shift.rate);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function decide(approve) {
    setBusy(true); setErr(null);
    try {
      const body = approve
        ? { start: start || null, end: end || null, shiftType: stype, rate: Number(rate), reviewNote: note }
        : { reviewNote: note };
      await (approve ? approveShift(shift.id, body) : rejectShift(shift.id, body));
      onChanged && onChanged();
    } catch (e) { setErr('Thao tác thất bại (' + e.message + ').'); onChanged && onChanged(); }
    finally { setBusy(false); }
  }

  async function cancel() {
    setBusy(true); setErr(null);
    try {
      await cancelShift(shift.id);
      onChanged && onChanged();
    } catch (e) { setErr('Hủy thất bại (' + e.message + ').'); onChanged && onChanged(); }
    finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{shift.empName}</h2>
            <Badge kind={STATE_KIND[shift.state]} dot>{STATE_LABEL[shift.state]}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
            {shift.code} · {shift.depName}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div className="grid-2" style={{ rowGap: 14 }}>
          <div className="kv"><div className="k">Bắt đầu</div><div className="v mono">{fmtDate(shift.start.slice(0, 10))} {fmtTime(shift.start)}</div></div>
          <div className="kv"><div className="k">Kết thúc</div><div className="v mono">{fmtTime(shift.end)}</div></div>
          <div className="kv"><div className="k">Loại ca</div><div className="v">{shift.shiftType === 'ctv' ? 'CTV' : 'Tăng ca (OT)'}</div></div>
          <div className="kv"><div className="k">Hệ số</div><div className="v mono" style={{ fontWeight: 600 }}>×{shift.rate}</div></div>
        </div>
        {shift.reason && <div className="muted" style={{ fontSize: 12.5, marginTop: 12 }}>Lý do: "{shift.reason}"</div>}
        {!canManage && !isPending && shift.reviewNote && (
          <div className="muted" style={{ fontSize: 12.5, marginTop: 8 }}>Ghi chú duyệt: {shift.reviewNote}</div>
        )}
      </div>

      {canManage && isPending && (
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <label style={{ fontSize: 12 }}>Bắt đầu
              <input type="datetime-local" className="sel" value={start} onChange={(e) => setStart(e.target.value)} />
            </label>
            <label style={{ fontSize: 12 }}>Kết thúc
              <input type="datetime-local" className="sel" value={end} onChange={(e) => setEnd(e.target.value)} />
            </label>
            <label style={{ fontSize: 12 }}>Loại
              <select className="sel" value={stype} onChange={(e) => setStype(e.target.value)}>
                <option value="ot">OT</option><option value="ctv">CTV</option>
              </select>
            </label>
            <label style={{ fontSize: 12 }}>Hệ số
              <input type="number" step="0.5" className="sel" style={{ width: 80 }} value={rate} onChange={(e) => setRate(e.target.value)} />
            </label>
          </div>
          <input className="sel" placeholder="Ghi chú duyệt" value={note} onChange={(e) => setNote(e.target.value)} />
          {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => decide(true)}>Duyệt</button>
            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={() => decide(false)}>Từ chối</button>
          </div>
        </div>
      )}
      {!canManage && isPending && (
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
          {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5, marginBottom: 8 }}>{err}</div>}
          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red-600)' }} disabled={busy} onClick={cancel}>Hủy ca</button>
        </div>
      )}
    </Modal>
  );
}
