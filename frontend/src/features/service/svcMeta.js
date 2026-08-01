/* ============================================================
   Hằng số + helper dùng chung của màn Dịch vụ nhân sự. Owner: Nhật Anh.
   Tách riêng để RequestForm / MyRequestsPanel / RequestThread (và InboxPanel
   ở P4) không mỗi nơi map trạng thái một kiểu.
   ============================================================ */

/* Badge trạng thái đơn — khớp STATE_SEL của hocba.hr.request. */
export const STATE_META = {
  new: { kind: 'blue', label: 'Mới' },
  in_progress: { kind: 'amber', label: 'Đang xử lý' },
  answered: { kind: 'green', label: 'Đã trả lời' },
  closed: { kind: 'gray', label: 'Đã đóng' },
  cancelled: { kind: 'gray', label: 'Đã rút' },
};

export const stateMeta = (s) => STATE_META[s] || { kind: 'gray', label: s || '—' };

export const RECIPIENT_LABEL = {
  hr: 'HR',
  manager: 'Trưởng phòng',
  both: 'HR và Trưởng phòng',
};

/* Giới hạn đính kèm — PHẢI trùng ALLOWED_MIME/MAX_SIZE_BYTES/MAX_FILES của
   controllers/main.py. Chặn ở client chỉ để báo lỗi sớm; BE vẫn là nơi chốt. */
export const ALLOWED_MIME = ['application/pdf', 'image/jpeg', 'image/png'];
export const MAX_SIZE = 5 * 1024 * 1024;
export const MAX_FILES = 3;

/* Datetime của Odoo là chuỗi UTC KHÔNG hậu tố ('2026-07-31 09:20:00').
   `new Date(s)` sẽ hiểu là giờ máy ⇒ lệch 7 tiếng ở VN. Thêm 'Z' để ép UTC
   rồi mới để browser đổi về giờ địa phương. */
export function parseDT(s) {
  if (!s) return null;
  const d = new Date(s.includes('T') || s.endsWith('Z') ? s : s.replace(' ', 'T') + 'Z');
  return isNaN(d) ? null : d;
}

const p2 = (n) => String(n).padStart(2, '0');

export function fmtDateTime(s) {
  const d = parseDT(s);
  if (!d) return s || '—';
  return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()} `
    + `${p2(d.getHours())}:${p2(d.getMinutes())}`;
}

export function fmtDateOnly(s) {
  const d = parseDT(s);
  if (!d) return s || '—';
  return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()}`;
}

/* Badge hạn xử lý (SLA) cho hộp thư người xử lý.
   isOverdue do BE tính (state còn mở + deadline < now) — KHÔNG tự suy ở FE để
   hai bên không lệch; ở đây chỉ đếm thêm số ngày còn lại cho đơn chưa trễ.
   Đơn đã kết thúc thì SLA hết ý nghĩa ⇒ trả null. */
export function slaInfo(req) {
  if (req.isOverdue) return { kind: 'red', label: 'Trễ hạn' };
  if (['answered', 'closed', 'cancelled'].includes(req.state)) return null;
  const d = parseDT(req.deadline);
  if (!d) return null;
  const days = Math.ceil((d.getTime() - Date.now()) / 86400000);
  if (days <= 0) return { kind: 'amber', label: 'Hạn hôm nay' };
  return { kind: days <= 1 ? 'amber' : 'green', label: `Còn ${days} ngày` };
}

/* File → base64 (bỏ tiền tố 'data:...;base64,') — cùng cách LeaveForm gửi
   chứng từ y tế. */
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(',')[1] || '');
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

/* Style ô input dùng lại trong form (repo không dùng CSS module cho form). */
export const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
