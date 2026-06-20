# Thiết kế — Gói 4C: Công OT theo hệ số (3 mốc) + sửa nốt 4B

**Ngày:** 19/06/2026 · **Trạng thái:** chốt (đã brainstorm với người dùng)
**Phạm vi:** `hocba_attendance` (model work_shift + attendance), `hocba_hrm/controllers/main.py` (API), frontend `frontend/src/features/attendance/`.
**Spec liên quan:** Gói 4A [đăng ký ca](2026-06-17-shift-registration-design.md), Gói 4B [check-in cửa sổ ca](2026-06-18-shift-checkin-window-design.md), Gói 1 [tính công](2026-06-17-attendance-work-credit-design.md).

---

## 0. Bối cảnh & quyết định đã chốt

Gói 4A có model `hocba.work_shift` (ca CTV/OT, state pending/approved/rejected, `rate` Float auto theo thứ qua `_default_rate`). Gói 4B mở check-in CTV/OT theo cửa sổ ca. Gói 4C: **quy đổi giờ ca OT × hệ số thành giờ công OT**, gộp vào tổng hợp tháng; đồng thời thay cơ chế hệ số auto bằng **3 mốc chọn tay**. Nhân tiện sửa nốt hạn chế đã biết của 4B.

### Quyết định (từ brainstorming)
1. **Đầu ra = giờ công OT quy đổi, nằm trong module attendance.** KHÔNG ra tiền VND, KHÔNG tích hợp `hocba_payroll`.
2. **Cơ sở giờ OT = giờ ca đã duyệt `(end − start)`**, **chỉ tính khi ngày đó (local) có bản ghi attendance đã check-in** của NV. (Không dùng giờ thực check-in→check-out; không tính ca không đi làm.)
3. **Hệ số = 3 mốc chọn tay {100%, 150%, 300%}** (lưu rate 1.0 / 1.5 / 3.0). User chọn khi đăng ký (mặc định 100%); manager đổi khi duyệt và trong màn quản lý OT. **Bỏ auto theo thứ** (`_default_rate`). Bỏ luật lễ/đêm auto — mức do người dùng chọn.
4. **Tổng hợp tháng:** giữ nguyên công thường (Gói 1); **thêm 2 chỉ số OT** (giờ OT + giờ OT quy đổi). Áp dụng cho **cả NV official lẫn CTV**.
5. **Màn quản lý OT = tab "Chấm công OT" riêng** cho manager (liệt kê ca OT trong tháng theo phạm vi + tổng, đổi mốc inline). User thường xem OT của mình qua 2 thẻ tổng trong "Chấm công của tôi" — **không** có bảng chi tiết riêng cho user.
6. **Sửa nốt 4B:** `_do_check` nhận biết cửa sổ ca cho NV non-official → không set `out_of_window` (hết cờ `needs_review` nhiễu cho CTV check-in đúng cửa sổ).

### Tái dùng (không viết lại)
`_todays_approved_shifts`, `shift_window_minutes` (policy), `_emp_scope_domain`, `_emp_in_scope`, `_user_can_manage`, `_shift_row`, `_to_utc`, `_dt_local`, `_att_me_history`, `fields.Datetime.context_timestamp`.

### KHÔNG làm (ngoài phạm vi)
Tiền lương VND / tích hợp payslip. Luật lễ/đêm auto (mức do người dùng tự chọn thay thế). Nhiều ca/ngày tính chồng (mỗi ca tính độc lập, miễn ngày đó có check-in). Bảng OT chi tiết riêng cho user.

---

## 1. Sửa nốt 4B — `out_of_window` cho non-official (`hocba_attendance/models/hr_attendance.py`)

Trong `_do_check`, dòng hiện tại:
```python
out_of_window = not policy.is_within_window(now_local, kind)
```
luôn dùng khung official → CTV check-in đúng cửa sổ ca vẫn bị `out_of_window=True` → `needs_review=True` (nhiễu báo cáo).

**Sửa:** phân nhánh theo `employee.x_employment_status`:
```python
if employee.x_employment_status == 'official':
    out_of_window = not policy.is_within_window(now_local, kind)
else:
    # non-official (CTV/OT): trong cửa sổ ±W quanh giờ ca approved hôm nay
    window = policy.shift_window_minutes or 15
    shifts = self._todays_approved_shifts(employee, today)
    in_win = False
    for s in shifts:
        anchor = fields.Datetime.context_timestamp(
            s, s.start if kind == 'in' else s.end).replace(tzinfo=None)
        if abs((now_local - anchor).total_seconds()) <= window * 60:
            in_win = True
            break
    out_of_window = not in_win
```
- `today` đã có sẵn trong `_do_check` (= `now_local.date()`).
- Vì `_assert_shift_check_allowed` (4B) đã chặn check-in ngoài cửa sổ, non-official check-in thành công ⇒ `in_win=True` ⇒ `out_of_window=False`. Tính lại ở đây để cờ luôn đúng (không phụ thuộc thứ tự gọi guard).
- `needs_review` (compute `_compute_needs_review`) không đổi — vẫn `face_suspect or out_of_zone or out_of_window`; nay non-official đúng cửa sổ sẽ không kích `out_of_window`.

---

## 2. Model `hocba.work_shift` — 3 mốc hệ số (`hocba_attendance/models/hocba_work_shift.py`)

Thêm field mốc + đổi `rate` thành computed-store:
```python
ot_level = fields.Selection(
    [('100', '100%'), ('150', '150%'), ('300', '300%')],
    string='Mức hệ số', default='100', required=True)
rate = fields.Float(
    string='Hệ số', compute='_compute_rate', store=True,
    help='Quy đổi từ mức: 100%→1.0, 150%→1.5, 300%→3.0.')

_OT_RATE = {'100': 1.0, '150': 1.5, '300': 3.0}

@api.depends('ot_level')
def _compute_rate(self):
    for rec in self:
        rec.rate = self._OT_RATE.get(rec.ot_level, 1.0)
```
- **Xóa `_default_rate`** (không còn auto theo thứ).
- `_check_overlap`, `_check_times` giữ nguyên.
- **Migration:** trên `-u`, `rate` các ca cũ tính lại từ `ot_level` (mặc định `100` ⇒ rate 1.0). Chấp nhận trên DB demo (ghi rõ ở handoff).

---

## 3. API (`hocba_hrm/controllers/main.py`)

### 3.1 `_shift_row` — thêm `otLevel`
```python
'otLevel': s.ot_level,
'rate': s.rate,   # giữ để hiển thị (đọc-only, suy từ otLevel)
```

### 3.2 `_shift_create` — nhận `otLevel`
- Đọc `level = body.get('otLevel') or '100'`; nếu `level not in ('100','150','300')` → `ValidationError('Mức hệ số không hợp lệ.')`.
- `vals['ot_level'] = level`; **bỏ** `vals['rate'] = Shift._default_rate(start)`.

### 3.3 `_shift_decide` — override bằng `otLevel`
- Thay nhánh `if 'rate' in body: vals['rate'] = float(body['rate'])` bằng:
```python
if 'otLevel' in body:
    if body['otLevel'] not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    vals['ot_level'] = body['otLevel']
```

### 3.4 MỚI `_shift_set_level(env, shift_id, level)` — manager đổi mốc ca approved
```python
def _shift_set_level(env, shift_id, level):
    """Manager (trong phạm vi) đổi mốc hệ số 1 ca approved (màn Chấm công OT).
    Trả _shift_row; None nếu không tồn tại; AccessError nếu vượt quyền;
    ValidationError nếu mốc sai / ca không ở trạng thái approved."""
    if level not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)):
        raise AccessError('forbidden')
    if shift.state != 'approved':
        raise ValidationError('Chỉ đổi mức cho ca đã duyệt.')
    shift.write({'ot_level': level})
    return _shift_row(shift)
```
Route: `POST /hocba-hrm/api/shifts/<int:shift_id>/level`, body `{otLevel}`. Map lỗi: AccessError→403, ValidationError→400 (rollback), None→404.

### 3.5 MỚI `_ot_table(env, month_str)` — bảng OT tháng theo phạm vi
```python
def _ot_table(env, month_str):
    """Ca approved trong tháng theo phạm vi vai trò (giống _att_day_table).
    Mỗi ca: giờ ca, số giờ, mốc, giờ quy đổi (giờ×rate), counted (ngày đó NV
    có check-in?). Chỉ ca counted mới cộng vào tổng quy đổi. Trả rows + totals."""
```
- Khoảng tháng → `start_utc`/`end_utc` (mẫu `_shifts_week`: localize tz, đổi UTC).
- Domain: `[('state','=','approved'), ('start','>=',start_utc), ('start','<',end_utc)]` + phạm vi NV (mẫu `_att_day_table`: lặp `_emp_scope_domain`, prefix `employee_id.`/`employee_id`); non-manager → `employee_id = emp.id`.
- Mỗi ca: `hours = (s.end - s.start).total_seconds()/3600`; `d = context_timestamp(s, s.start).date()`; `counted = bool(attendance approved có check-in của NV ngày d)`; `creditHours = round(hours * s.rate, 2) if counted else 0`.
- Row (camelCase): `id, empId, empName, code, depName, date, start, end, otLevel, rate, hours, counted, creditHours, state`.
- `totals`: `{otHours: Σ hours, otCreditHours: Σ creditHours, count: len(rows), countedCount}`.
- Trả `{month, canManage, rows, totals}`.

### 3.6 `_att_me_history` — thêm chỉ số OT vào summary
Sau khi tính `summary`, gộp OT của chính `emp` trong `[first, last]`:
```python
ot = _ot_for_employee(env, emp, first, last)
summary['otHours'] = ot['otHours']
summary['otCreditHours'] = ot['otCreditHours']
```
Tách helper dùng chung `_ot_for_employee(env, emp, first, last)` trả `{otHours, otCreditHours}` (cùng luật "ca approved + ngày có check-in"); `_ot_table` dùng lại cho phần tính per-row. (Có thể implement `_ot_table` gọi `_ot_for_employee` per NV, hoặc tách hàm tính 1 ca dùng chung — chọn cách gọn nhất khi code.)

### 3.7 Routes mới (class controller)
```python
@http.route('/hocba-hrm/api/shifts/ot', auth='user', type='http', methods=['GET'])
def api_shifts_ot(self, month=None, **kw):
    return request.make_json_response(_ot_table(request.env, month))

@http.route('/hocba-hrm/api/shifts/<int:shift_id>/level', auth='user',
            type='http', methods=['POST'], csrf=False)
def api_shift_set_level(self, shift_id, **kw):
    try:
        row = _shift_set_level(request.env, shift_id,
                               (request.get_json_data() or {}).get('otLevel'))
    except AccessError:
        return request.make_json_response({'error': 'forbidden'}, status=403)
    except (ValidationError, UserError) as ex:
        request.env.cr.rollback()
        return request.make_json_response({'error': 'rejected', 'message': str(ex)}, status=400)
    if row is None:
        return request.make_json_response({'error': 'not_found'}, status=404)
    return request.make_json_response(row)
```

---

## 4. Frontend (`frontend/src/features/attendance/`)

### 4.1 `api/attendance.js`
- `createShift`/`approveShift` đã truyền nguyên `body` → FE gửi thêm `otLevel`.
- Thêm:
```js
export const fetchOtTable = (month) => hbGet(`/hocba-hrm/api/shifts/ot?month=${month}`);
export const setShiftLevel = (id, otLevel) => hbPost(`/hocba-hrm/api/shifts/${id}/level`, { otLevel });
```

### 4.2 `ShiftForm.jsx` — thêm select "Mức hệ số"
- State `form.otLevel` default `'100'`; select 3 option (100%/150%/300%); gửi trong `createShift`.

### 4.3 `ShiftDrawer.jsx` — override bằng mốc
- Thay input `Hệ số` (number) bằng select 3 mốc; state `level` init `shift.otLevel`; body duyệt gửi `otLevel: level` (bỏ `rate`). Phần hiển thị "Hệ số ×{shift.rate}" giữ nguyên.

### 4.4 `MyHistory.jsx` — 2 thẻ tổng OT
- Đổi lưới summary sang `repeat(6,1fr)` (hoặc xuống dòng): thêm `Sum "Giờ OT" = summary.otHours`, `Sum "Giờ OT quy đổi" = summary.otCreditHours` (col xanh).

### 4.5 MỚI `OtTable.jsx` — tab "Chấm công OT" (manager)
- Props `{ search }` (tùy chọn). Month picker (mặc định `currentMonth()`); `fetchOtTable(month)`.
- Bảng: NV, Mã, Phòng, Ngày, Giờ ca (start–end), Số giờ, Mức, Giờ quy đổi, Đã chấm (✓/—).
- Dòng tổng: tổng giờ OT + tổng giờ quy đổi + số ca.
- Cột "Mức": select 100/150/300% inline → `setShiftLevel(id, level)` rồi reload tháng. (Ca chưa `counted` hiển thị mờ; vẫn đổi mốc được.)
- States chuẩn: `LoadingState`/`ErrorState`/`EmptyState`.

### 4.6 `Attendance.jsx` — thêm tab manager
- `tabs` (nhánh `isManager`): thêm `['otpay', 'Chấm công OT']`.
- `activeTab === 'otpay'` → `<OtTable search={search} />`.

### 4.7 Build SPA
`cd frontend && npm run build` → bundle vào `custom-addons/hocba_hrm/static/spa`.

---

## 5. Kiểm thử (TDD)

### 5.1 `hocba_attendance/tests/` (TransactionCase)
- **`_compute_rate`** (có thể trong `test_work_credit.py` hoặc file mới `test_ot_shift.py`): tạo shift `ot_level='100'/'150'/'300'` → `rate` 1.0/1.5/3.0; đổi `ot_level` → `rate` cập nhật.
- **4B fix** (`test_checkin_*` hoặc file mới): non-official có ca approved, check-in trong cửa sổ → record `out_of_window=False`, `needs_review=False`. Official ngoài khung → `out_of_window=True` (regression giữ nguyên). (Dựng now bằng ca có start≈`now`, mẫu `test_shift_checkin.py`.)

### 5.2 `hocba_hrm/tests/test_ot_payroll.py` (MỚI, TransactionCase)
Helper gọi trực tiếp (mẫu `test_shift_api.py`). CCCD 12 số cho official (BR-010); giờ UTC + tz context (+07).
- **Aggregation:** ca approved + ngày có attendance (check-in) → `otCreditHours = giờ×rate`; ca approved **không** có attendance ngày đó → không cộng; ca pending/rejected → không cộng; ca ngoài tháng → loại. Kiểm cả `_att_me_history.summary.otHours/otCreditHours` và `_ot_table.totals`.
- **`_ot_table` phạm vi:** trưởng phòng chỉ thấy ca NV phòng mình; HR thấy tất cả; user thường → ca của mình.
- **`_shift_set_level`:** manager trong phạm vi đổi mốc ca approved → `rate` đổi theo; mốc sai → ValidationError; ca pending → ValidationError; ngoài phạm vi → AccessError; ca không tồn tại → None.
- **`_shift_create`/`_shift_decide` với `otLevel`:** create mặc định `100`; create `otLevel='300'` → rate 3.0; decide override `otLevel='150'` → rate 1.5; `otLevel` sai → ValidationError.

### 5.3 Lệnh test (xem HANDOFF §5 — `MSYS_NO_PATHCONV=1`, xác nhận N>0)
```bash
# hocba_attendance
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
# hocba_hrm
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

### 5.4 Frontend (thủ công)
- User CTV: đăng ký ca chọn mốc 150%; xem 2 thẻ "Giờ OT"/"Giờ OT quy đổi" trong Chấm công của tôi.
- Manager: tab "Chấm công OT" — bảng tháng + tổng đúng; đổi mốc 1 dòng → giờ quy đổi + tổng cập nhật. Ca chưa chấm hiển thị mờ, không cộng tổng.
- Manager duyệt ca: override mốc bằng select.

---

## 6. Phạm vi

**Có làm:** (A) sửa `_do_check` out_of_window cho non-official; (B) `ot_level` Selection + `rate` computed-store, bỏ `_default_rate`; (C) `_shift_row.otLevel`, `_shift_create`/`_shift_decide` theo `otLevel`, `_shift_set_level` + route, `_ot_table` + route, OT vào `_att_me_history.summary`; (D) ShiftForm/ShiftDrawer select mốc, MyHistory 2 thẻ OT, `OtTable.jsx` + tab manager, api client + build; (E) test backend.

**KHÔNG làm:** tiền VND / payslip; luật lễ/đêm auto; nhiều ca/ngày tính chồng đặc biệt; bảng OT chi tiết riêng cho user.
