# Tích hợp CMS (cms.dangch.tech) vào HRM — Cách A (qua API)

Nối CMS `https://cms.dangch.tech` vào dự án HRM **qua REST API** (không nối thẳng MySQL).

## ĐÃ KHÁM PHÁ ĐƯỢC (2026-06-23)

`cms.dangch.tech` **KHÔNG phải** CMS đóng gói (Strapi/Directus/Ghost/WP). Nó là một
**web ERP/CMS tự code**:

- Frontend: **React 19 + Vite** (đang chạy DEV mode, expose qua Cloudflare) + Ant Design 5
  + Redux + React Router + Google OAuth.
- Backend: **microservices qua API gateway** (`cms-repo-api-gateway:8080`), có service
  `auth` (Java, JWT RS256) và service `id` (identity). Gateway proxy dưới `/api/*`.

### Kết nối API (đã test chạy ✓)

| Mục | Giá trị |
|-----|---------|
| Base API | `https://cms.dangch.tech/api` |
| Đăng nhập | `POST /api/auth/login`  body `{"email","password"}` |
| Trả về | `{ data: { accessToken, refreshToken } }` — JWT RS256 |
| Auth các API sau | header `Authorization: Bearer <accessToken>` |
| Hết hạn token | ~60 phút (dùng `refreshToken` để gia hạn) |
| Tài khoản admin | `admin@local.com` (role `ROLE_ADMIN`) — mật khẩu đặt qua env `CMS_ADMIN_PASSWORD`, không lưu trong repo |

Endpoint thấy trong source frontend (đường dẫn theo code — gateway có thể rewrite prefix,
cần dò lại từng cái): `/api/auth/signup`, `/api/auth/google`, `/api/auth/forgot-password`,
`/api/auth/reset-password`, `/api/auth/set-password`, `/api/auth/email/otp/send|verify`,
`/api/auth/profile`, `/api/id/users/me`, `/api/id/auth/logout`.

> Lưu ý: `/api/id/users/me` và `/api/auth/profile` hiện trả 404 khi gọi trực tiếp →
> gateway map prefix khác đường dẫn trong code. Cần dò đúng route trước khi dùng.

## Chạy lại để kiểm tra / lấy token

```bash
python tools/cms/detect_cms.py
```

In ra: stack, kết quả login, accessToken (rút gọn) và JWT claims. Không cần Odoo/MySQL.

## CHƯA làm (chờ chốt yêu cầu)

Để viết client tích hợp vào HRM cần biết **lấy/đẩy DỮ LIỆU GÌ** giữa CMS và HRM
(vd: người dùng/giáo viên, học viên, giáo trình/khoá học...) và **theo hướng nào**
(CMS → HRM, HRM → CMS, hay 2 chiều). Chốt xong sẽ viết client gọi REST trong
`hocba_hrm` (controller Odoo) dùng base + token ở trên.

## MySQL trực tiếp (Cách B) — bỏ qua

`14.232.211.255:58008` timeout từ máy dev + thiếu username/tên DB. Không cần nữa vì
API (Cách A) đã thông.
