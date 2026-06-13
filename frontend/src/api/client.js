/* ============================================================
   API client dùng chung — KHÔNG fetch trực tiếp trong component.
   Quy ước: docs/QUY_UOC_FRONTEND.md §5
   ============================================================ */

export class ApiError extends Error {
  constructor(status, code) {
    super(code ? `${status} ${code}` : `HTTP ${status}`);
    this.status = status;
    this.code = code;
  }
}

async function safeCode(res) {
  try {
    const body = await res.json();
    return body && body.error;
  } catch {
    return null;
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
  if (!res.ok) throw new ApiError(res.status, await safeCode(res));
  return res.json();
}

export async function hbPost(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload ?? {}),
  });
  if (!res.ok) throw new ApiError(res.status, await safeCode(res));
  return res.json();
}
