/* Gửi mail tuyển dụng qua Gmail (chuyển hướng) — Owner: Việt.
   Không cần SMTP / dịch vụ ngoài: mở tab Gmail soạn sẵn (to/subject/body) bằng chính
   tài khoản Gmail của người dùng; gửi xong bấm xác nhận để ghi lịch sử (/mail/log-sent).
   Nội dung mail render từ mail mẫu của app (endpoint /preview), HTML được lược thành
   text thuần vì link Gmail compose chỉ nhận body dạng text. */
import { previewMailTemplate, logSentMail } from '../../api/recruitment';

export { logSentMail };

/* HTML → text thuần (giữ xuống dòng) — không phụ thuộc layout nên chạy cả với node rời. */
export function htmlToText(html) {
  let s = html || '';
  s = s
    .replace(/<\s*br\s*\/?>/gi, '\n')
    .replace(/<\/\s*(p|div|tr|li|h[1-6]|table)\s*>/gi, '\n')
    .replace(/<[^>]+>/g, '');
  const ta = document.createElement('textarea');
  ta.innerHTML = s;                 // giải mã &nbsp; &amp; …
  s = ta.value;
  return s.replace(/ /g, ' ').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

/* Link soạn thư Gmail với nội dung điền sẵn. */
export function gmailComposeUrl(to, subject, bodyText) {
  const p = new URLSearchParams({
    view: 'cm', fs: '1', tf: '1',
    to: to || '', su: subject || '', body: bodyText || '',
  });
  return 'https://mail.google.com/mail/?' + p.toString();
}

/* Render nội dung cho 1 ứng viên → { subject, bodyText }.
   override {subject, bodyHtml}: dùng khi đã xem trước & sửa tay; bỏ trống thì tự render. */
export async function renderForGmail(tmplId, applicantId, override) {
  let subject = override ? override.subject : null;
  let bodyHtml = override ? override.bodyHtml : null;
  if (subject == null || bodyHtml == null) {
    const p = await previewMailTemplate(tmplId, applicantId);
    subject = p.subject; bodyHtml = p.bodyHtml;
  }
  return { subject: subject || '', bodyText: htmlToText(bodyHtml) };
}

/* Mở tab Gmail soạn thư cho 1 ứng viên. Trả về true nếu tab mở được (không bị chặn popup). */
export function openGmailCompose(email, subject, bodyText) {
  const w = window.open(gmailComposeUrl(email, subject, bodyText), '_blank', 'noopener');
  return !!w;
}
