/* ============================================================
   Chi tiết 1 đơn dịch vụ + hội thoại 2 chiều. Owner: Nhật Anh. Spec §7.2.
   Dùng chung cho CẢ HAI phía:
     role='sender'  → MyRequestsPanel (P3): trả lời, rút đơn, đóng đơn.
     role='handler' → InboxPanel (P4): nhận xử lý, ghi chú nội bộ, chốt, đóng.
   Payload lấy từ GET /service/request/<id> — BE đã lọc tin nội bộ và ẩn danh
   tính (BR-SVC-07/08), SPA KHÔNG tự lọc lại để hai lớp không lệch nhau.
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { LoadingState, ErrorState } from '../../components/states';
import {
  fetchRequest, replyRequest, cancelRequest,
  claimRequest, answerRequest, closeRequest,
} from '../../api/service';
import { RECIPIENT_LABEL, fmtDateTime, inp, stateMeta } from './svcMeta';

/* 1 bong bóng tin nhắn. Tin của "phía mình" đẩy sang phải. */
function Bubble({ msg, role }) {
  const mine = msg.authorRole === role;
  const internal = msg.isInternal;
  return (
    <div style={{ display: 'flex', justifyContent: mine ? 'flex-end' : 'flex-start' }}>
      <div style={{
        maxWidth: '78%', padding: '9px 13px', borderRadius: 12, fontSize: 13.5,
        lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        border: '1px solid ' + (internal ? 'var(--gold-500)' : mine ? 'var(--red-100)' : 'var(--border)'),
        background: internal ? '#fffdf5' : mine ? 'var(--red-50)' : '#fff',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
          <b style={{ fontSize: 12 }}>{msg.authorName}</b>
          {internal && <Badge kind="gold">Ghi chú nội bộ</Badge>}
          <span className="muted mono" style={{ fontSize: 11 }}>{fmtDateTime(msg.createdAt)}</span>
        </div>
        {msg.body}
      </div>
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div style={{ display: 'flex', gap: 8, fontSize: 12.5 }}>
      <span className="muted" style={{ minWidth: 96 }}>{label}</span>
      <span style={{ flex: 1 }}>{children}</span>
    </div>
  );
}

export default function RequestThread({ requestId, role = 'sender', onClose, onChanged }) {
  const [req, setReq] = useState(null);
  const [err, setErr] = useState(null);
  const [text, setText] = useState('');
  const [internal, setInternal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actErr, setActErr] = useState(null);
  const [closing, setClosing] = useState(false);   // đang mở ô nhập lý do đóng
  const [reason, setReason] = useState('');

  const load = useCallback(() => {
    setErr(null);
    fetchRequest(requestId).then(setReq).catch((e) => setErr(e.message));
  }, [requestId]);
  useEffect(() => { load(); }, [load]);

  /* Mọi thao tác đều trả về payload đơn MỚI ⇒ dùng luôn, không load lại. */
  const run = (promise) => {
    setBusy(true); setActErr(null);
    return promise
      .then((d) => { setReq(d); onChanged && onChanged(); return d; })
      .catch((e) => { setActErr(e.message); throw e; })
      .finally(() => setBusy(false));
  };

  const send = () => {
    const b = text.trim();
    if (!b) { setActErr('Nội dung trả lời không được để trống.'); return; }
    run(replyRequest(requestId, b, role === 'handler' && internal))
      .then(() => { setText(''); setInternal(false); })
      .catch(() => {});
  };

  const doClose = () => {
    run(closeRequest(requestId, reason.trim()))
      .then(() => { setClosing(false); setReason(''); })
      .catch(() => {});
  };

  if (err) return (
    <Modal onClose={onClose}>
      <ModalHeader icon="mail" title="Chi tiết đơn" onClose={onClose} />
      <ErrorState message={err} onRetry={load} />
    </Modal>
  );
  if (!req) return (
    <Modal onClose={onClose}>
      <ModalHeader icon="mail" title="Chi tiết đơn" onClose={onClose} />
      <LoadingState label="Đang tải đơn…" />
    </Modal>
  );

  const st = stateMeta(req.state);
  const msgs = req.messages || [];
  // action_answer đòi ≥1 tin của người xử lý KHÔNG phải ghi chú nội bộ
  // (BR-SVC-05) → nói trước ở nút thay vì để người dùng bấm rồi ăn lỗi.
  const hasPublicReply = msgs.some((m) => m.authorRole === 'handler' && !m.isInternal);

  const isHandler = role === 'handler';
  const canClaim = isHandler && req.state === 'new';
  const canAnswer = isHandler && req.state === 'in_progress';
  const canCloseNow = ['new', 'in_progress', 'answered'].includes(req.state)
    && (isHandler || req.state === 'answered');
  const canCancel = !isHandler && req.state === 'new';

  return (
    <Modal onClose={onClose} lg>
      <ModalHeader lg icon="mail" title={req.subject}
        sub={`${req.name} · ${req.typeName}`} onClose={onClose}>
        <Badge kind={st.kind} dot>{st.label}</Badge>
        {req.isAnonymous && <Badge kind="violet">Ẩn danh</Badge>}
        {req.isOverdue && <Badge kind="red">Trễ hạn</Badge>}
        {req.priority === 'urgent' && <Badge kind="amber">Gấp</Badge>}
      </ModalHeader>

      <div style={{ padding: '16px 24px', maxHeight: '60vh', overflowY: 'auto', display: 'grid', gap: 16 }}>
        {/* ---- Thông tin đơn ------------------------------------------- */}
        <div style={{ display: 'grid', gap: 6 }}>
          <Row label="Người gửi">
            {req.senderName}
            {req.departmentName ? ` · ${req.departmentName}` : ''}
          </Row>
          <Row label="Gửi tới">{RECIPIENT_LABEL[req.recipientScope] || req.recipientScope}</Row>
          <Row label="Gửi lúc">{fmtDateTime(req.createdAt)}</Row>
          <Row label="Hạn xử lý">
            <span style={req.isOverdue ? { color: 'var(--red-700)', fontWeight: 700 } : undefined}>
              {fmtDateTime(req.deadline)}
            </span>
          </Row>
          {req.handlerName && <Row label="Người xử lý">{req.handlerName}</Row>}
          {req.rating && <Row label="Điểm đánh giá">{req.rating}/5 ★</Row>}
          {req.answeredAt && <Row label="Trả lời lúc">{fmtDateTime(req.answeredAt)}</Row>}
          {req.closedAt && <Row label="Đóng lúc">{fmtDateTime(req.closedAt)}</Row>}
          {req.closedReason && <Row label="Lý do đóng">{req.closedReason}</Row>}
        </div>

        {/* ---- Nội dung gốc ------------------------------------------- */}
        <div style={{
          padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 11,
          background: 'var(--surface-2, #f7f8fa)', fontSize: 13.5, lineHeight: 1.6,
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        }}>{req.body}</div>

        {/* ---- Đính kèm (đơn ẩn danh luôn rỗng — BR-SVC-02) ----------- */}
        {(req.attachments || []).length > 0 && (
          <div style={{ display: 'grid', gap: 7 }}>
            {req.attachments.map((a) => (
              <a key={a.id} href={a.url} target="_blank" rel="noreferrer"
                style={{
                  display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5,
                  padding: '7px 11px', border: '1px solid var(--border)',
                  borderRadius: 9, color: 'var(--ink)', textDecoration: 'none',
                }}>
                <Icon name="file" size={15} />
                <span style={{ flex: 1 }}>{a.name}</span>
                <Icon name="download" size={15} />
              </a>
            ))}
          </div>
        )}

        {/* ---- Hội thoại ---------------------------------------------- */}
        <div style={{ display: 'grid', gap: 9 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
            Hội thoại ({msgs.length})
          </div>
          {msgs.length === 0 && (
            <div className="muted" style={{ fontSize: 12.5 }}>
              {isHandler
                ? 'Chưa có trao đổi nào — trả lời người gửi ở ô bên dưới.'
                : 'Chưa có phản hồi. Bạn sẽ nhận thông báo khi có người trả lời.'}
            </div>
          )}
          {msgs.map((m) => <Bubble key={m.id} msg={m} role={role} />)}
        </div>

        {/* ---- Ô trả lời ---------------------------------------------- */}
        {req.canReply && (
          <div style={{ display: 'grid', gap: 8 }}>
            <textarea rows={3} style={{ ...inp, resize: 'vertical' }} value={text}
              onChange={(e) => { setText(e.target.value); setActErr(null); }}
              placeholder={internal ? 'Ghi chú nội bộ — người gửi KHÔNG đọc được…' : 'Nhập trả lời…'} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {isHandler && (
                <label style={{ display: 'flex', gap: 7, alignItems: 'center', cursor: 'pointer', fontSize: 12.5 }}>
                  <input type="checkbox" checked={internal}
                    onChange={(e) => setInternal(e.target.checked)}
                    style={{ width: 15, height: 15, cursor: 'pointer' }} />
                  Ghi chú nội bộ (người gửi không thấy)
                </label>
              )}
              <div style={{ flex: 1 }} />
              <button className="btn btn-primary btn-sm" onClick={send} disabled={busy}>
                <Icon name="send" size={14} />{busy ? '…' : 'Gửi'}
              </button>
            </div>
          </div>
        )}

        {/* ---- Ô lý do đóng đơn --------------------------------------- */}
        {closing && (
          <div style={{ display: 'grid', gap: 8 }}>
            <textarea rows={2} style={{ ...inp, resize: 'vertical' }} value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Lý do đóng đơn (không bắt buộc)…" />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setClosing(false)} disabled={busy}>Bỏ</button>
              <button className="btn btn-primary btn-sm" onClick={doClose} disabled={busy}>
                {busy ? '…' : 'Xác nhận đóng'}
              </button>
            </div>
          </div>
        )}

        {actErr && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {actErr}
          </div>
        )}
      </div>

      {/* ---- Thanh thao tác ------------------------------------------- */}
      <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ flex: 1 }} />
        {canCancel && (
          <button className="btn btn-ghost" disabled={busy}
            onClick={() => run(cancelRequest(requestId)).catch(() => {})}>
            <Icon name="x" size={15} />Rút đơn
          </button>
        )}
        {canCloseNow && !closing && (
          <button className="btn btn-ghost" disabled={busy} onClick={() => setClosing(true)}>
            <Icon name="checkCircle" size={15} />Đóng đơn
          </button>
        )}
        {canClaim && (
          <button className="btn btn-primary" disabled={busy}
            onClick={() => run(claimRequest(requestId)).catch(() => {})}>
            <Icon name="checkCircle" size={15} />Nhận xử lý
          </button>
        )}
        {/* base.css KHÔNG có .btn:disabled ⇒ nút disabled vẫn trông bấm được;
            dim tại chỗ + nói lý do bằng chữ (tooltip thì phải hover mới thấy). */}
        {canAnswer && !hasPublicReply && (
          <span className="muted" style={{ fontSize: 12 }}>
            Trả lời người gửi ít nhất 1 lần rồi mới chốt được.
          </span>
        )}
        {canAnswer && (
          <button className="btn btn-primary" disabled={busy || !hasPublicReply}
            style={hasPublicReply ? undefined : { opacity: .45, cursor: 'not-allowed' }}
            title={hasPublicReply ? '' : 'Phải trả lời người gửi ít nhất 1 lần (ghi chú nội bộ không tính).'}
            onClick={() => run(answerRequest(requestId)).catch(() => {})}>
            <Icon name="send" size={15} />Chốt đã trả lời
          </button>
        )}
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
