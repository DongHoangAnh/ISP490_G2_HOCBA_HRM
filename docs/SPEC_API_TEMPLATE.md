# Template đặc tả API domain — `<TÊN DOMAIN>`

> **Cách dùng:** copy file này thành `docs/SPEC_API_<DOMAIN>.md` (vd
> `SPEC_API_ATTENDANCE.md`), điền các mục, mở PR cho cả team review TRƯỚC
> khi code (quy ước "spec trước code"). FE và BE cùng nhìn một hợp đồng.
>
> Mẫu đã hoàn chỉnh để tham khảo: **Employees** (`SPEC_HRM_SPA_API.md` §3).
> Quy ước chung: `QUY_UOC_FRONTEND.md`.

**Domain:** `<employees | attendance | recruitment | timeoff | payroll>`
**Owner:** `<tên>` · **Module backend:** `<hocba_xxx>` · **Màn FE:** `features/<domain>/`
**Phiên bản:** 0.1 · **Ngày:** `<dd/mm/yyyy>` · **Trạng thái:** nháp / đã review

---

## 1. Phạm vi

Màn này hiển thị/thao tác gì? Liệt kê ngắn gọn các chức năng (gắn mã FUNC/BR
nếu có). Cái gì KHÔNG làm ở SPA mà để trong Odoo backend (vd form nhập liệu
phức tạp) — ghi rõ để khỏi xây trùng.

## 2. Nguồn dữ liệu (model Odoo)

| Dữ liệu | Model | Ghi chú |
|---|---|---|
| ... | `hocba.xxx` | tự viết / kế thừa `hr.xxx` |

> ⚠️ Nếu đọc dữ liệu của domain khác (vd payroll đọc công từ
> `hocba.attendance`) **ghi rõ ở đây** + báo người sở hữu model đó.

## 3. Endpoints

> Quy ước chung (mọi endpoint phải theo):
> - Prefix: `/hocba-hrm/api/<domain>/...`
> - `auth='user'`, `type='http'`, trả JSON (`Content-Type: application/json`)
> - JSON key **camelCase**; ngày dạng ISO `YYYY-MM-DD`; tiền = số nguyên VND
> - Ẩn/hiện field nhạy cảm bằng `has_group` ở controller, KHÔNG để FE tự lọc
> - Lỗi: `{"error": "<code>"}` + HTTP status đúng nghĩa
>   (400 sai input · 401 chưa login · 403 không đủ quyền · 404 không thấy ·
>   500 lỗi server)

### 3.1. `GET /hocba-hrm/api/<domain>/<...>`  (auth=user)

**Mục đích:** ...

**Query params** (nếu có): `?month=2026-06` ...

**Response 200:**
```json
{
  "isManager": "bool — vd thuộc nhóm quản lý domain này",
  "items": [
    { "id": 1, "someField": "...", "amount": 0 }
  ]
}
```

**Lỗi có thể trả:** `404 not_found`, `403 forbidden`, ...

### 3.2. `POST /hocba-hrm/api/<domain>/<...>`  (auth=user)
*(nếu màn có thao tác ghi — duyệt đơn, check-in… Nếu chỉ đọc thì xoá mục này.)*

**Body:**
```json
{ "id": 1, "action": "approve" }
```

**Response:** ... · **Lỗi:** ...

## 4. Ma trận phân quyền

Field/khối nào trả theo nhóm nào? (bắt buộc — đây là phần BE quyết định, FE
chỉ ẩn/hiện UI theo flag trả về)

| Khối dữ liệu | Điều kiện (nhóm) |
|---|---|
| Cơ bản | mọi user đăng nhập |
| `<field nhạy cảm>` | `<hr.group_xxx>` |

## 5. Ghi chú test

Liệt kê case cần test HTTP (mỗi role 1 dòng) — theo mẫu API-1..12 của
Employees (`TEST_BACKEND_2026-06-12.md`):
- [ ] User thường: thấy gì / ẩn gì
- [ ] Manager domain: thấy thêm gì
- [ ] Edge: bản ghi không tồn tại → 404; input sai → 400

## 6. Câu hỏi mở / phụ thuộc

Điểm chưa chắc, cần chốt với team hoặc khách trước khi code.
