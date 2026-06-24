/* "Lịch sử xử lý" — dòng thời gian thao tác của 1 đơn nghỉ (Phase 5, audit).
   Đọc GET /request/<id>/history. Dùng trong modal chi tiết đơn + modal mở từ
   chuông thông báo. Owner: Nhật Anh. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchRequestHistory } from '../../api/timeoff';

/* Datetime ISO → 'dd/mm/yyyy HH:MM' (lịch sử cần cả giờ, khác fmtDate chỉ ngày). */
function fmtDateTime(s) {
  if (!s) return '—';
  const d = new Date(s);
  if (isNaN(d)) return s;
  const p = (n) => String(n).padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

export default function HistoryTimeline({ requestId }) {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setRows(null);
    fetchRequestHistory(requestId)
      .then((d) => setRows(d.history || []))
      .catch((e) => setErr(e.message));
  }, [requestId, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!rows) return <LoadingState label="Đang tải lịch sử…" />;
  if (rows.length === 0) return <EmptyState>Chưa có thao tác nào được ghi nhận.</EmptyState>;

  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
      {rows.map((r, i) => (
        <li key={r.id} style={{ display: 'flex', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--red-50,#fef2f2)', color: 'var(--red-600)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name="clock" size={14} />
            </span>
            {i < rows.length - 1 && <span style={{ width: 2, flex: 1, background: 'var(--border)', marginTop: 2 }}></span>}
          </div>
          <div style={{ paddingBottom: 2 }}>
            <div style={{ fontSize: 13.5, color: 'var(--ink)' }}>{r.body}</div>
            <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
              {r.author ? r.author + ' · ' : ''}<span className="mono">{fmtDateTime(r.date)}</span>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
