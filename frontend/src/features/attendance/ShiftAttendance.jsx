/* Màn chấm công theo ca (ctv/ot). Nhãn do Attendance.jsx quyết định.
   Mỗi ca approved hôm nay là 1 thẻ camera + nút check-in/out. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useFaceApi } from './useFaceApi';
import { enrollFace, shiftCheckIn, shiftCheckOut } from '../../api/attendance';
import { fmtTime } from './util';

const ERR = {
  no_shift: 'Không tìm thấy ca.',
  shift_not_approved: 'Ca chưa được duyệt.',
  outside_shift_window: 'Ngoài cửa sổ chấm công của ca (±15 phút).',
  already_checked_in: 'Ca này đã check-in rồi.',
  not_checked_in: 'Chưa check-in nên không thể check-out.',
  already_checked_out: 'Ca này đã check-out rồi.',
  forbidden: 'Ca không thuộc về bạn.',
  manager_no_checkin: 'Tài khoản quản lý không điểm danh.',
};

export default function ShiftAttendance({ me, onChanged }) {
  const { videoRef, ready, camError, capture } = useFaceApi();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [enrolled, setEnrolled] = useState(me.enrolled);
  useEffect(() => { setEnrolled(me.enrolled); }, [me.enrolled]);
  const shifts = me.shiftsToday || [];

  async function doEnroll() {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không thấy khuôn mặt. Thử lại.' }); return; }
      await enrollFace(cap.photo, cap.descriptor);
      setEnrolled(true);
      setMsg({ kind: 'ok', text: 'Đăng ký khuôn mặt thành công.' });
    } catch (e) { setMsg({ kind: 'err', text: 'Đăng ký thất bại (' + e.message + ').' }); }
    finally { setBusy(false); }
  }

  async function doCheck(shiftId, kind) {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không thấy khuôn mặt. Thử lại.' }); return; }
      const res = await (kind === 'in' ? shiftCheckIn(shiftId, cap) : shiftCheckOut(shiftId, cap));
      const flags = [];
      if (res.faceSuspect) flags.push('khuôn mặt nghi ngờ');
      if (res.outOfZone) flags.push('ngoài vùng văn phòng');
      if (res.outOfWindow) flags.push('ngoài cửa sổ giờ');
      setMsg({ kind: flags.length ? 'warn' : 'ok',
        text: (kind === 'in' ? 'Đã check-in' : 'Đã check-out') + (flags.length ? ' ⚠ ' + flags.join(', ') : ' thành công') });
      onChanged && onChanged();
    } catch (e) { setMsg({ kind: 'err', text: ERR[e.code] || ('Chấm công thất bại (' + e.message + ').') }); }
    finally { setBusy(false); }
  }

  return (
    <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start' }}>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', display: 'block', background: '#000', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        {camError && <div className="empty" style={{ color: 'var(--red-600)' }}>{camError}</div>}
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{me.name}</div>
        <div className="divider" style={{ margin: '14px 0' }}></div>

        {!enrolled ? (
          <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
            <Icon name="user" size={16} />Đăng ký khuôn mặt
          </button>
        ) : shifts.length === 0 ? (
          <div className="empty">Chưa có ca được duyệt hôm nay.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {shifts.map((s) => (
              <div key={s.id} style={{ borderTop: '1px solid var(--line)', paddingTop: 12 }}>
                <div className="muted" style={{ fontSize: 12.5, marginBottom: 8 }}>
                  Ca <b className="mono">{fmtTime(s.start)}–{fmtTime(s.end)}</b>
                  {' '}· {s.shiftType === 'ctv' ? 'CTV' : 'OT'} ×{s.rate} · ±15'
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  {s.checkIn ? (
                    <Badge kind="green" dot>Vào {fmtTime(s.checkIn)}</Badge>
                  ) : (
                    <button className="btn btn-primary btn-sm" disabled={busy || !ready || !s.checkInOpen}
                      onClick={() => doCheck(s.id, 'in')}>
                      <Icon name="checkCircle" size={15} />Check-in
                    </button>
                  )}
                  {s.checkOut ? (
                    <Badge kind="gray" dot>Ra {fmtTime(s.checkOut)}</Badge>
                  ) : (
                    <button className="btn btn-ghost btn-sm" disabled={busy || !ready || !s.checkOutOpen}
                      onClick={() => doCheck(s.id, 'out')}>
                      <Icon name="logout" size={15} />Check-out
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {!ready && !camError && <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>Đang khởi tạo camera…</div>}
        {msg && (
          <div style={{ marginTop: 12, fontSize: 13, fontWeight: 600,
            color: msg.kind === 'ok' ? 'var(--green)' : msg.kind === 'warn' ? 'var(--amber)' : 'var(--red-600)' }}>
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
}
