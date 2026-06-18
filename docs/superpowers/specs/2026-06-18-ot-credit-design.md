# Thiết kế — Gói 4C: Tính công/lương OT theo hệ số + luật lễ/đêm

**Ngày:** 18/06/2026 · **Trạng thái:** chốt (tự quyết theo tiêu chí khuyến nghị — goal autonomous)
**Phạm vi:** `hocba_attendance` (policy + model `hocba.work_shift`), `hocba_hrm/controllers/main.py` (tổng hợp tháng), frontend `MyHistory.jsx`.
**Spec liên quan:** Gói 1 [tính công](2026-06-17-attendance-work-credit-design.md), Gói 4A [đăng ký ca](2026-06-17-shift-registration-design.md).

---

## 0. Bối cảnh & quyết định

Gói 4A có model `hocba.work_shift` (ca CTV/OT, `rate`, `start`/`end`, `state`). `_default_rate` hiện chỉ: T2-6→1.5, T7/CN→2.0. `_att_me_history` (tổng hợp tháng của chính user) tính công từ `hocba.attendance` (chưa có OT). Gói 4C: (a) **luật lễ/đêm** cho `_default_rate`; (b) **quy đổi công OT** (Σ giờ ca × hệ số) gộp vào tổng hợp tháng.

Hệ thống KHÔNG có payroll engine thật → "công/lương OT" hiểu là **công quy đổi** (giờ ca × hệ số), dùng để báo cáo/đối chiếu, không xuất tiền.

### Quyết định đã chốt (tiêu chí khuyến nghị)
- **Ngày lễ qua policy field** `holiday_dates` (Text, danh sách YYYY-MM-DD) — KHÔNG thêm model/menu riêng (giảm rủi ro, HR sửa ngay trong form policy đã có). Ca rơi ngày lễ → hệ số nền 3.0.
- **Ca đêm** = giờ vào ≥ `night_start` (22:00) HOẶC < `night_end` (06:00) → cộng `night_bonus` (mặc định +0.3) vào hệ số (Luật LĐ +30%).
- `_default_rate` nền: **lễ 3.0 / cuối tuần 2.0 / ngày thường 1.5**, cộng phụ cấp đêm nếu có.
- **Ca cũ giữ `rate` đã lưu**; chỉ ca tạo mới (sau 4C) lấy default nâng cấp; manager vẫn override được. → không sửa ngược dữ liệu cũ, không phá test 4A (ca 09:00 không phải đêm → vẫn 1.5/2.0).
- **Quy đổi công OT** trong `_att_me_history`: `otHours` (Σ giờ ca approved trong tháng), `otCreditHours` (Σ giờ × `rate`), `otShiftCount`. Tính cho **mọi ca approved** của user trong tháng (cả ctv lẫn ot — `rate` đã mang hệ số).

### KHÔNG làm (sau)
- Payroll engine thật (xuất tiền). Model ngày lễ riêng + đồng bộ lịch quốc gia. Sửa `_do_check`/`needs_review` nhận biết cửa sổ ca (giới hạn 4B — để follow-up). Tính OT cho official gộp vào `work_credit` ngày (giữ tách bạch: OT credit là chỉ số riêng).

### Tái dùng
- `_default_rate` (model `hocba.work_shift`), `_att_me_history` (controller), `fields.Datetime.context_timestamp`, policy `get_policy()`.

---

## 1. Policy — field lễ/đêm (`hocba_attendance`)

File `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`, thêm sau `shift_window_minutes`:
```python
    night_start = fields.Float(
        string='Giờ bắt đầu ca đêm', default=22.0,
        help='Ca có giờ vào ≥ giờ này (22.0 = 22:00) được tính phụ cấp đêm.')
    night_end = fields.Float(
        string='Giờ kết thúc ca đêm', default=6.0,
        help='...hoặc giờ vào < giờ này (6.0 = 06:00).')
    night_bonus = fields.Float(
        string='Phụ cấp ca đêm (+hệ số)', default=0.3,
        help='Cộng vào hệ số nếu ca rơi vào khung đêm (Luật LĐ +30%).')
    holiday_dates = fields.Text(
        string='Ngày lễ (YYYY-MM-DD)',
        help='Danh sách ngày lễ, phân tách bằng dấu phẩy hoặc xuống dòng. '
             'Ca rơi vào ngày lễ → hệ số nền 300%.')
```
Thêm 4 field vào view `views/hocba_attendance_policy_views.xml` — tạo group mới `<group string="Hệ số ca (OT/lễ/đêm)">` chứa `night_start`, `night_end`, `night_bonus`, `holiday_dates`.

---

## 2. `_default_rate` — luật lễ/đêm (`hocba.work_shift`)

File `custom-addons/hocba_attendance/models/hocba_work_shift.py`. Thay thân `_default_rate`:
```python
    @api.model
    def _default_rate(self, start_dt):
        """Hệ số gợi ý: lễ=3.0 / cuối tuần=2.0 / ngày thường=1.5; cộng phụ cấp đêm
        nếu ca rơi khung đêm. Lễ lấy từ policy.holiday_dates (YYYY-MM-DD, phân tách
        dấu phẩy/xuống dòng). start_dt là Datetime UTC naive."""
        if not start_dt:
            return 1.0
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        local = fields.Datetime.context_timestamp(self, start_dt)
        holidays = set((policy.holiday_dates or '').replace(',', ' ').split())
        if local.strftime('%Y-%m-%d') in holidays:
            base = 3.0
        elif local.weekday() >= 5:
            base = 2.0
        else:
            base = 1.5
        hour = local.hour + local.minute / 60.0
        if hour >= (policy.night_start or 22.0) or hour < (policy.night_end or 6.0):
            base += (policy.night_bonus or 0.0)
        return base
```
(Giữ chữ ký `@api.model _default_rate(self, start_dt)` — `_shift_create`/`_shift_decide` gọi không đổi.)

---

## 3. `_att_me_history` — quy đổi công OT theo tháng (`hocba_hrm`)

File `controllers/main.py`, helper `_att_me_history(env, month_str)`. Sau khi dựng `summary` (trước `return`), thêm:
```python
    # --- Công OT quy đổi (Gói 4C): Σ giờ ca approved trong tháng × hệ số ---
    shifts = env['hocba.work_shift'].sudo().search([
        ('employee_id', '=', emp.id), ('state', '=', 'approved')])
    month_shifts = shifts.filtered(
        lambda s: first <= fields.Datetime.context_timestamp(s, s.start).date() <= last)
    ot_hours = sum((s.end - s.start).total_seconds() / 3600.0 for s in month_shifts)
    ot_credit = sum((s.end - s.start).total_seconds() / 3600.0 * s.rate for s in month_shifts)
    summary['otShiftCount'] = len(month_shifts)
    summary['otHours'] = round(ot_hours, 2)
    summary['otCreditHours'] = round(ot_credit, 2)
```
`first`/`last` (date đầu/cuối tháng) đã có sẵn trong `_att_me_history`. `emp` = `env.user.employee_id` (đã có).

---

## 4. Frontend — hiển thị OT trong `MyHistory.jsx`

File `frontend/src/features/attendance/MyHistory.jsx`. Khối summary hiện là `stat-grid` 4 cột (daysPresent, totalCredit, deficitCredit, netCredit). Thêm 2 thẻ OT và đổi lưới thành 6 cột:
- `<Sum val={data.summary.otHours} lbl="Giờ OT" />`
- `<Sum val={data.summary.otCreditHours} lbl="Công OT quy đổi" col="var(--green)" />`
- Đổi `gridTemplateColumns: 'repeat(4,1fr)'` → `'repeat(6,1fr)'`.
(Giá trị có thể là 0 nếu không có ca — vẫn hiển thị 0, chấp nhận.) Build SPA.

---

## 5. Kiểm thử

### Backend — bổ sung vào `custom-addons/hocba_hrm/tests/test_shift_api.py` (đã có `TestShiftApi`)
**`_default_rate` (gọi qua model, set tz context):**
- Ngày thường (T2) giờ ngày (09:00 local) → 1.5.
- Cuối tuần (T7) giờ ngày → 2.0.
- Ngày lễ (đặt `policy.holiday_dates` chứa ngày đó) → 3.0.
- Ca đêm ngày thường (giờ vào 23:00 local) → 1.5 + 0.3 = 1.8.
- Ca đêm sáng sớm (05:00 local) ngày thường → 1.8.

**`_att_me_history` OT (bổ sung vào `test_attendance_request.py` hoặc test mới — khuyến nghị file mới `test_ot_credit.py`):**
- Tạo NV + user; tạo 2 ca approved trong tháng (vd 2h ×1.5 và 3h ×2.0) → `otHours`=5.0, `otCreditHours`=3+6=... (2×1.5=3, 3×2.0=6 → 9.0), `otShiftCount`=2.
- Ca tháng khác KHÔNG tính.
- Ca pending KHÔNG tính.

> Lưu ý: test `_default_rate` phải set tz (`with_context(tz='Asia/Ho_Chi_Minh')` hoặc env user có tz) để weekday/giờ local đúng. Fixture NV official cần CCCD 12 số (BR-010); CTV không cần.

### Frontend (thủ công)
- MyHistory: tháng có ca OT approved → thấy "Giờ OT" + "Công OT quy đổi" đúng. Build sạch.

---

## 6. Phạm vi

**Có làm (4C):** policy `night_*` + `holiday_dates` (+ view); `_default_rate` luật lễ/đêm; `_att_me_history` otHours/otCreditHours/otShiftCount; FE MyHistory 2 thẻ OT; test backend.

**KHÔNG làm:** payroll thật; model ngày lễ riêng; sửa `_do_check`/`needs_review` cửa sổ ca (giới hạn 4B); gộp OT vào `work_credit` ngày.
