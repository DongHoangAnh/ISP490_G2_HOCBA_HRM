/* Dashboard — 5 tab theo quyền: Tổng quan / Tuyển dụng / Chấm công /
   Nghỉ phép / Lương. KPI + biểu đồ từ /api/dashboard/*; giữ widget chứng
   chỉ (F-009) ở tab Tổng quan.
   Spec: docs/superpowers/specs/SPEC_DASHBOARD_HR_OVERVIEW.md
   File [CHUNG] — sửa qua review. */
import { useState, useEffect } from 'react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, LabelList,
  XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend,
  AreaChart, Area, FunnelChart, Funnel,
} from 'recharts';
import {
  fetchDashboardStats, fetchDashboardRecruitment, fetchDashboardAttendance,
  fetchDashboardTimeoff, fetchDashboardPayroll,
} from '../../api/dashboard';
import { fetchCertAlerts } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState } from '../../components/states';
import { fmtDate, HB_CERT } from '../../utils/format';

const BLUE = '#3370ff';
/* Palette phân loại — thứ tự cố định, đã validate CVD (spec §màu).
   3 slot dưới 3:1 contrast → pie/donut luôn kèm nhãn trực tiếp. */
const CAT = ['#3370ff', '#1baf7a', '#eda100', '#008300',
  '#4a3aa7', '#e34948', '#e87ba4', '#eb6834'];
/* Ramp thứ tự (phễu, OT stacked) — sáng → đậm */
const RAMP = ['#86b6ef', '#5598e7', '#3987e5', '#256abf', '#184f95'];

const fmtVnd = (v) => (v >= 1e9 ? `${(v / 1e9).toFixed(1)} tỷ`
  : v >= 1e6 ? `${Math.round(v / 1e6)} tr` : Math.round(v).toLocaleString('vi'));

function ChartCard({ title, sub, children, style }) {
  return (
    <div className="card" style={style}>
      <div className="card-head">
        <h3>{title}</h3>
        {sub && <span className="sub">{sub}</span>}
      </div>
      <div style={{ padding: '12px 16px 16px' }}>{children}</div>
    </div>
  );
}

const NoData = () => <div className="empty">Chưa có dữ liệu.</div>;

function KpiRow({ items }) {
  return (
    <div className="stat-grid" style={{ gridTemplateColumns: `repeat(${items.length}, 1fr)` }}>
      {items.map(([lbl, val, sub]) => (
        <div className="stat" key={lbl}>
          <div style={{ fontSize: 13.5, fontWeight: 600, marginBottom: 14, minHeight: 34 }}>{lbl}</div>
          <div className="stat-val" style={{ fontSize: 38 }}>{val}</div>
          {sub && <div className="stat-trend" style={{ color: 'var(--muted)' }}>{sub}</div>}
        </div>
      ))}
    </div>
  );
}

/* Hook tải dữ liệu 1 tab — mỗi tab tự Loading/Error/Retry độc lập. */
function useTabData(fetcher) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const load = () => {
    setErr(null); setData(null);
    fetcher().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  return [data, err, load];
}

/* ══════════ Tab Tổng quan ══════════ */
function OverviewTab({ stats, certs, setView }) {
  const { kpi } = stats;
  const maxDep = Math.max(1, ...stats.byDepartment.map((d) => d.count));
  return (
    <>
      <KpiRow items={[
        ['Số nhân sự tính đến hiện tại', kpi.total],
        ['Onboard', kpi.onboard],
        ['Offboard', kpi.offboard],
        ['Độ tuổi trung bình', kpi.avgAge],
        ['Thâm niên trung bình', kpi.avgSeniority],
      ]} />

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16, marginBottom: 16 }}>
        <ChartCard title="Tỷ lệ nghỉ việc theo tháng" sub="% trên headcount cuối tháng">
          {stats.turnoverByMonth.every((r) => !r.count) ? <NoData /> : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={stats.turnoverByMonth} margin={{ top: 18, right: 24, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="label" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} unit="%" />
                <Tooltip formatter={(v, k) => (k === 'rate' ? [`${v}%`, 'Tỷ lệ nghỉ'] : [v, k])} />
                <Line type="monotone" dataKey="rate" stroke={BLUE} strokeWidth={2}
                  isAnimationActive={false} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Phân bổ theo phòng ban" sub={`${stats.byDepartment.length} phòng ban`}>
          {stats.byDepartment.length === 0 ? <NoData /> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 4 }}>
              {stats.byDepartment.map((d) => (
                <div key={d.dep}>
                  <div className="between" style={{ marginBottom: 5, fontSize: 12.5 }}>
                    <span style={{ fontWeight: 600 }}>{d.dep}</span>
                    <span className="muted mono">{d.count}</span>
                  </div>
                  <div className="bar"><span style={{ width: `${(d.count / maxDep) * 100}%`, background: BLUE }}></span></div>
                </div>
              ))}
            </div>
          )}
        </ChartCard>
      </div>

      <ChartCard title="Biến động nhân sự chính thức theo từng thời gian" style={{ marginBottom: 16 }}>
        {stats.officialByMonth.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={stats.officialByMonth} margin={{ top: 18, right: 24, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="label" fontSize={11} tickLine={false} />
              <YAxis fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} />
              <Tooltip formatter={(v) => [v, 'Số NV lên chính thức']} />
              <Line type="monotone" dataKey="count" stroke={BLUE} strokeWidth={2}
                isAnimationActive={false} dot={{ r: 3 }}
                label={{ position: 'top', fontSize: 11, fill: BLUE }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Số nhân sự theo độ tuổi" style={{ marginBottom: 16 }}>
        {stats.byAge.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stats.byAge} margin={{ top: 18, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="age" fontSize={11} tickLine={false} />
              <YAxis fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} />
              <Tooltip formatter={(v) => [v, 'Số nhân sự']} labelFormatter={(l) => `${l} tuổi`} />
              <Bar dataKey="count" fill={BLUE} radius={[3, 3, 0, 0]} maxBarSize={36}
                isAnimationActive={false}>
                <LabelList dataKey="count" position="top" fontSize={11} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Số nhân sự theo thâm niên" style={{ marginBottom: 16 }}>
        {stats.bySeniority.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={Math.max(160, stats.bySeniority.length * 48)}>
            <BarChart data={stats.bySeniority} layout="vertical"
              margin={{ top: 8, right: 32, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="years" fontSize={11} tickLine={false} width={34} />
              <Tooltip formatter={(v) => [v, 'Số nhân sự']} labelFormatter={(l) => `${l} năm`} />
              <Bar dataKey="count" fill={BLUE} radius={[0, 3, 3, 0]} maxBarSize={30}
                isAnimationActive={false}>
                <LabelList dataKey="count" position="right" fontSize={11} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {/* F-009: cảnh báo chứng chỉ sắp/đã hết hạn — chỉ HR mới có dữ liệu */}
      {certs && certs.isHr && certs.alerts.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-head">
            <h3>Chứng chỉ cần gia hạn</h3>
            <span className="sub">{certs.alerts.length} chứng chỉ sắp/đã hết hạn</span>
            <div className="actions">
              <Badge kind="red" dot>{certs.alerts.filter((a) => a.status === 'expired').length} hết hạn</Badge>
              <Badge kind="amber" dot>{certs.alerts.filter((a) => a.status === 'expiring').length} sắp hết</Badge>
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Nhân viên</th><th>Phòng ban</th><th>Kỹ năng</th><th>Cấp độ</th><th>Hết hạn</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {certs.alerts.map((a, i) => {
                  const [lbl, kind] = HB_CERT[a.status] || HB_CERT.none;
                  return (
                    <tr key={i} onClick={() => setView('employees')}>
                      <td>
                        <div className="cell-emp">
                          <Avatar emp={{ id: a.empId, name: a.empName, hasImg: a.hasImg }} size={32} />
                          <div>
                            <div className="nm">{a.empName}</div>
                            <div className="id">{a.empCode}</div>
                          </div>
                        </div>
                      </td>
                      <td className="muted">{a.dep}</td>
                      <td>{a.skill}</td>
                      <td className="muted">{a.level || '—'}</td>
                      <td className="mono">{fmtDate(a.expiry)}</td>
                      <td><Badge kind={kind} dot>{lbl}</Badge></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

/* ══════════ Tab Tuyển dụng ══════════ */
function RecruitmentTab() {
  const [data, err, retry] = useTabData(fetchDashboardRecruitment);
  if (err) return <ErrorState message={err} onRetry={retry} />;
  if (!data) return <LoadingState label="Đang tải số liệu tuyển dụng…" />;
  const openQty = data.openByDept.reduce((s, d) => s + d.qty, 0);
  const funnelHasData = data.funnel.length > 0 && data.funnel[0].count > 0;
  return (
    <>
      <KpiRow items={[
        ['Thời gian tuyển trung bình', `${data.timeToHire.avgDays} ngày`,
          `${data.timeToHire.hired} ứng viên đã nhận việc`],
        ['Tổng CV đã nhận', data.timeToHire.totalCv],
        ['Chỉ tiêu đang mở', openQty, `${data.openByDept.reduce((s, d) => s + d.requests, 0)} phiếu yêu cầu`],
      ]} />
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16, marginBottom: 16 }}>
        <ChartCard title="Phễu chuyển đổi ứng viên">
          {!funnelHasData ? <NoData /> : (
            <ResponsiveContainer width="100%" height={280}>
              <FunnelChart margin={{ top: 8, right: 120, left: 8, bottom: 8 }}>
                <Tooltip formatter={(v) => [v, 'Ứng viên']} />
                <Funnel dataKey="count" nameKey="stage" data={data.funnel} isAnimationActive={false}>
                  {data.funnel.map((f, i) => <Cell key={f.stage} fill={RAMP[i] || RAMP[RAMP.length - 1]} />)}
                  <LabelList dataKey="stage" position="right" fontSize={12} fill="var(--ink, #333)" stroke="none" />
                  <LabelList dataKey="count" position="center" fontSize={12} fill="#fff" stroke="none" />
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Nguồn ứng viên">
          {data.bySource.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={data.bySource} dataKey="count" nameKey="label"
                  isAnimationActive={false} innerRadius="52%" outerRadius="78%"
                  paddingAngle={1} labelLine fontSize={11}
                  label={({ label, count }) => `${label}: ${count}`}>
                  {data.bySource.map((s, i) => (
                    <Cell key={s.label} fill={CAT[i % CAT.length]} />
                  ))}
                </Pie>
                <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8} />
                <Tooltip formatter={(v) => [v, 'CV']} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
      <ChartCard title="Vị trí đang mở theo phòng ban" sub="phiếu yêu cầu đang tuyển" style={{ marginBottom: 16 }}>
        {data.openByDept.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={Math.max(160, data.openByDept.length * 48)}>
            <BarChart data={data.openByDept} layout="vertical"
              margin={{ top: 8, right: 32, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="dep" fontSize={11} tickLine={false} width={130} />
              <Tooltip formatter={(v, k) => [v, k === 'qty' ? 'Chỉ tiêu' : k]} />
              <Bar dataKey="qty" fill={BLUE} radius={[0, 3, 3, 0]} maxBarSize={26}
                isAnimationActive={false}>
                <LabelList dataKey="qty" position="right" fontSize={11} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </>
  );
}

/* ══════════ Tab Chấm công ══════════ */
function AttendanceTab() {
  const [data, err, retry] = useTabData(fetchDashboardAttendance);
  if (err) return <ErrorState message={err} onRetry={retry} />;
  if (!data) return <LoadingState label="Đang tải số liệu chấm công…" />;
  const hasRate = data.rateByMonth.some((r) => r.records > 0);
  const hasOt = data.otByMonth.some((r) => r.h100 + r.h150 + r.h300 > 0);
  return (
    <>
      <ChartCard title="Tỷ lệ đi muộn / về sớm theo tháng" sub="% trên số bản ghi chấm công" style={{ marginBottom: 16 }}>
        {!hasRate ? <NoData /> : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.rateByMonth} margin={{ top: 12, right: 24, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="label" fontSize={11} tickLine={false} />
              <YAxis fontSize={11} tickLine={false} axisLine={false} unit="%" />
              <Tooltip formatter={(v, k) => [`${v}%`, k === 'latePct' ? 'Đi muộn' : 'Về sớm']} />
              <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8}
                formatter={(v) => (v === 'latePct' ? 'Đi muộn' : 'Về sớm')} />
              <Line type="monotone" dataKey="latePct" stroke={CAT[0]} strokeWidth={2}
                isAnimationActive={false} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="earlyPct" stroke={CAT[1]} strokeWidth={2}
                isAnimationActive={false} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 16, marginBottom: 16 }}>
        <ChartCard title="Top đi muộn" sub="3 tháng gần nhất — số lần">
          {data.topLate.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={Math.max(160, data.topLate.length * 44)}>
              <BarChart data={data.topLate} layout="vertical"
                margin={{ top: 8, right: 32, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" fontSize={11} tickLine={false} width={120} />
                <Tooltip formatter={(v, k) => [v, k === 'count' ? 'Số lần muộn' : k]}
                  labelFormatter={(l, p) => `${l} · ${p?.[0]?.payload?.dep || ''} · ${p?.[0]?.payload?.minutes || 0} phút`} />
                <Bar dataKey="count" fill={BLUE} radius={[0, 3, 3, 0]} maxBarSize={24}
                  isAnimationActive={false}>
                  <LabelList dataKey="count" position="right" fontSize={11} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Tổng giờ làm thêm (OT) theo tháng" sub="chồng theo mức hệ số">
          {!hasOt ? <NoData /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.otByMonth} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="label" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} unit="h" />
                <Tooltip formatter={(v, k) => [`${v}h`, { h100: 'OT 100%', h150: 'OT 150%', h300: 'OT 300%' }[k] || k]} />
                <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8}
                  formatter={(v) => ({ h100: 'OT 100%', h150: 'OT 150%', h300: 'OT 300%' }[v] || v)} />
                <Bar dataKey="h100" stackId="ot" fill={RAMP[0]} isAnimationActive={false} maxBarSize={30} />
                <Bar dataKey="h150" stackId="ot" fill={RAMP[2]} isAnimationActive={false} maxBarSize={30} />
                <Bar dataKey="h300" stackId="ot" fill={RAMP[4]} radius={[3, 3, 0, 0]} isAnimationActive={false} maxBarSize={30} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </>
  );
}

/* ══════════ Tab Nghỉ phép ══════════ */
function TimeoffTab() {
  const [data, err, retry] = useTabData(fetchDashboardTimeoff);
  if (err) return <ErrorState message={err} onRetry={retry} />;
  if (!data) return <LoadingState label="Đang tải số liệu nghỉ phép…" />;
  const hasTrend = data.byMonth.some((r) => r.days > 0);
  return (
    <>
      <KpiRow items={[
        ['Quỹ phép tồn toàn công ty', `${data.remaining} ngày`, 'phép đã cấp − đã nghỉ (duyệt)'],
        ['Ngày nghỉ đã duyệt', `${data.takenDays} ngày`, '12 tháng gần nhất'],
      ]} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 16, marginBottom: 16 }}>
        <ChartCard title="Phân loại lý do nghỉ phép" sub="theo số ngày, 12 tháng">
          {data.byType.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={data.byType} dataKey="days" nameKey="label"
                  isAnimationActive={false} outerRadius="78%" labelLine fontSize={11}
                  label={({ label, days }) => `${label}: ${days}`}>
                  {data.byType.map((t, i) => (
                    <Cell key={t.label} fill={CAT[i % CAT.length]} />
                  ))}
                </Pie>
                <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8} />
                <Tooltip formatter={(v) => [`${v} ngày`, 'Đã nghỉ']} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Xu hướng nghỉ phép theo tháng" sub="tổng số ngày nghỉ đã duyệt">
          {!hasTrend ? <NoData /> : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={data.byMonth} margin={{ top: 12, right: 24, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="label" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => [`${v} ngày`, 'Đã nghỉ']} />
                <Area type="monotone" dataKey="days" stroke={BLUE} strokeWidth={2}
                  fill={BLUE} fillOpacity={0.14} isAnimationActive={false} dot={{ r: 2.5 }} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </>
  );
}

/* ══════════ Tab Lương ══════════ */
function PayrollTab() {
  const [data, err, retry] = useTabData(fetchDashboardPayroll);
  if (err) return <ErrorState message={err} onRetry={retry} />;
  if (!data) return <LoadingState label="Đang tải số liệu lương…" />;
  const hasFund = data.fundByMonth.some((r) => r.net > 0 || r.gross > 0);
  return (
    <>
      <ChartCard title="Tổng quỹ lương theo tháng" sub="net thực lĩnh & gross" style={{ marginBottom: 16 }}>
        {!hasFund ? <NoData /> : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.fundByMonth} margin={{ top: 12, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="label" fontSize={11} tickLine={false} />
              <YAxis fontSize={11} tickLine={false} axisLine={false} tickFormatter={fmtVnd} width={64} />
              <Tooltip formatter={(v, k) => [fmtVnd(v), k === 'net' ? 'Net' : 'Gross']} />
              <Legend verticalAlign="top" align="left" iconType="circle" iconSize={8}
                formatter={(v) => (v === 'net' ? 'Net (thực lĩnh)' : 'Gross')} />
              <Line type="monotone" dataKey="gross" stroke={RAMP[1]} strokeWidth={2}
                isAnimationActive={false} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="net" stroke={RAMP[4]} strokeWidth={2}
                isAnimationActive={false} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <ChartCard title="Chi phí nhân sự theo phòng ban"
          sub={data.byDeptPeriod ? `kỳ lương ${data.byDeptPeriod} · net` : 'net'}>
          {data.byDept.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={Math.max(160, data.byDept.length * 48)}>
              <BarChart data={data.byDept} layout="vertical"
                margin={{ top: 8, right: 56, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" fontSize={11} tickLine={false} axisLine={false} tickFormatter={fmtVnd} />
                <YAxis type="category" dataKey="dep" fontSize={11} tickLine={false} width={120} />
                <Tooltip formatter={(v) => [fmtVnd(v), 'Chi phí net']} />
                <Bar dataKey="net" fill={BLUE} radius={[0, 3, 3, 0]} maxBarSize={26}
                  isAnimationActive={false}>
                  <LabelList dataKey="net" position="right" fontSize={11} formatter={fmtVnd} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Mức lương trung bình theo phân cấp" sub="wage hợp đồng hiện tại">
          {data.avgByLevel.length === 0 ? <NoData /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.avgByLevel} margin={{ top: 20, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="label" fontSize={11} tickLine={false} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} tickFormatter={fmtVnd} width={64} />
                <Tooltip formatter={(v, k, p) => [fmtVnd(v), `Lương TB (${p?.payload?.count || 0} NV)`]} />
                <Bar dataKey="avg" fill={BLUE} radius={[3, 3, 0, 0]} maxBarSize={48}
                  isAnimationActive={false}>
                  <LabelList dataKey="avg" position="top" fontSize={11} formatter={fmtVnd} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </>
  );
}

/* ══════════ Trang Dashboard ══════════ */
export default function Dashboard({ setView }) {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState(null);
  const [certs, setCerts] = useState(null);
  const [tab, setTab] = useState('overview');

  const load = () => {
    setErr(null); setStats(null);
    fetchDashboardStats().then(setStats).catch((e) => setErr(e.message));
    // cert-alerts độc lập: lỗi/không phải HR thì chỉ ẩn widget, không chặn dashboard
    fetchCertAlerts().then(setCerts).catch(() => setCerts({ isHr: false, alerts: [] }));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!stats) return <LoadingState label="Đang tải tổng quan nhân sự…" />;

  const TABS = [
    ['overview', 'Tổng quan', true],
    ['recruitment', 'Tuyển dụng', stats.tabs?.recruitment],
    ['attendance', 'Chấm công', stats.tabs?.attendance],
    ['timeoff', 'Nghỉ phép', stats.tabs?.timeoff],
    ['payroll', 'Lương thưởng', stats.tabs?.payroll],
  ].filter(([, , show]) => show);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tổng quan tình hình nhân sự</h1>
          <p>Học Bá Education · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={() => setView('employees')}>
            <Icon name="users" size={16} />Xem nhân viên</button>
        </div>
      </div>

      {TABS.length > 1 && (
        <div className="tabs">
          {TABS.map(([id, label]) => (
            <button key={id} className={`tab${tab === id ? ' active' : ''}`}
              onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>
      )}

      {tab === 'overview' && <OverviewTab stats={stats} certs={certs} setView={setView} />}
      {tab === 'recruitment' && <RecruitmentTab />}
      {tab === 'attendance' && <AttendanceTab />}
      {tab === 'timeoff' && <TimeoffTab />}
      {tab === 'payroll' && <PayrollTab />}
    </div>
  );
}
