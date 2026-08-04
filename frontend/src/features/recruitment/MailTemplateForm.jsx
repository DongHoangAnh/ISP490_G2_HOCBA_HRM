/* Form Thêm / Sửa mail mẫu tuyển dụng — Owner: Việt.
   model cố định hr.applicant (BE set).

   HR không viết được HTML nên mặc định là ô soạn thảo TRỰC QUAN
   (contentEditable, cùng pattern với MailSendModal) + nút chèn thẻ tiếng Việt.
   Cú pháp Odoo `{{ object.* }}` được dịch qua lại ở mailTokens.js, DB vẫn lưu
   đúng cú pháp gốc. Giữ "Chế độ HTML" cho ai cần chỉnh sâu. */
import { useState, useEffect, useRef } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState } from '../../components/states';
import { fetchMailTemplate, createMailTemplate, updateMailTemplate } from '../../api/recruitment';
import { TOKENS, toFriendly, toOdoo, tokenSpan, editorToStored, storedToEditor } from './mailTokens';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const lbl = { fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 5, display: 'block' };
const toolBtn = {
  padding: '4px 9px', borderRadius: 7, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 12, cursor: 'pointer', fontFamily: 'inherit',
  color: 'var(--ink)',
};

const STARTER = `<p>Thân gửi bạn ${tokenSpan('Họ tên ứng viên')},</p>`
  + `<p>[Viết nội dung của bạn ở đây.]</p>`
  + `<p>Trân trọng,<br><strong>Bộ phận Tuyển dụng — Học Bá Education</strong></p>`;

export default function MailTemplateForm({ tmpl, onClose, onSaved }) {
  const isEdit = !!tmpl;
  const [f, setF] = useState({ name: tmpl?.name || '', subject: tmpl?.subject || '' });
  const [loading, setLoading] = useState(isEdit);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [htmlMode, setHtmlMode] = useState(false);
  const [raw, setRaw] = useState('');          // nội dung ở chế độ HTML (cú pháp Odoo)
  const [editorHtml, setEditorHtml] = useState(isEdit ? '' : STARTER);
  const [editorKey, setEditorKey] = useState(0);   // ép React nạp lại contentEditable
  const bodyRef = useRef(null);
  const subjRef = useRef(null);
  /* Ô tiêu đề là <input> nên thẻ không mang được data-expr như bên nội dung.
     Nhớ biểu thức gốc theo nhãn để lưu lại đúng bản gốc, không quy về dạng
     chuẩn làm mất phần dự phòng (vd `or 'bạn'`). */
  const subjMemo = useRef({});
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  useEffect(() => {
    if (!isEdit) return;
    fetchMailTemplate(tmpl.id)
      .then((d) => {
        subjMemo.current = {};
        setF({ name: d.name, subject: toFriendly(d.subject, subjMemo.current) });
        setRaw(d.bodyHtml || '');
        setEditorHtml(storedToEditor(d.bodyHtml));
        setEditorKey((k) => k + 1);
        setLoading(false);
      })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, []);

  /* Nội dung hiện hành, quy về HTML đúng cú pháp Odoo để lưu/đổi chế độ. */
  const currentStored = () => (htmlMode
    ? raw
    : editorToStored(bodyRef.current ? bodyRef.current.innerHTML : editorHtml));

  const toggleMode = () => {
    if (htmlMode) {                       // HTML → trực quan
      setEditorHtml(storedToEditor(raw));
      setEditorKey((k) => k + 1);
    } else {                              // trực quan → HTML
      setRaw(currentStored());
    }
    setHtmlMode(!htmlMode);
  };

  const exec = (cmd) => document.execCommand(cmd, false, null);

  const insertToken = (label) => {
    const el = bodyRef.current;
    if (!el) return;
    el.focus();
    document.execCommand('insertHTML', false, tokenSpan(label) + '&nbsp;');
  };

  /* Tiêu đề là <input> thường ⇒ chèn tại vị trí con trỏ, không dùng execCommand. */
  const insertTokenSubject = (label) => {
    const el = subjRef.current;
    const s = el && el.selectionStart != null ? el.selectionStart : f.subject.length;
    const e = el && el.selectionEnd != null ? el.selectionEnd : s;
    const next = f.subject.slice(0, s) + `[${label}]` + f.subject.slice(e);
    setF((p) => ({ ...p, subject: next }));
    setTimeout(() => {
      if (!el) return;
      const pos = s + label.length + 2;
      el.focus(); el.setSelectionRange(pos, pos);
    }, 0);
  };

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập tên mẫu.'); return; }
    setBusy(true); setErr(null);
    const payload = {
      name: f.name,
      subject: toOdoo(f.subject, subjMemo.current),
      bodyHtml: currentStored(),
    };
    try {
      const det = isEdit ? await updateMailTemplate(tmpl.id, payload)
        : await createMailTemplate(payload);
      onSaved(det);
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); } finally { setBusy(false); }
  };

  const TokenBar = ({ onPick }) => (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
      <span className="muted" style={{ fontSize: 11.5, alignSelf: 'center' }}>Chèn:</span>
      {TOKENS.map((t) => (
        <button key={t.label} type="button" style={toolBtn}
          onMouseDown={(ev) => ev.preventDefault()}   /* giữ con trỏ trong ô soạn */
          onClick={() => onPick(t.label)}>+ {t.label}</button>
      ))}
    </div>
  );

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="mail" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa mail mẫu' : 'Thêm mail mẫu'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Mẫu email gửi cho ứng viên tuyển dụng</div>
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
              <TokenBar onPick={insertTokenSubject} />
              <input ref={subjRef} style={inp} value={f.subject} onChange={set('subject')}
                placeholder="VD: [HỌC BÁ EDUCATION] - THƯ MỜI PHỎNG VẤN VỊ TRÍ [Vị trí ứng tuyển]" />
            </div>

            <div>
              <div className="between" style={{ marginBottom: 5 }}>
                <span style={{ ...lbl, marginBottom: 0 }}>Nội dung email</span>
                <button type="button" style={{ ...toolBtn, fontSize: 11.5 }} onClick={toggleMode}>
                  {htmlMode ? '← Soạn trực quan' : 'Chế độ HTML'}
                </button>
              </div>

              {htmlMode ? (
                <textarea style={{ ...inp, minHeight: 260, resize: 'vertical', fontFamily: 'monospace', fontSize: 12.5 }}
                  value={raw} onChange={(e) => setRaw(e.target.value)} />
              ) : (
                <>
                  <TokenBar onPick={insertToken} />
                  <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                    <button type="button" style={{ ...toolBtn, fontWeight: 800, width: 32 }}
                      onMouseDown={(ev) => ev.preventDefault()} onClick={() => exec('bold')} title="Đậm">B</button>
                    <button type="button" style={{ ...toolBtn, fontStyle: 'italic', width: 32 }}
                      onMouseDown={(ev) => ev.preventDefault()} onClick={() => exec('italic')} title="Nghiêng">I</button>
                    <button type="button" style={toolBtn}
                      onMouseDown={(ev) => ev.preventDefault()} onClick={() => exec('insertUnorderedList')}>• Gạch đầu dòng</button>
                  </div>
                  <div
                    key={editorKey}
                    ref={bodyRef}
                    contentEditable
                    suppressContentEditableWarning
                    style={{
                      padding: '14px 16px', minHeight: 260, maxHeight: '38vh', overflowY: 'auto',
                      fontSize: 13.5, lineHeight: 1.7, border: '1px solid var(--border-strong)',
                      borderRadius: 10, outline: 'none', background: '#fff',
                    }}
                    dangerouslySetInnerHTML={{ __html: editorHtml }} />
                </>
              )}

              <div className="muted" style={{ fontSize: 11.5, marginTop: 7, lineHeight: 1.6 }}>
                Bấm nút <b>Chèn</b> để thêm thông tin tự động — khi gửi, các ô vàng
                sẽ được thay bằng dữ liệu thật của từng ứng viên.
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
