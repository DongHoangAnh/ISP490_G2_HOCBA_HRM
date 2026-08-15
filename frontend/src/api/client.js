/* ============================================================
   API client dùng chung — KHÔNG fetch trực tiếp trong component.
   Quy ước: docs/QUY_UOC_FRONTEND.md §5
   ============================================================ */

export class ApiError extends Error {
  // detail = thông điệp người-đọc do BE trả ({"message": "..."}); nếu không có
  // thì rơi về "<status> <code>". `.code` luôn giữ mã máy để xử lý theo nhánh.
  // details = danh sách dòng lỗi chi tiết (BE trả {"details": [...]}), dùng cho
  // các luồng import file: message là câu tóm tắt, details liệt kê từng dòng sai.
  constructor(status, code, detail, details) {
    super(detail || (code ? `${status} ${code}` : `HTTP ${status}`));
    this.status = status;
    this.code = code;
    this.details = details || [];
  }
}

async function errBody(res) {
  try {
    return (await res.json()) || {};
  } catch {
    return {};
  }
}

/* Hết phiên đăng nhập: Odoo đá request sang /web/login và trả 200 kèm HTML,
   nên res.ok vẫn true. Không chặn ở đây thì res.json() ném SyntaxError và người
   dùng nhận câu "Unexpected token '<'…" giữa lúc đang lưu form. */
function throwIfLoggedOut(res) {
  if (res.redirected && res.url.includes('/web/login')) {
    throw new ApiError(401, 'login_required',
      'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
  }
}

export async function hbGet(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  throwIfLoggedOut(res);
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message);
  }
  return res.json();
}

export async function hbPost(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload ?? {}),
  });
  throwIfLoggedOut(res);
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message);
  }
  return res.json();
}

/* Upload file (multipart/form-data) — không set Content-Type để browser tự thêm boundary. */
export async function hbUpload(url, file, field = 'file') {
  const fd = new FormData();
  fd.append(field, file);
  const res = await fetch(url, { method: 'POST', credentials: 'same-origin', body: fd });
  throwIfLoggedOut(res);
  if (!res.ok) throw new ApiError(res.status, await safeCode(res));
  return res.json();
}

/* Upload kèm field phụ + giữ nguyên message/details lỗi của BE (luồng import
   file Excel: cần liệt kê từng dòng sai cho người dùng sửa). */
export async function hbUploadFields(url, file, fields = {}, field = 'file') {
  const fd = new FormData();
  fd.append(field, file);
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  const res = await fetch(url, { method: 'POST', credentials: 'same-origin', body: fd });
  throwIfLoggedOut(res);
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message, b.details);
  }
  return res.json();
}

export async function hbPut(url, payload) {
  const res = await fetch(url, {
    method: 'PUT',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload ?? {}),
  });
  throwIfLoggedOut(res);
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message);
  }
  return res.json();
}

export async function hbDelete(url) {
  const res = await fetch(url, {
    method: 'DELETE',
    credentials: 'same-origin',
  });
  throwIfLoggedOut(res);
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message);
  }
  return res.json();
}

