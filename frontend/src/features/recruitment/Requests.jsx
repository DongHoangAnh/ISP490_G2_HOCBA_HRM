/* Tab "Phiếu yêu cầu" — danh sách + workflow phê duyệt, xem chi tiết, sửa, thêm.
   Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect, useRef } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fmtDate } from '../../utils/format';
import { fetchRequests } from '../../api/recruitment';
import { REQUEST_STATE_KIND } from './util';
import RequestDrawer from './RequestDrawer';
import RequestForm from './RequestForm';

export default function Requests({ search, focus }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [state, setState] = useState('all');
  const [sel, setSel] = useState(null);
  const [creating, setCreating] = useState(false);
  const handledFocus = useRef(null);   // nonce thông báo đã xử lý

  const load = () => { setErr(null); setData(null); fetchRequests().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  /* Bấm thông báo "Phiếu chờ duyệt" ở chuông → mở drawer đúng phiếu. Cùng cách
     làm với CvList: chốt bằng ref theo nonce để drawer không tự bật lại mỗi lần
     `data` đổi, và reset chip lọc để đóng drawer xong còn thấy phiếu đó. */
  useEffect(() => {
    if (!focus || !focus.requestId || !data) return;
    if (handledFocus.current === focus.nonce) return;
    const row = data.rows.find((r) => r.id === focus.requestId);
    if (!row) return;
    handledFocus.current = focus.nonce;
    setState('all');
    setSel(row);
  }, [focus, data]);

  /* Lọc + phân trang đặt TRƯỚC early-return: usePaged là hook, gọi sau
     `if (!data) return` sẽ đổi số hook giữa lúc loading và lúc có dữ liệu. */
  const filtered = (data ? data.rows : []).filter((r) => {
    if (state !== 'all' && r.state !== state) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((r.name || '').toLowerCase().includes(q) || (r.jobTitle || '').toLowerCase().includes(q)
        || (r.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  });
  const pg = usePaged(filtered, [state, search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phiếu yêu cầu…" />;

  const { rows, stateLabels, reasonLabels, levelLabels, educationLabels, workTypeLabels, departments, jobs, isRecruiter, canApprove } = data;
  const meta = { stateLabels, reasonLabels, levelLabels, educationLabels, workTypeLabels, departments, jobs };

  const applyRow = (det) => setData((p) => {
    const exists = p.rows.some((r) => r.id === det.id);
    return { ...p, rows: exists ? p.rows.map((r) => (r.id === det.id ? { ...r, ...det } : r)) : [det, ...p.rows] };
  });

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (state === 'all' ? ' active' : '')} onClick={() => setState('all')}>
          Tất cả <span className="ct">{rows.length}</span></button>
        {Object.entries(stateLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (state === k ? ' active' : '')} onClick={() => setState(k)}>
            {l} <span className="ct">{rows.filter((r) => r.state === k).length}</span></button>
        ))}
        {isRecruiter && (
          <div style={{ marginLeft: 'auto' }}>
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm phiếu</button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <th>Mã phiếu</th><th>Vị trí</th><th>Phòng ban</th>
              <th className="tbl-num">SL</th><th>Lý do</th><th>Ngày order</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {pg.rows.map((r) => (
                <tr key={r.id} onClick={() => setSel(r)}>
                  <td className="mono" style={{ fontWeight: 600 }}>{r.name}</td>
                  <td><div className="nm">{r.jobTitle || '—'}</div>{r.level && <div className="id">{levelLabels[r.level]}</div>}</td>
                  <td className="muted">{r.depName || '—'}</td>
                  <td className="tbl-num mono">{r.qty}</td>
                  <td className="muted">{reasonLabels[r.reason] || '—'}</td>
                  <td className="muted mono">{fmtDate(r.dateRequest)}</td>
                  <td><Badge kind={REQUEST_STATE_KIND[r.state] || 'gray'} dot>{stateLabels[r.state]}</Badge></td>
                  <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <EmptyState>Không có phiếu yêu cầu phù hợp.</EmptyState>}
        <Pagination {...pg} />
      </div>

      {sel && (
        <RequestDrawer req={sel} meta={meta} isRecruiter={isRecruiter} canApprove={canApprove}
          onClose={() => setSel(null)} onChanged={applyRow} />
      )}
      {creating && (
        <RequestForm req={null} meta={meta}
          onClose={() => setCreating(false)}
          onSaved={(det) => { setCreating(false); applyRow(det); }} />
      )}
    </div>
  );
}
