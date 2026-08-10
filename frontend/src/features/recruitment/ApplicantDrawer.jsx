/* Hồ sơ chi tiết CV ứng viên (drawer) — Owner: Việt.
   Xem chi tiết + nút Chỉnh sửa (mở ApplicantForm). */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchApplicant } from '../../api/recruitment';
import { CV_RESULT_KIND, CALL_STATUS_KIND, ATTENDANCE_KIND, INTERVIEW_RESULT_KIND } from './util';
import ApplicantForm from './ApplicantForm';

export default function ApplicantDrawer({ app, meta, isRecruiter, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    fetchApplicant(app.id).then(setDet).catch((e) => setDerr(e.message));
  }, [app.id]);

  const d = det || app;
  const cvLbl = d.cvResult ? meta.cvResultLabels[d.cvResult] : '';
  const callLbl = d.callStatus ? meta.callStatusLabels[d.callStatus] : '';
  const attLbl = d.attendanceStatus ? (meta.attendanceLabels?.[d.attendanceStatus] || '') : '';
  const resLbl = d.interviewResult ? (meta.interviewResultLabels?.[d.interviewResult] || '') : '';
  const hasInterview = d.attendanceStatus || d.interviewResult;
  const hasOffer = d.offerContent || d.startDate || d.candidateConfirmed;

  const rows = [
    ['Họ tên ứng viên', d.name],
    ['Số điện thoại', d.phone || '—'],
    ['Email', d.email || '—'],
    ['Vị trí ứng tuyển', d.jobName || '—'],
    ['Đợt tuyển', d.requestCode || '—'],
    ['Bước hiện tại', d.stage || '—'],
    ['CTV tuyển dụng', d.ctv || '—'],
    ['Ngày nhận CV', fmtDate(d.dateReceived)],
    ['Ngày hẹn PV', d.interviewDate ? `${fmtDate(d.interviewDate)}${d.interviewTime ? ' · ' + d.interviewTime : ''}` : '—'],
    ['Người PV', d.interviewer || '—'],
  ];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0, fontSize: 22, fontWeight: 800 }}>
          {(d.name || '?').trim().charAt(0).toUpperCase()}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{d.name}</h2>
            {d.stage && <Badge kind="violet" dot>{d.stage}</Badge>}
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{d.jobName || 'Chưa gán vị trí'}</div>
          <div style={{ display: 'flex', gap: 14, marginTop: 10, flexWrap: 'wrap' }}>
            {d.phone && <span className="muted" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }}><Icon name="phone" size={15} />{d.phone}</span>}
            {d.email && <span className="muted" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }}><Icon name="mail" size={15} />{d.email}</span>}
          </div>
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
        {derr && <EmptyState>Không tải được hồ sơ ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải hồ sơ…</EmptyState>}
        {det && (
          <>
            <div className="grid-2" style={{ rowGap: 18 }}>
              {rows.map(([k, v], i) => (
                <div className="kv" key={i}><div className="k">{k}</div><div className="v">{v || '—'}</div></div>
              ))}
              <div className="kv"><div className="k">Lọc CV</div><div className="v">
                {cvLbl ? <Badge kind={CV_RESULT_KIND[d.cvResult] || 'gray'}>{cvLbl}</Badge> : '—'}</div></div>
              <div className="kv"><div className="k">Gọi điện</div><div className="v">
                {callLbl ? <Badge kind={CALL_STATUS_KIND[d.callStatus] || 'gray'}>{callLbl}</Badge> : '—'}</div></div>
            </div>
            {d.cvLink && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 4 }}>Link CV</div>
                <a href={d.cvLink} target="_blank" rel="noreferrer" style={{ color: 'var(--red-700)', fontSize: 13, wordBreak: 'break-all' }}>{d.cvLink}</a>
              </div>
            )}
            {d.cvNote && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 4 }}>Ghi chú CV</div>
                <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{d.cvNote}</div>
              </div>
            )}

            {hasInterview && (
              <div style={{ marginTop: 22 }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Phỏng vấn</div>
                <div className="grid-2" style={{ rowGap: 18 }}>
                  <div className="kv"><div className="k">Trạng thái</div><div className="v">
                    {attLbl ? <Badge kind={ATTENDANCE_KIND[d.attendanceStatus] || 'gray'} dot>{attLbl}</Badge> : '—'}</div></div>
                  <div className="kv"><div className="k">Kết quả PV</div><div className="v">
                    {resLbl ? <Badge kind={INTERVIEW_RESULT_KIND[d.interviewResult] || 'gray'}>{resLbl}</Badge> : '—'}</div></div>
                </div>
              </div>
            )}

            {hasOffer && (
              <div style={{ marginTop: 22 }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Offer &amp; Nhận việc</div>
                <div className="grid-2" style={{ rowGap: 18 }}>
                  <div className="kv"><div className="k">Ngày nhận việc</div><div className="v">{d.startDate ? fmtDate(d.startDate) : '—'}</div></div>
                  <div className="kv"><div className="k">UV xác nhận</div><div className="v">{d.candidateConfirmed || '—'}</div></div>
                </div>
                {d.offerContent && (
                  <div style={{ marginTop: 14 }}>
                    <div className="k" style={{ marginBottom: 4 }}>Nội dung Offer</div>
                    <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{d.offerContent}</div>
                  </div>
                )}
                {d.offerNote && (
                  <div style={{ marginTop: 14 }}>
                    <div className="k" style={{ marginBottom: 4 }}>Ghi chú Offer</div>
                    <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{d.offerNote}</div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {editing && det && (
        <ApplicantForm app={det} meta={meta}
          onClose={() => setEditing(false)}
          onSaved={(newDet) => { setDet(newDet); setEditing(false); onChanged && onChanged(newDet); }} />
      )}
    </Modal>
  );
}
