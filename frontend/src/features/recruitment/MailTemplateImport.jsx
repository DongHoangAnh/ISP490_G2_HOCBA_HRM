/* Import mail mẫu — Owner: Việt.
   Dán nguyên lá mail đang dùng (Word / Gmail / sheet 7.7 của Học Bá) → tự tách
   tiêu đề, dựng HTML, nhận diện placeholder tiếng Việt `[Tên ứng viên]` thành
   thẻ điền tự động. Bổ sung cho nhập tay (MailTemplateForm), cùng khuôn với
   SlotImport: dán → xem trước → tạo. */
import { useState, useMemo, useRef } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createMailTemplate } from '../../api/recruitment';
import { bracketsToTokens, textToHtml, toOdoo, storedToEditor } from './mailTokens';
import { readMailFile, ACCEPT } from './mailFileRead';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const lbl = { fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 5, display: 'block' };

const SAMPLE = `[HỌC BÁ EDUCATION] - THƯ MỜI THAM GIA PHỎNG VẤN VỊ TRÍ [TÊN VỊ TRÍ]

Thân gửi bạn [Tên ứng viên],

Cảm ơn bạn đã ứng tuyển vào vị trí [Tên vị trí tuyển dụng] tại Học Bá Education.
Thời gian phỏng vấn: [giờ], ngày [Ngày phỏng vấn]

Trân trọng,
Bộ phận Tuyển dụng — Học Bá Education`;

export default function MailTemplateImport({ onClose, onSaved }) {
  const [name, setName] = useState('');
  const [raw, setRaw] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [fileName, setFileName] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  /* File → văn bản, rồi đi tiếp đúng luồng của ô dán (một đường xử lý duy nhất,
     khỏi phải kiểm hai nhánh riêng). Tên mẫu để trống thì lấy tạm tên file. */
  const takeFile = async (file) => {
    if (!file) return;
    setErr(null);
    try {
      const text = await readMailFile(file);
      if (!text.trim()) { setErr('File không có nội dung chữ nào.'); return; }
      setRaw(text);
      setFileName(file.name);
      setName((p) => p || file.name.replace(/\.[^.]+$/, ''));
    } catch (e) {
      setErr(e.message || 'Không đọc được file.');
    }
  };

  /* Dòng đầu tiên có chữ = tiêu đề, phần còn lại = nội dung. Đúng bố cục 4 mẫu
     thật của Học Bá (sheet 7.7): dòng 1 luôn là "[HỌC BÁ EDUCATION] - ...". */
  const parsed = useMemo(() => {
    const lines = (raw || '').replace(/\r\n?/g, '\n').split('\n');
    let i = 0;
    while (i < lines.length && !lines[i].trim()) i++;
    const subjectRaw = (lines[i] || '').trim();
    const bodyRaw = lines.slice(i + 1).join('\n').trim();

    const s = bracketsToTokens(subjectRaw);
    const b = bracketsToTokens(bodyRaw);
    const seen = new Set();
    const matched = [...s.matched, ...b.matched].filter(([g, l]) => {
      const k = g + '→' + l;
      if (seen.has(k)) return false;
      seen.add(k); return true;
    });
    const skipped = [...new Set([...s.skipped, ...b.skipped])];
    return {
      subject: s.text,
      bodyHtml: textToHtml(b.text),
      matched,
      skipped,
      empty: !subjectRaw && !bodyRaw,
    };
  }, [raw]);

  const submit = async () => {
    if (!name.trim()) { setErr('Vui lòng đặt tên mẫu.'); return; }
    if (parsed.empty) { setErr('Chưa dán nội dung mail.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = await createMailTemplate({
        name: name.trim(),
        subject: toOdoo(parsed.subject),
        bodyHtml: toOdoo(parsed.bodyHtml),
      });
      onSaved(det);
    } catch (e) { setErr(e.message || 'Tạo mẫu thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="upload" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>Import mail mẫu</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            Dán nguyên lá mail đang dùng — hệ thống tự tách tiêu đề và nhận diện chỗ điền
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '62vh', overflowY: 'auto' }}>
        <div style={{ marginBottom: 16 }}>
          <span style={lbl}>Tên mẫu *</span>
          <input style={inp} value={name} onChange={(e) => setName(e.target.value)}
            placeholder="VD: Thư mời phỏng vấn - Học Bá" />
        </div>

        <div style={{ marginBottom: 16 }}>
          <span style={lbl}>Chọn file mail mẫu</span>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault(); setDragOver(false);
              takeFile(e.dataTransfer.files && e.dataTransfer.files[0]);
            }}
            onClick={() => fileRef.current && fileRef.current.click()}
            style={{
              padding: '18px 16px', borderRadius: 11, textAlign: 'center', cursor: 'pointer',
              border: '1.5px dashed ' + (dragOver ? 'var(--red-600)' : 'var(--border-strong)'),
              background: dragOver ? 'var(--red-50)' : 'var(--surface-2)',
              transition: 'background .12s, border-color .12s',
            }}>
            <Icon name="upload" size={20} className="faint" />
            <div style={{ fontSize: 13, fontWeight: 600, marginTop: 6 }}>
              {fileName || 'Bấm để chọn file, hoặc kéo thả vào đây'}
            </div>
            <div className="muted" style={{ fontSize: 11.5, marginTop: 3 }}>
              Hỗ trợ .docx · .txt · .html · .eml — nội dung sẽ hiện ở ô bên dưới để bạn sửa trước khi tạo
            </div>
          </div>
          <input ref={fileRef} type="file" accept={ACCEPT} style={{ display: 'none' }}
            onChange={(e) => { takeFile(e.target.files && e.target.files[0]); e.target.value = ''; }} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <div className="between" style={{ marginBottom: 5 }}>
            <span style={{ ...lbl, marginBottom: 0 }}>Nội dung mail {fileName ? '(đọc từ file, sửa được)' : '(hoặc dán trực tiếp)'}</span>
            <button type="button" className="btn btn-ghost" style={{ fontSize: 11.5, padding: '3px 9px' }}
              onClick={() => { setRaw(SAMPLE); setFileName(''); }}>Dán thử mẫu ví dụ</button>
          </div>
          <textarea style={{ ...inp, minHeight: 200, resize: 'vertical', fontSize: 13 }}
            value={raw} onChange={(e) => setRaw(e.target.value)}
            placeholder={'Dòng đầu tiên là TIÊU ĐỀ, các dòng sau là nội dung.\n\nCopy thẳng từ Word / Gmail / file Excel rồi dán vào đây.'} />
          <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>
            Dòng đầu tiên được lấy làm <b>tiêu đề email</b>. Dòng trống ngăn cách các đoạn.
          </div>
        </div>

        {!parsed.empty && (
          <>
            <div style={{ marginBottom: 14 }}>
              <span style={lbl}>Chỗ điền tự động nhận ra được</span>
              {parsed.matched.length === 0 ? (
                <div className="muted" style={{ fontSize: 12.5 }}>
                  Không tìm thấy chỗ nào — mẫu vẫn tạo được, sau đó bạn tự chèn bằng nút trong form sửa.
                </div>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                  {parsed.matched.map(([orig, label]) => (
                    <span key={orig + label} style={{ fontSize: 12, padding: '3px 8px', borderRadius: 7, background: '#ecfdf5', border: '1px solid #a7f3d0' }}>
                      <code>{orig}</code> → <b>[{label}]</b>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {parsed.skipped.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <span style={lbl}>Giữ nguyên (không phải chỗ điền)</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                  {parsed.skipped.map((s) => (
                    <code key={s} style={{ fontSize: 12, padding: '3px 8px', borderRadius: 7, background: 'var(--surface-2)', border: '1px solid var(--border)' }}>{s}</code>
                  ))}
                </div>
                <div className="muted" style={{ fontSize: 11.5, marginTop: 5 }}>
                  Những chỗ này để nguyên vì là chữ thật trong mail, hoặc hệ thống chưa có dữ liệu tương ứng.
                </div>
              </div>
            )}

            <div>
              <span style={lbl}>Xem trước</span>
              <div style={{ border: '1px solid var(--border-strong)', borderRadius: 10, overflow: 'hidden' }}>
                <div style={{ padding: '9px 13px', background: 'var(--surface-2)', borderBottom: '1px solid var(--border)', fontSize: 13, fontWeight: 700 }}
                  dangerouslySetInnerHTML={{ __html: storedToEditor(toOdoo(parsed.subject)) || '(không có tiêu đề)' }} />
                <div style={{ padding: '12px 14px', fontSize: 13.5, lineHeight: 1.7, maxHeight: 220, overflowY: 'auto', background: '#fff' }}
                  dangerouslySetInnerHTML={{ __html: storedToEditor(toOdoo(parsed.bodyHtml)) }} />
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
        <button className="btn btn-primary" onClick={submit} disabled={busy || parsed.empty}>
          <Icon name="plus" size={16} />{busy ? 'Đang tạo…' : 'Tạo mẫu'}
        </button>
      </div>
    </Modal>
  );
}
