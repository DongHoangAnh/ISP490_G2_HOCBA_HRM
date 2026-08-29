/* Chi tiết vị trí tuyển dụng / JD (drawer) — Owner: Việt.
   Xem mô tả JD + nút Chỉnh sửa.

   KHÔNG có gì dính tới TIN ĐĂNG và SỐ LIỆU TUYỂN ở đây (bỏ 2026-08-29): không
   nút Đăng tuyển / Ngừng đăng, không badge "Đang hiển thị trên web", không link
   trang công khai, không "Số lượng cần tuyển" / "Số đơn ứng tuyển". Kho JD là
   màn TRA CỨU và soạn JD; tin đăng và số liệu của đợt tuyển nằm gọn ở tab
   "Theo dõi tuyển dụng" — một chỗ duy nhất, đúng như hướng dẫn thao tác in ở
   cuối màn Kho JD. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { fetchJob } from '../../api/recruitment';
import JobForm from './JobForm';

export default function JobDrawer({ job, meta, isRecruiter, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    fetchJob(job.id).then(setDet).catch((e) => setDerr(e.message));
  }, [job.id]);

  const d = det || job;

  /* Chỉ thông tin của JD. Số liệu tuyển dụng (số lượng cần tuyển, số đơn ứng
     tuyển) và tình trạng đăng tin đã gỡ khỏi đây 2026-08-29: chúng thuộc về ĐỢT
     tuyển, xem ở tab Theo dõi tuyển dụng — bày ở Kho JD chỉ gây hiểu nhầm là
     JD tự mang chỉ tiêu. */
  const rows = [
    ['Phòng ban', d.depName],
    ['Trạng thái tuyển', meta.statusLabels[d.status] || '—'],
    ['Địa điểm', d.location || '—'],
    // teachingLevel là chữ nhập tự do — giá trị chính là nhãn, không tra bảng nữa.
    ['Trình độ', d.teachingLevel || '—'],
    ['Số buổi/tuần tối thiểu', d.sessionsPerWeek || '—'],
  ];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="briefcase" size={26} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{d.name}</h2>
            <Badge kind={d.status === 'recruiting' ? 'green' : 'gray'} dot>{meta.statusLabels[d.status] || '—'}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{d.depName}</div>
        </div>
        <div className="modal-x" style={{ display: 'flex', gap: 8 }}>
          {isRecruiter && det && (
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
              <Icon name="edit" size={15} />Chỉnh sửa</button>
          )}
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
        </div>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '56vh', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được vị trí ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải…</EmptyState>}
        {det && (
          <>
            <div className="grid-2" style={{ rowGap: 18 }}>
              {rows.map(([k, v], i) => (
                <div className="kv" key={i}><div className="k">{k}</div><div className="v">{(v === 0 || v) ? v : '—'}</div></div>
              ))}
            </div>
            {d.jdLink && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 4 }}>Link JD</div>
                <a href={d.jdLink} target="_blank" rel="noreferrer" style={{ color: 'var(--red-700)', fontSize: 13, wordBreak: 'break-all' }}>{d.jdLink}</a>
              </div>
            )}
            <div style={{ marginTop: 18 }}>
              <div className="k" style={{ marginBottom: 6 }}>Mô tả công việc (JD)</div>
              {d.description
                ? <div className="muted" style={{ fontSize: 13, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: d.description }} />
                : <div className="muted" style={{ fontSize: 13 }}>Chưa có mô tả JD.</div>}
            </div>
          </>
        )}
      </div>

      {editing && det && (
        <JobForm job={det} meta={meta}
          onClose={() => setEditing(false)}
          onSaved={(nd) => { setDet(nd); setEditing(false); onChanged && onChanged(nd); }} />
      )}
    </Modal>
  );
}
