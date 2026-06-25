/* Tab "Lịch sử gửi mail" — liệt kê email đã gửi cho ứng viên (nguồn: mail.message).
   Owner: Việt. Lọc theo trạng thái + tìm kiếm. */
import { useState, useEffect } from 'react';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMailLogs } from '../../api/recruitment';

const STATUS = {
  sent: ['green', 'Đã gửi'],
  outgoing: ['blue', 'Trong hàng đợi'],
  failed: ['red', 'Lỗi'],
};

const fmtDateTime = (iso) => {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }); }
  catch { return iso; }
};

export default function MailLogs({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [filter, setFilter] = useState('all');

  const load = () => { setErr(null); setData(null); fetchMailLogs().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải lịch sử gửi mail…" />;

  const { rows } = data;
  const counts = rows.reduce((m, r) => ({ ...m, [r.status]: (m[r.status] || 0) + 1 }), {});
  const filtered = rows
    .filter((r) => filter === 'all' || r.status === filter)
    .filter((r) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return [r.applicant, r.email, r.subject].some((v) => (v || '').toLowerCase().includes(q));
    });

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (filter === 'all' ? ' active' : '')} onClick={() => setFilter('all')}>
          Tất cả <span className="ct">{rows.length}</span></button>
        {Object.entries(STATUS).map(([k, [, label]]) => (
          <button key={k} className={'chip' + (filter === k ? ' active' : '')} onClick={() => setFilter(k)}>
            {label} <span className="ct">{counts[k] || 0}</span></button>
        ))}
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <th>Ứng viên</th><th>Email</th><th>Tiêu đề</th><th>Ngày gửi</th><th>Trạng thái</th>
            </tr></thead>
            <tbody>
              {filtered.map((r) => {
                const [kind, label] = STATUS[r.status] || ['gray', r.status];
                return (
                  <tr key={r.id}>
                    <td><div className="nm">{r.applicant || '—'}</div></td>
                    <td className="muted">{r.email || '—'}</td>
                    <td>{r.subject}</td>
                    <td className="muted mono">{fmtDateTime(r.date)}</td>
                    <td>
                      <Badge kind={kind} dot>{label}</Badge>
                      {r.failure && <div className="muted" style={{ fontSize: 11, marginTop: 3, color: 'var(--red-600)' }} title={r.failure}>{r.failure.slice(0, 60)}</div>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <EmptyState>Chưa có email nào được gửi.</EmptyState>}
      </div>
    </div>
  );
}
