/* Lịch dạy giáo viên + chấm công theo buổi.
   Lịch lấy từ CMS MySQL (không tự đăng ký được).
   Giao diện tương tự ShiftAttendance nhưng dành riêng cho giáo viên. */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useFaceApi } from './useFaceApi';
import { enrollFace, fetchTeachingSchedule, teachingCheckIn, teachingCheckOut } from '../../api/attendance';
import { fetchSubstitutions } from '../../api/timeoff';

const ERR = {
  session_not_found: 'Không tìm thấy buổi học trong lịch CMS.',
  outside_shift_window: 'Ngoài cửa sổ chấm công của buổi (±15 phút).',
  already_checked_in: 'Buổi này đã check-in rồi.',
  not_checked_in: 'Chưa check-in nên không thể check-out.',
  already_checked_out: 'Buổi này đã check-out rồi.',
  not_teacher: 'Tài khoản chưa được liên kết với CMS.',
};

const ROLE_LABEL = {
  MAIN_TEACHER: 'GV chính',
  ASSISTANT: 'Trợ giảng',
  TEACHER: 'GV',
};

function SessionCard({ session, busy, onCheck }) {
  const role = ROLE_LABEL[session.roleType] || session.roleType;
  const statusDone = session.status === 'COMPLETED';

  return (
    <div style={{
      borderRadius: 8,
      border: '1px solid var(--line)',
      padding: '14px 16px',
      background: statusDone ? 'var(--surface-2, #f8f9fa)' : 'var(--card-bg, #fff)',
    }}>
      {/* Header: tên lớp + vai trò */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div style={{ fontWeight: 700, fontSize: 15 }}>{session.className || '(Chưa đặt tên lớp)'}</div>
        <Badge kind={statusDone ? 'green' : 'blue'}>{statusDone ? 'Đã hoàn thành' : 'Kế hoạch'}</Badge>
      </div>

      {/* Thời gian + vai trò */}
      <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
        <b className="mono">{session.startTime}–{session.endTime}</b>
        {' '}· <span>{role}</span>
        {' '}· ±15 phút
      </div>

      {/* Trạng thái & nút check-in/out */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        {session.checkIn ? (
          <Badge kind="green" dot>Vào {session.checkIn.slice(11, 16)}</Badge>
        ) : session.checkInOpen ? (
          <button className="btn btn-primary btn-sm" disabled={busy}
            onClick={() => onCheck(session.id, 'in')}>
            <Icon name="checkCircle" size={15} />Check-in
          </button>
        ) : (
          <span className="muted" style={{ fontSize: 12 }}>Chưa đến giờ check-in</span>
        )}

        {session.checkOut ? (
          <Badge kind="gray" dot>Ra {session.checkOut.slice(11, 16)}</Badge>
        ) : session.checkIn && session.checkOutOpen ? (
          <button className="btn btn-ghost btn-sm" disabled={busy}
            onClick={() => onCheck(session.id, 'out')}>
            <Icon name="logout" size={15} />Check-out
          </button>
        ) : null}
      </div>

      {/* Cờ cảnh báo */}
      {(session.faceSuspect || session.outOfZone || session.outOfWindow) && (
        <div style={{ marginTop: 8, fontSize: 11.5, color: 'var(--amber)' }}>
          ⚠{session.faceSuspect ? ' Khuôn mặt nghi ngờ' : ''}
          {session.outOfZone ? ' · Ngoài vùng VP' : ''}
          {session.outOfWindow ? ' · Ngoài cửa sổ giờ' : ''}
        </div>
      )}
    </div>
  );
}

export default function TeachingSchedule({ me, onChanged, onGoTimeOff }) {
  const { videoRef, ready, camError, capture } = useFaceApi();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [enrolled, setEnrolled] = useState(me.enrolled);
  // Nhắc yêu cầu dạy thay đang chờ (từ module Nghỉ phép) — link sang panel xử lý.
  const [subPending, setSubPending] = useState(0);
  useEffect(() => {
    fetchSubstitutions()
      .then((d) => setSubPending((d.items || []).filter((r) => r.state === 'pending').length))
      .catch(() => {});
  }, []);
  // sessions lấy từ teachingToday (preloaded trong me) hoặc fetch lại
  const [sessions, setSessions] = useState(me.teachingToday || []);
  const [date, setDate] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  });

  useEffect(() => { setEnrolled(me.enrolled); }, [me.enrolled]);

  const loadDate = useCallback((d) => {
    fetchTeachingSchedule(d)
      .then((res) => setSessions(res.rows || []))
      .catch(() => setSessions([]));
  }, []);

  // Khi đổi ngày thì fetch lại; ngày hôm nay đã có sẵn từ me.teachingToday
  const todayStr = date;
  useEffect(() => {
    const today = new Date();
    const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    if (date !== todayIso) {
      loadDate(date);
    } else {
      setSessions(me.teachingToday || []);
    }
  }, [date, me.teachingToday, loadDate]);

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

  async function doCheck(sessionId, kind) {
    setBusy(true); setMsg(null);
    try {
      const cap = await capture();
      if (!cap) { setMsg({ kind: 'err', text: 'Camera chưa sẵn sàng.' }); return; }
      if (cap.error === 'no_face') { setMsg({ kind: 'warn', text: 'Không thấy khuôn mặt. Thử lại.' }); return; }
      const res = await (kind === 'in'
        ? teachingCheckIn(sessionId, cap)
        : teachingCheckOut(sessionId, cap));
      const flags = [];
      if (res.faceSuspect) flags.push('khuôn mặt nghi ngờ');
      if (res.outOfZone) flags.push('ngoài vùng văn phòng');
      if (res.outOfWindow) flags.push('ngoài cửa sổ giờ');
      setMsg({
        kind: flags.length ? 'warn' : 'ok',
        text: (kind === 'in' ? 'Đã check-in' : 'Đã check-out')
          + (flags.length ? ' ⚠ ' + flags.join(', ') : ' thành công'),
      });
      // Reload sessions để cập nhật trạng thái check-in/out
      loadDate(date);
      onChanged && onChanged();
    } catch (e) {
      setMsg({ kind: 'err', text: ERR[e.code] || ('Chấm công thất bại: ' + e.message) });
    } finally { setBusy(false); }
  }

  const today = new Date();
  const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const isToday = date === todayIso;

  return (
    <>
    {subPending > 0 && (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, padding: '11px 14px', background: 'var(--amber-50,#fffbeb)', border: '1px solid var(--amber-100,#fef3c7)', borderRadius: 10, fontSize: 13, color: 'var(--amber-700,#b45309)' }}>
        <Icon name="bell" size={16} />
        <span style={{ flex: 1 }}>
          Bạn có <b>{subPending}</b> yêu cầu dạy thay đang chờ phản hồi.
        </span>
        {onGoTimeOff && (
          <button className="btn btn-ghost btn-sm" onClick={onGoTimeOff}>Xem &amp; phản hồi</button>
        )}
      </div>
    )}
    <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 1fr', alignItems: 'start' }}>
      {/* Camera */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', display: 'block', background: '#000', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        {camError && <div className="empty" style={{ color: 'var(--red-600)' }}>{camError}</div>}
      </div>

      {/* Danh sách buổi dạy */}
      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>{me.name}</div>
        <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Giáo viên · Lịch từ CMS</div>
        <div className="divider" style={{ margin: '14px 0' }} />

        {/* Date picker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={{ fontSize: 13, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--line)' }}
          />
          {!isToday && (
            <button className="btn btn-ghost btn-sm" onClick={() => setDate(todayIso)}>
              Hôm nay
            </button>
          )}
        </div>

        {!enrolled ? (
          <button className="btn btn-primary" disabled={busy || !ready} onClick={doEnroll}>
            <Icon name="user" size={16} />Đăng ký khuôn mặt
          </button>
        ) : sessions.length === 0 ? (
          <div className="empty">
            {isToday ? 'Không có lịch dạy hôm nay.' : 'Không có lịch dạy ngày này.'}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {sessions.map((s) => (
              <SessionCard
                key={s.id}
                session={s}
                busy={busy || !ready}
                onCheck={doCheck}
              />
            ))}
          </div>
        )}

        {!ready && !camError && (
          <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>Đang khởi tạo camera…</div>
        )}
        {msg && (
          <div style={{
            marginTop: 12, fontSize: 13, fontWeight: 600,
            color: msg.kind === 'ok' ? 'var(--green)'
              : msg.kind === 'warn' ? 'var(--amber)'
              : 'var(--red-600)',
          }}>
            {msg.text}
          </div>
        )}
      </div>
    </div>
    </>
  );
}
