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
import GuideNote from './GuideNote';

/* Hướng dẫn thao tác của tab này — khung dùng chung ở GuideNote.jsx.
   Các bước bám đúng ACTIONS_BY_STATE trong RequestDrawer.jsx và state của
   hb.recruitment.request; đổi luồng duyệt thì sửa cả đây. */
const REQ_STEPS = [
  ['Tạo phiếu',
   <>Bấm <b>Thêm phiếu</b>, chọn phòng ban rồi chọn <b>JD từ kho</b> — tên vị trí
     và link JD tự điền. Điền số lượng, lý do tuyển và <b>Ngày cần onboard</b>
     (đây chính là deadline ở tab Theo dõi tuyển dụng).</>],
  ['Gửi duyệt',
   <>Phiếu mới ở trạng thái <b>Nháp</b>. Bấm <b>Gửi duyệt</b> để chuyển sang
     <b> Chờ BP duyệt</b> — người duyệt sẽ nhận thông báo ở chuông.</>],
  ['Duyệt hoặc từ chối',
   <>HR / bộ phận tuyển dụng bấm <b>Duyệt</b> (phiếu sang <b>Đang tuyển</b> và cộng
     chỉ tiêu vào vị trí) hoặc <b>Từ chối</b> kèm lý do. Người order chỉ gửi duyệt
     hoặc đưa phiếu <b>về nháp</b>.</>],
  ['Bắt đầu nhận CV',
   <>Phiếu <b>Đang tuyển</b> mới lên tab <b>Theo dõi tuyển dụng</b> và mới nhận CV
     — CV nộp vào vị trí sẽ tự gắn vào phiếu đang mở của vị trí đó.</>],
  ['Đóng hoặc mở lại',
   <>Tuyển đủ chỉ tiêu thì hệ thống <b>tự đóng phiếu</b>; cần đóng sớm thì bấm
     <b> Đóng phiếu</b>. Phiếu <b>Đã đóng</b> / <b>Từ chối</b> vẫn mở lại được bằng
     <b> Mở lại (về nháp)</b>.</>],
];

const REQ_GUIDE_NOTE = (
  <>Mã phiếu do hệ thống tự sinh. Hàng chip ở đầu bảng lọc theo trạng thái và đếm
    trên dữ liệu thật — bấm <b>Chờ BP duyệt</b> là ra ngay việc cần xử lý.</>
);

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

  /* Ô tìm kiếm cũng là một bộ lọc: số trên chip phải đếm trên tập ĐÃ tìm kiếm,
     không thì gõ vào ô tìm kiếm là chip đứng yên trong khi bảng đã đổi. */
  const matchSearch = (r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (r.name || '').toLowerCase().includes(q) || (r.jobTitle || '').toLowerCase().includes(q)
      || (r.depName || '').toLowerCase().includes(q);
  };

  /* Lọc + phân trang đặt TRƯỚC early-return: usePaged là hook, gọi sau
     `if (!data) return` sẽ đổi số hook giữa lúc loading và lúc có dữ liệu. */
  const searched = (data ? data.rows : []).filter(matchSearch);
  const filtered = searched.filter((r) => state === 'all' || r.state === state);
  const pg = usePaged(filtered, [state, search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phiếu yêu cầu…" />;

  const { stateLabels, reasonLabels, levelLabels, educationLabels, workTypeLabels, departments, jobs, isRecruiter, canApprove } = data;
  const meta = { stateLabels, reasonLabels, levelLabels, educationLabels, workTypeLabels, departments, jobs };

  const applyRow = (det) => setData((p) => {
    const exists = p.rows.some((r) => r.id === det.id);
    return { ...p, rows: exists ? p.rows.map((r) => (r.id === det.id ? { ...r, ...det } : r)) : [det, ...p.rows] };
  });

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (state === 'all' ? ' active' : '')} onClick={() => setState('all')}>
          Tất cả <span className="ct">{searched.length}</span></button>
        {Object.entries(stateLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (state === k ? ' active' : '')} onClick={() => setState(k)}>
            {l} <span className="ct">{searched.filter((r) => r.state === k).length}</span></button>
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

      <GuideNote title="Các bước cần làm ở màn này"
        steps={REQ_STEPS} note={REQ_GUIDE_NOTE} />

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
