/* ============================================================
   Tab "Thống kê" — KPI hộp thư của CHÍNH người xử lý. Owner: Nhật Anh.
   Spec §6 (GET /service/stats) + §10.5.
   ⚠️ Không phải KPI toàn hệ thống: BE tính trên _inbox_domain(scope) nên
   HR Manager cũng chỉ thấy phạm vi mình đọc được (BR-SVC-13). Đừng gắn nhãn
   "toàn trung tâm" cho mấy con số này.
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import { fetchStats } from '../../api/service';

/* Thẻ KPI riêng của màn này (không import Kpi.jsx của features/timeoff —
   dùng chéo feature là buộc 2 owner vào nhau khi merge). */
function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{
        fontSize: 26, fontWeight: 800, margin: '4px 0 2px',
        color: color || 'var(--ink)',
      }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}

const COLORS = ['#7C5CFF', '#2F9E6E', '#E0A02E', '#3B82F6', '#D9534F', '#8A8577'];

/* Giờ → "2,5 giờ" / "1,3 ngày": SLA tính theo NGÀY nên quá 48h mà vẫn đọc số
   giờ thì phải tự nhẩm. */
function fmtHours(h) {
  if (h === null || h === undefined) return '—';
  if (h < 48) return `${h.toFixed(1).replace('.', ',')} giờ`;
  return `${(h / 24).toFixed(1).replace('.', ',')} ngày`;
}

export default function StatsPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = useCallback(() => {
    setErr(null); setData(null);
    fetchStats().then(setData).catch((e) => setErr(e.message));
  }, []);
  useEffect(() => { load(); }, [load]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <TableSkeleton rows={4} />;

  const max = Math.max(1, ...data.byType.map((r) => r.count));
  const pctOf = (n) => (data.total ? Math.round((n / data.total) * 100) : 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="stat-grid" style={{
        gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', marginBottom: 0,
      }}>
        <Kpi label="Tổng đơn" value={data.total}
          sub="Trong phạm vi bạn xử lý" />
        <Kpi label="Đang mở" value={data.open}
          sub={`${pctOf(data.open)}% tổng đơn`}
          color={data.open ? '#E0A02E' : undefined} />
        <Kpi label="Quá hạn" value={data.overdue}
          sub={data.overdue ? 'Cần xử lý ngay' : 'Không có đơn trễ hạn'}
          color={data.overdue ? '#D9534F' : '#2F9E6E'} />
        <Kpi label="Thời gian trả lời TB" value={fmtHours(data.avgHandleHours)}
          sub="Từ lúc gửi tới lúc chốt “Đã trả lời”" />
        <Kpi label="Điểm đánh giá TB"
          value={data.avgRating === null ? '—'
            : `${data.avgRating.toFixed(2).replace('.', ',')} ★`}
          sub={data.ratedCount ? `${data.ratedCount} đơn có chấm điểm`
            : 'Chưa có đơn nào chấm điểm'} />
        <Kpi label="Đơn ẩn danh" value={data.anonymous}
          sub={`${pctOf(data.anonymous)}% tổng đơn`} />
      </div>

      <div className="card">
        <div className="card-head"><h3>Phân bố theo loại yêu cầu</h3></div>
        <div style={{ padding: '4px 16px 18px' }}>
          {data.byType.length ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
              {data.byType.map((r, i) => (
                <div key={r.typeId}>
                  <div className="between" style={{ marginBottom: 5 }}>
                    <span style={{
                      fontSize: 13, fontWeight: 600, display: 'inline-flex',
                      gap: 8, alignItems: 'center',
                    }}>
                      <span style={{
                        width: 9, height: 9, borderRadius: 3,
                        background: COLORS[i % COLORS.length],
                      }} />
                      {r.typeName}
                    </span>
                    <span className="muted mono" style={{ fontSize: 12 }}>
                      {r.count} đơn · {pctOf(r.count)}%
                    </span>
                  </div>
                  {/* Chiều dài so với loại NHIỀU NHẤT (không so với tổng): với
                      6 loại thì thanh theo % tổng đều tí xíu, không đọc được. */}
                  <div className="bar">
                    <span style={{
                      width: Math.round((r.count / max) * 100) + '%',
                      background: COLORS[i % COLORS.length],
                    }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState>Chưa có đơn nào trong phạm vi của bạn.</EmptyState>
          )}
        </div>
      </div>
    </div>
  );
}
