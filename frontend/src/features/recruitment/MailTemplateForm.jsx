/* Form Thêm / Sửa mail mẫu tuyển dụng — Owner: Việt.
   model cố định hr.applicant (BE set). Hỗ trợ placeholder {{ object.* }}. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState } from '../../components/states';
import { fetchMailTemplate, createMailTemplate, updateMailTemplate } from '../../api/recruitment';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const lbl = { fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 5, display: 'block' };

export default function MailTemplateForm({ tmpl, onClose, onSaved }) {
  const isEdit = !!tmpl;
  const [f, setF] = useState({ name: tmpl?.name || '', subject: tmpl?.subject || '', bodyHtml: '' });
  const [loading, setLoading] = useState(isEdit);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  useEffect(() => {
    if (isEdit) fetchMailTemplate(tmpl.id)
      .then((d) => { setF({ name: d.name, subject: d.subject, bodyHtml: d.bodyHtml }); setLoading(false); })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, []);

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập tên mẫu.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateMailTemplate(tmpl.id, f) : await createMailTemplate(f);
      onSaved(det);
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="mail" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa mail mẫu' : 'Thêm mail mẫu'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Mẫu áp dụng cho ứng viên (hr.applicant)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        {loading ? <LoadingState label="Đang tải mẫu…" /> : (
          <>
            <div style={{ marginBottom: 16 }}>
              <span style={lbl}>Tên mẫu *</span>
              <input style={inp} value={f.name} onChange={set('name')} placeholder="VD: Thư mời phỏng vấn - Học Bá" />
            </div>
            <div style={{ marginBottom: 16 }}>
              <span style={lbl}>Tiêu đề email</span>
              <input style={inp} value={f.subject} onChange={set('subject')} placeholder="[HỌC BÁ] - THƯ MỜI..." />
            </div>
            <div>
              <span style={lbl}>Nội dung (HTML)</span>
              <textarea style={{ ...inp, minHeight: 240, resize: 'vertical', fontFamily: 'monospace', fontSize: 12.5 }}
                value={f.bodyHtml} onChange={set('bodyHtml')} placeholder="<p>Thân gửi {{ object.partner_name }}…</p>" />
              <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>
                Placeholder: <code>{'{{ object.partner_name }}'}</code>, <code>{'{{ object.job_id.name }}'}</code>, <code>{'{{ object.email_from }}'}</code>…
              </div>
            </div>
          </>
        )}
        {err && (
          <div style={{ marginTop: 12, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || loading}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo mẫu')}
        </button>
      </div>
    </Modal>
  );
}
