/* ============================================================
   API client dùng chung — KHÔNG fetch trực tiếp trong component.
   Quy ước: docs/QUY_UOC_FRONTEND.md §5
   ============================================================ */

export class ApiError extends Error {
  // detail = thông điệp người-đọc do BE trả ({"message": "..."}); nếu không có
  // thì rơi về "<status> <code>". `.code` luôn giữ mã máy để xử lý theo nhánh.
  constructor(status, code, detail) {
    super(detail || (code ? `${status} ${code}` : `HTTP ${status}`));
    this.status = status;
    this.code = code;
  }
}

async function errBody(res) {
  try {
    return (await res.json()) || {};
  } catch {
    return {};
  }
}

export async function hbGet(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (res.redirected && res.url.includes('/web/login')) {
    // session hết hạn → sang trang đăng nhập Odoo rồi quay lại đúng trang
    // hiện tại (dev: /hocba_hrm/static/spa/ trên Vite; prod: /hocba-hrm)
    window.location.href = '/web/login?redirect=' + encodeURIComponent(window.location.pathname);
    throw new ApiError(401, 'login_required');
  }
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
  if (!res.ok) {
    const b = await errBody(res);
    throw new ApiError(res.status, b.error, b.message);
  }
  return res.json();
}
