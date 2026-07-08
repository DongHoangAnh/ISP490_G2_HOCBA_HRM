/* Tab "Lịch" — lịch nghỉ phép (toggle Năm/Tháng), giống màn Time Off của Odoo.
   Owner: Nhật Anh. Spec §3.7. */
import { useState, useEffect, useMemo, useRef } from 'react';
import Icon from '../../components/Icon';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
import { fmtDate } from '../../utils/format';
import { fetchCalendar } from '../../api/timeoff';
import { fetchTeachingDays } from '../../api/attendance';

const NOW = new Date();
const DOW = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']; // Chủ nhật trước
const MONTH_LABEL = (m) => 'Tháng ' + (m + 1);

const pad = (n) => String(n).padStart(2, '0');
const isoOf = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`;        // m: 0-based
const parseISO = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };

/* Thứ hạng trạng thái để chọn "đơn mạnh nhất" khi 1 ngày trùng nhiều đơn. */
const RANK = { validate: 3, validate1: 2, confirm: 2, draft: 1, refuse: 1, cancel: 0 };

/* Ngưỡng cảnh báo trùng lịch (Phase 4) — khớp OVERLAP_WARN của backend.
   Ngày có >= ngần này người nghỉ (đã duyệt) tô cảnh báo "quá tải". */
const OVERLAP_WARN = 3;

/* Bản đồ ngày → thông tin nghỉ (sau khi lọc loại). count = số người đã DUYỆT
   nghỉ trong ngày (Phase 4: cảnh báo ngày trùng lịch khi xem "Cả đội"). */
function buildDayMap(leaves, activeIds) {
  const map = {};
  for (const lv of leaves) {
    if (lv.state === 'cancel' || !lv.from || !lv.to) continue;
    if (activeIds && !activeIds.has(lv.leaveTypeId)) continue;
    const end = parseISO(lv.to);
    for (let cur = parseISO(lv.from); cur <= end; cur.setDate(cur.getDate() + 1)) {
      const key = isoOf(cur.getFullYear(), cur.getMonth(), cur.getDate());
      const r = RANK[lv.state] ?? 1;
      const slot = map[key] || (map[key] = { rank: -1, count: 0 });
      if (lv.state === 'validate') slot.count += 1;
      if (r > slot.rank) {
        slot.rank = r; slot.color = lv.color; slot.state = lv.state;
        slot.leaveType = lv.leaveType; slot.employee = lv.employee;
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

/* Tập ngày đi làm thêm (date string) → nhãn. */
function buildWorkdays(workDays) {
  const set = new Map();
  for (const w of (workDays || [])) {
    if (w.date) set.set(w.date, w.name || 'Ngày đi làm');
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
    // đã duyệt: nền tint nhẹ + viền mảnh + chữ đậm (dịu hơn nền tô đặc cũ)
    return { ...base, background: info.color + '22', boxShadow: `inset 0 0 0 1px ${info.color}`, fontWeight: 700 };
  }
  if (info.state === 'refuse') {
    return { ...base, color: 'var(--muted)', textDecoration: 'line-through' };
  }
  // chờ duyệt: nền trắng + viền màu + chữ màu
  return { ...base, color: info.color, boxShadow: `inset 0 0 0 1.5px ${info.color}` };
}

function MonthGrid({ year, month, dayMap, mandatory, workdays, teaching, teacherView, big }) {
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
          // GV (xem "Của tôi"): bỏ ngày đi làm văn phòng, thay bằng lịch dạy.
          const wdName = teacherView ? null : workdays.get(key);
          const teachCount = teacherView ? (teaching.get(key) || 0) : 0;
          const dow = (firstDow + d - 1) % 7;
          const st = cellStyle(info, big);
          if (!info) {
            if (wdName) { st.background = 'rgba(16,185,129,.12)'; st.boxShadow = 'inset 0 0 0 1.5px var(--green)'; }
            else if (teacherView) {
              if (teachCount) st.background = 'var(--blue-bg)';
              else if (dow === 0 || dow === 6) st.color = 'var(--faint)';
            }
            else if (dow === 0 || dow === 6) st.background = st.background || 'var(--surface-2)';
          }
          const overloaded = info && info.count >= OVERLAP_WARN;
          if (overloaded) st.boxShadow = 'inset 0 0 0 2px var(--amber-600,#d97706)';
          return (
            <div key={key} style={st} title={[
              info && `${info.leaveType}${info.employee ? ' — ' + info.employee : ''}`,
              info && info.count > 1 && (info.count + ' người nghỉ ngày này'),
              teachCount > 0 && (teachCount + ' buổi dạy'),
              wdName && ('Đi làm: ' + wdName),
              mdName,
            ].filter(Boolean).join(' · ')}>
              {d}
              {teachCount > 0 && (
                <span style={{ position: 'absolute', left: 2, top: 4, bottom: 4, width: 3, borderRadius: 2, background: 'var(--blue)' }}></span>
              )}
              {overloaded && (
                <span style={{ position: 'absolute', top: 2, left: 2, minWidth: 13, height: 13, padding: '0 3px', borderRadius: 7, background: 'var(--amber-600,#d97706)', color: '#fff', fontSize: 9, fontWeight: 800, display: 'grid', placeItems: 'center', lineHeight: 1 }}>{info.count}</span>
              )}
              {mdName && (
                <span style={{ position: 'absolute', top: 2, right: 2, width: 6, height: 6, borderRadius: 3, background: 'var(--red-600)' }}></span>
              )}
              {wdName && (
                <span style={{ position: 'absolute', bottom: 2, left: 2, width: 6, height: 6, borderRadius: 3, background: 'var(--green)' }}></span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CalendarPanel({ isOfficer, isTeacher, seeAll }) {
  const [year, setYear] = useState(NOW.getFullYear());
  const [month, setMonth] = useState(NOW.getMonth());
  const [mode, setMode] = useState('year');   // 'year' | 'month'
  const [dept, setDept] = useState('');         // HR lọc 1 phòng ban ('' = tất cả)
  const [active, setActive] = useState(null);   // Set id loại đang bật (null = tất cả)
  const [teaching, setTeaching] = useState(new Map()); // ngày dạy → số buổi (GV)
  const { data, err, loading, reload } = useFetch(
    () => fetchCalendar(year, seeAll ? (dept || undefined) : undefined),
    [year, dept, seeAll], `timeoff:calendar:${year}:${seeAll ? dept : 'mine'}`);

  // Query đổi (năm/phòng ban) và data MỚI về → bật tất cả loại nghỉ. Hai điều
  // kiện qua ref: (1) cùng query mà revalidate trả payload mới → không reset,
  // khỏi xóa toggle user đang chỉnh; (2) query vừa đổi nhưng data còn của query
  // cũ (effect chạy trước khi useFetch kịp setState) → chờ payload mới rồi mới
  // reset, không chốt nhầm danh sách loại của query trước.
  const activeKeyRef = useRef(null);
  const prevDataRef = useRef(null);
  useEffect(() => {
    if (!data) return;
    const key = `${year}:${seeAll ? dept : 'mine'}`;
    const dataChanged = prevDataRef.current !== data;
    prevDataRef.current = data;
    if (activeKeyRef.current === key || !dataChanged) return;
    activeKeyRef.current = key;
    setActive(new Set(data.leaveTypes.map((t) => t.id)));
  }, [data, year, dept, seeAll]);

  // GV xem lịch cá nhân: đánh dấu ngày có lịch dạy cả năm. Lỗi gọi API lịch dạy
  // KHÔNG chặn render lịch nghỉ — chỉ bỏ qua đánh dấu. (Officer xem lịch đội → tắt.)
  const teacherView = isTeacher && !isOfficer;
  useEffect(() => {
    if (!teacherView) { setTeaching(new Map()); return; }
    let cancelled = false;
    fetchTeachingDays(`${year}-01-01`, `${year}-12-31`)
      .then((d) => { if (!cancelled) setTeaching(new Map((d.days || []).map((x) => [x.date, x.count]))); })
      .catch(() => { if (!cancelled) setTeaching(new Map()); });
    return () => { cancelled = true; };
  }, [teacherView, year]);

  const dayMap = useMemo(() => data ? buildDayMap(data.leaves, active) : {}, [data, active]);
  const mandatory = useMemo(() => data ? buildMandatory(data.mandatoryDays) : new Map(), [data]);
  const workdays = useMemo(() => data ? buildWorkdays(data.workDays) : new Map(), [data]);
  const teachTotal = useMemo(() => [...teaching.values()].reduce((a, b) => a + b, 0), [teaching]);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton rows={8} />;

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
              <MonthGrid key={m} year={year} month={m} dayMap={dayMap} mandatory={mandatory} workdays={workdays} teaching={teaching} teacherView={teacherView} />
            ))}
          </div>
        ) : (
          <MonthGrid year={year} month={month} dayMap={dayMap} mandatory={mandatory} workdays={workdays} teaching={teaching} teacherView={teacherView} big />
        )}
      </div>

      {/* Cột phải: chọn phòng ban (HR) + lọc loại + legend + ngày bắt buộc */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {seeAll && (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Phòng ban</div>
            <DeptSelect value={dept} onChange={setDept} style={{ width: '100%' }}
              departments={data.allDepartments} />
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
          <LegendRow swatch={{ background: 'rgba(200,16,46,.13)', boxShadow: 'inset 0 0 0 1px var(--red-600)' }} label="Đã duyệt" />
          <LegendRow swatch={{ boxShadow: 'inset 0 0 0 1.5px var(--red-600)' }} label="Chờ duyệt" />
          <LegendRow swatch={{ border: '1px solid var(--border-strong)' }} label="Từ chối (gạch ngang)" />
          {teacherView
            ? <LegendRow swatch={{ background: 'var(--blue-bg)', boxShadow: 'inset 3px 0 0 var(--blue)' }} label="Ngày có lịch dạy" />
            : <LegendRow swatch={{ background: 'rgba(16,185,129,.12)', boxShadow: 'inset 0 0 0 1.5px var(--green)' }} label="Ngày đi làm (Thứ 7)" />}
          <LegendRow swatch={{ boxShadow: 'inset 0 0 0 2px var(--amber-600,#d97706)' }} label={`Trùng lịch (≥ ${OVERLAP_WARN} người nghỉ)`} />
          <LegendRow dot label="Ngày bắt buộc / nghỉ lễ" />
        </div>

        {teacherView ? (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>Lịch dạy</div>
            <div className="muted" style={{ fontSize: 12.5 }}>
              Ngày có lịch dạy lấy từ lịch giảng dạy của bạn.
            </div>
            <div style={{ fontSize: 12.5, marginTop: 8 }}>
              <b>{teaching.size}</b> ngày dạy · <b>{teachTotal}</b> buổi trong năm {year}
            </div>
          </div>
        ) : (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>Lịch làm việc</div>
            <div className="muted" style={{ fontSize: 12.5, marginBottom: workdays.size ? 10 : 0 }}>
              Chuẩn: Thứ 2 – Thứ 6. Các ngày Thứ 7 đi làm do HR thêm.
            </div>
            {workdays.size > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {[...workdays.entries()].sort().map(([d, name]) => (
                  <div key={d} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 3, background: 'var(--green)', flexShrink: 0 }}></span>
                    <span className="mono" style={{ fontWeight: 600 }}>{fmtDate(d)}</span>
                    <span className="muted">{name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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
