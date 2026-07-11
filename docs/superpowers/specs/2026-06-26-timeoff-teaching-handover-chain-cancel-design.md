# Spec — Đổi lịch dạy chuyền tiếp + Hủy/Trả buổi + Đồng bộ DB↔FE

- **Ngày:** 2026-06-26
- **Module:** `hocba_timeoff` (owner: Nhật Anh)
- **Nhánh:** `NhatAnh/TimeOff`
- **Tiền đề:** Tiếp nối spec `2026-06-25-timeoff-teacher-leave-teaching-conflict` (nghỉ-theo-buổi của GV: loại "Nghỉ Buổi Dạy", resolution `class_off`/`substitute`, áp lịch khi duyệt).

## 1. Bối cảnh & vấn đề

Luồng hiện tại: GV A xin nghỉ buổi dạy → mỗi buổi trùng tạo 1 `hocba.leave.session.resolution`
(`class_off` chốt ngay / `substitute` chờ GV thay đồng ý). Lịch dạy thật
(`hocba.teaching.session`) **chỉ đổi khi đơn A được HR duyệt** (`_apply_teaching_changes`):
`substitute` → `employee_id = B, state = 'substituted'`; `class_off` → `state = 'cancelled'`.

Ba thiếu sót cần xử lý:

1. **Chủ mới không thấy buổi (Gap hiển thị).** `_upcoming_teaching_sessions` và
   `_find_teaching_conflicts` lọc `state = 'planned'`. Sau khi buổi thành `substituted`,
   GV B (chủ mới) **không thấy** buổi trong form nghỉ-theo-buổi → B không thể xin nghỉ
   buổi đó, cũng không thể giao tiếp cho GV khác. Đây là gốc của hiện tượng
   "đã đổi lịch mà FE không hiện".
2. **Không có đường trả buổi sau khi đã nhận.** GV thay chỉ accept/decline lúc resolution
   còn `pending`. Sau khi đã nhận (đơn A đã duyệt), B muốn "trả lại" buổi → không có cơ chế.
3. **Hủy/rút đơn không báo & không chặn chuỗi.**
   - Hủy đơn *chờ duyệt* (`api_request_cancel` → `unlink`): lịch chưa đổi nên không cần
     revert, **nhưng GV thay đã nhận chuông `sub_request` lại không được báo hủy**.
   - Rút đơn *đã duyệt* (`withdraw` → `action_refuse` → `_revert_teaching_changes`): có
     revert về GV gốc, **nhưng không báo GV thay** và **không chặn khi buổi đã được giao
     tiếp xuống GV kế tiếp** (revert sai chuỗi).

## 2. Quyết định thiết kế (đã chốt với owner)

| # | Quyết định | Chọn |
|---|-----------|------|
| Q1 | Độ sâu chuỗi bàn giao | **Không giới hạn** (A→B→C→D…). `employee_id` = chủ hiện tại; ai đang giữ buổi đều xin nghỉ/giao tiếp được. |
| Q2 | Khi chủ hiện tại "trả" buổi đã nhận | **Về GV liền trước** (người vừa giao) + báo chuông cho người đó. |
| Q3 | Thời điểm chủ mới sở hữu buổi | **Sau khi đơn người giao được HR duyệt** (giữ nguyên: lịch chỉ đổi ở bước duyệt). |
| Q4 | Khi người giao hủy/rút mà buổi đã giao tiếp xuống dưới | **Chặn** (báo rõ phải gỡ chuỗi phía sau trước). Không "hủy ép" cả chuỗi. |

## 3. Mô hình dữ liệu

**Nguyên tắc lõi — stack bàn giao suy từ resolution (không thêm bảng lịch sử):**

- `hocba.teaching.session.employee_id` **luôn = chủ hiện tại**.
- Một "lần bàn giao đang hiệu lực" của buổi S = một `hocba.leave.session.resolution` thỏa:
  `session_id = S`, `resolution = 'substitute'`, `state = 'accepted'`, và `leave_id.state = 'validate'`.
- Các lần bàn giao hiệu lực của S xếp thành **ngăn xếp**; `session.source_leave_id` trỏ **đỉnh**
  (đơn gây ra thay đổi hiện tại). Chủ liền trước của một lần bàn giao = `leave_id.employee_id`
  của lần đó.
- "Pop" một lần bàn giao = đưa buổi về chủ liền trước, rồi tính lại đỉnh mới từ lần bàn
  giao kế dưới (hoặc về GV gốc / `planned` nếu hết).

### 3.1. `hocba.leave.session.resolution` — thêm state

```python
state = fields.Selection([
    ('pending',  'Chờ GV thay đồng ý'),
    ('accepted', 'Đã chốt'),
    ('declined', 'GV thay từ chối'),     # từ chối TRƯỚC khi nhận (giữ nguyên)
    ('returned', 'GV thay đã trả lại'),  # MỚI: trả lại SAU khi đã nhận
])
```

`returned` bị loại khỏi tập "bàn giao hiệu lực" (chỉ `accepted` mới tính) → pop xong buổi
tự khỏi chuỗi.

### 3.2. `hocba.teaching.session` — hàm pop dùng chung

Gộp toàn bộ logic revert vào model session để cả endpoint "trả buổi" lẫn luồng
refuse/withdraw dùng chung:

```python
def _pop_handover(self, resolution):
    """Đưa buổi về chủ liền trước = resolution.leave_id.employee_id; tính lại
    source_leave_id/state từ lần bàn giao kế dưới (substitute accepted + leave validate,
    substitute_id = chủ liền trước) hoặc về original_employee_id/'planned' nếu hết.
    KHÔNG tự đổi resolution.state — caller quyết ('returned' khi trả, để nguyên khi
    leave bị refuse vì leave.state != 'validate' đã tự loại khỏi tập hiệu lực)."""
```

- `class_off` (buổi `cancelled`, `employee_id` không đổi): pop = tính lại `state` từ bàn giao
  hiệu lực còn lại (`substituted` nếu còn, ngược lại `planned`); `source_leave_id` theo đỉnh mới.

### 3.3. Tương thích `original_employee_id`

Giữ field (GV gốc, thông tin/để fallback). Revert **không** dựa vào nó nữa mà dựa vào chủ
liền trước suy từ stack — chỉ fallback về `original_employee_id` khi hết bàn giao hiệu lực
mà chủ liền trước chính là GV gốc.

## 4. Hiển thị buổi cho chủ hiện tại (Gap hiển thị)

Đổi điều kiện lọc của 2 helper (chỉ thêm `substituted`, vẫn bỏ `cancelled`):

```python
# _upcoming_teaching_sessions & _find_teaching_conflicts
('employee_id', '=', employee.id),
('state', 'in', ['planned', 'substituted']),   # trước: '=', 'planned'
```

Vì `employee_id` luôn = chủ hiện tại, mỗi buổi chỉ khớp đúng 1 GV → không xử lý chồng.
Hệ quả: B (chủ mới) thấy buổi đã nhận → xin nghỉ / giao tiếp cho C (chuỗi không giới hạn).

## 5. Endpoint & luồng

### 5.1. MỚI — Trả buổi: `POST /hocba-hrm/api/timeoff/substitution/<int:res_id>/return`
- `auth='user'`, `type='http'`, `csrf=False`, body JSON `{ }` (không bắt buộc lý do).
- Điều kiện hợp lệ (ngược lại 403 `rejected` kèm message):
  - resolution tồn tại, `resolution='substitute'`, `state='accepted'`;
  - `emp == resolution.substitute_id` (đúng người đang giữ buổi);
  - là **đỉnh stack**: `session.source_leave_id == resolution.leave_id`
    (nếu đã giao tiếp xuống dưới → "Buổi này bạn đã giao tiếp cho GV khác; không thể trả.").
- Thực hiện (sudo): `session._pop_handover(resolution)`; `resolution.write(state='returned',
  decided_at=now)`; `_notify_substitute_returned(env, resolution)` → báo
  `resolution.leave_id.employee_id` (= A) chuông `sub_returned`.
- Trả `self._overview_payload()`.

### 5.2. Sửa — Hủy đơn chờ duyệt: `api_request_cancel`
- Trước khi `unlink`: với mỗi resolution `substitute` (state `pending`/`accepted`) của đơn,
  `_notify_substitute_cancelled(env, r)` → báo GV thay `sub_cancelled`. (Lịch chưa đổi nên
  không revert.)

### 5.3. Sửa — Revert khi refuse/withdraw đơn đã duyệt
`action_refuse` **chụp trước** tập đơn đã từng áp lịch rồi mới `super()`:
```python
def action_refuse(self):
    applied = self.filtered(lambda l: l.state == 'validate')  # CHỤP trước super
    res = super().action_refuse()
    for leave in self:
        leave._revert_teaching_changes(was_applied=leave in applied)
    return res
```
`HrLeave._revert_teaching_changes(was_applied)`:
- **Nếu `was_applied = False`** (refuse đơn *pending* — lịch chưa hề đổi): **bỏ qua hoàn toàn**,
  không revert, không báo. (Việc báo GV thay khi hủy đơn pending do `api_request_cancel` lo —
  xem 5.2.)
- **Nếu `was_applied = True`** (đơn đã duyệt, đang bị refuse/withdraw): với mỗi resolution:
  - **Chặn nếu có bàn giao xuống dưới**: `session.source_leave_id != leave.id` (buổi giờ do
    đơn khác giữ đỉnh) → `raise ValidationError("Không thể hủy/từ chối: buổi %s đã được giao
    tiếp cho GV khác. Cần gỡ các thay đổi phía sau trước.")`.
  - Ngược lại (`source_leave_id == leave.id`, đơn này đang giữ đỉnh) → `session._pop_handover(r)`;
    với `substitute` báo GV thay `sub_cancelled`.
- `_pop_handover`/`_has_downstream` phán đoán "đỉnh" dựa vào `session.source_leave_id` (đã set
  lúc apply), **không** dựa vào `leave.state` (đã bị `super()` đổi thành `refuse`).

### 5.4. Chuông — thêm 2 kind (`hr_leave_teacher.py` / model notification)
```python
('sub_cancelled', 'Yêu cầu dạy thay đã hủy'),   # → GV thay, khi người giao hủy/rút
('sub_returned',  'GV thay đã trả lại buổi'),    # → người giao, khi chủ hiện tại trả buổi
```
Kèm `ondelete` cascade như các kind dạy thay hiện có.

Helper controller mới: `_notify_substitute_cancelled(env, resolution)`,
`_notify_substitute_returned(env, resolution)` (cùng khuôn `_push_notification`, đọc
employee người khác qua `.sudo()`).

## 6. Payload & cột "GV dạy thay" (tab "Của tôi")

`_my_request(leave)` — với đơn `isTeachingOff` trả thêm:
- `substituteNames`: chuỗi tóm tắt để hiển thị nhanh ở bảng:
  - buổi `class_off` → góp "Cả lớp nghỉ";
  - buổi `substitute` → tên `substitute_id`;
  - nhiều buổi khác nhau → nối bằng ", " (loại trùng, giữ thứ tự buổi).
- `sessionResolutions`: danh sách chi tiết `[{date, className, kind, substituteName, state}]`
  (cho phần chi tiết đơn / tooltip; `state` ∈ pending/accepted/declined/returned).

FE `TimeOff.jsx` — bảng "Đơn nghỉ của tôi":
- Thêm cột **"GV dạy thay"** giữa "Lý do" và "Trạng thái".
- Đơn thường hoặc không phải dạy thay → `—`.
- Đơn dạy thay → hiện `substituteNames` + badge trạng thái buổi (Đang chờ / Đã đồng ý /
  Đã trả / Từ chối). Nhiều buổi: hiện tóm tắt, chi tiết theo `sessionResolutions`.

## 7. FE khác

- `SubstitutionsPanel.jsx`: với yêu cầu `state='accepted'` mà mình đang giữ buổi, thêm nút
  **"Trả buổi"** → gọi endpoint 5.1; xác nhận trước khi gửi. Yêu cầu `pending` giữ
  Đồng ý/Từ chối như cũ.
- `NotificationBell.jsx`: thêm chấm màu + điều hướng cho `sub_cancelled` (mở tab phù hợp),
  `sub_returned` (mở "Của tôi" để người giao xử lý lại).
- `api/timeoff.js`: thêm `returnSubstitution(resId)` (POST endpoint 5.1).

## 8. Quy tắc nghiệp vụ (BR)

- **BR-H1**: `employee_id` của buổi luôn là chủ hiện tại; query lịch dạy/nghỉ theo buổi của
  một GV gồm `planned` + `substituted` (bỏ `cancelled`).
- **BR-H2**: Chỉ chủ hiện tại của lần bàn giao đỉnh mới được "trả" buổi — điều kiện đỉnh =
  `session.source_leave_id == resolution.leave_id`; nếu đã giao tiếp xuống dưới → chặn.
- **BR-H3**: Không hủy/rút được đơn đã duyệt nếu buổi nó tạo ra đã được giao tiếp xuống dưới
  (`session.source_leave_id != leave.id`) → phải gỡ chuỗi phía sau trước.
- **BR-H4**: Trả buổi → về GV liền trước + báo người đó (`sub_returned`). Hủy/rút đơn → revert
  + báo GV thay (`sub_cancelled`).
- **BR-H5**: Mọi đổi lịch (apply/pop) ghi thẳng `hocba.teaching.session` qua sudo; controller
  trả overview mới → FE luôn hiện đúng chủ hiện tại.

## 9. Kế hoạch test (TDD — red→green)

Model/helper (không qua HTTP, gọi trực tiếp như test hiện có):

1. **Hiển thị chủ mới**: A→B (apply), B thấy buổi trong `_upcoming_teaching_sessions` /
   `_find_teaching_conflicts`; A không còn thấy.
2. **Chuỗi A→B→C**: apply 2 lần → `employee_id=C`, đỉnh = đơn của B; chủ liền trước của C = B.
3. **Trả buổi (đỉnh)**: C trả → buổi về B, `state='substituted'`, đỉnh = đơn của A;
   resolution C `returned`; chuông `sub_returned` tới B.
4. **Trả buổi giữa chuỗi bị chặn**: B trả khi C đang giữ → chặn (B không phải chủ hiện tại /
   không phải đỉnh).
5. **Pop về gốc**: A→B, B trả → buổi về A, `state='planned'`, `source_leave_id=False`.
6. **Hủy đơn chờ duyệt**: A hủy đơn pending có substitute → GV thay nhận `sub_cancelled`;
   buổi không đổi (chưa từng áp).
7. **Rút đơn đã duyệt**: A→B (validate) rồi refuse → buổi về A `planned`; GV thay nhận
   `sub_cancelled`.
8. **Chặn rút khi có chuỗi dưới**: A→B→C rồi A refuse đơn gốc → `ValidationError` (buổi đã
   giao tiếp xuống dưới).
9. **class_off pop**: A class_off (cancelled) rồi refuse → buổi về `planned`.

Lệnh test (local Docker, theo CLAUDE.md):
```
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```
Mục tiêu: "0 failed, 0 error(s) of N tests" với N tăng so với hiện tại.

## 10. Phạm vi & không làm (YAGNI)

- **Không** "hủy ép" cả chuỗi (Q4 = chặn).
- **Không** đổi thời điểm áp lịch (vẫn ở bước HR duyệt — Q3).
- **Không** tạo bảng lịch sử bàn giao riêng (suy từ resolution).
- **Không** đụng module `hocba_attendance` (view "Lịch dạy" đọc cùng `hocba.teaching.session`
  nên tự đúng; nếu cần chỉnh là việc của owner attendance).
- **Không** sửa core Odoo.

## 11. Rủi ro

- Đổi lọc `substituted` có thể khiến buổi xuất hiện ở 2 nơi nếu có dữ liệu cũ sai
  `employee_id` — chấp nhận, vì `employee_id` là invariant chủ hiện tại.
- Migration: thêm giá trị selection `returned` là cộng thêm, không cần migration dữ liệu.
  Bump version manifest để nạp code mới.
