# Spec — Trả buổi dạy → từ chối đơn của GV gốc + cho phép xin nghỉ lại

- **Ngày:** 2026-06-26
- **Owner:** Nhật Anh (nhánh `NhatAnh/TimeOff`)
- **Module:** `hocba_timeoff`

## 1. Bối cảnh & vấn đề

Luồng "Nghỉ Buổi Dạy": GV A xin nghỉ 1 buổi, nhờ GV B dạy thay; B đồng ý; đơn A được
duyệt (`validate`) → buổi chuyển sang B (`substituted`, `source_leave_id = đơn A`).

Khi **B trả lại buổi** (`returnSubstitution`), hiện tại:
- Buổi quay về A (`_pop_handover`): `employee_id = A`, `state = 'planned'`, `source_leave_id` rỗng.
- Resolution → `returned`; A nhận thông báo `sub_returned`.
- **NHƯNG đơn của A vẫn `validate`** → (a) đơn hiển thị "Đã duyệt" dù A phải dạy lại;
  (b) A **không tạo lại được** đơn nghỉ cho buổi đó vì guard tạo đơn chặn buổi có
  resolution thuộc đơn ở trạng thái `confirm/validate1/validate`.

Yêu cầu: khi B trả buổi cho A → **đơn của A chuyển `Từ chối`** và A **xin nghỉ lại được** buổi đó.

## 2. Phạm vi & quyết định

- Một đơn "Nghỉ Buổi Dạy" có thể gồm **nhiều buổi** (mỗi buổi 1 resolution). Vì vậy:
  - Trả 1 buổi **chỉ từ chối cả đơn khi đơn không còn buổi nào đang hiệu lực** (không
    còn resolution `pending`/`accepted`). Đây là case thường gặp (đơn 1 buổi → trả 1 buổi → từ chối).
  - Nếu đơn còn buổi khác đang hiệu lực (vd buổi class_off, hoặc buổi khác đang nhờ dạy
    thay) → **giữ đơn `validate`**, chỉ giải phóng buổi vừa trả để xin lại.
- Áp dụng đệ quy theo chuỗi A→B→C: C trả cho B → đơn của B từ chối (B phải dạy lại);
  B trả cho A → đơn của A từ chối.

## 3. Thay đổi

### 3.1 `controllers/main.py` — `_return_substitution`
Sau khi `_pop_handover` + set `returned` + thông báo: nếu `leave_id.state == 'validate'`
và **không còn** resolution nào `state in ('pending','accepted')` → gọi `leave_id.action_refuse()`.

### 3.2 `models/hr_leave_teacher.py` — `_revert_teaching_changes`
Bỏ qua resolution đã ở trạng thái cuối (`returned`/`declined`) trong vòng lặp revert.
Lý do: buổi của resolution `returned` đã được pop/đổi chủ từ trước (trong chuỗi có thể
đã gắn `source_leave_id` sang đơn dưới) — nếu không bỏ qua, guard "đã giao tiếp cho GV
khác" sẽ chặn nhầm khi `action_refuse` đơn lúc trả buổi.

### 3.3 `controllers/main.py` — guard tạo đơn (chặn trùng)
Thêm điều kiện `('state', 'in', ['pending', 'accepted'])` vào search resolution trùng.
→ Buổi có resolution `returned`/`declined` không còn chặn, A xin nghỉ lại được kể cả khi
đơn cũ (nhiều buổi) vẫn `validate`.

## 4. Kiểm thử (mở rộng `tests/test_handover_chain.py`)

- B trả buổi về A (đơn 1 buổi) → `đơn A.state == 'refuse'`; buổi `planned`; A xin lại được
  (guard trùng trả rỗng).
- Chuỗi A→B→C: C trả về B → `đơn B.state == 'refuse'`, buổi vẫn do B giữ (`substituted`,
  `source = đơn A`), **không** lỗi `ValidationError`.
- Đơn nhiều buổi: 2 buổi nhờ B; B trả 1 buổi → `đơn A vẫn 'validate'`; buổi đã trả `planned`
  + xin lại được; buổi còn lại vẫn `substituted`.
- Giữ nguyên các test hiện có (trả giữa chuỗi bị chặn, refuse revert, class_off, …).

## 5. Rủi ro

- `action_refuse` gọi nội bộ với quyền sudo (record đến từ `.sudo()`); loại "Nghỉ Buổi Dạy"
  `requires_allocation=False` → không hoàn quỹ, chỉ revert lịch (đã được bỏ qua vì resolution `returned`).
- Không đổi hành vi rút/hủy đơn thủ công (vẫn chặn khi buổi đã giao tiếp xuống dưới qua
  resolution `accepted`).
