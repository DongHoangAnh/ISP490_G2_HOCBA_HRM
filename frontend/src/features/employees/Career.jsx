/* ============================================================
   Trang "Lộ trình sự nghiệp" — dashboard lịch sử cho TỪNG nhân viên.
   Khách (họp 2026-08-07, 09:06): "phải có đầy đủ thông tin, cả nhận xét…
   chứ không phải là theo kiểu phải click nhiều… giống như kiểu một cái
   bảng lịch sử"; (09:37) "dashboard thống kê cho từng người".
   Trang riêng chứ KHÔNG phải popup — chính là thứ khách bảo bỏ.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';
import { fetchCareer } from '../../api/career';
import { fetchEmployees } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind } from '../../utils/format';

const BLUE = '#3370ff';

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
    if (needPick) { setErr(null); setData(null); return; }
    setErr(null); setData(null);
    fetchCareer(empId).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [empId]);

  // Ô chọn nhân viên chỉ dành cho vai trò quản lý; danh sách đã lọc theo
  // phạm vi ở BE (HR = tất cả, trưởng phòng = phòng mình, giáo vụ = GV).
  useEffect(() => {
    if (!canManage) return;
    fetchEmployees().then((d) => setPeople(d.employees || [])).catch(() => {});
  }, [canManage]);

  const e = data?.employee;
  const st = data?.stats;
  const rows = !data ? [] : kind === 'all'
    ? data.timeline
    : data.timeline.filter((t) => t.kind === kind);

  const count = (k) => data.timeline.filter((t) => t.kind === k).length;

  // Header (gồm ô chọn NV) luôn render: nếu lỗi mà nuốt mất ô chọn thì trang
  // thành ngõ cụt — không còn cách nào chọn người khác để thoát lỗi.
  const head = (
    <div className="page-head">
      <div>
        <h1>{data?.isSelf ? 'Lộ trình của tôi' : 'Lộ trình sự nghiệp'}</h1>
        <p>Toàn bộ thăng tiến, đánh giá và nhận xét từ ngày vào làm</p>
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

  if (needPick) {
    return (
      <div className="content fade-in">
        {head}
        <div className="card" style={{ padding: 36 }}>
          <EmptyState>Chọn một nhân viên ở trên để xem toàn bộ lộ trình.</EmptyState>
        </div>
      </div>
    );
  }
  if (err) {
    return <div className="content fade-in">{head}
      <ErrorState message={err} onRetry={load} /></div>;
  }
  if (!data) {
    return <div className="content fade-in">{head}
      <LoadingState label="Đang dựng lộ trình sự nghiệp…" /></div>;
  }

  return (
    <div className="content fade-in">
      {head}

      {/* Thẻ nhân sự */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 16 }}>
        <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
          <Avatar emp={{ id: e.id, name: e.name, hasImg: e.hasImg }} size={62} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{e.name}</h2>
              <Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge>
            </div>
            <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>
              {e.code} · {e.jobTitle} · {e.depName}
            </div>
            <div className="faint" style={{ fontSize: 12.5, marginTop: 6 }}>
              Vào làm: {e.start ? fmtDate(e.start) : '—'}
            </div>
          </div>
        </div>
      </div>

      {/* KPI — "thống kê cho từng người" */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
        <Stat label="Thâm niên (tháng)" value={st.tenureMonths ?? '—'} />
        <Stat label="Từ lần thăng tiến" value={st.monthsSincePromo ?? '—'} />
        <Stat label="Lần thăng chức" value={st.promoCount} />
        <Stat label="Đợt đánh giá" value={st.evalCount} />
        <Stat label="Điểm trung bình" value={st.avgScore != null ? `${st.avgScore}%` : '—'} />
        <Stat label="Được vinh danh" value={st.honorCount} />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: data.canSeeSalary ? '1fr 1fr' : '1fr',
        gap: 16, marginBottom: 16,
      }}>
        {data.canSeeSalary && (
          <ChartCard title="Lộ trình lương" sub="theo từng mốc có mức lương mới">
            {data.salaryJourney.length === 0 ? <NoData /> : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data.salaryJourney} margin={{ top: 14, right: 20, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="date" fontSize={11} tickLine={false} />
                  <YAxis fontSize={11} tickLine={false} axisLine={false}
                    tickFormatter={(v) => hbVND(v)} width={70} />
                  <Tooltip formatter={(v, k, p) => [`${hbVND(v)} ₫`, p?.payload?.label || 'Lương']} />
                  <Line type="stepAfter" dataKey="wage" stroke={BLUE} strokeWidth={2}
                    isAnimationActive={false} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        )}
        <ChartCard title="Xu hướng điểm đánh giá" sub="% theo từng đợt">
          {data.scoreTrend.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.scoreTrend} margin={{ top: 14, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} unit="%" domain={[0, 100]} />
                <Tooltip formatter={(v) => [`${v}%`, 'Tổng điểm']} />
                <Line type="monotone" dataKey="score" stroke={BLUE} strokeWidth={2}
                  isAnimationActive={false} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
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
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 10, minHeight: 30 }}>{label}</div>
      <div className="stat-val" style={{ fontSize: 30 }}>{value}</div>
    </div>
  );
}

function ChartCard({ title, sub, children }) {
  return (
    <div className="card">
      <div className="card-head">
        <h3>{title}</h3>
        {sub && <span className="sub">{sub}</span>}
      </div>
      <div style={{ padding: '12px 16px 16px' }}>{children}</div>
    </div>
  );
}

const NoData = () => <div className="empty">Chưa có dữ liệu.</div>;

function Timeline({ rows, canSeeSalary }) {
  return (
    <div>
      {rows.map((t, i) => {
        const last = i === rows.length - 1;
        const delta = canSeeSalary && t.toWage > t.fromWage
          ? t.toWage - t.fromWage : 0;
        return (
          <div key={i} style={{ display: 'flex', gap: 16, paddingBottom: last ? 0 : 20, position: 'relative' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
                background: t.kind === 'honor' ? 'var(--gold-100, #fdf3d7)' : 'var(--red-50)',
                color: t.kind === 'honor' ? 'var(--gold-600, #a8760a)' : 'var(--red-600)',
                display: 'grid', placeItems: 'center', zIndex: 1,
                border: '2px solid #fff',
              }}>
                <Icon name={KIND_ICON[t.kind] || 'file'} size={15} />
              </div>
              {!last && <div style={{ width: 2, flex: 1, background: 'var(--border-strong)', marginTop: 2 }}></div>}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="between" style={{ gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{t.title}</span>
                  {t.badge && <Badge kind={t.badgeKind || 'gray'}>{t.badge}</Badge>}
                  {t.dep && <Badge kind="gray">{t.dep}</Badge>}
                  {delta > 0 && (
                    <span className="badge badge-gold">
                      <Icon name="arrowUp" size={11} />+{hbVND(delta)}</span>
                  )}
                </div>
                <span className="mono muted" style={{ fontSize: 12.5, whiteSpace: 'nowrap' }}>
                  {t.date ? fmtDate(t.date) : '—'}</span>
              </div>
              {canSeeSalary && t.toWage > 0 && (
                <div className="mono" style={{ fontWeight: 800, fontSize: 13.5, color: 'var(--green)', marginTop: 4 }}>
                  {hbVND(t.toWage)} ₫
                </div>
              )}
              {t.detail && (
                <div className="muted" style={{ fontSize: 12.5, marginTop: 5, whiteSpace: 'pre-wrap' }}>
                  {t.detail}
                </div>
              )}
              {/* Bảng điểm hiện luôn — khách: "không phải là theo kiểu phải click nhiều" */}
              {t.lines?.length > 0 && (
                <div className="card" style={{ padding: 0, marginTop: 8 }}>
                  <table className="tbl">
                    <thead><tr><th>Tiêu chí</th><th style={{ width: 90 }}>Điểm</th><th style={{ width: 80 }}>Trọng số</th><th>Ghi chú</th></tr></thead>
                    <tbody>
                      {t.lines.map((l, j) => (
                        <tr key={j} style={{ cursor: 'default' }}>
                          <td>{l.name}</td>
                          <td className="mono">{l.score}/{l.maxScore}</td>
                          <td className="mono muted">{l.weight}</td>
                          <td className="muted">{l.note || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
