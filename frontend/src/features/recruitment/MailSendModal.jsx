/* Modal gửi 1 mail mẫu cho 1 ứng viên — chọn mẫu, xem trước (render điền thông tin),
   chỉnh sửa nội dung rồi gửi. Dùng chung cho tab Offer & tab Danh sách PV. Owner: Việt.
   applicant: { id, name, email, jobName } · templates: [{ id, name }] */
import { useState, useRef } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { sendMailTemplate, previewMailTemplate } from '../../api/recruitment';

export default function MailSendModal({ applicant, templates, onClose }) {
  const [tmplId, setTmplId] = useState(() => (templates[0] ? String(templates[0].id) : ''));
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);
  const [preview, setPreview] = useState(null);   // {subject, bodyHtml, emailTo, key}
  const [previewing, setPreviewing] = useState(false);
  const [subject, setSubject] = useState('');
  const bodyRef = useRef(null);
  const hasEmail = !!applicant.email;

  const onPickTmpl = (v) => { setTmplId(v); setPreview(null); };

  const doPreview = async () => {
    if (!tmplId) { setErr('Vui lòng chọn mẫu mail.'); return; }
    setPreviewing(true); setErr(null);
    try {
      const p = await previewMailTemplate(Number(tmplId), applicant.id);
      setSubject(p.subject || '');
      setPreview({ ...p, key: (preview?.key || 0) + 1 });
    } catch (e) { setErr(e.message || 'Không tạo được bản xem trước.'); } finally { setPreviewing(false); }
  };

  const send = async () => {
    if (!tmplId) { setErr('Vui lòng chọn mẫu mail.'); return; }
    setBusy(true); setErr(null);
    try {
      const override = preview
        ? { subject, bodyHtml: bodyRef.current ? bodyRef.current.innerHTML : preview.bodyHtml }
        : undefined;
      setResult(await sendMailTemplate(Number(tmplId), [applicant.id], override));
    } catch (e) { setErr(e.message || 'Gửi thất bại.'); } finally { setBusy(false); }
  };

  const inp = {
    width: '100%', padding: '9px 12px', borderRadius: 10,
    border: '1px solid var(--border-strong)', background: '#fff',
    fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="mail" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Gửi mail ứng viên</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>{applicant.name}{applicant.jobName ? ' · ' + applicant.jobName : ''}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {result ? (
        <div style={{ padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 8 }}>
            {result.sent ? 'Đã đưa vào hàng đợi gửi' : 'Chưa gửi được'}</div>
          <p className="muted" style={{ margin: 0 }}>
            {result.sent
              ? <>Email tới <b>{applicant.email}</b> sẽ được gửi qua máy chủ thư của hệ thống.</>
              : <>Bỏ qua {result.skipped} (ứng viên chưa có email).</>}
          </p>
          <button className="btn btn-primary" style={{ marginTop: 18 }} onClick={onClose}>Đóng</button>
        </div>
      ) : (
        <>
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="kv"><div className="k">Người nhận</div>
              <div className="v">{applicant.email
                ? applicant.email
                : <span style={{ color: 'var(--red-600)' }}>Ứng viên chưa có email — không gửi được</span>}</div>
            </div>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Mẫu mail</span>
              {templates.length === 0 ? (
                <span className="muted" style={{ fontSize: 13 }}>Chưa có mẫu mail nào. Tạo ở tab "Mail mẫu tuyển dụng".</span>
              ) : (
                <select style={inp} value={tmplId} onChange={(e) => onPickTmpl(e.target.value)}>
                  {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              )}
            </label>
            <div className="muted" style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Icon name="check" size={14} />Bấm "Xem trước" để kiểm tra &amp; chỉnh sửa nội dung trước khi gửi.
            </div>

            {preview && (
              <div style={{ border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden' }}>
                <div style={{ padding: '10px 14px', background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Tới</div>
                  <div style={{ fontSize: 13 }}>{preview.emailTo || '(trống)'}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', marginTop: 8, marginBottom: 3 }}>Tiêu đề</div>
                  <input value={subject} onChange={(e) => setSubject(e.target.value)}
                    style={{ width: '100%', padding: '6px 9px', borderRadius: 8, border: '1px solid var(--border-strong)', background: '#fff', fontSize: 13.5, fontWeight: 600, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit' }} />
                </div>
                <div style={{ padding: '8px 10px' }}>
                  <div className="muted" style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', margin: '2px 4px 6px' }}>Nội dung (có thể sửa)</div>
                  <div
                    key={preview.key}
                    ref={bodyRef}
                    contentEditable
                    suppressContentEditableWarning
                    style={{ padding: '12px 14px', minHeight: 120, maxHeight: '34vh', overflowY: 'auto', fontSize: 13.5, lineHeight: 1.6, border: '1px solid var(--border-strong)', borderRadius: 8, outline: 'none', background: '#fff' }}
                    dangerouslySetInnerHTML={{ __html: preview.bodyHtml || '<p>(Nội dung trống)</p>' }} />
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            {err && <span style={{ color: 'var(--red-600)', fontSize: 12.5, marginRight: 'auto', alignSelf: 'center' }}>{err}</span>}
            <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
            <button className="btn btn-soft" onClick={doPreview} disabled={previewing || busy || !tmplId}>
              <Icon name="search" size={16} />{previewing ? 'Đang tạo…' : 'Xem trước'}</button>
            <button className="btn btn-primary" onClick={send} disabled={busy || !tmplId || !hasEmail}>
              <Icon name="mail" size={16} />{busy ? 'Đang gửi…' : 'Gửi mail'}</button>
          </div>
        </>
      )}
    </Modal>
  );
}
