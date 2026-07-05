/* Chi tiết vị trí tuyển dụng / JD (drawer) — Owner: Việt.
   Xem mô tả JD + nút Chỉnh sửa / toggle Đăng tuyển. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { fetchJob, updateJob } from '../../api/recruitment';
import JobForm from './JobForm';
import CopyLinkBtn from './CopyLinkBtn';
import { publicJobUrl } from './util';

export default function JobDrawer({ job, meta, isRecruiter, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchJob(job.id).then(setDet).catch((e) => setDerr(e.message));
  }, [job.id]);

  const d = det || job;

  const togglePublish = async () => {
    setBusy(true);
    try {
      const nd = await updateJob(d.id, { published: !d.published });
      setDet(nd); onChanged && onChanged(nd);
    } catch (e) { alert(e.message); } finally { setBusy(false); }
  };

  const rows = [
    ['Phòng ban', d.depName],
    ['Trạng thái tuyển', meta.statusLabels[d.status] || '—'],
    ['Số lượng cần tuyển', d.expected],
    ['Số đơn ứng tuyển', d.applications],
    ['Địa điểm', d.location || '—'],
    ['Trình độ giảng dạy', d.requiresTeaching ? (meta.teachingLevels[d.teachingLevel] || '—') : '—'],
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
            {d.published && <Badge kind="teal">Đang hiển thị trên web</Badge>}
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{d.depName}</div>
        </div>
        <div className="modal-x" style={{ display: 'flex', gap: 8 }}>
          {isRecruiter && det && (
            <>
              <button className="btn btn-ghost btn-sm" onClick={togglePublish} disabled={busy}>
                <Icon name={d.published ? 'x' : 'check'} size={15} />{d.published ? 'Ngừng đăng' : 'Đăng tuyển'}</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
                <Icon name="edit" size={15} />Chỉnh sửa</button>
            </>
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
            {d.published && d.websiteUrl && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 4 }}>Trang tuyển dụng công khai</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <a href={publicJobUrl(d.websiteUrl)} target="_blank" rel="noreferrer" style={{ color: 'var(--teal)', fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 6, wordBreak: 'break-all' }}>
                    <Icon name="briefcase" size={14} />{publicJobUrl(d.websiteUrl)}</a>
                  <CopyLinkBtn url={d.websiteUrl} />
                </div>
              </div>
            )}
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
