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
   <>Lọc bằng chip <b>trạng thái tuyển</b>, ô chọn <b>phòng ban</b> và ô tìm kiếm.
     Cột <b>JD</b> cho biết vị trí nào đã có file — bấm <b>Mở file JD</b> để xem
     bản gốc trên Drive.</>],
  ['Thêm vị trí mới',
   <>Bấm <b>Thêm vị trí</b> để tạo vị trí kèm JD. Tên vị trí <b>không trùng</b>
     trong cùng phòng ban, nên tra kho trước khi tạo.</>],
  ['Sửa nội dung JD',
   <>Bấm vào dòng để mở chi tiết (mô tả, yêu cầu, link JD). Sửa ở đây thì mọi
     nơi dùng JD đó đổi theo, kể cả trang tuyển dụng công khai. Số lượng cần
     tuyển và số đơn ứng tuyển <b>không</b> nằm ở kho này — chúng thuộc từng đợt
     tuyển, xem ở tab <b>Theo dõi tuyển dụng</b>.</>],
  ['Dùng lại khi mở phiếu',
   <>Ở tab <b>Phiếu yêu cầu</b>, chọn phòng ban rồi chọn <b>JD từ kho</b> — tên vị
     trí và link JD tự điền.</>],
  ['Đăng tuyển ở tab khác',
   <>Kho này chỉ để tra cứu và soạn JD. <b>Bật đăng tuyển</b> và chép link trang
     công khai nằm ở tab <b>Theo dõi tuyển dụng</b>.</>],
];

const JD_GUIDE_NOTE = (
  <><b>Trạng thái</b> ở đây là trạng thái tuyển của vị trí, không phải của file
    JD: tuyển đủ chỉ tiêu thì vị trí tự <b>Dừng tuyển</b>, JD vẫn nằm trong kho để
    dùng lại đợt sau.</>
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

  /* Một hàm lọc duy nhất cho cả bảng lẫn số trên chip, cho phép ghi đè từng
     tiêu chí. Số trên chip đếm theo các bộ lọc CÒN LẠI đang bật ("bấm chip này
     thì thấy bao nhiêu dòng") — đếm trên tập chưa lọc thì chọn phòng ban hoặc
     gõ ô tìm kiếm là chip đứng yên trong khi bảng đã đổi. Cùng khuôn với
     Phòng ban / Nhận việc / Nghỉ việc (xem Offboarding.jsx). */
  const keep = (r, o = {}) => {
    const st = 'status' in o ? o.status : status;
    const d = 'dep' in o ? o.dep : dep;
    if (st !== 'all' && r.status !== st) return false;
    if (d !== 'all' && r.depId !== d) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((r.name || '').toLowerCase().includes(q) || (r.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  };

  /* Lọc + phân trang đặt TRƯỚC early-return (quy tắc hook — xem Requests.jsx). */
  const filtered = (data ? data.rows : []).filter((r) => keep(r))
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
          Tất cả <span className="ct">{rows.filter((r) => keep(r, { status: 'all' })).length}</span></button>
        {Object.entries(statusLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (status === k ? ' active' : '')} onClick={() => setStatus(k)}>
            {l} <span className="ct">{rows.filter((r) => keep(r, { status: k })).length}</span></button>
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

      <GuideNote title="Các bước cần làm ở màn này"
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
