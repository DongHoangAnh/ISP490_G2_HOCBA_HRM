/* ============================================================
   Tab "Đơn của tôi" — người gửi theo dõi & trả lời đơn của chính mình.
   Owner: Nhật Anh. Spec §4.5 + §7.2.
   Đơn ẩn danh VẪN nằm ở đây: danh tính được ẩn với người xử lý, không phải
   với người gửi — đó là cách người gửi tiếp tục hội thoại 2 chiều.
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import { fetchMyRequests } from '../../api/service';
import { fmtDateTime, stateMeta } from './svcMeta';
import RequestThread from './RequestThread';

const FILTERS = [
  ['', 'Tất cả'],
  ['open', 'Đang mở'],
  ['answered', 'Đã trả lời'],
  ['closed', 'Đã đóng'],
  ['cancelled', 'Đã rút'],
];

export default function MyRequestsPanel({ search, focus }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [state, setState] = useState('');
  const [year, setYear] = useState('');
  const [open, setOpen] = useState(null);   // id đơn đang mở modal

  const load = useCallback(() => {
    // setData(null) ở đây chứ không ở onChange của select: đặt ở onChange mà
    // giá trị không đổi thật thì load giữ nguyên identity ⇒ effect không chạy
    // lại ⇒ skeleton treo vĩnh viễn.
    setErr(null); setData(null);
    fetchMyRequests(state, year).then(setData).catch((e) => setErr(e.message));
  }, [state, year]);
  useEffect(() => { load(); }, [load]);

  /* Bấm thông báo ở chuông → mở đúng đơn (App truyền focus xuống). */
  useEffect(() => {
    if (focus && focus.requestId) setOpen(focus.requestId);
  }, [focus]);

  if (err) return <ErrorState message={err} onRetry={load} />;

  const rows = (data ? data.requests : []).filter((r) => {
    const k = (search || '').trim().toLowerCase();
    if (!k) return true;
    return [r.name, r.subject, r.typeName, r.body]
      .some((v) => (v || '').toLowerCase().includes(k));
  });

  return (
    <div className="card">
      <div className="card-head" style={{ gap: 10, flexWrap: 'wrap' }}>
        <h3>Đơn của tôi</h3>
        <div style={{ flex: 1 }} />
        <select className="sel" value={state}
          onChange={(e) => { setState(e.target.value); }}>
          {FILTERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select className="sel" value={year}
          onChange={(e) => { setYear(e.target.value); }}>
          <option value="">Mọi năm</option>
          {(data && data.years ? data.years : []).map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      {!data ? <div style={{ padding: '0 16px 16px' }}><TableSkeleton rows={5} /></div> : (
        <>
          {/* tbl-scroll: `table.tbl td` mặc định nowrap + max-width:0 nên badge
              đặt sau tiêu đề bị CẮT MẤT — mà "Ẩn danh" là nhãn quan trọng nhất
              của màn này. Modifier này bỏ giới hạn đó (ô tiêu đề tự cắt bằng
              div bên trong). */}
          <div className="tbl-wrap tbl-scroll">
            <table className="tbl">
              <thead><tr>
                <th>Mã đơn</th><th>Tiêu đề</th><th>Loại</th><th>Gửi tới</th>
                <th>Gửi lúc</th><th>Trạng thái</th><th></th>
              </tr></thead>
              <tbody>
                {rows.map((r) => {
                  const st = stateMeta(r.state);
                  return (
                    <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => setOpen(r.id)}>
                      <td className="mono muted">{r.name}</td>
                      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                        <span style={{
                          display: 'inline-block', maxWidth: 320, overflow: 'hidden',
                          textOverflow: 'ellipsis', verticalAlign: 'middle',
                        }}>{r.subject}</span>
                        {r.isAnonymous && (
                          <span style={{ marginLeft: 7 }}><Badge kind="violet">Ẩn danh</Badge></span>
                        )}
                        {r.priority === 'urgent' && (
                          <span style={{ marginLeft: 7 }}><Badge kind="amber">Gấp</Badge></span>
                        )}
                      </td>
                      <td>{r.typeName}</td>
                      <td>{r.recipientScope === 'hr' ? 'HR'
                        : r.recipientScope === 'manager' ? 'Trưởng phòng' : 'HR & TP'}</td>
                      <td className="mono muted">{fmtDateTime(r.createdAt)}</td>
                      <td>
                        <Badge kind={st.kind} dot>{st.label}</Badge>
                        {r.isOverdue && (
                          <span style={{ marginLeft: 6 }}><Badge kind="red">Trễ hạn</Badge></span>
                        )}
                      </td>
                      <td>
                        <button className="btn btn-ghost btn-sm"
                          onClick={(e) => { e.stopPropagation(); setOpen(r.id); }}>
                          <Icon name="eye" size={14} />Xem
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {rows.length === 0 && (
            <EmptyState>
              {search
                ? 'Không có đơn nào khớp từ khóa.'
                : 'Bạn chưa gửi đơn nào. Bấm “Gửi yêu cầu” ở trên để bắt đầu.'}
            </EmptyState>
          )}
        </>
      )}

      {open && (
        <RequestThread requestId={open} role="sender"
          onClose={() => setOpen(null)} onChanged={load} />
      )}
    </div>
  );
}
