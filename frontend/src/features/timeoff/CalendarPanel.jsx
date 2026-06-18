/* Tab "Lịch" — lịch nghỉ phép (toggle Năm/Tháng), giống màn Time Off của Odoo.
   Owner: Nhật Anh. Spec §3.7. */
import { useState, useEffect, useMemo } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchCalendar } from '../../api/timeoff';

const NOW = new Date();
const DOW = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']; // Chủ nhật trước
const MONTH_LABEL = (m) => 'Tháng ' + (m + 1);

const pad = (n) => String(n).padStart(2, '0');
const isoOf = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`;        // m: 0-based
const parseISO = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };

/* Thứ hạng trạng thái để chọn "đơn mạnh nhất" khi 1 ngày trùng nhiều đơn. */
const RANK = { validate: 3, validate1: 2, confirm: 2, draft: 1, refuse: 1, cancel: 0 };

/* Bản đồ ngày → thông tin nghỉ (sau khi lọc loại). */
function buildDayMap(leaves, activeIds) {
  const map = {};
  for (const lv of leaves) {
    if (lv.state === 'cancel' || !lv.from || !lv.to) continue;
    if (activeIds && !activeIds.has(lv.leaveTypeId)) continue;
    const end = parseISO(lv.to);
    for (let cur = parseISO(lv.from); cur <= end; cur.setDate(cur.getDate() + 1)) {
      const key = isoOf(cur.getFullYear(), cur.getMonth(), cur.getDate());
      const r = RANK[lv.state] ?? 1;
      if (!map[key] || r > map[key].rank) {
        map[key] = { rank: r, color: lv.color, state: lv.state, leaveType: lv.leaveType, employee: lv.employee };
      }
    }
  }
  return map;
}

/* Tập ngày bắt buộc (date string) + nhãn. */
function buildMandatory(mdays) {
  const set = new Map();
  for (const m of mdays) {
    if (!m.from || !m.to) continue;
    const end = parseISO(m.to);
    for (let cur = parseISO(m.from); cur <= end; cur.setDate(cur.getDate() + 1)) {
      set.set(isoOf(cur.getFullYear(), cur.getMonth(), cur.getDate()), m.name);
    }
  }
  return set;
}

function cellStyle(info, big) {
  const base = {
    aspectRatio: '1', display: 'flex', alignItems: 'center', justifyContent: 'center',
    borderRadius: big ? 8 : 5, fontSize: big ? 14 : 11, fontWeight: 600,
    color: 'var(--ink)', position: 'relative',
  };
  if (!info) return base;
  if (info.state === 'validate') {
    return { ...base, background: info.color, color: '#fff' };
  }
  if (info.state === 'refuse') {
    return { ...base, color: 'var(--muted)', textDecoration: 'line-through' };
  }
  // chờ duyệt: nền nhạt + viền màu (sọc nhẹ qua border)
  return { ...base, background: info.color + '26', boxShadow: `inset 0 0 0 1.5px ${info.color}` };
}

function MonthGrid({ year, month, dayMap, mandatory, big }) {
  const firstDow = new Date(year, month, 1).getDay(); // 0 = CN
  const nDays = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= nDays; d++) cells.push(d);

  return (
    <div className="card" style={{ padding: big ? 16 : 12, boxShadow: big ? undefined : 'none', border: '1px solid var(--border)' }}>
      <div style={{ fontWeight: 800, fontSize: big ? 16 : 13, marginBottom: 8 }}>
        {MONTH_LABEL(month)} {year}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: big ? 6 : 3 }}>
        {DOW.map((d, i) => (
          <div key={d} style={{ textAlign: 'center', fontSize: big ? 12 : 10, fontWeight: 700, color: i === 0 ? 'var(--red-600)' : 'var(--muted)' }}>{d}</div>
        ))}
        {cells.map((d, i) => {
          if (d === null) return <div key={'e' + i}></div>;
          const key = isoOf(year, month, d);
          const info = dayMap[key];
          const mdName = mandatory.get(key);
          const dow = (firstDow + d - 1) % 7;
          const st = cellStyle(info, big);
          if (!info && (dow === 0 || dow === 6)) st.background = st.background || 'var(--surface-2)';
          return (
            <div key={key} style={st} title={[
              info && `${info.leaveType}${info.employee ? ' — ' + info.employee : ''}`,
              mdName,
            ].filter(Boolean).join(' · ')}>
              {d}
              {mdName && (
                <span style={{ position: 'absolute', top: 2, right: 2, width: 6, height: 6, borderRadius: 3, background: 'var(--red-600)' }}></span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CalendarPanel({ isOfficer }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(NOW.getFullYear());
  const [month, setMonth] = useState(NOW.getMonth());
  const [mode, setMode] = useState('year');   // 'year' | 'month'
  const [scope, setScope] = useState('me');     // 'me' | 'all'
  const [active, setActive] = useState(null);   // Set id loại đang bật (null = tất cả)
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchCalendar(year, scope).then((d) => {
      setData(d);
      setActive(new Set(d.leaveTypes.map((t) => t.id))); // bật tất cả loại
    }).catch((e) => setErr(e.message));
  }, [year, scope, tick]);

  const dayMap = useMemo(() => data ? buildDayMap(data.leaves, active) : {}, [data, active]);
  const mandatory = useMemo(() => data ? buildMandatory(data.mandatoryDays) : new Map(), [data]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải lịch nghỉ phép…" />;

  const toggleType = (id) => setActive((prev) => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  const stepBack = () => mode === 'year' ? setYear((y) => y - 1)
    : (month === 0 ? (setMonth(11), setYear((y) => y - 1)) : setMonth((m) => m - 1));
  const stepFwd = () => mode === 'year' ? setYear((y) => y + 1)
    : (month === 11 ? (setMonth(0), setYear((y) => y + 1)) : setMonth((m) => m + 1));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 16, alignItems: 'start' }}>
      {/* Cột lịch */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="filterbar">
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="icon-btn" onClick={stepBack}>
              <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
            <span className="mono" style={{ fontWeight: 700, minWidth: mode === 'year' ? 48 : 110, textAlign: 'center' }}>
              {mode === 'year' ? year : `${MONTH_LABEL(month)} ${year}`}</span>
            <button className="icon-btn" onClick={stepFwd}><Icon name="chevR" size={16} /></button>
            <button className="btn btn-ghost btn-sm" onClick={() => { setYear(NOW.getFullYear()); setMonth(NOW.getMonth()); }}>Hôm nay</button>
          </div>
          <div style={{ marginLeft: 'auto' }} className="seg">
            <button className={mode === 'year' ? 'active' : ''} onClick={() => setMode('year')}>Năm</button>
            <button className={mode === 'month' ? 'active' : ''} onClick={() => setMode('month')}>Tháng</button>
          </div>
        </div>

        {mode === 'year' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(230px,1fr))', gap: 12 }}>
            {Array.from({ length: 12 }, (_, m) => (
              <MonthGrid key={m} year={year} month={m} dayMap={dayMap} mandatory={mandatory} />
            ))}
          </div>
        ) : (
          <MonthGrid year={year} month={month} dayMap={dayMap} mandatory={mandatory} big />
        )}
      </div>

      {/* Cột phải: phạm vi + lọc + legend + ngày bắt buộc */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {isOfficer && (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Phạm vi</div>
            <div className="seg" style={{ width: '100%' }}>
              <button className={scope === 'me' ? 'active' : ''} onClick={() => setScope('me')}>Của tôi</button>
              <button className={scope === 'all' ? 'active' : ''} onClick={() => setScope('all')}>Cả đội</button>
            </div>
          </div>
        )}

        <div className="card" style={{ padding: 14 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Loại nghỉ</div>
          {data.leaveTypes.length === 0 && <div className="muted" style={{ fontSize: 12.5 }}>Không có đơn nào trong năm.</div>}
          {data.leaveTypes.map((t) => (
            <label key={t.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '5px 0', fontSize: 13, cursor: 'pointer' }}>
              <input type="checkbox" checked={active?.has(t.id) || false} onChange={() => toggleType(t.id)} />
              <span style={{ width: 11, height: 11, borderRadius: 3, background: t.color }}></span>
              {t.name}
            </label>
          ))}
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Chú thích</div>
          <LegendRow swatch={{ background: 'var(--red-600)' }} label="Đã duyệt" />
          <LegendRow swatch={{ background: 'rgba(200,16,46,.15)', boxShadow: 'inset 0 0 0 1.5px var(--red-600)' }} label="Chờ duyệt" />
          <LegendRow swatch={{ border: '1px solid var(--border-strong)' }} label="Từ chối (gạch ngang)" />
          <LegendRow dot label="Ngày bắt buộc / nghỉ lễ" />
        </div>

        {data.mandatoryDays.length > 0 && (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Ngày bắt buộc</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.mandatoryDays.map((m, i) => (
                <div key={i} style={{ fontSize: 12.5 }}>
                  <div style={{ fontWeight: 600 }}>{m.name}</div>
                  <div className="muted mono" style={{ fontSize: 11.5 }}>
                    {fmtDate(m.from)}{m.to !== m.from ? ' → ' + fmtDate(m.to) : ''}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LegendRow({ swatch, dot, label }) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 0', fontSize: 12.5 }}>
      <span style={{ width: 16, height: 16, borderRadius: 4, position: 'relative', ...(swatch || {}) }}>
        {dot && <span style={{ position: 'absolute', top: 1, right: 1, width: 6, height: 6, borderRadius: 3, background: 'var(--red-600)' }}></span>}
      </span>
      {label}
    </div>
  );
}
