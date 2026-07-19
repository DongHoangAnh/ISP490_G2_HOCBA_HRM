/* Panel tự chấm công face/geo (thay kiosk). Nhận `me` (từ /api/attendance/me)
   và onChanged() để refetch sau khi chấm. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useFaceApi } from './useFaceApi';
import { enrollFace, checkIn, checkOut } from '../../api/attendance';
import { fmtTime, attStatus } from './util';

export default function CheckInPanel({ me, onChanged }) {
  const { videoRef, ready, camError, capture } = useFaceApi();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null); // {kind:'ok'|'warn'|'err', text}
  const [enrolled, setEnrolled] = useState(me.enrolled);

  const p = me.policy;
  const t = me.today;

  async function doEnroll() {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không phát hiện khuôn mặt. Thử lại.' }); return; }
      await enrollFace(cap.photo, cap.descriptor);
      setEnrolled(true);
      setMsg({ kind: 'ok', text: 'Đăng ký khuôn mặt thành công.' });
    } catch (e) {
      setMsg({ kind: 'err', text: 'Đăng ký thất bại (' + e.message + ').' });
    } finally { setBusy(false); }
  }

  async function doCheck(kind) {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không phát hiện khuôn mặt. Thử lại.' }); return; }
      const res = await (kind === 'in' ? checkIn(cap) : checkOut(cap));
      const flags = [];
      if (res.faceSuspect) flags.push('khuôn mặt nghi ngờ');
      if (res.outOfZone) flags.push('ngoài vùng văn phòng');
      if (res.outOfWindow && me.isOfficial) flags.push('ngoài khung giờ');
      setMsg({
        kind: flags.length ? 'warn' : 'ok',
        text: (kind === 'in' ? 'Đã check-in' : 'Đã check-out')
          + (flags.length ? ' ⚠ ' + flags.join(', ') : ' thành công'),
      });
      onChanged && onChanged();
    } catch (e) {
      const M = {
        manager_no_checkin: 'Tài khoản quản lý không điểm danh.',
        not_workday: 'Hôm nay không phải ngày làm việc.',
        already_checked_in: 'Bạn đã check-in hôm nay rồi.',
        not_checked_in: 'Bạn chưa check-in nên không thể check-out.',
        already_checked_out: 'Bạn đã check-out hôm nay rồi.',
        no_shift_today: 'Chưa có ca được duyệt hôm nay.',
        outside_shift_window: 'Ngoài cửa sổ check-in của ca (±15 phút).',
        on_approved_leave: 'Bạn đang trong kỳ nghỉ phép đã duyệt — không thể chấm công hôm nay.',
      };
      setMsg({ kind: 'err', text: M[e.code] || ('Điểm danh thất bại (' + e.message + ').') });
    } finally { setBusy(false); }
  }

  const [stLabel, stKind] = attStatus(t ? t.statusKey : 'none');

  return (
    <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start' }}>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', display: 'block', background: '#000', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        {camError && <div className="empty" style={{ color: 'var(--red-600)' }}>{camError}</div>}
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{me.name}</div>
        {me.isOfficial && (
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            Khung giờ: check-in {p.checkInStart}–{p.checkInEnd} · check-out {p.checkOutStart}–{p.checkOutEnd}
          </div>
        )}

        <div className="divider" style={{ margin: '14px 0' }}></div>

        <div className="between" style={{ marginBottom: 6 }}>
          <span className="muted" style={{ fontSize: 13 }}>Hôm nay</span>
          <Badge kind={stKind} dot>{stLabel}</Badge>
        </div>
        <div style={{ display: 'flex', gap: 18, fontSize: 13 }}>
          <div><span className="muted">Check-in: </span><b className="mono">{fmtTime(t && t.checkIn)}</b>
            {t && t.lateMinutes > 0 && <span style={{ color: 'var(--amber)', fontWeight: 600 }}> +{t.lateMinutes}'</span>}</div>
          <div><span className="muted">Check-out: </span><b className="mono">{fmtTime(t && t.checkOut)}</b></div>
        </div>

        <div className="divider" style={{ margin: '14px 0' }}></div>

        {!me.isOfficial ? (
          <div className="empty">Bạn chấm công theo ca ở tab "Chấm công".</div>
        ) : !enrolled ? (
          <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
            <Icon name="user" size={16} />Đăng ký khuôn mặt
          </button>
        ) : !me.isWorkdayToday ? (
          <div className="empty">Hôm nay không phải ngày làm việc — không điểm danh.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {t && t.checkIn ? (
              <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                <Icon name="checkCircle" size={15} /> Đã check-in lúc {fmtTime(t.checkIn)}
              </div>
            ) : (
              <button className="btn btn-primary" disabled={busy || !ready} onClick={() => doCheck('in')}>
                <Icon name="checkCircle" size={16} />Check-in
              </button>
            )}
            {t && t.checkOut ? (
              <div className="muted" style={{ fontSize: 13, fontWeight: 600 }}>
                <Icon name="logout" size={15} /> Đã check-out lúc {fmtTime(t.checkOut)}
              </div>
            ) : (
              <button className="btn btn-ghost" disabled={busy || !ready || !(t && t.checkIn)} onClick={() => doCheck('out')}>
                <Icon name="logout" size={16} />Check-out
              </button>
            )}
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
