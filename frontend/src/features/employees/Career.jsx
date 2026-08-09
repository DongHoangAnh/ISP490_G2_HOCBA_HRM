/* ============================================================
   Dashboard sự nghiệp — MỘT màn duy nhất: bảng vinh danh toàn công ty
   + toàn bộ lộ trình của từng người.
   Khách (họp 2026-08-07, 09:06): "phải có đầy đủ thông tin, cả nhận xét…
   chứ không phải là theo kiểu phải click nhiều"; (09:37) "dashboard thống
   kê cho từng người… như xem lại một album của đời".
   Trang riêng chứ KHÔNG phải popup — chính là thứ khách bảo bỏ.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area,
  BarChart, Bar, Cell, LabelList, PieChart, Pie, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from 'recharts';
import { fetchCareer } from '../../api/career';
import { fetchEmployees } from '../../api/employees';
import HonorBoard from '../../components/HonorBoard';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind } from '../../utils/format';

const BLUE = '#3370ff';
const GREEN = '#1baf7a';
const AMBER = '#eda100';
const RED = '#e34948';
const GRAY = '#94a3b8';

const SEL = {
  padding: '6px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', fontFamily: 'inherit',
  minWidth: 240,
};

/* Bộ lọc dòng thời gian — lọc client-side, dữ liệu đã về hết trong 1 lượt. */
const KIND_FILTERS = [
  ['all', 'Tất cả'],
  ['promotion', 'Thăng tiến'],
  ['evaluation', 'Đánh giá'],
  ['onboarding', 'Thử việc'],
  ['honor', 'Vinh danh'],
];

const KIND_ICON = {
  join: 'user', promotion: 'arrowUp', evaluation: 'star',
  onboarding: 'checkCircle', honor: 'award',
};

const INSIGHT_STYLE = {
  up: { icon: 'arrowUp', color: GREEN },
  down: { icon: 'arrowDown', color: RED },
  warn: { icon: 'alertTriangle', color: AMBER },
  info: { icon: 'info', color: BLUE },
};

const ONB_COLORS = { done: GREEN, skipped: GRAY, open: AMBER, waiting: BLUE };
const ONB_LABELS = {
  done: 'Hoàn thành', skipped: 'Bỏ qua', open: 'Đang chờ', waiting: 'Chưa tới lượt',
};

export default function Career({ canManage, focusEmpId, onBack }) {
  const [empId, setEmpId] = useState(focusEmpId || 0);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [people, setPeople] = useState([]);
  const [kind, setKind] = useState('all');

  useEffect(() => {
    if (focusEmpId) setEmpId(focusEmpId);
  }, [focusEmpId]);

  // Tài khoản vai trò quản lý (HR/Admin/Giáo vụ) KHÔNG gắn hồ sơ nhân viên
  // (tách tài khoản quản lý ↔ cá nhân, họp #2) → mở trang mà tự nạp "chính
  // mình" là chắc chắn lỗi. Với họ, mặc định là chờ chọn người.
  const needPick = canManage && !empId;

  const load = () => {
    setErr(null); setData(null);
    if (needPick) return;
    fetchCareer(empId).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [empId]);

  useEffect(() => {
    if (!canManage) return;
    fetchEmployees().then((d) => setPeople(d.employees || [])).catch(() => {});
  }, [canManage]);

  // Header (gồm ô chọn NV) luôn render: nếu lỗi mà nuốt mất ô chọn thì trang
  // thành ngõ cụt — không còn cách nào chọn người khác để thoát lỗi.
  const head = (
    <div className="page-head">
      <div>
        <h1>Dashboard sự nghiệp</h1>
        <p>Vinh danh toàn công ty · thăng tiến, đánh giá và nhận xét của từng người</p>
      </div>
      <div className="actions" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {canManage && (
          <select style={SEL} value={empId}
            onChange={(ev) => setEmpId(Number(ev.target.value))}>
            <option value={0}>— Chọn nhân viên —</option>
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code ? `${p.code} · ` : ''}{p.name}
              </option>
            ))}
          </select>
        )}
        {onBack && (
          <button className="btn btn-ghost" onClick={onBack}>
            <Icon name="users" size={16} />Danh sách nhân viên</button>
        )}
      </div>
    </div>
  );

  // Bảng vinh danh là dữ liệu CHUNG, không phụ thuộc người đang chọn → hiện
  // ngay cả khi chưa chọn ai hoặc phần lộ trình lỗi.
  const body = () => {
    if (needPick) {
      return (
        <div className="card" style={{ padding: 36 }}>
          <EmptyState>Chọn một nhân viên ở trên để xem toàn bộ lộ trình.</EmptyState>
        </div>
      );
    }
    if (err) return <ErrorState message={err} onRetry={load} />;
    if (!data) return <LoadingState label="Đang dựng lộ trình sự nghiệp…" />;
    return <CareerBody data={data} kind={kind} setKind={setKind} />;
  };

  return (
    <div className="content fade-in">
      {head}
      <HonorBoard />
      {body()}
    </div>
  );
}

function CareerBody({ data, kind, setKind }) {
  const e = data.employee;
  const st = data.stats;
  const rows = kind === 'all'
    ? data.timeline
    : data.timeline.filter((t) => t.kind === kind);
  const count = (k) => data.timeline.filter((t) => t.kind === k).length;

  // Radar: chuẩn hoá về % để các tiêu chí khác thang điểm so được với nhau.
  const radar = data.criteriaRadar.map((c) => ({
    crit: c.name,
    hienTai: c.maxScore ? Math.round((c.score / c.maxScore) * 100) : 0,
    truoc: c.previous != null && c.maxScore
      ? Math.round((c.previous / c.maxScore) * 100) : null,
  }));
  const hasPrev = radar.some((r) => r.truoc != null);
  const delta = data.criteriaRadar
    .filter((c) => c.previous != null && c.maxScore)
    .map((c) => ({ crit: c.name, delta: Math.round(c.score - c.previous) }))
    .sort((a, b) => b.delta - a.delta);

  const onb = data.onboardingProgress;
  const onbPie = ['done', 'open', 'waiting', 'skipped']
    .filter((k) => onb[k] > 0)
    .map((k) => ({ key: k, label: ONB_LABELS[k], value: onb[k] }));

  return (
    <>
      {/* Thẻ nhân sự + KPI gộp một khối cho gọn */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 16 }}>
        <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
          <Avatar emp={{ id: e.id, name: e.name, hasImg: e.hasImg }} size={56} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.4px' }}>{e.name}</h2>
              <Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge>
            </div>
            <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
              {e.code} · {e.jobTitle} · {e.depName} · vào làm {e.start ? fmtDate(e.start) : '—'}
            </div>
          </div>
        </div>
        <div className="stat-grid" style={{
          gridTemplateColumns: 'repeat(6, 1fr)', margin: 0, borderTop: '1px solid var(--border)',
        }}>
          <Stat label="Thâm niên" value={st.tenureMonths ?? '—'} unit="tháng" />
          <Stat label="Lần thăng chức" value={st.promoCount} />
          <Stat label="Từ lần thăng tiến" value={st.monthsSincePromo ?? '—'} unit="tháng" />
          <Stat label="Đợt đánh giá" value={st.evalCount} />
          <Stat label="Điểm gần nhất"
            value={st.lastScore != null ? `${st.lastScore}%` : '—'}
            sub={st.avgScore != null ? `TB ${st.avgScore}%` : null} />
          <Stat label="Được vinh danh" value={st.honorCount} />
        </div>
      </div>

      {/* Insight — đọc là hiểu, không phải tự suy từ biểu đồ */}
      {data.insights.length > 0 && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          {data.insights.map((ins, i) => {
            const s = INSIGHT_STYLE[ins.kind] || INSIGHT_STYLE.info;
            return (
              <div key={i} style={{
                flex: '1 1 240px', minWidth: 220, background: '#fff',
                border: '1px solid var(--border)', borderLeft: `3px solid ${s.color}`,
                borderRadius: 10, padding: '10px 13px',
                display: 'flex', gap: 9, alignItems: 'flex-start',
              }}>
                <span style={{ color: s.color, flexShrink: 0, marginTop: 1 }}>
                  <Icon name={s.icon} size={15} />
                </span>
                <span style={{ fontSize: 12.5, lineHeight: 1.45 }}>{ins.text}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Biểu đồ */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: 16, marginBottom: 16,
      }}>
        <ChartCard title="Năng lực theo tiêu chí"
          sub={hasPrev ? 'đợt gần nhất so với đợt trước (%)' : 'đợt đánh giá gần nhất (%)'}>
          {radar.length < 3 ? (
            <NoData hint={radar.length ? 'Cần từ 3 tiêu chí trở lên để vẽ radar.' : null} />
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radar} outerRadius="72%">
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="crit" fontSize={10.5} />
                <PolarRadiusAxis domain={[0, 100]} fontSize={9} angle={90} />
                {hasPrev && (
                  <Radar name="Đợt trước" dataKey="truoc" stroke={GRAY}
                    fill={GRAY} fillOpacity={0.15} isAnimationActive={false} />
                )}
                <Radar name="Đợt này" dataKey="hienTai" stroke={BLUE}
                  fill={BLUE} fillOpacity={0.32} isAnimationActive={false} />
                <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8} />
                <Tooltip formatter={(v) => [`${v}%`, '']} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Xu hướng điểm đánh giá" sub="tổng điểm % qua từng đợt">
          {data.scoreTrend.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data.scoreTrend} margin={{ top: 16, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} unit="%" domain={[0, 100]} />
                <Tooltip formatter={(v) => [`${v}%`, 'Tổng điểm']} />
                {/* 80% = ngưỡng "Đủ điều kiện" mặc định của bộ tiêu chí */}
                <ReferenceLine y={80} stroke={GREEN} strokeDasharray="4 4"
                  label={{ value: 'Đủ điều kiện', position: 'right', fontSize: 10, fill: GREEN }} />
                <Line type="monotone" dataKey="score" stroke={BLUE} strokeWidth={2}
                  isAnimationActive={false} dot={{ r: 3.5 }}
                  label={{ position: 'top', fontSize: 10.5, fill: BLUE }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {delta.length > 0 && (
          <ChartCard title="Tiến bộ từng tiêu chí" sub="chênh lệch điểm so với đợt trước">
            <ResponsiveContainer width="100%" height={Math.max(180, delta.length * 40)}>
              <BarChart data={delta} layout="vertical"
                margin={{ top: 8, right: 30, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="crit" fontSize={11} tickLine={false} width={130} />
                <Tooltip formatter={(v) => [v > 0 ? `+${v}` : v, 'Chênh lệch']} />
                <ReferenceLine x={0} stroke="var(--border-strong)" />
                <Bar dataKey="delta" maxBarSize={22} isAnimationActive={false}>
                  {delta.map((d, i) => (
                    <Cell key={i} fill={d.delta >= 0 ? GREEN : RED} />
                  ))}
                  <LabelList dataKey="delta" position="right" fontSize={11}
                    formatter={(v) => (v > 0 ? `+${v}` : v)} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {onbPie.length > 0 && (
          <ChartCard title="Tiến độ quy trình nhận việc"
            sub={`${onb.done + onb.skipped}/${onb.total} bước đã xong`}>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={onbPie} dataKey="value" nameKey="label"
                  innerRadius="52%" outerRadius="78%" paddingAngle={2}
                  isAnimationActive={false} labelLine fontSize={11}
                  label={({ label, value }) => `${label}: ${value}`}>
                  {onbPie.map((s) => <Cell key={s.key} fill={ONB_COLORS[s.key]} />)}
                </Pie>
                <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8} />
                <Tooltip formatter={(v) => [`${v} bước`, '']} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {data.canSeeSalary && (
          <ChartCard title="Lộ trình lương" sub="mức lương sau từng mốc">
            {data.salaryJourney.length === 0 ? <NoData /> : (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={data.salaryJourney} margin={{ top: 16, right: 20, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="date" fontSize={11} tickLine={false} />
                  <YAxis fontSize={11} tickLine={false} axisLine={false}
                    tickFormatter={(v) => hbVND(v)} width={72} />
                  <Tooltip formatter={(v, k, p) => [`${hbVND(v)} ₫`, p?.payload?.label || 'Lương']} />
                  <Area type="stepAfter" dataKey="wage" stroke={BLUE} strokeWidth={2}
                    fill={BLUE} fillOpacity={0.14} isAnimationActive={false} dot={{ r: 3 }} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        )}
      </div>

      {/* Dòng thời gian — mở sẵn, không phải bấm để xem chi tiết */}
      <div className="card">
        <div className="card-head">
          <h3>Bảng lịch sử</h3>
          <span className="sub">{rows.length} mốc</span>
          <div className="actions" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {KIND_FILTERS.map(([id, label]) => {
              const n = id === 'all' ? data.timeline.length : count(id);
              if (id !== 'all' && n === 0) return null;
              return (
                <button key={id}
                  className={'btn btn-sm ' + (kind === id ? 'btn-primary' : 'btn-ghost')}
                  onClick={() => setKind(id)}>{label} ({n})</button>
              );
            })}
          </div>
        </div>
        <div style={{ padding: '16px 20px 20px' }}>
          {rows.length === 0 ? (
            <EmptyState>Chưa có mốc nào trong nhóm này.</EmptyState>
          ) : (
            <Timeline rows={rows} canSeeSalary={data.canSeeSalary} />
          )}
        </div>
      </div>
    </>
  );
}

function Stat({ label, value, unit, sub }) {
  return (
    <div className="stat">
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, minHeight: 28 }}>{label}</div>
      <div className="stat-val" style={{ fontSize: 27 }}>
        {value}
        {/* "— tháng" là vô nghĩa: chỉ gắn đơn vị khi thực sự có số. */}
        {unit && value !== '—' && (
          <span style={{ fontSize: 12, fontWeight: 600, marginLeft: 4 }} className="muted">{unit}</span>
        )}
      </div>
      {sub && <div className="faint" style={{ fontSize: 11, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function ChartCard({ title, sub, children }) {
  return (
    <div className="card" style={{ margin: 0 }}>
      <div className="card-head">
        <h3>{title}</h3>
        {sub && <span className="sub">{sub}</span>}
      </div>
      <div style={{ padding: '12px 16px 16px' }}>{children}</div>
    </div>
  );
}

const NoData = ({ hint }) => <div className="empty">{hint || 'Chưa có dữ liệu.'}</div>;

function Timeline({ rows, canSeeSalary }) {
  return (
    <div>
      {rows.map((t, i) => {
        const last = i === rows.length - 1;
        const delta = canSeeSalary && t.toWage > t.fromWage
          ? t.toWage - t.fromWage : 0;
        return (
          <div key={i} style={{ display: 'flex', gap: 14, paddingBottom: last ? 0 : 16, position: 'relative' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                background: t.kind === 'honor' ? 'var(--gold-100, #fdf3d7)' : 'var(--red-50)',
                color: t.kind === 'honor' ? 'var(--gold-600, #a8760a)' : 'var(--red-600)',
                display: 'grid', placeItems: 'center', zIndex: 1,
                border: '2px solid #fff',
              }}>
                <Icon name={KIND_ICON[t.kind] || 'file'} size={14} />
              </div>
              {!last && <div style={{ width: 2, flex: 1, background: 'var(--border-strong)', marginTop: 2 }}></div>}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="between" style={{ gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13 }}>{t.title}</span>
                  {t.badge && <Badge kind={t.badgeKind || 'gray'}>{t.badge}</Badge>}
                  {t.dep && <Badge kind="gray">{t.dep}</Badge>}
                  {canSeeSalary && t.toWage > 0 && (
                    <span className="mono" style={{ fontWeight: 700, fontSize: 12.5, color: 'var(--green)' }}>
                      {hbVND(t.toWage)} ₫
                    </span>
                  )}
                  {delta > 0 && (
                    <span className="badge badge-gold">
                      <Icon name="arrowUp" size={11} />+{hbVND(delta)}</span>
                  )}
                </div>
                <span className="mono muted" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                  {t.date ? fmtDate(t.date) : '—'}</span>
              </div>
              {t.detail && (
                <div className="muted" style={{ fontSize: 12.5, marginTop: 4, whiteSpace: 'pre-wrap' }}>
                  {t.detail}
                </div>
              )}
              {/* Điểm từng tiêu chí dạng chip — dày đặc mà vẫn không phải bấm.
                  Phân tích sâu đã có ở radar + biểu đồ chênh lệch phía trên. */}
              {t.lines?.length > 0 && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                  {t.lines.map((l, j) => (
                    <span key={j} title={l.note || ''} style={{
                      fontSize: 11.5, padding: '3px 8px', borderRadius: 6,
                      background: 'var(--red-50)', border: '1px solid var(--border)',
                    }}>
                      {l.name}: <b className="mono">{l.score}/{l.maxScore}</b>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
