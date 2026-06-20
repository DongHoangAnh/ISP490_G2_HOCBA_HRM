/* Tab "Tổng hợp" — BÁO CÁO CÁ NHÂN của nhân viên đang đăng nhập.
   Chỉ hiển thị cho role Nhân viên (xem TimeOff.jsx). Thống kê nghỉ phép
   của chính mình trong năm: quỹ phép năm, KPI, theo loại nghỉ, theo tháng,
   và danh sách đơn. Owner: Nhật Anh. Spec §3.8 (đã đổi sang báo cáo cá nhân). */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchSummary } from '../../api/timeoff';

const THIS_YEAR = new Date().getFullYear();
const MONTHS = ['Th1', 'Th2', 'Th3', 'Th4', 'Th5', 'Th6',
                'Th7', 'Th8', 'Th9', 'Th10', 'Th11', 'Th12'];

export default function SummaryPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchSummary(year).then(setData).catch((e) => setErr(e.message));
  }, [year, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải báo cáo nghỉ phép…" />;

  const nav = (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button className="icon-btn" onClick={() => setYear((y) => y - 1)}>
        <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
      <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
      <button className="icon-btn" onClick={() => setYear((y) => y + 1)}><Icon name="chevR" size={16} /></button>
      <button className="btn btn-ghost btn-sm" onClick={() => setYear(THIS_YEAR)}>Năm nay</button>
    </div>
  );

  if (data.empMissing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="filterbar">{nav}</div>
        <EmptyState>Tài khoản chưa gắn hồ sơ nhân viên — chưa có dữ liệu báo cáo.</EmptyState>
      </div>
    );
  }

  const k = data.kpi;
  const a = data.annual;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Thanh điều khiển + danh tính */}
      <div className="filterbar">
        {nav}
        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 13.5 }}>{data.employee.name}</div>
          <div className="muted" style={{ fontSize: 12 }}>{data.employee.department}</div>
        </div>
      </div>

      {/* Quỹ phép năm nổi bật */}
      {a && (
        <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="between">
            <span style={{ fontWeight: 700, fontSize: 14, display: 'inline-flex', gap: 8, alignItems: 'center' }}>
              <span style={{ width: 10, height: 10, borderRadius: 3, background: a.color }}></span>{a.name}
            </span>
            {a.low && <Badge kind="amber">Sắp hết phép</Badge>}
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 34, fontWeight: 800, color: a.low ? 'var(--amber)' : 'var(--ink)' }}>{a.remaining}</span>
            <span className="muted" style={{ fontSize: 13.5 }}>/ {a.allocated} ngày phép còn lại · đã dùng {a.taken}</span>
          </div>
          <div className="bar"><span style={{ width: a.pct + '%', background: a.low ? 'var(--amber)' : a.color }}></span></div>
        </div>
      )}

      {/* KPI */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))' }}>
        <Kpi label="Tổng ngày đã nghỉ" value={k.approvedDays} sub="đã duyệt trong năm" />
        <Kpi label="Ngày nghỉ có lương" value={k.paidDays} color="var(--green)" />
        <Kpi label="Ngày nghỉ không lương" value={k.unpaidDays} color="var(--red-600)" />
        <Kpi label="Đơn đã gửi" value={k.total} />
        <Kpi label="Đang chờ duyệt" value={k.pending} color="var(--amber)" />
      </div>

      {/* Theo loại nghỉ + theo tháng */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-head"><h3>Theo loại nghỉ</h3><span className="sub">{data.byType.length} loại</span></div>
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 13 }}>
            {data.byType.length === 0 && <EmptyState>Chưa có đơn nào trong năm.</EmptyState>}
            {data.byType.map((t) => (
              <div key={t.id}>
                <div className="between" style={{ marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ width: 9, height: 9, borderRadius: 3, background: t.color }}></span>{t.name}
                    <Badge kind={t.unpaid ? 'gray' : 'green'}>{t.unpaid ? 'Không lương' : 'Có lương'}</Badge>
                  </span>
                  <span className="muted mono" style={{ fontSize: 12 }}>{t.days} ngày · {t.count} đơn</span>
                </div>
                <div className="bar"><span style={{ width: t.pct + '%', background: t.color }}></span></div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-head"><h3>Ngày nghỉ theo tháng</h3><span className="sub">đã duyệt</span></div>
          <div style={{ padding: '18px 16px', display: 'flex', alignItems: 'flex-end', gap: 6, height: 200 }}>
            {data.byMonth.map((m) => (
              <div key={m.month} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, height: '100%' }}>
                <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'flex-end' }}>
                  <div title={m.days + ' ngày'} style={{
                    width: '100%', borderRadius: '5px 5px 0 0',
                    height: (m.days > 0 ? Math.max(4, m.pct) : 0) + '%',
                    background: m.days > 0 ? 'var(--red-600)' : 'transparent',
                    transition: 'height .2s',
                  }}></div>
                </div>
                <span className="muted" style={{ fontSize: 10 }}>{MONTHS[m.month - 1]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Danh sách đơn trong năm */}
      <div className="card">
        <div className="card-head"><h3>Lịch sử đơn nghỉ {year}</h3><span className="sub">{data.requests.length} đơn</span></div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Loại nghỉ</th><th>Lương</th><th>Từ ngày</th><th>Đến ngày</th>
              <th className="tbl-num">Số ngày</th><th>Lý do</th><th>Trạng thái</th>
            </tr></thead>
            <tbody>
              {data.requests.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span style={{ fontWeight: 600, display: 'inline-flex', gap: 7, alignItems: 'center' }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: r.color }}></span>{r.leaveType}
                    </span>
                    {r.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
                  </td>
                  <td><Badge kind={r.unpaid ? 'gray' : 'green'}>{r.unpaid ? 'Không lương' : 'Có lương'}</Badge></td>
                  <td className="mono muted">{fmtDate(r.from)}</td>
                  <td className="mono muted">{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 600 }}>{r.days}</td>
                  <td className="muted">{r.reason || '—'}</td>
                  <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.requests.length === 0 && <EmptyState>Chưa có đơn nghỉ nào trong năm.</EmptyState>}
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px', color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}
