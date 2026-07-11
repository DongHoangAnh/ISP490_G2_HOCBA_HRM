/* Lịch dạy theo tuần của giáo viên — chỉ hiển thị sessions của chính họ (từ CMS).
   Không có dữ liệu giáo viên khác; khác với ShiftCalendar (CTV thấy của mọi người). */
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchTeachingWeek } from '../../api/attendance';

const ROLE_LABEL = { MAIN_TEACHER: 'GV chính', ASSISTANT: 'Trợ giảng', TEACHER: 'GV' };

function mondayOf(date) {
  const d = new Date(date);
  const wd = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - wd);
  d.setHours(0, 0, 0, 0);
  return d;
}
function ymd(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export default function TeachingCalendar() {
  const [monday, setMonday] = useState(() => mondayOf(new Date()));
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setErr(null); setData(null);
    fetchTeachingWeek(ymd(monday))
      .then(setData)
      .catch((e) => setErr(e.message));
  }, [monday]);

  const moveWeek = (n) => {
    const d = new Date(monday); d.setDate(d.getDate() + n * 7); setMonday(d);
  };

  if (err) return <ErrorState message={err} onRetry={() => { setErr(null); setData(null); fetchTeachingWeek(ymd(monday)).then(setData).catch((e) => setErr(e.message)); }} />;
  if (!data) return <LoadingState label="Đang tải lịch dạy tuần…" />;

  const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  // Nhóm sessions theo ngày từ data.rows
  const byDate = {};
  for (const s of data.rows || []) {
    const key = s.date;
    if (!byDate[key]) byDate[key] = [];
    byDate[key].push(s);
  }

  // Tạo 7 ngày từ monday
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday); d.setDate(d.getDate() + i);
    const key = ymd(d);
    return { date: key, weekday: WEEKDAYS[i], sessions: byDate[key] || [] };
  });

  const today = ymd(new Date());

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(-1)}>‹ Tuần trước</button>
        <div style={{ fontWeight: 600, fontSize: 13.5 }}>
          Tuần {fmtDate(days[0].date)} – {fmtDate(days[6].date)}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(1)}>Tuần sau ›</button>
        <button className="btn btn-ghost btn-sm" style={{ marginLeft: 4 }} onClick={() => setMonday(mondayOf(new Date()))}>
          Tuần này
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 8 }}>
        {days.map((day) => (
          <div key={day.date} className="card" style={{
            padding: 8, minHeight: 120,
            background: day.date === today ? 'var(--primary-5, #eff6ff)' : undefined,
          }}>
            <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 6 }}>
              {day.weekday}
              <span className="muted" style={{ fontWeight: 400, marginLeft: 4 }}>
                {fmtDate(day.date).slice(0, 5)}
              </span>
            </div>

            {day.sessions.length === 0
              ? <div className="faint" style={{ fontSize: 11 }}>—</div>
              : day.sessions.map((s) => (
                <div key={s.id} style={{
                  borderRadius: 6,
                  padding: '6px 8px',
                  marginBottom: 6,
                  fontSize: 11,
                  background: s.checkIn && s.checkOut ? '#ecfdf5'
                    : s.checkIn ? '#eff6ff'
                    : 'var(--surface-2, #f8f9fa)',
                  border: '1px solid ' + (s.checkIn && s.checkOut ? '#6ee7b7'
                    : s.checkIn ? '#bfdbfe'
                    : 'var(--line)'),
                }}>
                  <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.className || '(Chưa đặt tên)'}
                  </div>
                  <div className="mono" style={{ fontWeight: 600 }}>
                    {s.startTime}–{s.endTime}
                  </div>
                  <div style={{ color: 'var(--muted)', marginTop: 2 }}>
                    {ROLE_LABEL[s.roleType] || s.roleType}
                  </div>
                  {s.checkIn && (
                    <div style={{ marginTop: 3, color: 'var(--green, #16a34a)' }}>
                      ✓ {s.checkIn.slice(11, 16)}
                      {s.checkOut ? ` → ${s.checkOut.slice(11, 16)}` : ''}
                    </div>
                  )}
                </div>
              ))
            }
          </div>
        ))}
      </div>
    </div>
  );
}
