# DB Schema & Hướng dẫn dựng DB lên server — Học Bá HRM

> Tài liệu này mô tả **cấu trúc database** của hệ thống Học Bá HRM (Odoo 19) và
> **cách dựng lại / migrate DB lên server riêng** khi không còn dùng Neon.
>
> **Điều quan trọng cần hiểu trước:** Trong Odoo, schema PostgreSQL (bảng, cột,
> khóa, ràng buộc) **không viết tay bằng SQL**. Odoo tự sinh DDL từ các model
> Python (`custom-addons/*/models/*.py`) khi **cài/upgrade module**. Vì vậy:
> - Phần **A–E** dưới đây là *tài liệu tham khảo* schema (đọc để hiểu, làm báo cáo, vẽ ERD).
> - Phần **F** là *quy trình thực tế* để dựng DB lên server mới — bằng cách cài module
>   hoặc dump/restore, **không** chạy file `.sql` tự chế.

Cập nhật lần cuối: 2026-06-24 · Phạm vi: custom + bảng Odoo core liên quan.

---

## A. Tổng quan kiến trúc DB

- **DBMS**: PostgreSQL (Neon cloud hiện tại → đích là Postgres tự host). Odoo 19 yêu cầu **PostgreSQL ≥ 13** (khuyến nghị 15, đúng version đang dùng local).
- **Một database = một instance Odoo**. Tên DB hiện tại: `neondb` (Neon) / `hocba_hrm` (Docker local).
- Mọi bảng nghiệp vụ nằm trong **một** database đó. Ngoài bảng custom còn có **hàng trăm bảng core Odoo** (`ir_*`, `res_*`, `hr_*`, `mail_*`...) do framework + các module phụ thuộc sinh ra.
- **CMS Mabble (MySQL ngoài)**: chỉ là nguồn dữ liệu đọc qua API (lịch dạy, import giáo viên). **Không** thuộc DB này, **không** cần migrate cùng. Cấu hình qua biến `CMS_MYSQL_*`.
- Module custom dùng tiền tố bảng:
  - `hocba_*` — module thế hệ mới (employees, attendance, users).
  - `hb_*` — module payroll, recruitments, timeoff.
  - Bảng mở rộng (`_inherit` thuần) **thêm cột** vào bảng core (`hr_employee`, `res_users`...), **không** tạo bảng mới.

---

## B. Thứ tự cài đặt module (dependency graph)

Khi dựng DB mới, **phải cài đúng thứ tự phụ thuộc** (Odoo tự lo nếu liệt kê đủ tên, nhưng hiểu thứ tự giúp debug):

```
base, web, mail                      (lõi Odoo — luôn có sẵn)
 └─ hr                               (Employees core)
     ├─ hr_skills                    → hocba_employees
     ├─ hr_holidays                  → hocba_timeoff
     ├─ hr_recruitment               → hocba_recruitments
     │
     ├─ hocba_employees  ──────────┐ (nền tảng — gần như mọi module phụ thuộc)
     │   ├─ hocba_attendance ───────┤
     │   │     └─ hocba_users        │  (users phụ thuộc cả attendance + employees)
     │   ├─ hocba_payroll  ──────────┤  (phụ thuộc employees + attendance + mail)
     │   ├─ hocba_recruitments ──────┤
     │   └─ hocba_hrm  ──────────────┘  (controller API + SPA, route /hocba-hrm)
     └─ hocba_timeoff                   (phụ thuộc hr_holidays)
```

**Bảng phụ thuộc trực tiếp (từ `__manifest__.py`):**

| Module | `depends` |
|--------|-----------|
| `hocba_employees` | `hr`, `hr_skills` |
| `hocba_attendance` | `hr`, `web`, `hocba_employees` |
| `hocba_users` | `hr`, `web`, `hocba_attendance`, `hocba_employees` |
| `hocba_payroll` | `hr`, `mail`, `hocba_employees`, `hocba_attendance` |
| `hocba_recruitments` | `hr_recruitment`, `hocba_employees` |
| `hocba_timeoff` | `hr_holidays` |
| `hocba_hrm` | `base`, `hr`, `hocba_employees`, `hocba_attendance` |

**Danh sách cài đặt khuyến nghị (một dòng `-i`):**
```
hocba_employees,hocba_attendance,hocba_users,hocba_recruitments,hocba_payroll,hocba_timeoff,hocba_hrm
```

> ⚠️ **Legacy:** `docker-compose.local.yml` hiện còn init các module cũ
> `hr_holidays_modern`, `hb_timeoff_config/policy/emergency/medical_validation/schedule_conflict/analytics`.
> Theo CLAUDE.md đây là **tồn đọng đang dọn** — module timeoff đang hoạt động là
> **`hocba_timeoff`**. Khi dựng server mới, **chỉ cài `hocba_timeoff`**, bỏ các `hb_timeoff_*` legacy
> (chúng gây cảnh báo "not loaded"/"inconsistent states", vô hại nhưng nên bỏ cho sạch).

---

## C. Schema chi tiết — bảng do module custom tạo mới

Quy ước: tên bảng PostgreSQL = `_name` thay `.` bằng `_`. PK luôn là `id` (serial).
Mọi bảng còn có các cột audit chuẩn Odoo: `create_uid`, `create_date`, `write_uid`, `write_date`.
Selection lưu dưới dạng `VARCHAR`.

### C.1 — `hocba_employees`

#### `hocba_employee_type` — Loại nhân viên
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| sequence | int | default 10 |
| name | varchar | NOT NULL |
| code | varchar | NOT NULL, **UNIQUE** |
| description | text | |
| color_code | varchar | default `#0066CC` |
| benefits | text | |
| active | bool | default true |

#### `hocba_asset_type` — Loại tài sản cấp phát
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| sequence | int | default 10 |
| name | varchar | NOT NULL |
| code | varchar | NOT NULL, **UNIQUE** |
| x_is_default | bool | cấp tự động khi onboarding |
| active | bool | default true |

#### `hr_employee_asset` — Tài sản nhân viên đang giữ
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **restrict**, index |
| asset_type_id | m2o → `hocba_asset_type` | NOT NULL |
| asset_code | varchar | NOT NULL (unique khi state=assigned) |
| grant_date | date | NOT NULL, default today |
| condition_in | varchar | NOT NULL, default `good` (new/good/fair) |
| state | varchar | NOT NULL, default `assigned`, index (assigned/returned/transferred) |
| return_date | date | bắt buộc khi returned |
| transferred_to | m2o → `hr_employee` | bắt buộc khi transferred |
| condition_out_note | text | |

#### `hr_employee_dependent` — Người phụ thuộc (giảm trừ gia cảnh)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| name | varchar | NOT NULL |
| relationship | varchar | NOT NULL (spouse/child/parent/sibling/other) |
| birthday | date | NOT NULL |
| national_id | varchar | |
| date_start | date | NOT NULL |
| date_end | date | |
| notes | text | |

#### `hr_promotion_history` — Lịch sử thăng tiến & lương (audit, không xóa được)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **restrict**, index |
| x_change_type | varchar | NOT NULL, default `promotion`, index (join/probation/promotion/salary/other) |
| date_effective | date | NOT NULL, default today |
| from_job_id / to_job_id | m2o → `hr_job` | |
| to_department_id | m2o → `hr_department` | |
| x_work_form | varchar | offline/online |
| x_employment_status | varchar | (xem hr_employee) |
| from_wage / to_wage | float | group hr_manager |
| allowance_note / reason | text | reason bắt buộc khi đổi lương |
| x_evidence_url / decision_ref | varchar | evidence bắt buộc khi đổi lương |
| approved_by | m2o → `res_users` | NOT NULL, default current user |

> **Mở rộng `hr_employee`, `hr_department`, `hr_employee_skill`, `hr_version`** — xem Mục D.

### C.2 — `hocba_users`

#### `hocba_user_role` — Vai trò hệ thống
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| sequence | int | default 10 |
| name | varchar | NOT NULL |
| code | varchar | NOT NULL, **UNIQUE** (admin/hr_manager/employee/contractor) |
| description / permissions | text | |
| active | bool | default true |
| color_code | varchar | default `#808080` |
| *(M2M)* group_ids → `res_groups` | bảng nối tự sinh | nhóm quyền Odoo liên kết |

#### `hocba_user` — Người dùng HOCBA (wrapper của res.users)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | varchar | NOT NULL |
| user_id | m2o → `res_users` | NOT NULL, ondelete **cascade**, **UNIQUE** |
| email | varchar | related res_users.email, store |
| role_id | m2o → `hocba_user_role` | NOT NULL, ondelete **restrict** |
| role_code | varchar | related role_id.code, store |
| employee_id | m2o → `hr_employee` | ondelete **set null** |
| employee_type_id | m2o → `hocba_employee_type` | related, store |
| department_id | m2o → `hr_department` | related, store |
| is_active | bool | default true (đồng bộ res_users.active) |
| last_login | timestamp | |
| created_at / updated_at | timestamp | default now |

#### `hocba_access_control` — Quyền chi tiết (module + action)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| user_id | m2o → `hocba_user` | NOT NULL, ondelete **cascade** |
| module_name | varchar | NOT NULL (attendance/leaves/reports/admin/hr_management) |
| action | varchar | NOT NULL (read/write/create/delete/all) |
| allowed | bool | default true |
| notes | text | |
| | | **UNIQUE(user_id, module_name, action)** |

#### `hocba_department_manager` — Phân công quản lý phòng ban
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| department_id | m2o → `hr_department` | NOT NULL, ondelete **cascade** |
| user_id | m2o → `hocba_user` | NOT NULL, ondelete **cascade** |
| can_manage_attendance | bool | default true |
| can_manage_leaves | bool | default true |
| can_manage_employees | bool | default false |
| can_approve_reports | bool | default false |
| | | **UNIQUE(department_id, user_id)** |

> **Mở rộng `res_users`** (set tz mặc định `Asia/Ho_Chi_Minh`) — xem Mục D.

### C.3 — `hocba_attendance`

#### `hocba_work_shift` — Ca làm việc / OT
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| start / end | timestamp | NOT NULL |
| shift_type | varchar | NOT NULL (ctv/ot) |
| ot_level | varchar | NOT NULL, default `100` (100/150/300 %) |
| rate | float | computed, store |
| state | varchar | NOT NULL, default `pending`, index (pending/approved/rejected) |
| reason / review_note | text | |
| reviewer_id | m2o → `res_users` | |
| decision_date / deadline | timestamp | deadline computed store |
| department_id | m2o → `hr_department` | related, store |

#### `hocba_work_assignment` — Phân công công việc
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | varchar | NOT NULL |
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade** |
| job_title / project_name | varchar | |
| description | text | |
| assigned_date | date | NOT NULL, default today |
| end_date | date | |
| active | bool | default true |
| department_id | m2o → `hr_department` | related, store |

#### `hocba_attendance_status` — Trạng thái chấm công (danh mục)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| sequence | int | default 10 |
| name | varchar | NOT NULL |
| code | varchar | NOT NULL, **UNIQUE** |
| description | text | |
| color_code | varchar | default `#808080` |
| active | bool | default true |

#### `hocba_attendance_policy` — Chính sách chấm công (geofence/giờ/face)
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| name | varchar | NOT NULL, default 'Default Policy' |
| active | bool | default true |
| morning_start/end, evening_start/end | float | khung giờ sáng/chiều |
| workday_mon..workday_sun | bool | T2–T6 true, T7/CN false |
| office_lat / office_lng | float(10,7) | tọa độ văn phòng |
| office_radius_m | float | default 150 |
| face_threshold | float | default 0.6 |
| late_cutoff, morning_credit_cutoff | float | |
| std_work_hours | float | default 8 |
| afternoon_margin_hours | float | default 2 |
| violation_free_days | int | default 2 |
| shift_window_minutes | int | default 15 |

#### `hocba_attendance` — Bản ghi chấm công (HOCBA, khác hr.attendance core)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| check_in | timestamp | NOT NULL |
| check_out | timestamp | |
| work_assignment_id | m2o → `hocba_work_assignment` | ondelete **set null** |
| department_id | m2o → `hr_department` | related, store |
| status_id | m2o → `hocba_attendance_status` | computed, store |
| status_code | varchar | related, store |
| date | date | computed, store, index |
| working_hours, expected_check_out | float/timestamp | computed metrics |
| late_minutes, early_leave_minutes, missing_minutes | int | computed |
| morning_credit, afternoon_credit, work_credit | float | computed |
| check_in_photo / check_out_photo | binary (attachment) | |
| check_in_lat/lng, check_out_lat/lng | float(10,7) | |
| check_in_face_score, check_out_face_score | float | |
| face_suspect, out_of_zone, out_of_window, needs_review | bool | |
| active | bool | default true |

#### `hocba_attendance_request` — Đơn xin sửa/giải trình chấm công
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| request_date | date | NOT NULL |
| attendance_id | m2o → `hocba_attendance` | ondelete **set null** |
| proposed_check_in / proposed_check_out | timestamp | |
| reason | text | NOT NULL |
| state | varchar | NOT NULL, default `pending`, index |
| reviewer_id | m2o → `res_users` | |
| review_note | text | · decision_date timestamp |
| department_id | m2o → `hr_department` | related, store |

#### `hocba_shift_attendance` — Chấm công theo ca
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| shift_id | m2o → `hocba_work_shift` | NOT NULL, ondelete **cascade**, index, **UNIQUE** (1 ca = 1 bản ghi) |
| employee_id | m2o → `hr_employee` | related shift_id, store, index |
| check_in / check_out | timestamp | |
| check_in_photo / check_out_photo | text (base64) | |
| *(lat/lng, face_score, face_suspect, out_of_zone, out_of_window)* | như hocba_attendance | |
| worked_hours | float | computed, store |

#### `hocba_teaching_attendance` — Chấm công buổi dạy (theo session CMS)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| cms_session_id | varchar | NOT NULL, index |
| cms_class_id | varchar | index |
| class_name | varchar | |
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| session_date | date | index · session_start/end varchar · role_type varchar |
| check_in / check_out | timestamp | |
| *(photo/lat/lng/face/flags)* | như trên | |
| worked_hours | float | computed, store |
| | | **UNIQUE(cms_session_id, employee_id)** |

### C.4 — `hocba_timeoff`

#### `hb_timeoff_policy_rule` — Quy tắc chính sách nghỉ phép theo loại NV
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | varchar | NOT NULL |
| employment_type | varchar | NOT NULL, index, **UNIQUE** (fulltime/teacher/ta/parttime/visiting/ctv) |
| accrual_plan_id | m2o → `hr_leave_accrual_plan` | |
| allocation_mode | varchar | NOT NULL, default `none` (accrual/fixed/none) |
| annual_days | float | default 0 |
| active | bool | default true · notes text |
| *(M2M)* leave_type_ids → `hr_leave_type` | bảng nối `hb_policy_rule_leave_type_rel(rule_id, leave_type_id)` | |

#### `hb_leave_policy_log` — Lịch sử áp/đổi chính sách
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| old_policy_id / new_policy_id | m2o → `hb_timeoff_policy_rule` | ondelete **set null** |
| applied_date | timestamp | NOT NULL, default now |
| triggered_by | varchar | NOT NULL, default `auto` (auto/manual/probation) |
| notes | text | |
| *(M2M)* allocation_ids → `hr_leave_allocation` | bảng nối `hb_policy_log_allocation_rel(log_id, allocation_id)` | |

#### `hb_leave_adjustment` — Điều chỉnh quỹ phép thủ công (HR)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| employee_id | m2o → `hr_employee` | NOT NULL, ondelete **cascade**, index |
| leave_type_id | m2o → `hr_leave_type` | NOT NULL, ondelete **cascade** |
| delta_days | float | NOT NULL · reason text NOT NULL |
| allocation_id | m2o → `hr_leave_allocation` | ondelete **set null** |
| applied_by | m2o → `hr_employee` | default current user's employee |
| applied_date | timestamp | NOT NULL, default now |

#### `hb_work_day` — Ngày làm việc thêm (lịch công ty)
| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | varchar | default 'Ngày đi làm' |
| date | date | NOT NULL, index |
| company_id | m2o → `res_company` | default env.company |
| | | **UNIQUE(date, company_id)** |

#### SQL Views (model `_auto=False` — **VIEW**, không phải table)
- **`hb_timeoff_burnout_line`** — cảnh báo burnout (gom số đơn ốm/vắng 3 tháng, quỹ phép còn lại). Tạo bằng `CREATE VIEW` khi cài module.
- **`hb_timeoff_leave_analysis`** — phân tích đơn nghỉ (year/month, is_sick, is_emergency).
- `hb.timeoff.cron` là **AbstractModel** → **không** có bảng.

> **Mở rộng** `hr_employee` (x_hb_leave_emp_type, x_policy_override, x_current_policy_id...),
> `hr_leave` (emergency/medical/schedule_conflict flags), `hr_leave_allocation` (x_from_policy),
> `hr_leave_type` (x_is_emergency_type) — xem Mục D.

### C.5 — `hocba_payroll` (tiền tố `hb_`)

| Bảng | Vai trò | Khóa/quan hệ chính |
|------|---------|--------------------|
| `hb_contract` | Hợp đồng lao động + cấu hình lương/phụ cấp/BHXH | employee_id → hr_employee (restrict); x_structure_id → hb_salary_structure; nhiều cột phụ cấp `x_pc_*`, `x_sp_*`, đơn giá giờ dạy `x_*_rate` |
| `hb_salary_structure` | Cấu trúc lương | code **UNIQUE**; rule_ids ← hb_salary_rule |
| `hb_salary_rule` | Quy tắc tính lương (fixed/%/formula/code/lookup) | structure_id → hb_salary_structure (cascade); category_id → hb_salary_rule_category (restrict) |
| `hb_salary_rule_category` | Danh mục quy tắc | code **UNIQUE** |
| `hb_payslip_run` | Lô phiếu lương theo kỳ | state draft/verify/close; slip_ids ← hb_payslip |
| `hb_payslip` | Phiếu lương | employee_id → hr_employee (restrict); contract_id, structure_id, payslip_run_id (cascade); `number` auto-sequence; `x_access_token` cho self-service; gross_amount/net_amount computed store |
| `hb_payslip_line` | Dòng chi tiết phiếu | payslip_id (cascade); rule_id/category_id (set null) |
| `hb_payslip_input` | Input thủ công (khấu trừ/tạm ứng) | payslip_id (cascade) |
| `hb_payslip_worked_days` | Công làm việc trong kỳ | payslip_id (cascade) |
| `hb_work_entry` | Bản ghi giờ dạy | employee_id (cascade); work_entry_type_id; duration computed |
| `hb_work_entry_type` | Loại work entry | code **UNIQUE** |
| `hb_bank_format` | Cấu hình format file ngân hàng | code **UNIQUE**; formatter_class |
| `hb_bank_file` | Log file thanh toán đã sinh | batch_id → hb_payslip_run (restrict); bank_format_id (restrict); attachment_id → ir_attachment |

Phần lớn các bảng này `_inherit = 'mail.thread'` ⇒ tạo thêm record trong `mail_message` / `mail_followers` (bảng core).

### C.6 — `hocba_recruitments` (tiền tố `hb_`)

| Bảng | Vai trò | Khóa/quan hệ chính |
|------|---------|--------------------|
| `hb_recruitment_request` | Phiếu yêu cầu tuyển dụng | department_id → hr_department (NOT NULL); job_id → hr_job; `name` auto-sequence; state draft/submitted/recruiting/closed/refused (index) |
| `hb_interview_slot` | Slot lịch phỏng vấn | user_id → res_users; applicant_id → hr_applicant; department_id computed store; state available/booked |
| `hb_interview_slot_wizard` | **TransientModel** (wizard, dữ liệu tạm, tự dọn) | line_ids ← wizard_line |
| `hb_interview_slot_wizard_line` | **TransientModel** | wizard_id (cascade) |

> **Mở rộng** `hr_job` (x_published, recruitment_status, jd_google_link, x_teaching_level...),
> `hr_recruitment_stage` (success_criteria, support_person), `hr_applicant` (cv_link, interview_*,
> offer_*...) — xem Mục D. Các bảng `hb_*` ở đây `_inherit mail.thread/mail.activity.mixin`.

---

## D. Bảng Odoo core liên quan (module custom **thêm cột** vào, không tạo mới)

Các bảng này **đã tồn tại** trong Odoo (do `hr`, `hr_holidays`, `hr_recruitment`...). Module custom
chỉ `ALTER TABLE ADD COLUMN`. Khi dựng DB mới, chúng tự có khi cài các module `depends`.

| Bảng core | Module thêm cột | Cột tiêu biểu (custom) |
|-----------|-----------------|------------------------|
| `hr_employee` | employees / timeoff | `x_employee_code` (UNIQUE, index), `x_work_form`, `x_employment_status`, `x_position_type`, `x_employee_type_id`→hocba_employee_type, `x_seniority_level`, `x_official_date`, hồ sơ pháp lý VN (`x_pit_code`, `x_social_insurance_no`...), liên kết CMS/face (`x_cms_user_id`, `x_face_descriptor`...), địa chỉ thường/tạm trú, dòng thời gian thử việc + 3 cổng đánh giá (`x_eval_2w_*`, `x_eval_1m_*`, `x_eval_2m_*`), thử giảng (`x_trial_*`); + timeoff: `x_hb_leave_emp_type`, `x_current_policy_id` |
| `hr_department` | employees | `x_function_desc` |
| `hr_employee_skill` | employees | `x_cert_date`, `x_cert_expiry`, `x_cert_verified`, `x_cert_status` (computed) |
| `hr_version` | employees | ràng buộc CCCD `identification_id` = 12 chữ số (BR-010) |
| `res_users` | users | logic set `tz = Asia/Ho_Chi_Minh` mặc định (không thêm cột) |
| `hr_leave` | timeoff | `x_is_emergency`, `x_has_medical_doc`, `x_medical_override`, `x_schedule_conflict`, `x_academic_review_required`, `x_conflict_info`... |
| `hr_leave_type` | timeoff | `x_is_emergency_type` |
| `hr_leave_allocation` | timeoff | `x_from_policy` |
| `hr_job` | recruitments | `x_published`, `recruitment_status`, `jd_google_link`, `x_teaching_level`, `x_required_sessions_per_week` |
| `hr_recruitment_stage` | recruitments | `success_criteria`, `support_person` |
| `hr_applicant` | recruitments | `date_received`, `cv_link`, `cv_filter_result`, `call_status`, `interview_*`, `offer_*`, `candidate_confirmed`... |

Ngoài ra hệ thống dùng nhiều bảng core không sửa: `res_company`, `res_partner`, `res_groups`,
`res_country_state`, `ir_attachment`, `ir_sequence` (sinh mã NV/phiếu lương/phiếu tuyển dụng),
`ir_cron` (job định kỳ: cổng đánh giá, nhắc nghỉ phép, đóng ca...), `mail_message`, `mail_followers`.

---

## E. Bản đồ quan hệ (ERD rút gọn)

```
                         res_users ──1:1── hocba_user ──*── hocba_access_control
                            │                  │  └──*── hocba_department_manager ──→ hr_department
                            │                  └──→ hocba_user_role ──*── res_groups (M2M)
                            │
   hocba_employee_type ──→ hr_employee ←──────────────────────────────┐
        ▲                    │  ▲                                       │
        │                    │  └── hr_department ──*── (manager_id)    │
   hr_employee_asset ────────┤                                          │
   hr_employee_dependent ────┤                                          │
   hr_promotion_history ─────┤                                          │
   hr_employee_skill (ext) ──┤                                          │
                             ├── hocba_work_shift ──1:1── hocba_shift_attendance
                             ├── hocba_work_assignment ──*── hocba_attendance ──→ hocba_attendance_status
                             │                              hocba_attendance_request ─┘
                             ├── hocba_teaching_attendance  (CMS session)
                             ├── hb_contract ──→ hb_salary_structure ──*── hb_salary_rule ──→ hb_salary_rule_category
                             ├── hb_payslip ──*── hb_payslip_line / _input / _worked_days
                             │      └──→ hb_payslip_run ──*── hb_bank_file ──→ hb_bank_format
                             ├── hb_work_entry ──→ hb_work_entry_type
                             ├── hb_recruitment_request ──→ hr_job / hr_department
                             │      hb_interview_slot ──→ hr_applicant
                             └── (timeoff) hr_leave / hr_leave_allocation ──→ hb_timeoff_policy_rule
                                    hb_leave_policy_log, hb_leave_adjustment, hb_work_day
```

---

## F. Hướng dẫn dựng DB lên server riêng (rời Neon)

Có **2 con đường**. Chọn theo nhu cầu:

| | F1. Cài fresh (DB trống) | F2. Dump & Restore (giữ dữ liệu Neon) |
|--|--------------------------|----------------------------------------|
| Khi nào | Bắt đầu lại, chỉ cần seed data mặc định | Cần giữ nhân viên/chấm công/lương đang có |
| Cách | Odoo `-i` tạo schema + seed | `pg_dump` Neon → `pg_restore` server mới |
| Rủi ro | Mất dữ liệu vận hành | Phải khớp version Odoo/Postgres |

### F0. Chuẩn bị server đích

1. **Cài PostgreSQL 15** (khớp với local đang dùng). Tạo user + quyền tạo DB:
   ```sql
   CREATE USER odoo WITH PASSWORD 'odoo_password' CREATEDB;
   ```
   *(Đổi mật khẩu mạnh cho production.)*
2. Mở port 5432 cho host chạy Odoo (hoặc để chung mạng Docker).
3. Đảm bảo có **cùng version Odoo 19** và **toàn bộ `custom-addons/`** trên server.

### F1. Cài fresh — khuyến nghị cho môi trường mới sạch

Dùng chính Docker stack có sẵn, chỉ trỏ DB sang server mới. Mẫu dựa trên `docker-compose.local.yml`:

```bash
# 1) Tạo .env (copy .env.example) trỏ về Postgres server mới:
#    DB_HOST=<ip-server>  DB_PORT=5432  DB_USER=odoo  DB_PASSWORD=...  DB_NAME=hocba_hrm

# 2) Khởi tạo DB + cài toàn bộ module custom (đúng thứ tự, Odoo tự sắp xếp depends):
docker compose -f docker-compose.yml run --rm odoo \
  odoo -d hocba_hrm \
  -i hocba_employees,hocba_attendance,hocba_users,hocba_recruitments,hocba_payroll,hocba_timeoff,hocba_hrm \
  --addons-path=/mnt/extra-addons --stop-after-init

# 3) Chạy app
docker compose -f docker-compose.yml up -d odoo
```

> ⚠️ **SSL**: `odoo.conf` gốc có `db_sslmode = require` (dành cho Neon). Postgres tự host thường
> **không bật SSL** → đổi thành `db_sslmode = prefer` (hoặc `disable`), giống `odoo.local.conf`.
> Cập nhật luôn `db_host/db_user/db_password` trong `odoo.conf` cho khớp server mới
> (hoặc để trống và truyền qua biến môi trường `HOST/USER/PASSWORD` như compose đang làm).

### F2. Dump & Restore — giữ nguyên dữ liệu đang chạy trên Neon

**Bước 1 — Dump từ Neon** (dùng endpoint **trực tiếp**, bỏ `-pooler` trong host để tránh rớt SSL giữa dump dài):
```bash
pg_dump \
  "postgresql://neondb_owner:<password>@ep-cool-wave-aoam4gfh.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" \
  -Fc -f hocba_hrm.dump
```
*(`-Fc` = custom format, nén, restore song song được. Lấy connection string từ Neon console.)*

**Bước 2 — Tạo DB rỗng trên server mới & restore:**
```bash
createdb -U odoo hocba_hrm
pg_restore -U odoo -d hocba_hrm --no-owner --no-privileges -j 4 hocba_hrm.dump
```
- `--no-owner --no-privileges`: bỏ owner/quyền của Neon (user `neondb_owner` không tồn tại trên server mới).
- `-j 4`: restore 4 luồng cho nhanh.

**Bước 3 — Dump cả filestore** (ảnh khuôn mặt, ảnh chấm công, file đính kèm lương):
- Ảnh lưu dạng `ir_attachment` (binary attachment=True) → **một phần trong DB**, một phần ngoài **filestore** (`/var/lib/odoo/filestore/<dbname>`). Copy thư mục filestore của volume `odoo_data` sang server mới, đổi tên thư mục con thành tên DB mới (`hocba_hrm`).

**Bước 4 — Trỏ Odoo sang DB mới & "neutralize" cấu hình môi trường mới:**
```bash
# Sửa odoo.conf: db_host/user/password = server mới, db_sslmode = prefer
docker compose -f docker-compose.yml run --rm odoo \
  odoo -d hocba_hrm -u all --addons-path=/mnt/extra-addons --stop-after-init
```
- `-u all`: cập nhật schema cho khớp code (Odoo tự `ALTER TABLE` nếu model đổi). **Bắt buộc** nếu version code khác lúc dump.
- Sau khi restore production-clone sang server test, nên chạy lệnh neutralize để **tắt cron/email/outgoing** kẻo gửi nhầm:
  ```bash
  odoo -d hocba_hrm --stop-after-init  # rồi dùng UI Settings, hoặc:
  # đặt lại ir_mail_server, vô hiệu ir_cron không cần thiết
  ```

### F3. Checklist sau khi dựng xong

- [ ] Đăng nhập được `/web/login`, vào được app `/hocba-hrm`.
- [ ] Menu "Học Bá HRM" hiện (nếu thiếu: chạy lại `-u hocba_hrm`).
- [ ] Múi giờ user = `Asia/Ho_Chi_Minh` (kẻo lệch +7h chấm công).
- [ ] `ir_sequence` còn số đếm đúng (mã NV `HB.xx`, số phiếu lương, mã phiếu tuyển dụng không trùng).
- [ ] Các `ir_cron` (cổng đánh giá, nhắc phép, đóng ca) đang **active** và đúng múi giờ.
- [ ] 2 SQL view timeoff (`hb_timeoff_burnout_line`, `hb_timeoff_leave_analysis`) tồn tại (cài lại `hocba_timeoff` nếu thiếu).
- [ ] Cấu hình CMS MySQL (`CMS_MYSQL_*`) nếu cần đồng bộ lịch dạy/giáo viên.
- [ ] Backup tự động: lên lịch `pg_dump` định kỳ + sao lưu filestore.

### F4. Khác biệt Neon → Postgres tự host cần nhớ

| Khía cạnh | Neon | Postgres tự host |
|-----------|------|------------------|
| SSL | bắt buộc (`require`) | thường tắt → `prefer`/`disable` |
| Pooler | có `-pooler` (pgbouncer), **rớt SSL khi DDL dài** | không có vấn đề pooler |
| Cài/upgrade module nặng | phải dùng endpoint trực tiếp (bỏ `-pooler`) | dùng bình thường |
| Owner/role | `neondb_owner` | tự đặt (`odoo`) → restore `--no-owner` |
| Backup | Neon snapshot/branch | tự lo `pg_dump` + cron |

---

## G. Cập nhật tài liệu này khi nào?

- Thêm/sửa model hoặc field trong `custom-addons/*/models/` → cập nhật Mục C/D.
- Đổi `depends` trong `__manifest__.py` → cập nhật Mục B.
- Đổi hạ tầng DB (version Postgres, host, SSL) → cập nhật Mục F.
- Nguồn sự thật vẫn là **code model**; tài liệu là ảnh chụp để người đọc nhanh.
</content>
</invoke>
