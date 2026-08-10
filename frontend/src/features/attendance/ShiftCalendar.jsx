/* Lịch ca theo tuần — lưới 7 cột (T2→CN) (Gói 4A). Điều phối: tải tuần, đăng ký
   ca (ShiftForm), xem/duyệt/hủy 1 ca (ShiftDrawer), chuyển tuần trước/sau. */
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fmtTime } from './util';
import { fetchWeekShifts } from '../../api/attendance';
import ShiftForm from './ShiftForm';
import ShiftDrawer from './ShiftDrawer';

const CHIP_BG = { pending: 'var(--amber-bg)', approved: '#ecfdf5', rejected: 'var(--red-50)' };

function ymd(d) {
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}
function mondayOf(date) {
  const d = new Date(date);
  const wd = (d.getDay() + 6) % 7;   // 0=Th2
  d.setDate(d.getDate() - wd);
  d.setHours(0, 0, 0, 0);
  return d;
}

export default function ShiftCalendar({ canManage, me }) {
  const [monday, setMonday] = useState(() => mondayOf(new Date()));
  const [typeFilter, setTypeFilter] = useState('');   // '' | 'ot' | 'ctv' (manager only)
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchWeekShifts(ymd(monday), typeFilter || undefined).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [monday, typeFilter]);

  const moveWeek = (n) => {
    const d = new Date(monday); d.setDate(d.getDate() + n); setMonday(d);
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải lịch ca…" />;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(-7)}>‹ Tuần trước</button>
        <div style={{ fontWeight: 600, fontSize: 13.5 }}>
          Tuần {fmtDate(data.days[0].date)} – {fmtDate(data.days[6].date)}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => moveWeek(7)}>Tuần sau ›</button>
        <div style={{ flex: 1 }} />
        {canManage && (
          <select className="sel" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            style={{ width: 'auto' }}>
            <option value="">Tất cả</option>
            <option value="ot">OT</option>
            <option value="ctv">CTV</option>
          </select>
        )}
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>Đăng ký ca</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 8 }}>
        {data.days.map((day) => (
          <div key={day.date} className="card" style={{ padding: 8, minHeight: 120 }}>
            <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 6 }}>
              {day.weekday}<span className="muted" style={{ fontWeight: 400, marginLeft: 4 }}>{fmtDate(day.date).slice(0, 5)}</span>
            </div>
            {day.shifts.length === 0 && <div className="faint" style={{ fontSize: 11 }}>—</div>}
            {day.shifts.map((s) => (
              <button key={s.id} onClick={() => setSel(s)}
                style={{ display: 'block', width: '100%', textAlign: 'left', border: '1px solid ' + (s.mine ? 'var(--red-300,#fca5a5)' : 'var(--border)'), borderRadius: 8, padding: '6px 8px', marginBottom: 6, background: CHIP_BG[s.state], cursor: 'pointer', opacity: s.locked ? 0.6 : 1 }}>
                <div style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.empName}</div>
                <div className="mono" style={{ fontSize: 12, fontWeight: 600 }}>{fmtTime(s.start)}–{fmtTime(s.end)}</div>
                <div style={{ fontSize: 11 }}>{s.shiftTypeLabel} ×{s.rate}{s.locked ? ' · đã khóa' : ''}</div>
              </button>
            ))}
          </div>
        ))}
      </div>

      {showForm && <ShiftForm canManage={canManage} me={me} onClose={() => setShowForm(false)} onSaved={load} />}
      {sel && <ShiftDrawer shift={sel} canManage={canManage}
        onClose={() => setSel(null)} onChanged={() => { setSel(null); load(); }} />}
    </div>
  );
}
