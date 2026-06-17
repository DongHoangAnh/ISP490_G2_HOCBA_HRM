# HANDOFF — Nâng cấp hệ thống Chấm công (4 gói)

**Cập nhật:** 17/06/2026 · **Người bàn giao:** phiên làm việc với Claude Code
**Mục đích:** Giúp thành viên khác tiếp tục đúng mạch công việc đang dở. Đọc file này trước, rồi làm theo "Bước tiếp theo".

---

## 1. Bức tranh tổng thể

Nâng cấp module chấm công, chia thành **4 gói phụ thuộc**, làm tuần tự. Mỗi gói theo chu trình: **spec → plan → implement (TDD) → test → merge `main`**.

| Gói | Nội dung | Trạng thái |
|---|---|---|
| **Gói 1** | Tính công (công sáng/chiều, lương theo ngày) + phút trễ/về sớm/thiếu + tổng hợp công tháng (trừ công thiếu, bỏ 2 ngày vi phạm đầu) + chuẩn hóa policy 8h, mốc trễ 9:30 | ✅ **XONG** (đã merge main) |
| **Gói 2** | Tách tài khoản manager (chỉ quản lý, không check-in) ↔ user (tự chấm) + khóa check-in/out 1 lần/ngày, chỉ ngày làm việc + manager sửa/xóa bản ghi theo phạm vi | ✅ **XONG** (đã merge main) |
| **Gói 3** | Luồng **đơn**: user gửi đơn sửa/tạo bản ghi → manager duyệt (chỉnh giờ được) & áp dụng, hoặc từ chối | 🟡 **ĐANG DỞ** — spec xong, **chưa có plan, chưa code** |
| **Gói 4** | Đăng ký ca **CTV/OT** + lịch tuần + manager thêm/duyệt ca + check-in cửa sổ ±15' quanh giờ ca | 🔴 **CHƯA bắt đầu** |

---

## 2. Đang dở ở đâu (Gói 3)

- **Spec đã xong & commit:** [docs/superpowers/specs/2026-06-17-attendance-correction-request-design.md](specs/2026-06-17-attendance-correction-request-design.md). Đã chốt:
  - Đơn bao trùm: (a) sửa bản ghi đã có; (b) ngày thiếu (chưa có bản ghi) → duyệt thì TẠO bản ghi.
  - Luồng: user nhập giờ đề xuất + lý do → manager xem, **chỉnh được giờ** rồi Duyệt (ghi/tạo bản ghi, công tự tính lại) hoặc Từ chối kèm lý do.
  - Model mới `hocba.attendance.request` (gọn, không mail.thread).
- **CHƯA làm:** plan triển khai + code + test. Tab "Đơn quên chấm công" hiện vẫn là **mock** (`FORGOT_REQUESTS` trong `frontend/src/features/attendance/mock.js`) — Gói 3 sẽ thay bằng luồng thật.

---

## 3. Bước tiếp theo (làm đúng thứ tự)

### A. Hoàn tất Gói 3
1. **Viết plan** từ spec Gói 3: dùng skill `superpowers:writing-plans`, lưu vào `docs/superpowers/plans/2026-06-17-attendance-correction-request.md`. (Tham khảo 2 plan đã có của Gói 1/2 trong `docs/superpowers/plans/` làm mẫu cấu trúc + cách viết task TDD.)
2. **Thực thi** plan: skill `superpowers:subagent-driven-development` (giao từng task cho subagent + 2 vòng review spec/chất lượng) — hoặc tự làm theo `superpowers:executing-plans`. Tạo nhánh `feature/attendance-correction-request` trước (đừng code thẳng trên main).
3. **Test** cả 2 suite + build FE (lệnh ở §5), rồi merge về `main` (skill `superpowers:finishing-a-development-branch`).

### B. Làm Gói 4
Bắt đầu bằng `superpowers:brainstorming` (chưa có spec). Yêu cầu gốc của Gói 4 (từ khách):
> CTV và OT tự đăng ký ca làm việc, hiển thị **lịch theo tuần** và cho tự đăng ký. Manager có thể vào thêm ca và **duyệt** ca cho user; ca CTV/OT chỉ **hiển thị sau khi manager duyệt**. Họ cần **check-in trong cửa sổ ±15'** quanh giờ ca (vd ca 9h → mở check-in 8h45–9h15, ngoài thời gian khóa nút); **checkout** có cơ chế tương tự. Cơ chế cửa sổ này CHỈ cho CTV/OT. Vẫn dùng luồng **đơn** (Gói 3) để gửi manager.

Lưu ý: hiện check-in chỉ mở cho NV `official` (CTV bị chặn — xem `api_attendance_check`). Gói 4 sẽ mở check-in cho CTV/OT **theo ca đã duyệt** + cửa sổ ±15' (khác cơ chế ngày-làm-việc của NV official ở Gói 2). Tab "Tăng ca (OT)" hiện vẫn mock (`OT_LOG` trong `mock.js`).

---

## 4. Kiến trúc & điểm bám (đã làm ở Gói 1-2)

**Backend**
- `custom-addons/hocba_attendance/models/hr_attendance.py` — model `hocba.attendance` (1 bản ghi/NV/ngày). Field tính công store: `work_credit`, `morning_credit`, `afternoon_credit`, `late_minutes`, `early_leave_minutes`, `missing_minutes`, `expected_check_out` (compute `_compute_work_metrics`, depends check_in/out). Guard khóa: `_assert_check_allowed(employee, kind)` raise `UserError('<code>')` (not_workday/already_checked_in/not_checked_in/already_checked_out), gọi trong `action_check_in`/`action_check_out`. `_do_check` = lõi face/geo (không sửa).
- `custom-addons/hocba_attendance/models/hocba_attendance_policy.py` — policy: `late_cutoff` 9.5, `morning_credit_cutoff` 10.0, `std_work_hours` 8.0, `afternoon_margin_hours` 2.0, `violation_free_days` 2 + window/workday/geofence.
- `custom-addons/hocba_hrm/controllers/main.py` — API SPA. **Helper module-level tái dùng:** `_user_can_manage(env)`, `_is_dept_manager(env, emp)`, `_emp_scope_domain(env)`, `_emp_in_scope(env, emp)`, `_managed_department_ids(env, emp)`, `_to_utc(env, s)` (local ISO→UTC), `_att_row(rec, policy)`, `_attendance_edit/_attendance_delete`, `_att_day_table`/`_att_me_info`/`_att_me_history`. Map lỗi check-in: `_CHECK_ERR_STATUS`. **Gói 3 nên thêm `_request_*` helper + endpoint cùng file này** (xem spec §2).
- Phạm vi vai trò: HR/Admin = tất cả; trưởng phòng (`hr.department.manager_id`) = phòng mình; giáo vụ = giáo viên; user thường = của mình. `canManage` = bất kỳ nhóm quản lý nào.

**Frontend** (SPA React/Vite, build → `custom-addons/hocba_hrm/static/spa`)
- `frontend/src/features/attendance/`: `Attendance.jsx` (điều phối tab theo `me.canManage`), `CheckInPanel.jsx` (khóa nút + map lỗi), `MyHistory.jsx`, `AttendanceTable.jsx` (bảng ngày manager), `AttendanceDrawer.jsx` (chi tiết + manager Sửa/Xóa), `useFaceApi.js`, `util.js` (`fmtCredit`...), `mock.js` (còn `FORGOT_REQUESTS`+`OT_LOG`).
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
- Plans: `docs/superpowers/plans/2026-06-17-attendance-work-credit.md` (Gói 1), `...account-split-lock.md` (Gói 2). **Gói 3 plan: chưa có — cần viết.**
- Tài khoản test (vai trò): admin / hr_manager / hr / giáo vụ / trưởng phòng / employee / ctv — xem `docs/MANUAL_TEST_GUIDE.md`, `docs/SPEC_USERS_AUTH.md`.
- Quy ước frontend: `docs/QUY_UOC_FRONTEND.md`.

---

## 7. Quy trình làm việc (skills)

Mỗi gói: `brainstorming` (ra spec) → `writing-plans` (ra plan TDD) → `subagent-driven-development` hoặc `executing-plans` (code từng task, test đỏ→xanh→commit) → `finishing-a-development-branch` (merge). Làm trên nhánh `feature/...`, không code thẳng main. Commit nhỏ, thường xuyên; mỗi task chạy test xác nhận xanh trước khi commit.
