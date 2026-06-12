# Quy ước phát triển Frontend — Học Bá HRM SPA

**Phiên bản:** 1.0 · **Ngày:** 12/06/2026 · **Trạng thái:** chờ team duyệt
**Áp dụng cho:** thư mục `frontend/` (SPA React + Vite) — luồng phát triển tách riêng backend, nối qua JSON API.
**Màn mẫu chuẩn:** Employees (`hrm-employees.jsx` hiện tại) — đã nối API thật, mọi quy ước dưới đây lấy từ đó.

---

## 1. Nguyên tắc nền (4 điều bất di bất dịch)

1. **FE chỉ nói chuyện với BE qua `/hocba-hrm/api/*`.** Không gọi `/web/dataset/call_kw`, không ORM, không xài session info ngoài API. *Ngoại lệ duy nhất:* `/web/image/...` cho ảnh đại diện (read-only).
2. **BE là nguồn chân lý về quyền.** API đã ẩn field nhạy cảm (lương, CCCD, MST...) theo `has_group`. FE chỉ ẩn/hiện UI dựa trên **flags do API trả về** (`isHr`, `isHrManager`...), tuyệt đối không tự suy luận quyền hay che giấu chỉ bằng FE.
3. **Spec API trước, code sau.** Mỗi domain có file đặc tả trong `docs/` (theo khung `SPEC_HRM_SPA_API.md` §3) được review trước khi FE lẫn BE implement. FE code theo spec, không theo "hỏi miệng".
4. **Mỗi người chỉ sửa file trong địa phận của mình** (xem §3). File dùng chung muốn sửa → PR + người quản FE review.

## 2. Cấu trúc thư mục

```
frontend/
├── package.json  vite.config.js  index.html
└── src/
    ├── main.jsx              # entry, mount App
    ├── app/                  # App, router, Shell (sidebar/topbar)  [CHUNG]
    ├── api/
    │   ├── client.js         # hbGet/hbPost — fetch wrapper duy nhất [CHUNG]
    │   ├── employees.js      # Tân
    │   ├── attendance.js     # Hoàng Anh
    │   ├── recruitment.js    # Việt
    │   ├── timeoff.js        # Nhật Anh
    │   └── payroll.js        # Hùng
    ├── components/           # Avatar, Badge, Icon, Modal, EmptyState… [CHUNG]
    ├── hooks/                # useFetch, useDebounce…                  [CHUNG]
    ├── features/
    │   ├── dashboard/        # [CHUNG — người quản FE]
    │   ├── employees/        # Tân
    │   ├── attendance/       # Hoàng Anh
    │   ├── recruitment/      # Việt
    │   ├── timeoff/          # Nhật Anh
    │   └── payroll/          # Hùng
    └── styles/
        ├── tokens.css        # biến màu/font Học Bá [CHUNG]
        └── base.css          # layout, utility class [CHUNG]
```

- Trong `features/<domain>/` mỗi người **toàn quyền**: tự chia component con, thêm `mock.js` nếu cần.
- `[CHUNG]` = sửa phải qua review người quản FE (hiện tại: Tân).

## 3. Phân địa phận (ownership)

| Người | Được sửa tự do | Spec API tương ứng |
|---|---|---|
| Tân | `features/employees/`, `api/employees.js` + các phần `[CHUNG]` (vai trò quản FE) | đã có (`SPEC_HRM_SPA_API.md`) |
| Hoàng Anh | `features/attendance/`, `api/attendance.js` | tự viết, đọc từ `hocba.attendance` |
| Việt | `features/recruitment/`, `api/recruitment.js` | tự viết (hợp nhất `rec-*.jsx` cũ về đây) |
| Nhật Anh | `features/timeoff/`, `api/timeoff.js` | tự viết |
| Hùng | `features/payroll/`, `api/payroll.js` | tự viết, **phải khai báo nguồn dữ liệu công từ `hocba.attendance`** |

Git: làm trên nhánh cá nhân như hiện nay (`<Tên>/<TínhNăng>`), merge vào `main` qua PR. Hai người không cùng sửa một file `[CHUNG]` trong cùng đợt.

## 4. Quy ước code

- **Component:** function component + hooks, KHÔNG class. Tên `PascalCase`, file component chính trùng tên màn: `features/attendance/Attendance.jsx`.
- **Hooks:** `useXxx`, đặt trong `hooks/` nếu dùng chung, trong feature nếu riêng.
- **Helper/biến:** `camelCase`; hằng số `UPPER_SNAKE`.
- **Ngôn ngữ:** UI tiếng Việt; comment tiếng Việt OK; tên biến/hàm tiếng Anh.
- **Format:** Prettier config mặc định của repo (sẽ thêm ở Giai đoạn 1) — không bàn cãi style bằng miệng, máy format là chuẩn.
- Không thêm thư viện UI nặng (MUI, AntD, Bootstrap JS...). Giữ CSS thuần theo design system hiện có. Muốn thêm dependency mới → hỏi nhóm trước.

## 5. Gọi API — pattern bắt buộc

**a) Không `fetch` trực tiếp trong component.** Mọi lời gọi đi qua `api/client.js`:

```js
// api/client.js (chung — đã có sẵn dạng phôi là hbGet trong hrm-employees.jsx)
export async function hbGet(url) {
  const r = await fetch(url, { credentials: 'same-origin' });
  if (!r.ok) throw new ApiError(r.status, await safeCode(r));
  return r.json();
}
```

```js
// api/attendance.js (ví dụ — Hoàng Anh)
import { hbGet } from './client';
export const fetchAttendanceSummary = (month) =>
  hbGet(`/hocba-hrm/api/attendance/summary?month=${month}`);
```

**b) Ba trạng thái màn hình** — mọi màn phải xử lý đủ, theo đúng mẫu Employees:

```jsx
if (err)   return <ErrorState message={err} onRetry={load} />;  // có nút "Thử lại"
if (!data) return <LoadingState />;                              // "Đang tải dữ liệu…"
return <NộiDungMàn data={data} />;
```

**c) Quy ước dữ liệu trên dây (wire format):**
- JSON key `camelCase` (`depName`, `statusKey`, `hasImg` — như API employees hiện có).
- Ngày: API trả ISO `YYYY-MM-DD`; FE hiển thị `dd/mm/yyyy` qua helper chung `fmtDate` — không tự format tay.
- Tiền: số nguyên VND; hiển thị qua `fmtVND`.
- Lỗi: `{"error": "<code>"}` + HTTP status đúng nghĩa (401/403/404/410/500).

## 6. Giao diện & style

- **Token bắt buộc** (trong `styles/tokens.css`): đỏ Học Bá `#C8102E`, font *Be Vietnam Pro*. Không hardcode mã màu trong component — dùng biến CSS.
- Badge/trạng thái dùng bộ "kind" sẵn có: `green / amber / red / blue / violet / teal / gray` (mapping mẫu: `hbStatusKind` trong màn Employees).
- Component dùng chung **phải lấy từ `components/`** (Avatar, Badge, Icon, Modal, EmptyState...). Thấy thiếu thì đề nghị người quản FE thêm, không tự chép code nhân bản vào feature.
- Inline style chỉ cho giá trị động (kích thước avatar...); còn lại dùng class.

## 7. Mock data

- Mock để **trong feature của mình**: `features/<domain>/mock.js`, có cờ `USE_MOCK` ở đầu màn để bật/tắt.
- Không import mock chéo giữa các feature. `hrm-data.jsx` cũ sẽ bị tách nhỏ về từng feature rồi xoá.
- Khi màn đã nối API thật và pass kiểm thử → **xóa mock + cờ** trong cùng PR.

## 8. Chạy dev & build

```bash
cd frontend
npm install
npm run dev      # Vite :5173, proxy /hocba-hrm/api + /web/image → localhost:8069
npm run build    # xuất vào custom-addons/hocba_hrm/static/spa/
```

- Dev cần Odoo Docker chạy sẵn (db `hocba_hrm`) để API có dữ liệu; đăng nhập bằng 4 user test role (mật khẩu chung của team).
- **Bản build được commit** khi merge vào `main` (để ai không cài Node vẫn chạy demo được). Không commit `node_modules/`; `.gitignore` sẽ cập nhật ở Giai đoạn 1.

## 9. Definition of Done — một màn được coi là xong khi:

- [ ] Nối API thật theo spec đã duyệt, mock đã xóa
- [ ] Đủ 3 trạng thái loading / error (có Thử lại) / data
- [ ] Ẩn/hiện đúng theo flags quyền từ API — test với cả 4 user role test
- [ ] Search/filter (nếu có) hoạt động; không lỗi đỏ trong console
- [ ] Chỉ đụng file trong địa phận của mình; file chung (nếu sửa) đã được review
- [ ] Cập nhật spec API nếu hợp đồng có thay đổi trong lúc làm

---

*Thắc mắc/đề xuất sửa quy ước: mở issue hoặc nhắn nhóm — quy ước là của chung, sửa được, nhưng sửa xong phải cập nhật file này.*
