/* Chi tiết phiếu yêu cầu tuyển dụng (drawer) — Owner: Việt.
   Xem chi tiết + nút workflow (gửi duyệt / duyệt / đóng / từ chối / về nháp). */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchRequest, requestAction } from '../../api/recruitment';
import { REQUEST_STATE_KIND } from './util';
import RequestForm from './RequestForm';

/* Action khả dụng theo state hiện tại.
   "Mở lại (về nháp)" CHỈ có ở trạng thái Từ chối — backend chặn mọi trạng thái
   khác (hb_recruitment_request.action_reset_draft). Phiếu đang tuyển đã cộng
   chỉ tiêu vào vị trí nên muốn dừng thì Đóng phiếu, lúc đó chỉ tiêu chưa tuyển
   được trả lại; phiếu đã đóng là chốt đợt, cần nữa thì tạo phiếu mới. */
const ACTIONS_BY_STATE = {
  draft: [['submit', 'Gửi duyệt', 'check']],
  submitted: [['approve', 'Duyệt', 'checkCircle'], ['refuse', 'Từ chối', 'x']],
  recruiting: [['close', 'Đóng phiếu', 'checkCircle']],
  refused: [['reset', 'Mở lại (về nháp)', 'edit']],
  closed: [],
};

/* Tách vai: duyệt/từ chối/đóng/mở lại nháp chỉ BP tuyển dụng/HR (canApprove);
   TBP (người order) chỉ gửi duyệt (isRecruiter). */
const HR_ACTIONS = new Set(['approve', 'refuse', 'close', 'reset']);

export default function RequestDrawer({ req, meta, isRecruiter, canApprove, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actErr, setActErr] = useState(null);

  useEffect(() => {
    fetchRequest(req.id).then(setDet).catch((e) => setDerr(e.message));
  }, [req.id]);

  const d = det || req;

  const runAction = async (action) => {
    let extra = {};
    if (action === 'refuse') {
      const reason = window.prompt('Lý do từ chối / trả về:');
      if (reason === null) return;
      extra.refuseReason = reason;
    }
    setBusy(true); setActErr(null);
    try {
      const nd = await requestAction(d.id, action, extra);
      setDet(nd); onChanged && onChanged(nd);
    } catch (e) { setActErr(e.message); } finally { setBusy(false); }
  };

  const rows = det ? [
    ['Mã phiếu', d.name],
    ['Người tạo', d.requester || '—'],
    ['Ngày order', fmtDate(d.dateRequest)],
    ['Phòng ban', d.depName || '—'],
    ['Vị trí', d.jobTitle || '—'],
    ['Số lượng cần tuyển', d.qty],
    ['Lý do tuyển', meta.reasonLabels[d.reason] || '—'],
    ['Cấp bậc', meta.levelLabels[d.level] || '—'],
    ['Bằng cấp tối thiểu', meta.educationLabels[d.education] || '—'],
    ['Kinh nghiệm tối thiểu', d.experienceYears ? `${d.experienceYears} năm` : '—'],
    ['Ngoại ngữ', d.languageRequirement || '—'],
    ['Ngày cần onboard', fmtDate(d.expectedStartDate)],
    ['Mức lương dự kiến', d.salaryRange || '—'],
    ['Hình thức làm việc', meta.workTypeLabels[d.workType] || '—'],
  ] : [];

  const actions = (ACTIONS_BY_STATE[d.state] || []).filter(([act]) =>
    HR_ACTIONS.has(act) ? canApprove : isRecruiter);

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="file" size={26} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{d.name || 'Phiếu mới'}</h2>
            <Badge kind={REQUEST_STATE_KIND[d.state] || 'gray'} dot>{meta.stateLabels[d.state] || '—'}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{d.jobTitle} · {d.depName}</div>
        </div>
        <div className="modal-x" style={{ display: 'flex', gap: 8 }}>
          {isRecruiter && det && d.state === 'draft' && (
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
              <Icon name="edit" size={15} />Chỉnh sửa</button>
          )}
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
        </div>
      </div>

      {actions.length > 0 && (
        <div style={{ display: 'flex', gap: 8, padding: '12px 24px', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', alignItems: 'center' }}>
          {actions.map(([act, label, icon]) => (
            <button key={act} className={'btn btn-sm ' + (act === 'refuse' ? 'btn-ghost' : 'btn-primary')}
              disabled={busy}
              style={act === 'approve' || act === 'close' ? { background: 'var(--green)', borderColor: 'var(--green)' } : undefined}
              onClick={() => runAction(act)}>
              <Icon name={icon} size={14} />{label}
            </button>
          ))}
          {busy && <span className="muted" style={{ fontSize: 12 }}>Đang xử lý…</span>}
          {actErr && <span style={{ color: 'var(--red-600)', fontSize: 12 }}>{actErr}</span>}
        </div>
      )}

      <div style={{ padding: '22px 24px', maxHeight: '52vh', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được phiếu ({derr}).</EmptyState>}
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
            {d.skillDescription && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 4 }}>Kỹ năng yêu cầu</div>
                <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{d.skillDescription}</div>
              </div>
            )}
            {d.state === 'refused' && d.refuseReason && (
              <div style={{ marginTop: 18, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10 }}>
                <div className="k" style={{ marginBottom: 4, color: 'var(--red-700)' }}>Lý do từ chối</div>
                <div style={{ fontSize: 13, color: 'var(--red-700)' }}>{d.refuseReason}</div>
              </div>
            )}
            {d.note && (
              <div style={{ marginTop: 18 }}>
                <div className="k" style={{ marginBottom: 6 }}>Ghi chú nội bộ</div>
                <div className="muted" style={{ fontSize: 13, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: d.note }} />
              </div>
            )}
          </>
        )}
      </div>

      {editing && det && (
        <RequestForm req={det} meta={meta}
          onClose={() => setEditing(false)}
          onSaved={(nd) => { setDet(nd); setEditing(false); onChanged && onChanged(nd); }} />
      )}
    </Modal>
  );
}
