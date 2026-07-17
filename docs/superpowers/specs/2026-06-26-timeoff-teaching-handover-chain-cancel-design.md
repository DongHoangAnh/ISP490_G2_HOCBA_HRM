# Spec — Đổi lịch dạy chuyền tiếp + Hủy buổi + Đồng bộ DB↔FE

- **Ngày:** 2026-06-26 (bản sửa 2026-07-17: bỏ "trả lại buổi" — xem §12)
- **Module:** `hocba_timeoff` (owner: Nhật Anh)
- **Nhánh:** `NhatAnh/TimeOff`
- **Tiền đề:** Tiếp nối spec `2026-06-25-timeoff-teacher-leave-teaching-conflict` (nghỉ-theo-buổi của GV: loại "Nghỉ Buổi Dạy", resolution `class_off`/`substitute`, áp lịch khi duyệt).

> **BẢN SỬA 2026-07-17 — mô hình "không trả lại":** Khi GV dạy thay đã xác nhận,
> buổi do GV thay đảm nhiệm. Nếu sau đó GV thay bận thì **KHÔNG được hoàn buổi
> lại cho giáo viên cũ**, mà phải **tự xử lý tiến**: hủy lớp (cả lớp nghỉ) hoặc
> tạo đơn mới nhờ một GV dạy thay khác. Toàn bộ cơ chế "trả buổi" (endpoint
> `/return`, `_return_substitution`, cờ `canReturn`, state `returned`, chuông
> `sub_returned`, nút "Trả buổi" ở FE) **bị gỡ bỏ**. Các mục dưới đây giữ lại
> để ghi vết lịch sử; phần bị đảo được đánh dấu ~~gạch ngang~~ và §12 tóm tắt
> trạng thái cuối cùng đang có hiệu lực.

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
| Q2 | Khi chủ hiện tại bận sau khi đã nhận | **(SỬA 2026-07-17)** **KHÔNG trả lại GV cũ.** Chủ hiện tại tự xử lý tiến: hủy lớp (`class_off`) hoặc tạo đơn mới nhờ GV khác (`substitute`). ~~Về GV liền trước + báo chuông.~~ |
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

### 3.1. `hocba.leave.session.resolution` — state (SỬA 2026-07-17: bỏ `returned`)

```python
state = fields.Selection([
    ('pending',  'Chờ GV thay đồng ý'),
    ('accepted', 'Đã chốt'),
    ('declined', 'GV thay từ chối'),     # từ chối TRƯỚC khi nhận
])
```

~~`returned` (trả lại SAU khi đã nhận)~~ — **đã gỡ**. Không còn đường trả buổi nên
không còn trạng thái này. Dữ liệu cũ `state='returned'` được migration đổi về
`declined` (đều nghĩa "GV thay không còn giữ buổi"). `_pop_handover` **vẫn giữ**
nhưng chỉ phục vụ revert khi CHÍNH CHỦ rút/từ chối đơn của mình (§5.3).

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

### 5.1. (SỬA 2026-07-17) ~~Trả buổi~~ → GỠ BỎ. Thay bằng "tự xử lý tiến"

~~`POST /hocba-hrm/api/timeoff/substitution/<int:res_id>/return`~~ **đã gỡ** cùng
`_return_substitution` và `_notify_substitute_returned`.

Thay vào đó, chủ hiện tại của buổi `substituted` bận thì **tạo đơn nghỉ-theo-buổi
mới** cho chính buổi đó (chế độ A, `scope='sessions'`) và chọn `class_off` (hủy lớp)
hoặc `substitute` (nhờ GV khác) — đây chính là mắt xích tiến của chuỗi bàn giao.
Để đường này thông, nới guard tạo đơn (`_create_teaching_session_leave`):

- Buổi hợp lệ khi `s.employee_id == emp` **và** `s.state in ('planned', 'substituted')`
  (trước: chỉ `'planned'`). Chủ hiện tại của buổi đã nhận dạy thay vẫn tạo đơn được.
- Chặn-trùng **bỏ qua mắt xích đang sở hữu**: resolution thuộc `session.source_leave_id`
  (đơn đã đưa buổi cho `emp`) không tính là "trùng". Chỉ chặn khi có mắt xích **tiến
  khác** đang hiệu lực (emp đã tạo đơn khác cho cùng buổi và còn `pending`/`accepted`).

Guard được tách thành helper cấp module `_sessions_requestable_error(env, emp, ids)`
để test gọi trực tiếp (không qua HTTP).

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

### 5.4. Chuông (SỬA 2026-07-17: bỏ `sub_returned`)
```python
('sub_cancelled', 'Yêu cầu dạy thay đã hủy'),   # → GV thay, khi người giao hủy/rút
# ('sub_returned', ...)  # ĐÃ GỠ — không còn đường trả buổi
```
Helper `_notify_substitute_returned` **đã gỡ**. Giữ `_notify_substitute_cancelled`
(báo GV thay khi người giao hủy/rút — §5.2, §5.3).

## 6. Payload & cột "GV dạy thay" (tab "Của tôi")

`_my_request(leave)` — với đơn `isTeachingOff` trả thêm:
- `substituteNames`: chuỗi tóm tắt để hiển thị nhanh ở bảng:
  - buổi `class_off` → góp "Cả lớp nghỉ";
  - buổi `substitute` → tên `substitute_id`;
  - nhiều buổi khác nhau → nối bằng ", " (loại trùng, giữ thứ tự buổi).
- `sessionResolutions`: danh sách chi tiết `[{date, className, kind, substituteName, state}]`
  (cho phần chi tiết đơn / tooltip; `state` ∈ pending/accepted/declined — SỬA: bỏ `returned`).

FE `TimeOff.jsx` — bảng "Đơn nghỉ của tôi":
- Thêm cột **"GV dạy thay"** giữa "Lý do" và "Trạng thái".
- Đơn thường hoặc không phải dạy thay → `—`.
- Đơn dạy thay → hiện `substituteNames` + badge trạng thái buổi (Đang chờ / Đã đồng ý /
  Từ chối). Nhiều buổi: hiện tóm tắt, chi tiết theo `sessionResolutions`.

## 7. FE khác (SỬA 2026-07-17)

- `SubstitutionsPanel.jsx`: **gỡ** nút "Trả buổi" và `ConfirmModal` trả buổi. Yêu cầu
  `pending` giữ Đồng ý/Từ chối như cũ; yêu cầu `accepted` chỉ hiển thị trạng thái.
- `NotificationBell.jsx` / `TimeOff.jsx`: **gỡ** điều hướng cho `sub_returned`. Giữ
  `sub_cancelled` (mở tab phù hợp).
- `api/timeoff.js`: **gỡ** `returnSubstitution(resId)`.

## 8. Quy tắc nghiệp vụ (BR)

- **BR-H1**: `employee_id` của buổi luôn là chủ hiện tại; query lịch dạy/nghỉ theo buổi của
  một GV gồm `planned` + `substituted` (bỏ `cancelled`).
- **BR-H2** (SỬA 2026-07-17): **Không có đường trả buổi.** Chủ hiện tại bận thì tự xử lý
  tiến — tạo đơn mới cho buổi `substituted` mình đang giữ (`class_off` hủy lớp / `substitute`
  nhờ GV khác). Buổi chỉ được đưa vào đơn mới bởi đúng chủ hiện tại (`s.employee_id == emp`).
- **BR-H3**: Không hủy/rút được đơn đã duyệt nếu buổi nó tạo ra đã được giao tiếp xuống dưới
  (`session.source_leave_id != leave.id`) → phải gỡ chuỗi phía sau trước.
- **BR-H4** (SỬA 2026-07-17): Hủy/rút đơn của **chính mình** → revert về chủ liền trước
  (qua `_pop_handover`) + báo GV thay (`sub_cancelled`). Đây là đường DUY NHẤT buổi quay
  ngược lại chủ cũ, và chỉ do chính chủ đơn kích hoạt — không phải GV thay trả.
- **BR-H5**: Mọi đổi lịch (apply/pop) ghi thẳng `hocba.teaching.session` qua sudo; controller
  trả overview mới → FE luôn hiện đúng chủ hiện tại.

## 9. Kế hoạch test (TDD — red→green)

Model/helper (không qua HTTP, gọi trực tiếp như test hiện có):

1. **Hiển thị chủ mới**: A→B (apply), B thấy buổi trong `_upcoming_teaching_sessions` /
   `_find_teaching_conflicts`; A không còn thấy.
2. **Chuỗi A→B→C**: apply 2 lần → `employee_id=C`, đỉnh = đơn của B; chủ liền trước của C = B.
3. *(SỬA 2026-07-17 — GỠ)* ~~Trả buổi (đỉnh)~~ — không còn đường trả buổi.
4. *(SỬA 2026-07-17 — GỠ)* ~~Trả buổi giữa chuỗi bị chặn~~.
5. *(SỬA 2026-07-17 — GỠ)* ~~Pop về gốc qua trả buổi~~ (pop chỉ còn qua refuse — case 7).
6. **Hủy đơn chờ duyệt**: A hủy đơn pending có substitute → GV thay nhận `sub_cancelled`;
   buổi không đổi (chưa từng áp).
7. **Rút đơn đã duyệt**: A→B (validate) rồi refuse → buổi về A `planned`; GV thay nhận
   `sub_cancelled`.
8. **Chặn rút khi có chuỗi dưới**: A→B→C rồi A refuse đơn gốc → `ValidationError` (buổi đã
   giao tiếp xuống dưới).
9. **class_off pop**: A class_off (cancelled) rồi refuse → buổi về `planned`.
10. **(MỚI 2026-07-17) Tự xử lý tiến**: A→B (buổi `substituted`, chủ = B).
    `_sessions_requestable_error(env, B, [session])` → không lỗi (B tạo đơn mới được).
11. **(MỚI 2026-07-17) Chủ cũ không tạo đơn cho buổi đã giao**: sau A→B,
    `_sessions_requestable_error(env, A, [session])` → lỗi `invalid_session`.

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
- (SỬA 2026-07-17) Gỡ giá trị selection `returned`: dữ liệu cũ có thể còn dòng
  `state='returned'` → migration pre `19.0.17.0.0` đổi về `declined` bằng SQL trước
  khi nạp model mới. Bump version manifest để chạy migration + nạp code mới.

## 12. Tóm tắt bản sửa 2026-07-17 (trạng thái đang có hiệu lực)

Mô hình cuối cùng = **chuỗi bàn giao tiến, KHÔNG trả lại**:

1. GV thay xác nhận (`accepted`) → khi đơn được duyệt, buổi do GV thay đảm nhiệm
   (`employee_id = GV thay`, `state = 'substituted'`). *(giữ nguyên)*
2. GV thay bận → **không trả lại GV cũ**. Tự xử lý tiến: tạo đơn nghỉ-theo-buổi mới
   cho buổi mình đang giữ, chọn hủy lớp (`class_off`) hoặc nhờ GV khác (`substitute`).
3. Đường buổi quay về chủ cũ **chỉ còn** khi chính chủ đơn rút/từ chối đơn của mình
   (`action_refuse` → `_revert_teaching_changes` → `_pop_handover` + báo `sub_cancelled`),
   và bị **chặn** nếu buổi đã giao tiếp xuống dưới (BR-H3).

**Đã gỡ:** route `POST .../substitutions/<id>/return`, `_return_substitution`,
`_notify_substitute_returned`, cờ `canReturn` (payload `_substitution_rows`), state
`returned`, chuông `sub_returned`, nút "Trả buổi" + `returnSubstitution` (FE).

**Đã nới:** guard `_create_teaching_session_leave` (tách helper
`_sessions_requestable_error`) cho phép buổi `substituted` do chính chủ hiện tại giữ
vào đơn mới; chặn-trùng bỏ qua mắt xích đang sở hữu (`session.source_leave_id`).
