# HANDOFF — Nâng cấp hệ thống Chấm công (4 gói)

**Cập nhật:** 19/06/2026 · **Người bàn giao:** phiên làm việc với Claude Code
**Mục đích:** Giúp thành viên khác tiếp tục đúng mạch công việc đang dở. Đọc file này trước, rồi làm theo "Bước tiếp theo".

---

## 1. Bức tranh tổng thể

Nâng cấp module chấm công, chia thành **4 gói phụ thuộc**, làm tuần tự. Mỗi gói theo chu trình: **spec → plan → implement (TDD) → test → merge `main`**.

| Gói | Nội dung | Trạng thái |
|---|---|---|
| **Gói 1** | Tính công (công sáng/chiều, lương theo ngày) + phút trễ/về sớm/thiếu + tổng hợp công tháng (trừ công thiếu, bỏ 2 ngày vi phạm đầu) + chuẩn hóa policy 8h, mốc trễ 9:30 | ✅ **XONG** (đã merge main) |
| **Gói 2** | Tách tài khoản manager (chỉ quản lý, không check-in) ↔ user (tự chấm) + khóa check-in/out 1 lần/ngày, chỉ ngày làm việc + manager sửa/xóa bản ghi theo phạm vi | ✅ **XONG** (đã merge main) |
| **Gói 3** | Luồng **đơn**: user gửi đơn sửa/tạo bản ghi → manager duyệt (chỉnh giờ được) & áp dụng, hoặc từ chối | ✅ **XONG** (đã merge main) |
| **Gói 4A** | Đăng ký ca **CTV/OT** + **lịch tuần** (lưới 7 cột) + manager thêm/duyệt/từ chối ca + hủy ca pending; hệ số auto theo luật (T2-6=1.5 / cuối tuần=2.0) | ✅ **XONG** (đã merge main) |
| **Gói 4B** | Check-in **cửa sổ ±15'** quanh giờ ca cho CTV/OT (mở check-in theo ca đã duyệt; official giữ cơ chế workday Gói 2) | ✅ **XONG** (đã merge main; đã sửa cờ needs_review nhiễu cho CTV) |
| **Gói 4C** | Tính **công OT theo 3 mốc hệ số** {100/150/300%} chọn tay (bỏ auto theo thứ), giờ OT quy đổi gộp vào tổng hợp tháng (cả official + CTV), tab "Chấm công OT" cho manager, API `_ot_table`/`_shift_set_level` + routes | ✅ **XONG** (nhánh `feature/ot-credit-rate`; chờ merge main) |

---

## 2. Gói 3 — đã hoàn tất (nhánh `feature/attendance-correction-request`)

- **Spec:** [docs/superpowers/specs/2026-06-17-attendance-correction-request-design.md](specs/2026-06-17-attendance-correction-request-design.md). **Plan:** [docs/superpowers/plans/2026-06-17-attendance-correction-request.md](plans/2026-06-17-attendance-correction-request.md) (14 task TDD).
- **Đã làm (test xanh 46/46 suite `hocba_hrm`, build SPA sạch):**
  - Model `hocba.attendance.request` + ACL (`hocba_attendance`).
  - Helper backend module-level trong `controllers/main.py`: `_req_row`, `_request_apply` (duyệt → ghi/tạo bản ghi), `_request_create` (user gửi, pin employee), `_request_decide` (manager duyệt/từ chối, chỉnh giờ override), `_att_requests_mine`, `_att_requests_pending` (theo phạm vi vai trò).
  - 5 endpoint: `POST /api/attendance/requests`, `GET .../requests/mine`, `GET .../requests/pending`, `POST .../requests/<id>/approve|reject`.
  - FE: `RequestForm.jsx` (gửi đơn 2 chế độ), `RequestList.jsx` (user xem / manager duyệt), tab "Đơn của tôi" (user) + "Đơn chấm công" (manager) trong `Attendance.jsx`, nút "Gửi đơn sửa" trong `AttendanceDrawer.jsx`. Đã bỏ mock `FORGOT_REQUESTS` (giữ `OT_LOG` cho Gói 4).
- **Còn lại:** merge nhánh về `main`; kiểm thử thủ công SPA (xem spec §4) trên DB demo.

---

## 3. Bước tiếp theo (làm đúng thứ tự)

### A. Gói 3 — ĐÃ XONG (xem §2)
Đã merge `main`. Test 46/46 xanh, build SPA sạch.

### B. Gói 4A — ĐÃ XONG (nhánh `feature/shift-registration`)
- **Spec:** [docs/superpowers/specs/2026-06-17-shift-registration-design.md](specs/2026-06-17-shift-registration-design.md). **Plan:** [docs/superpowers/plans/2026-06-17-shift-registration.md](plans/2026-06-17-shift-registration.md) (13 task TDD).
- **Đã làm (test xanh 70/70 suite `hocba_hrm`, build SPA sạch):**
  - Model `hocba.work_shift` + ACL (`hocba_attendance`): `start`/`end` (Datetime UTC), `shift_type` (ctv/ot chọn tay), `rate` (Float), `state` (pending/approved/rejected), reviewer/review_note/decision_date, related `department_id`. Constraint `_check_times` (end>start) + `_check_overlap` (chặn trùng giờ pending/approved). `_default_rate(start)` = T2-6→1.5, T7/CN→2.0.
  - Helper module-level trong `controllers/main.py`: `_shift_row`, `_shift_create` (pin employee; manager gửi `empId` trong phạm vi → tạo hộ, vào thẳng approved), `_shifts_week` (lịch tuần T2→CN; owner thấy mọi state, người khác chỉ approved trong phạm vi — dùng `expression.OR`), `_shift_decide` (manager duyệt/từ chối, override start/end/type/rate), `_shift_cancel` (owner/manager hủy ca pending).
  - 5 endpoint: `POST /api/shifts`, `GET .../shifts/week?monday=`, `POST .../shifts/<id>/approve|reject`, `POST .../shifts/<id>/cancel`.
  - FE: `ShiftCalendar.jsx` (lưới 7 cột, chuyển tuần ‹›, nút Đăng ký ca), `ShiftForm.jsx`, `ShiftDrawer.jsx` (manager override+duyệt/từ chối / owner hủy). Tab "Ca làm việc (CTV/OT)" thay `OtMock` cho cả user lẫn manager. **Đã xóa `mock.js`** (hết mock).
- **Còn lại:** merge nhánh về `main`; kiểm thử thủ công SPA (spec §4).

### C. Làm Gói 4B rồi 4C (bước kế tiếp)
Yêu cầu gốc Gói 4 (từ khách) đã tách: 4A (lịch+đăng ký) xong; còn:
> ...check-in trong **cửa sổ ±15'** quanh giờ ca (vd ca 9h → mở check-in 8h45–9h15, ngoài thời gian khóa nút); **checkout** có cơ chế tương tự. Cơ chế cửa sổ này CHỈ cho CTV/OT. ...OT có **hệ số** (150/200/300%) tính công/lương.

- **Gói 4B (check-in cửa sổ ±15') — ✅ XONG (đã merge main; đã sửa cờ needs_review nhiễu cho CTV):** Spec [2026-06-18-shift-checkin-window-design.md](specs/2026-06-18-shift-checkin-window-design.md), plan [2026-06-18-shift-checkin-window.md](plans/2026-06-18-shift-checkin-window.md). Test 81/81 xanh, build SPA sạch.
  - Policy `shift_window_minutes` (default 15) + view.
  - Model `hocba.attendance`: `_todays_approved_shifts(emp, today)` + `_assert_shift_check_allowed(emp, kind)` (no_shift_today / outside_shift_window / already_checked_in / not_checked_in / already_checked_out).
  - `api_attendance_check` **phân nhánh**: official → `_assert_check_allowed` (workday Gói 2); non-official (CTV/OT) → `_assert_shift_check_allowed` (ca + cửa sổ). Bỏ block `not_official`. Gọi trực tiếp `_do_check` (pin employee_id). Thêm mã lỗi vào `_CHECK_ERR_STATUS`.
  - `_att_me_info.shiftToday` = {start, end, shiftType, rate, checkInOpen, checkOutOpen} (None cho official / non-official không có ca).
  - FE `CheckInPanel.jsx`: non-official → enroll → "chưa có ca" → UI check-in/out theo ca (nút khóa khi ngoài cửa sổ); official giữ nguyên. Bỏ cảnh báo "ngoài khung giờ" cho CTV.
  - **Cờ `needs_review` nhiễu đã sửa trong Gói 4C:** `_do_check` đã được cập nhật để nhận biết cửa sổ ca — ca CTV/OT check-in đúng cửa sổ không còn bị `needs_review`. Đã merge main.

- **Gói 4C (công OT theo hệ số) — ✅ XONG (nhánh `feature/ot-credit-rate`):** Spec [2026-06-19-ot-credit-rate-design.md](specs/2026-06-19-ot-credit-rate-design.md), plan [2026-06-19-ot-credit-rate.md](plans/2026-06-19-ot-credit-rate.md). Test 43/43 (hocba_attendance) + 95/95 (hocba_hrm) xanh.
  - **Backend model:** Field `ot_level` (Selection '100'/'150'/'300', default '100') thay `_default_rate`. Field `rate` (Float, compute+store từ `ot_level`). Map `_OT_RATE = {'100': 1.0, '150': 1.5, '300': 3.0}`. Bỏ hệ số auto theo thứ (T2-6/cuối tuần).
  - **`_do_check`:** nhận biết cửa sổ ca → không set `out_of_window`/`needs_review` cho CTV/OT check-in đúng (sửa giới hạn 4B).
  - **`_att_me_history`:** gộp `otHours` (tổng giờ OT) + `otCreditHours` (tổng giờ OT quy đổi = Σ hours × rate) cho mỗi tháng — cả official lẫn CTV.
  - **`_ot_row` / `_ot_for_employee`:** helper tổng hợp ca OT đã approved theo tháng (date, shiftType, hours, counted, creditHours, otLevel).
  - **`_ot_table`:** aggregate OT tất cả nhân viên trong phạm vi (manager) → `GET /api/attendance/ot-summary`.
  - **`_shift_set_level`:** cập nhật `ot_level` cho ca → `POST /api/shifts/<id>/level` (body `{otLevel}`).
  - **FE:** Tab "Chấm công OT" trong `Attendance.jsx` (manager): bảng `OtTable.jsx` + drawer `OtDrawer.jsx` (manager chỉnh `ot_level`). `MyHistory.jsx` hiển thị `otHours`/`otCreditHours`. Nút "Đổi hệ số" gọi `setShiftLevel` qua `attendance.js`.

  **Migration caveat:** Vì `rate` đổi sang computed-store từ `ot_level` (mặc định '100'), khi chạy `-u hocba_attendance` các ca CTV/OT cũ sẽ tính lại `rate` về 1.0. Chấp nhận trên DB demo; nếu DB thật có ca cần giữ hệ số, phải migrate `ot_level` trước khi upgrade.

  **Sửa kèm theo:** Một lỗi build SPA có sẵn trước (thiếu `}` đóng trong `App.jsx` ở dòng Recruitment, đưa vào bởi merge TimeOff) đã được sửa trong nhánh này.

  **Còn lại:** merge nhánh `feature/ot-credit-rate` về `main`; kiểm thử thủ công SPA (xem spec §4 và plan §testing).

---

## 4. Kiến trúc & điểm bám (đã làm ở Gói 1-2)

**Backend**
- `custom-addons/hocba_attendance/models/hr_attendance.py` — model `hocba.attendance` (1 bản ghi/NV/ngày). Field tính công store: `work_credit`, `morning_credit`, `afternoon_credit`, `late_minutes`, `early_leave_minutes`, `missing_minutes`, `expected_check_out` (compute `_compute_work_metrics`, depends check_in/out). Guard khóa: `_assert_check_allowed(employee, kind)` raise `UserError('<code>')` (not_workday/already_checked_in/not_checked_in/already_checked_out), gọi trong `action_check_in`/`action_check_out`. `_do_check` = lõi face/geo (không sửa).
- `custom-addons/hocba_attendance/models/hocba_attendance_policy.py` — policy: `late_cutoff` 9.5, `morning_credit_cutoff` 10.0, `std_work_hours` 8.0, `afternoon_margin_hours` 2.0, `violation_free_days` 2 + window/workday/geofence.
- `custom-addons/hocba_hrm/controllers/main.py` — API SPA. **Helper module-level tái dùng:** `_user_can_manage(env)`, `_is_dept_manager(env, emp)`, `_emp_scope_domain(env)`, `_emp_in_scope(env, emp)`, `_managed_department_ids(env, emp)`, `_to_utc(env, s)` (local ISO→UTC), `_att_row(rec, policy)`, `_attendance_edit/_attendance_delete`, `_att_day_table`/`_att_me_info`/`_att_me_history`. Map lỗi check-in: `_CHECK_ERR_STATUS`. **Gói 3 nên thêm `_request_*` helper + endpoint cùng file này** (xem spec §2).
- Phạm vi vai trò: HR/Admin = tất cả; trưởng phòng (`hr.department.manager_id`) = phòng mình; giáo vụ = giáo viên; user thường = của mình. `canManage` = bất kỳ nhóm quản lý nào.

**Frontend** (SPA React/Vite, build → `custom-addons/hocba_hrm/static/spa`)
- `frontend/src/features/attendance/`: `Attendance.jsx` (điều phối tab theo `me.canManage`), `CheckInPanel.jsx` (khóa nút + map lỗi), `MyHistory.jsx`, `AttendanceTable.jsx` (bảng ngày manager), `AttendanceDrawer.jsx` (chi tiết + manager Sửa/Xóa + nút Gửi đơn sửa), `RequestForm.jsx`/`RequestList.jsx` (Gói 3), `useFaceApi.js`, `util.js` (`fmtCredit`...), `mock.js` (chỉ còn `OT_LOG` cho Gói 4).
- `frontend/src/api/attendance.js` — hàm gọi API (`editAttendance`, `deleteAttendance`...). Client `frontend/src/api/client.js` ném `ApiError` có `.code` = field `error` của response.

---

## 5. Lệnh test & build + cạm bẫy (QUAN TRỌNG)

Chạy test trên stack Docker local (KHÔNG chạy test trên Neon). Docker Desktop phải bật. **`MSYS_NO_PATHCONV=1` BẮT BUỘC trên Git Bash Windows** (thiếu nó → chạy 0 test mà vẫn báo "thành công"). Luôn xác nhận số test in ra **khác 0**. Luôn `-u <module>,hocba_employees` để đồng bộ schema (tránh lỗi `x_eval_*`).

```bash
# hocba_attendance
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_attendance,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
# hocba_hrm
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
# Build SPA
cd frontend && npm install && npm run build   # output → custom-addons/hocba_hrm/static/spa
```
Dòng kết quả cần thấy: `0 failed, 0 error(s) of N tests` với **N > 0**.

**Cạm bẫy:**
- **BR-010:** NV `official` trong test PHẢI có `identification_id` (CCCD) **đúng 12 chữ số** (mỗi NV một giá trị khác nhau) — không thì `ValidationError` ngay ở setUp. Xem chi tiết: [../../memory](#) (memory `br010-official-employee-cccd`).
- Self-service (user thường) không có ACL trên policy/attendance → đọc/ghi qua `.sudo()` sau khi đã kiểm phạm vi/pin employee (pattern hiện có).
- Giờ lưu UTC; test truyền UTC với `.with_context(tz='Asia/Ho_Chi_Minh')` (+07): 09:00 local = 02:00 UTC.
- Test controller `hocba_hrm`: lần đầu nếu báo `of 0 tests` thì `-i hocba_hrm` (cài) trước, sau đó `-u` chạy được.

---

## 6. Tài liệu tham chiếu

- Specs: `docs/superpowers/specs/2026-06-17-attendance-work-credit-design.md` (Gói 1), `...account-split-lock-design.md` (Gói 2), `...correction-request-design.md` (Gói 3).
- Plans: `docs/superpowers/plans/2026-06-17-attendance-work-credit.md` (Gói 1), `...account-split-lock.md` (Gói 2), `...correction-request.md` (Gói 3).
- Tài khoản test (vai trò): admin / hr_manager / hr / giáo vụ / trưởng phòng / employee / ctv — xem `docs/MANUAL_TEST_GUIDE.md`, `docs/SPEC_USERS_AUTH.md`.
- Quy ước frontend: `docs/QUY_UOC_FRONTEND.md`.

---

## 7. Quy trình làm việc (skills)

Mỗi gói: `brainstorming` (ra spec) → `writing-plans` (ra plan TDD) → `subagent-driven-development` hoặc `executing-plans` (code từng task, test đỏ→xanh→commit) → `finishing-a-development-branch` (merge). Làm trên nhánh `feature/...`, không code thẳng main. Commit nhỏ, thường xuyên; mỗi task chạy test xác nhận xanh trước khi commit.
