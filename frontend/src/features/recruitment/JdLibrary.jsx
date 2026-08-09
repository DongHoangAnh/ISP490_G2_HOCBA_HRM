/* Tab "Kho quản lý JD" — tra cứu nhanh JD theo vị trí. Owner: Việt.

   Ba cột theo yêu cầu: Vị trí · Phòng ban · Trạng thái. Kèm cột JD để biết vị
   trí nào đã có mô tả công việc, vì đó là lý do người ta mở kho này.

   Dùng lại API /jobs của tab "Theo dõi tuyển dụng" (không thêm endpoint mới)
   và JobDrawer để xem/sửa JD — kho này là màn TRA CỨU, mọi thao tác nặng
   (thêm vị trí, đăng tuyển, xem theo phòng ban) vẫn ở tab kia. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fetchJobs } from '../../api/recruitment';
import JobDrawer from './JobDrawer';
import JobForm from './JobForm';
import GuideNote from './GuideNote';

/* Hướng dẫn thao tác của tab này — khung dùng chung ở GuideNote.jsx. */
const JD_STEPS = [
  ['Tra cứu JD',
   <>Lọc bằng hàng chip <b>trạng thái tuyển</b> (Đang tuyển / Dừng tuyển), ô chọn
     <b> phòng ban</b> và ô tìm kiếm ở đầu màn. Cột <b>JD</b> cho biết vị trí nào đã
     có file mô tả công việc — bấm <b>Mở file JD</b> để xem bản gốc trên Drive.</>],
  ['Thêm vị trí mới',
   <>Bấm <b>Thêm vị trí</b> để tạo vị trí kèm JD. Tên vị trí <b>không được trùng</b>
     trong cùng một phòng ban, nên tra ở kho trước khi tạo để khỏi dựng bản thứ hai
     của cùng một JD.</>],
  ['Xem & cập nhật nội dung JD',
   <>Bấm vào dòng để mở chi tiết: mô tả công việc, yêu cầu, số lượng cần tuyển,
     link JD. Sửa ở đây là mọi nơi dùng JD đó cập nhật theo — kể cả trang tuyển
     dụng công khai nếu vị trí đang được đăng.</>],
  ['Dùng JD khi mở phiếu yêu cầu',
   <>Sang tab <b>Phiếu yêu cầu</b>, chọn <b>phòng ban</b> rồi chọn <b>JD từ kho</b>
     — hệ thống tự điền tên vị trí và link JD, khỏi copy tay.</>],
  ['Đăng tuyển',
   <>Kho này chỉ để tra cứu và soạn JD. Việc <b>bật đăng tuyển</b> (badge PUBLISHED)
     và <b>chép link</b> trang tuyển dụng công khai nằm ở tab
     <b> Theo dõi tuyển dụng</b>.</>],
];

const JD_GUIDE_NOTE = (
  <><b>Trạng thái</b> ở đây là trạng thái tuyển của vị trí, không phải trạng thái
    của file JD: vị trí tự chuyển <b>Dừng tuyển</b> khi đã tuyển đủ chỉ tiêu, còn
    JD thì vẫn nằm trong kho để dùng lại cho đợt sau.</>
);

export default function JdLibrary({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [status, setStatus] = useState('all');
  const [dep, setDep] = useState('all');
  const [sel, setSel] = useState(null);
  const [creating, setCreating] = useState(false);

  const load = () => { setErr(null); setData(null); fetchJobs().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  /* Lọc + phân trang đặt TRƯỚC early-return (quy tắc hook — xem Requests.jsx). */
  const filtered = (data ? data.rows : []).filter((r) => {
    if (status !== 'all' && r.status !== status) return false;
    if (dep !== 'all' && r.depId !== dep) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((r.name || '').toLowerCase().includes(q) || (r.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  })
    /* Vị trí ĐANG TUYỂN lên đầu — đó là việc đang chạy, phải thấy ngay ở trang 1
       thay vì lẫn giữa các JD cũ. Sort ổn định nên trong cùng nhóm vẫn giữ
       nguyên thứ tự BE trả về. */
    .sort((a, b) => (a.status === 'recruiting' ? 0 : 1) - (b.status === 'recruiting' ? 0 : 1));
  const pg = usePaged(filtered, [status, dep, search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải kho JD…" />;

  const { rows, statusLabels, teachingLevels, departments, isRecruiter, isHr } = data;
  const meta = { statusLabels, teachingLevels, departments };

  /* Drawer sửa JD xong → cập nhật đúng dòng; vị trí vừa tạo thì chèn lên đầu
     (dòng mới có thể rơi ngoài bộ lọc đang chọn — đó là hành vi đúng, không ép
     hiện). Khỏi tải lại cả kho. */
  const applyRow = (det) => setData((p) => {
    const exists = p.rows.some((r) => r.id === det.id);
    return {
      ...p,
      rows: exists ? p.rows.map((r) => (r.id === det.id ? { ...r, ...det } : r))
        : [det, ...p.rows],
    };
  });

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (status === 'all' ? ' active' : '')} onClick={() => setStatus('all')}>
          Tất cả <span className="ct">{rows.length}</span></button>
        {Object.entries(statusLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (status === k ? ' active' : '')} onClick={() => setStatus(k)}>
            {l} <span className="ct">{rows.filter((r) => r.status === k).length}</span></button>
        ))}
        {/* Trưởng phòng đã bị BE giới hạn trong phòng mình ⇒ ẩn bộ lọc phòng ban
            (giống tab Theo dõi tuyển dụng), bày ra chỉ tổ gây hiểu nhầm là thiếu dữ liệu. */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          {isHr && (
            <select className="sel" value={dep}
              onChange={(e) => setDep(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
              <option value="all">Mọi phòng ban</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          )}
          {isRecruiter && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm vị trí</button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <th>Vị trí</th><th>Phòng ban</th><th>Trạng thái</th><th>JD</th><th></th>
            </tr></thead>
            <tbody>
              {pg.rows.map((r) => (
                <tr key={r.id} onClick={() => setSel(r)}>
                  <td><div className="nm">{r.name}</div>
                    {r.teachingLevel && <div className="id">{r.teachingLevel}</div>}</td>
                  <td className="muted">{r.depName}</td>
                  <td><Badge kind={r.status === 'recruiting' ? 'green' : 'gray'} dot>
                    {statusLabels[r.status] || '—'}</Badge></td>
                  <td>
                    {r.jdLink ? (
                      <a href={r.jdLink} target="_blank" rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }}>
                        <Icon name="file" size={14} />Mở file JD</a>
                    ) : (
                      <span className="muted" style={{ fontSize: 12.5 }}>Chưa có file</span>
                    )}
                  </td>
                  <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}>
                    <Icon name="chevR" size={18} className="faint" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <EmptyState>Không tìm thấy JD phù hợp.</EmptyState>}
        <Pagination {...pg} />
      </div>

      <GuideNote title="Các bước bộ phận tuyển dụng cần làm ở màn này"
        steps={JD_STEPS} note={JD_GUIDE_NOTE} />

      {sel && (
        <JobDrawer job={sel} meta={meta} isRecruiter={isRecruiter}
          onClose={() => setSel(null)} onChanged={applyRow} />
      )}
      {creating && (
        <JobForm job={null} meta={meta}
          onClose={() => setCreating(false)}
          onSaved={(det) => { setCreating(false); applyRow(det); }} />
      )}
    </div>
  );
}
