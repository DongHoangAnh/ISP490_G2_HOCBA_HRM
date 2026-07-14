# Spec — Quy trình nhận việc/thử việc cấu hình được (Onboarding Config)

- **Ngày**: 2026-07-15 · **Owner**: Tân (nhánh `Tan/Employee`)
- **Nguồn yêu cầu**: mentor đề xuất — admin config được các bước nhận việc/thử việc
  để dễ thay đổi khi nghiệp vụ đổi, không phải sửa code.
- **Trạng thái**: đã duyệt thiết kế qua brainstorming (6 quyết định chốt bên dưới).

## 1. Bối cảnh & vấn đề

Luồng thử việc hiện tại **hard-code** trong `hocba_employees/models/hr_employee.py`:

- 2 luồng cứng: Nhóm A (giáo viên → thử giảng F-008), Nhóm B (staff/manager
  offline → 3 cổng ĐG tuần-2 / tháng-1 / tháng-2 + cấp thiết bị, F-004/F-005).
- Hạn cứng +14/+30/+60 ngày; khung ràng buộc cứng (7–21 / 21–45 / 30–120 ngày).
- Trình tự cứng: tháng-1 mở sau tuần-2 Đạt; tháng-2 chỉ khi tháng-1 = Gia hạn.
- Automation AUT-001/002 (Đạt → lên chính thức), cron nhắc chuông, timeline
  HTML 6 bước cứng; SPA `Onboarding.jsx` suy phase từ key cứng `g1/g1m/g2/trial`.

Muốn đổi bất kỳ chi tiết nào (thêm bước ký hợp đồng, đổi hạn cổng, bỏ cấp
thiết bị…) đều phải sửa code + deploy → mentor yêu cầu chuyển sang **cấu hình**.

## 2. Quyết định thiết kế (đã chốt với user)

| # | Quyết định | Lựa chọn |
|---|---|---|
| 1 | Mức độ config | **Danh sách bước động** — admin thêm/xóa/sắp xếp bước |
| 2 | Cổng đánh giá | **Cũng là bước động** (type `evaluation`), không giữ field cứng |
| 3 | Gán template | **Tự động theo loại vị trí/hình thức/loại NV + HR đổi tay được** |
| 4 | Rẽ nhánh | **Tuyến tính + 2 cờ** trên bước evaluation (`pass_completes`, `is_extension`) — không làm workflow engine |
| 5 | Sửa template giữa chừng | **Snapshot khi gán** — NV đang chạy giữ nguyên lộ trình |
| 6 | UI config / dữ liệu cũ | **SPA React** (HR Manager/Admin) / **migration script** field cũ → bước động |

Kiến trúc chọn: **Phương án A — 3 model custom `hb.onboarding.*`** (đúng
pattern `hocba.offboarding`); loại phương án Activity Plan Odoo (thiếu kết quả
đánh giá + automation) và JSON config (không constraint/ACL/query được).

## 3. Data model

### 3.1 `hb.onboarding.template` — template quy trình

| Field | Kiểu | Ghi chú |
|---|---|---|
| `name` | Char, required | vd "Thử việc Giáo viên" |
| `active` | Boolean, default True | archive, không xoá (giữ audit) |
| `sequence` | Integer | NV khớp nhiều template → lấy sequence nhỏ nhất |
| `apply_position_types` | Char CSV | tập con của `x_position_type` (manager/staff/ctv/freelancer/advisor); rỗng = mọi loại; validate bằng constraint |
| `apply_work_form` | Selection offline/online/any, default any | khớp `x_work_form` |
| `apply_employee_type_ids` | M2m `hocba.employee.type` | rỗng = mọi loại NV |
| `step_ids` | O2m `hb.onboarding.template.step` | |

### 3.2 `hb.onboarding.template.step` — bước mẫu

| Field | Kiểu | Ghi chú |
|---|---|---|
| `template_id` / `sequence` / `name` | | thứ tự tuyến tính |
| `step_type` | Selection `task` / `evaluation` | task = checklist; evaluation = Đạt/Gia hạn/Không đạt |
| `due_days` | Integer ≥ 0 | hạn = `x_probation_start` + N ngày; 0 = không hạn |
| `pass_completes` | Boolean | chỉ evaluation: Đạt → lên chính thức, skip bước sau. Phải bật TƯỜNG MINH (thử giảng pass hiện KHÔNG lên chính thức → không có rule ngầm) |
| `is_extension` | Boolean | chỉ evaluation: chỉ kích hoạt khi bước evaluation liền trước = Gia hạn |
| `auto_action` | Selection `none`/`grant_assets`, default none | chỉ task: bước mở → chạy automation (`grant_assets` = `_hocba_grant_default_assets` F-006) rồi tự done |
| `note` | Text | hướng dẫn người thực hiện |

**Constraints template**: ≥ 1 bước; cờ evaluation chỉ hợp lệ trên
`evaluation`, `auto_action` chỉ trên `task`; `is_extension` phải đứng
**ngay sau** một bước `evaluation`.

### 3.3 `hb.onboarding.step` — instance trên từng NV (snapshot)

| Field | Kiểu | Ghi chú |
|---|---|---|
| `employee_id` | M2o `hr.employee`, required, index, ondelete cascade | |
| `template_id` | M2o | trace nguồn, KHÔNG đọc lại logic |
| `sequence`, `name`, `step_type`, `pass_completes`, `is_extension`, `auto_action` | snapshot | copy lúc gán |
| `due_date` | Date | tính sẵn; HR sửa tay được từng ca |
| `state` | Selection `waiting`/`open`/`done`/`skipped` | |
| `result` | Selection `pass`/`fail` | chỉ evaluation, set khi done |
| `extend_count` | Integer, default 0 | số lần "Gia hạn tái đánh giá" trên chính bước này |
| `done_date`, `done_by_id` (res.users), `result_note` | | audit |

**Constraints instance**: chỉ ghi `result`/hoàn thành/gia hạn khi
`state='open'`; `fail` bắt buộc `result_note`; `done_date` trong
[`x_probation_start`, hôm nay].

### 3.4 Trên `hr.employee`

- Thêm `x_onboarding_template_id` (M2o) + `x_onboarding_step_ids` (O2m).
- Field cổng cũ (`x_eval_2w_*`, `x_eval_1m_*`, `x_eval_2m_*`,
  `x_trial_lesson_*`, `x_equip_grant_date`) **gỡ khỏi view/API/logic**, giữ
  cột DB một thời gian để đối chiếu sau migration.
- `x_probation_timeline_html` render từ instance steps (giữ style màu/ký hiệu).

## 4. Vòng đời & Automation

### 4.1 Gán template

- Trigger: NV `x_employment_status='probation'` **và** có `x_probation_start`
  (create/write) mà chưa có step → tìm template active khớp cả 3 tiêu chí
  (tiêu chí rỗng = khớp tất), lấy `sequence` nhỏ nhất → sinh instance.
- Không khớp → **không chặn lưu**, bắn chuông cảnh báo HR
  ("chưa có quy trình nhận việc phù hợp").
- Đổi template tay: xoá step `waiting`/`open` chưa kết quả, giữ `done`/`skipped`,
  sinh step mới từ template mới nối tiếp sau.

### 4.2 Máy trạng thái

```
waiting ──(bước trước done/skipped)──▶ open ──(complete/evaluate)──▶ done
                                        └──(chốt sớm / extension không kích hoạt)──▶ skipped
```

- Bước đầu sinh ra `open`, còn lại `waiting`.
- Khi một bước chuyển sang `open`: nếu là `task` có `auto_action='grant_assets'`
  → gọi `_hocba_grant_default_assets()` + tự `done` (mở tiếp bước sau) —
  giữ nguyên F-006 (AUT-001 hiện cấp tài sản ngay khi tuần-2 Đạt).
- `task` hoàn thành (tay): ghi `done_date` + `done_by_id`, mở bước kế.
- `evaluation` — 3 nút hành động:
  - **Đạt** → `done`, `result='pass'`. Nếu `pass_completes` → set
    `x_employment_status='official'`, `x_official_date=today` (context
    `hocba_gate_automation`), bước còn lại → `skipped`, ghi
    `hr.promotion.history` (source `probation`), chuông `probation_pass`.
    Nếu không → mở bước kế; bước kế `is_extension` → skip nó, mở tiếp.
  - **Gia hạn** → nếu bước kế là `is_extension`: bước này `done`, mở bước kế
    (hành vi cổng tháng-1 cũ). Nếu KHÔNG: bước **giữ `open`**, tăng
    `extend_count`, ghi note — tái đánh giá sau (hành vi cổng tuần-2/tháng-2
    cũ "GIA HẠN — hẹn tái đánh giá"). Cả 2 nhánh: chuông `probation_extend`.
  - **Không đạt** → `done`, `result='fail'`, bước còn lại `skipped`, gọi
    `_hocba_start_offboarding(tên bước)` (giữ hành vi hiện tại: đơn
    `hocba.offboarding` source `probation` state `hr_approved`, NV `exiting`,
    chuông `probation_fail` — helper đã idempotent).
- Chuỗi hoàn tất (mọi bước done/skipped) mà NV chưa `official` (vd luồng giáo
  viên — thử giảng pass chỉ dẫn tới task "Ký HĐ thỉnh giảng") → chuông báo HR
  "quy trình nhận việc hoàn tất, chờ quyết định" — KHÔNG tự đổi trạng thái.
- Tôn trọng `x_skip_auto_trigger` (field sẵn có): bật → ghi kết quả bước
  nhưng bỏ side-effect automation (official/offboarding/grant assets/chuông),
  vẫn mở bước kế.

### 4.3 Quyền

- Ghi kết quả `evaluation`: HR Manager / quản lý trực tiếp / trưởng phòng ban
  NV (chuyển check `GATE_EDIT_FIELDS` hiện có sang model step).
- Hoàn thành `task`: như trên + Giáo vụ trong phạm vi (giáo viên).
- Config template: chỉ `hr.group_hr_manager`.
- User thường: đọc step của chính mình qua `.sudo()` sau khi pin employee
  (pattern self-service hiện hành). ACL: base user read-only record của mình,
  ghi qua sudo trong controller sau khi check quyền.

### 4.4 Cron & chuông

- Viết lại `_cron_probation_eval_reminders`: quét step `open` có `due_date`
  sắp đến/quá hạn → chuông `probation_eval` qua `hb.notification`, dedup
  `onb_step:{step.id}:{due_date}`. Xoá 3 khối 2w/1m/2m cứng.

## 5. API (`hocba_hrm/controllers/main.py`)

### Config (HR Manager only, 403 nếu không)

| Route | Method | Chức năng |
|---|---|---|
| `/hocba-hrm/api/onboarding/templates` | GET | list template + steps |
| `/hocba-hrm/api/onboarding/templates` | POST | tạo (kèm mảng steps) |
| `/hocba-hrm/api/onboarding/templates/<id>` | POST | sửa (replace-all steps trong 1 transaction) / archive |

### Vận hành (phạm vi vai trò như màn Onboarding hiện tại)

| Route | Method | Chức năng |
|---|---|---|
| `/hocba-hrm/api/employees/onboarding` | GET | viết lại: trả `steps[]` động (id, name, type, state, result, dueDate, doneDate, doneBy, canAct) thay key cứng |
| `/hocba-hrm/api/onboarding/steps/<id>/complete` | POST | hoàn thành task |
| `/hocba-hrm/api/onboarding/steps/<id>/evaluate` | POST | `{result, note, date}` |
| `/hocba-hrm/api/onboarding/steps/<id>/due` | POST | HR sửa hạn |
| `/hocba-hrm/api/employees/<id>/onboarding/assign` | POST | gán/đổi template tay |

- Mọi route ghi trả **payload NV đã refresh** (pattern timeoff).
- Lỗi nghiệp vụ → 400 `{error}` message tiếng Việt từ ValidationError.

## 6. SPA

1. **Màn "Cấu hình nhận việc"** (mới, menu chỉ HR Manager/Admin): list
   template → drawer sửa (sắp xếp/thêm/xoá bước, loại + hạn + 2 cờ). Tái dùng
   `ModalHeader`, `ConfirmModal`, `useFetch`.
2. **`Onboarding.jsx` viết lại**: bỏ `phaseOf()` cứng — phase = bước `open`
   đầu tiên; cột tiến độ "n/m bước" + bước hiện tại + hạn (đỏ quá hạn).
3. **EmployeeDrawer tab thử việc**: timeline dọc bước động, nút theo `canAct`
   (hoàn thành / Đạt–Gia hạn–Không đạt kèm note / HR sửa hạn).

## 7. Migration & seed

1. Seed 2 template mặc định tái hiện luồng hiện tại (data XML `noupdate`):
   - **Thử việc Giáo viên** (khớp employee_type `teacher`): "Thử giảng"
     (evaluation, KHÔNG `pass_completes` — pass hiện không lên chính thức) →
     "Ký HĐ thỉnh giảng" (task) — thay activity nhắc HR hiện tại.
   - **Thử việc NV văn phòng** (khớp position staff+manager, offline):
     ĐG tuần-2 (evaluation, due 14) → Cấp thiết bị (task,
     `auto_action='grant_assets'`) → ĐG tháng-1 (evaluation, due 30,
     `pass_completes`) → ĐG tháng-2 (evaluation, due 60, `is_extension`,
     `pass_completes`).
2. Migration script (`hocba_employees/migrations/`): NV có `x_probation_start`
   hoặc kết quả cổng cũ (kể cả `official`) → sinh instance steps, map kết
   quả/ngày/evaluator cũ vào.
3. Field cũ giữ cột DB, gỡ khỏi view/API. Chạy local trước, Neon sau
   (endpoint trực tiếp, không pooler). Cập nhật `docs/DB_TEST_DATA.md`.

## 8. Test (TDD, Docker local)

- **Template**: constraints (extension sau evaluation, cờ chỉ evaluation,
  ≥1 bước), matching 3 tiêu chí + sequence, CSV position_types validate.
- **Instance**: máy trạng thái đủ nhánh (pass thường / pass_completes /
  extend→bước gia hạn / extend→tái đánh giá tại chỗ / fail / skip extension /
  auto_action grant_assets / chuỗi xong không official → chuông), chặn ghi
  khi chưa `open`, fail bắt buộc note, quyền theo vai trò (TP/GV/QL trực
  tiếp/user thường), tôn trọng `x_skip_auto_trigger`.
- **Automation**: lên chính thức đúng AUT-001/002 cũ, promotion history,
  chuông + dedup, cron nhắc hạn, gán template tự động khi tạo NV thử việc.
- **Migration**: dựng dữ liệu kiểu cũ → chạy script → so khớp từng bước.
- **API**: quyền 403/400 + shape payload.

## 9. Ngoài phạm vi (YAGNI)

- Workflow engine điều kiện/graph; bước song song.
- Đồng bộ template mới cho NV đang chạy (chỉ snapshot; nút "re-sync" để sau
  nếu cần).
- Thông báo email (chỉ chuông `hb.notification`).
