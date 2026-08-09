/* Tab "Lịch" — lịch NGÀY NGHỈ/LÀM của công ty (toggle Năm/Tháng).
   Chỉ tô 3 loại ngày: nghỉ cố định (T7/CN) · nghỉ lễ · ngày làm bù; cộng cảnh
   báo ngày trùng lịch (>= 3 người nghỉ đã duyệt). KHÔNG tô từng loại nghỉ phép
   nữa — quá nhiều đơn 1 ngày, tô lên lịch không đọc được.
   Owner: Nhật Anh. Spec §3.7. */
import { useState, useEffect, useMemo } from 'react';
import Icon from '../../components/Icon';
import { ErrorState, TableSkeleton } from '../../components/states';
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

/* Ngưỡng cảnh báo trùng lịch (Phase 4) — khớp OVERLAP_WARN của backend.
   Ngày có >= ngần này người nghỉ (đã duyệt) tô cảnh báo "quá tải". */
const OVERLAP_WARN = 3;

/* Màu cảnh báo trùng lịch — cam NHẠT, để không lấn át 3 màu ngày bên dưới.
   Badge dùng nền cam nhạt hơn + chữ nâu đậm cho đủ tương phản ở cỡ 9px. */
const OVERLAP_CLR = { line: '#F59E0B', badgeBg: '#FDBA74', badgeInk: '#7C2D12' };

/* 3 loại NGÀY được tô trên lịch. Lịch KHÔNG còn tô từng loại nghỉ phép
   (quá nhiều đơn 1 ngày, tô lên không đọc được) — chỉ còn khung ngày nghỉ/làm
   của công ty + cảnh báo trùng lịch. Ưu tiên: lễ > làm bù > nghỉ cố định. */
const DAY_KIND = {
  holiday: { label: 'Nghỉ lễ', bg: 'var(--red-50)', line: 'var(--red-600)', fg: 'var(--red-700)' },
  workday: { label: 'Ngày làm bù', bg: 'var(--green-bg)', line: 'var(--green)', fg: 'var(--green)' },
  weekend: { label: 'Nghỉ cố định (T7 / CN)', bg: 'var(--border)', line: 'var(--border-strong)', fg: 'var(--faint)' },
};

/* Bản đồ ngày → { count, names } của các đơn ĐÃ DUYỆT, chỉ để cảnh báo ngày
   trùng lịch (>= OVERLAP_WARN người nghỉ). Không dùng để tô màu ngày nữa. */
function buildLeaveLoad(leaves) {
  const map = {};
  for (const lv of leaves) {
    if (lv.state !== 'validate' || !lv.from || !lv.to) continue;
    const end = parseISO(lv.to);
    for (let cur = parseISO(lv.from); cur <= end; cur.setDate(cur.getDate() + 1)) {
      const key = isoOf(cur.getFullYear(), cur.getMonth(), cur.getDate());
      const slot = map[key] || (map[key] = { count: 0, names: [] });
      slot.count += 1;
      if (lv.employee && slot.names.length < 8) slot.names.push(lv.employee);
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

/* Tập ngày làm bù (date string) → nhãn. */
function buildWorkdays(workDays) {
  const set = new Map();
  for (const w of (workDays || [])) {
    if (w.date) set.set(w.date, w.name || 'Ngày làm bù');
  }
  return set;
}

function cellStyle(kind, big) {
  const base = {
    aspectRatio: '1', display: 'flex', alignItems: 'center', justifyContent: 'center',
    borderRadius: big ? 8 : 5, fontSize: big ? 14 : 11, fontWeight: 600,
    color: 'var(--ink)', position: 'relative',
  };
  if (!kind) return base;
  const k = DAY_KIND[kind];
  return {
    ...base, background: k.bg, color: k.fg, fontWeight: 700,
    boxShadow: kind === 'weekend' ? undefined : `inset 0 0 0 1.5px ${k.line}`,
  };
}

function MonthGrid({ year, month, load, mandatory, workdays, teaching, teacherView, big }) {
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
          const mdName = mandatory.get(key);
          // GV (xem lịch cá nhân): bỏ ngày làm bù văn phòng, thay bằng lịch dạy.
          const wdName = teacherView ? null : workdays.get(key);
          const teachCount = teacherView ? (teaching.get(key) || 0) : 0;
          const dow = (firstDow + d - 1) % 7;
          // Ưu tiên: nghỉ lễ > ngày làm bù > nghỉ cố định (T7/CN) > ngày thường.
          const kind = mdName ? 'holiday'
            : wdName ? 'workday'
              : (dow === 0 || dow === 6) ? 'weekend' : null;
          const st = cellStyle(kind, big);
          if (!kind && teachCount) st.background = 'var(--blue-bg)';
          const slot = load[key];
          const overloaded = slot && slot.count >= OVERLAP_WARN;
          if (overloaded) st.boxShadow = `inset 0 0 0 2px ${OVERLAP_CLR.line}`;
          return (
            <div key={key} style={st} title={[
              mdName && ('Nghỉ lễ: ' + mdName),
              wdName && ('Ngày làm bù: ' + wdName),
              !mdName && !wdName && (dow === 0 || dow === 6) && 'Nghỉ cố định',
              teachCount > 0 && (teachCount + ' buổi dạy'),
              overloaded && (`${slot.count} người nghỉ ngày này`
                + (slot.names.length ? ': ' + slot.names.join(', ') : '')),
            ].filter(Boolean).join(' · ')}>
              {d}
              {teachCount > 0 && (
                <span style={{ position: 'absolute', left: 2, top: 4, bottom: 4, width: 3, borderRadius: 2, background: 'var(--blue)' }}></span>
              )}
              {overloaded && (
                <span style={{ position: 'absolute', top: 2, left: 2, minWidth: 13, height: 13, padding: '0 3px', borderRadius: 7, background: OVERLAP_CLR.badgeBg, color: OVERLAP_CLR.badgeInk, fontSize: 9, fontWeight: 800, display: 'grid', placeItems: 'center', lineHeight: 1 }}>{slot.count}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CalendarPanel({ isOfficer, isTeacher, seeAll, year, onYearChange, dept, onDeptChange }) {
  const [month, setMonth] = useState(NOW.getMonth());
  const [mode, setMode] = useState('year');   // 'year' | 'month'
  const [teaching, setTeaching] = useState(new Map()); // ngày dạy → số buổi (GV)
  const { data, err, loading, reload } = useFetch(
    () => fetchCalendar(year, seeAll ? (dept || undefined) : undefined),
    [year, dept, seeAll], `timeoff:calendar:${year}:${seeAll ? dept : 'mine'}`);

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

  const load = useMemo(() => data ? buildLeaveLoad(data.leaves) : {}, [data]);
  const mandatory = useMemo(() => data ? buildMandatory(data.mandatoryDays) : new Map(), [data]);
  const workdays = useMemo(() => data ? buildWorkdays(data.workDays) : new Map(), [data]);
  const teachTotal = useMemo(() => [...teaching.values()].reduce((a, b) => a + b, 0), [teaching]);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton rows={8} />;

  const stepBack = () => mode === 'year' ? onYearChange(year - 1)
    : (month === 0 ? (setMonth(11), onYearChange(year - 1)) : setMonth((m) => m - 1));
  const stepFwd = () => mode === 'year' ? onYearChange(year + 1)
    : (month === 11 ? (setMonth(0), onYearChange(year + 1)) : setMonth((m) => m + 1));

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
            <button className="btn btn-ghost btn-sm" onClick={() => { onYearChange(NOW.getFullYear()); setMonth(NOW.getMonth()); }}>Hôm nay</button>
          </div>
          <div style={{ marginLeft: 'auto' }} className="seg">
            <button className={mode === 'year' ? 'active' : ''} onClick={() => setMode('year')}>Năm</button>
            <button className={mode === 'month' ? 'active' : ''} onClick={() => setMode('month')}>Tháng</button>
          </div>
        </div>

        {mode === 'year' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(230px,1fr))', gap: 12 }}>
            {Array.from({ length: 12 }, (_, m) => (
              <MonthGrid key={m} year={year} month={m} load={load} mandatory={mandatory} workdays={workdays} teaching={teaching} teacherView={teacherView} />
            ))}
          </div>
        ) : (
          <MonthGrid year={year} month={month} load={load} mandatory={mandatory} workdays={workdays} teaching={teaching} teacherView={teacherView} big />
        )}
      </div>

      {/* Cột phải: chọn phòng ban (HR) + lọc loại + legend + ngày bắt buộc */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {seeAll && (
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Phòng ban</div>
            <DeptSelect value={dept} onChange={onDeptChange} style={{ width: '100%' }}
              departments={data.allDepartments} />
          </div>
        )}

        <div className="card" style={{ padding: 14 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Chú thích</div>
          <LegendRow kind="weekend" />
          <LegendRow kind="holiday" />
          {!teacherView && <LegendRow kind="workday" />}
          {teacherView && (
            <LegendRow swatch={{ background: 'var(--blue-bg)', boxShadow: 'inset 3px 0 0 var(--blue)' }}
              label="Ngày có lịch dạy" />
          )}
          <LegendRow swatch={{ background: '#FEF3E2', boxShadow: `inset 0 0 0 2px ${OVERLAP_CLR.line}` }}
            label={`Trùng lịch (≥ ${OVERLAP_WARN} người nghỉ)`} />
          <div className="muted" style={{ fontSize: 12, marginTop: 6, lineHeight: 1.5 }}>
            Lịch chỉ hiển thị ngày nghỉ/làm của công ty. Chi tiết từng đơn nghỉ xem ở
            tab {isOfficer ? <><b>Đơn chờ duyệt</b> / <b>Đơn đã duyệt</b></> : <b>Đơn của tôi</b>}.
          </div>
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
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>Ngày làm bù</div>
            <div className="muted" style={{ fontSize: 12.5, marginBottom: workdays.size ? 10 : 0 }}>
              Chuẩn: Thứ 2 – Thứ 6. Các ngày Thứ 7 đi làm bù do HR thêm.
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
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Nghỉ lễ</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.mandatoryDays.map((m, i) => (
                <div key={i} style={{ fontSize: 12.5, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 3, background: 'var(--red-600)', flexShrink: 0, marginTop: 4 }}></span>
                  <div>
                  <div style={{ fontWeight: 600 }}>{m.name}</div>
                  <div className="muted mono" style={{ fontSize: 11.5 }}>
                    {fmtDate(m.from)}{m.to !== m.from ? ' → ' + fmtDate(m.to) : ''}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* `kind` = 1 trong 3 loại ngày (dùng đúng màu ô lịch); hoặc truyền swatch/label tay. */
function LegendRow({ kind, swatch, label }) {
  const k = kind ? DAY_KIND[kind] : null;
  const box = k
    ? { background: k.bg, boxShadow: kind === 'weekend' ? undefined : `inset 0 0 0 1.5px ${k.line}` }
    : (swatch || {});
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '4px 0', fontSize: 12.5 }}>
      <span style={{ width: 16, height: 16, borderRadius: 4, flexShrink: 0, position: 'relative', ...box }}></span>
      {k ? k.label : label}
    </div>
  );
}
