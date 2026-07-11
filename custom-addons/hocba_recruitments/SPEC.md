# SPEC — Module `hocba_recruitments` (v19.0.2.0.0)

> **Trạng thái:** Đã implement — branch `Viet/Recruitment`  
> **Cập nhật:** 2026-06-21 (tách vai duyệt phiếu, đặt lịch PV cho UV, map ngày nhận việc, dọn legacy)  
> **Odoo version:** 19.0-20260609  
> **Depends:** `hr_recruitment` (Odoo 19 core), `hocba_employees` (dùng `x_employee_code` / `x_employment_status` / `x_probation_start` khi tạo hồ sơ NV từ ứng viên)

Module mở rộng tuyển dụng Odoo cho Học Bá Education. UI có **2 lớp**:
1. **Backend Odoo** — menu **Recruitment** (models/views mô tả §1–§9 bên dưới).
2. **SPA Tuyển dụng** (React, trong `frontend/` build vào `hocba_hrm`) — 7 tab, gọi
   **API domain `recruitment`** (`/hocba-hrm/api/recruitment/*`) do controller
   `controllers/main.py` cung cấp. Chi tiết hợp đồng API: **`docs/SPEC_API_RECRUITMENT.md`**.

> Controller React legacy `/hocba-tuyen-dung` đã bỏ; `controllers/main.py` giờ là controller API thật cho SPA.

---

## 1. Cấu trúc file

```
hocba_recruitments/
├── __manifest__.py
├── __init__.py
├── controllers/
│   └── main.py               # Controller API JSON cho SPA (/hocba-hrm/api/recruitment/*)
├── models/
│   ├── hb_recruitment_request.py   # Model mới
│   ├── hb_interview_slot.py        # Model mới — Screen 7.3
│   ├── hr_applicant.py             # Inherit
│   ├── hr_job.py                   # Inherit
│   └── hr_recruitment_stage.py     # Inherit
├── views/
│   ├── menu.xml                         # Toàn bộ menu items + window actions
│   ├── hb_recruitment_request_views.xml # Screen 7.2
│   ├── hb_interview_slot_views.xml      # Screen 7.3
│   ├── hb_cv_list_views.xml             # Screen 7.4
│   ├── hb_interview_list_views.xml      # Screen 7.5
│   ├── hr_applicant_kanban.xml          # Screen 7.1
│   ├── hr_job_form_inherit.xml          # Screen 7.8
│   └── hr_recruitment_stage_views.xml   # Screen 7.1 config
├── data/
│   ├── hr_recruitment_stages.xml        # 10 bước quy trình (noupdate=0)
│   ├── hb_recruitment_request_sequence.xml
│   ├── hb_job_positions.xml             # 8 vị trí (noupdate=1)
│   ├── hb_recruitment_request_data.xml  # Sample phiếu
│   ├── hb_applicant_data.xml            # Sample ứng viên (3 file)
│   ├── hb_applicant_data2.xml
│   ├── hb_applicant_data3.xml
│   ├── hb_interview_results.xml         # Sample kết quả PV
│   └── hb_mail_templates.xml            # 4 mail templates
└── security/
    └── ir.model.access.csv
```

---

## 2. Menu & Navigation (9 screens)

Tất cả nằm dưới root menu `hr_recruitment.menu_hr_recruitment_root`.

| Seq | Menu | Model | View mode mặc định |
|-----|------|-------|--------------------|
| 5 | **Vị trí / JD** | `hr.job` | list, kanban, form |
| 10 | **Ứng viên** _(parent)_ | — | — |
| 10.1 | → Pipeline Kanban | `hr.applicant` | kanban, list, form |
| 10.2 | → Danh sách CV | `hr.applicant` | **list custom**, kanban, form |
| 15 | **Phiếu yêu cầu** | `hb.recruitment.request` | list, form |
| 20 | **Phỏng vấn** _(parent)_ | — | — |
| 20.1 | → Khai báo lịch rảnh | `hb.interview.slot.wizard` | form dialog (wizard) |
| 20.2 | → Lịch rảnh PV | `hb.interview.slot` | **calendar week**, list, form |
| 20.3 | → Danh sách phỏng vấn | `hr.applicant` | **list custom**, calendar, form — domain: `interview_date != False` |
| 25 | **Offer & Nhận việc** | `hr.applicant` | list, kanban, form — domain: `date_closed != False` |
| 30 | **Báo cáo** | `hr.applicant` | pivot, graph, list |
| Config.45 | **Mail mẫu** | `mail.template` | list, form — domain: `model = hr.applicant` |

**Access groups trên menu:**
- `group_hr_recruitment_user`: thấy tất cả
- `group_hr_recruitment_interviewer`: thấy Ứng viên + Phỏng vấn

---

## 3. Model: `hb.recruitment.request` — Phiếu Yêu Cầu Tuyển Dụng

Model mới. Inherit `mail.thread`, `mail.activity.mixin`. Order: `create_date desc`.

### 3.1 Fields

| Field | Type | Ghi chú |
|-------|------|---------|
| `name` | Char | Auto-sequence `hb.recruitment.request`, readonly, copy=False |
| `date_request` | Date | Default: today |
| `requester_id` | Many2one `res.users` | Default: current user, readonly |
| `department_id` | Many2one `hr.department` | Required |
| `job_id` | Many2one `hr.job` | Domain: `department_id`, tuỳ chọn |
| `job_title` | Char | Required |
| `jd_link` | Char | Link Google Drive hoặc tên file |
| `qty_expected` | Integer | Default: 1, required |
| `reason` | Selection | `new` / `replacement` / `expansion` |
| `level` | Selection | intern / fresher / junior / mid / senior / lead / manager |
| `education` | Selection | none / intermediate / college / bachelor / master / doctor |
| `experience_years` | Float | digits(5,1) |
| `skill_description` | Text | |
| `language_requirement` | Char | |
| `expected_start_date` | Date | |
| `salary_range` | Char | Mô tả dạng text |
| `salary_from` | Float | digits(15,0) |
| `salary_to` | Float | digits(15,0) |
| `work_type` | Selection | onsite / remote / hybrid |
| `manager_id` | Many2one `res.users` | Trưởng phòng phê duyệt |
| `hr_manager_id` | Many2one `res.users` | HR Manager phê duyệt |
| `director_id` | Many2one `res.users` | Ban giám đốc phê duyệt |
| `refuse_reason` | Text | Hiển thị chỉ khi state = refused |
| `note` | Html | Ghi chú nội bộ, sanitize=True |
| `state` | Selection | Xem §3.2 |

### 3.2 State Machine

```
            ┌────────────────────┐
            │                    │
  draft ──► submitted ──► recruiting ──► closed
    ▲           │
    │         refused
    │           │
    └───── reset_draft
```

| State | Label | Màu badge |
|-------|-------|-----------|
| `draft` | Nháp | — |
| `submitted` | Chờ BP duyệt | info (xanh dương) |
| `recruiting` | Đang tuyển | success (xanh lá) |
| `closed` | Đã đóng | muted (xám) |
| `refused` | Từ chối | danger (đỏ) |

### 3.3 Buttons trên form header

| Nút | Hiển thị khi | Action |
|-----|-------------|--------|
| Gửi duyệt | state = draft | `action_submit` |
| BP Duyệt | state = submitted | `action_approve` |
| Đóng phiếu | state = recruiting | `action_close` |
| Từ chối | state = submitted | `action_refuse` |
| Trả về nháp | state = refused | `action_reset_draft` |

**Smart button Job Position:** Nếu chưa có `job_id` → tạo mới `hr.job` từ `job_title + department_id`. Nếu đã có → mở xem.

### 3.4 Security

| Group | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `group_hr_recruitment_interviewer` | ✓ | — | — | — |

**Tách vai theo sheet quy trình (TBP order ≠ BP tuyển dụng duyệt).** Sheet chỉ có 2 vai
nên workflow chỉ cần **một** lần duyệt (BP tuyển dụng tiếp nhận order), không phải chuỗi
"TBP duyệt → HR duyệt → BGĐ". Quyền chia **theo từng action** (enforce ở controller SPA
`api_recruitment_request_action`; form backend đã gate sẵn bằng `group_hr_recruitment_user`):

TBP = _is_dept_manager() (đứng manager_id của phòng), không thuộc group_hr_recruitment_user.
BP tuyển dụng/HR = _is_hr() (recruitment user/manager + HR manager + admin).

| Action | Trạng thái | Ai được làm |
|--------|-----------|-------------|
| `submit` (Gửi duyệt), `reset` (Về nháp) | draft / refused / closed | `_is_recruiter()` = **TBP** (trưởng phòng của phòng mình) **hoặc** BP tuyển dụng/HR |
| `approve`, `refuse`, `close` | submitted / recruiting | **chỉ `_is_hr()`** = BP tuyển dụng (`group_hr_recruitment_user/manager`), HR Manager, Admin |

- API list trả thêm cờ **`canApprove = _is_hr()`**; SPA (`RequestDrawer.jsx`) ẩn nút
  Duyệt/Từ chối/Đóng nếu không có cờ này → TBP chỉ thấy Gửi duyệt / Về nháp.
- ⚙️ **Ghi qua `.sudo()` sau khi kiểm vai+phạm vi:** model ACL chỉ cho
  `group_hr_recruitment_user` ghi `hb.recruitment.request`, nên endpoint `create/update/action`
  của SPA dùng `.sudo()` (sau khi đã chặn `_is_recruiter` + scope + gate `_is_hr` cho duyệt)
  để **TBP order được phiếu** dù không có ACL model. `requester_id` vẫn = người đăng nhập
  (sudo không đổi `env.user`).
- 3 field `manager_id / hr_manager_id / director_id` chỉ **ghi nhận** ai ký duyệt, KHÔNG
  enforce làm cổng workflow.
- ⚠️ Điều kiện cấu hình: **TBP không được gán `group_hr_recruitment_user`** — nếu gán, TBP
  trở thành BP tuyển dụng và mất tách vai.

---

## 4. Model: `hr.job` (inherit)

### 4.1 Fields thêm

| Field | Type | Ghi chú |
|-------|------|---------|
| `x_published` | Boolean | Badge PUBLISHED xanh trên kanban. Default: False |
| `recruitment_status` | Selection | `recruiting` / `stopped`. Default: recruiting |
| `jd_google_link` | Char | Link JD Google Drive |
| `x_teaching_level` | Selection | `hsk2` / `hsk3` / `tocfl` / `na`. Default: na |
| `x_required_sessions_per_week` | Integer | Số buổi/tuần tối thiểu. Default: 0 |
| `x_requires_teaching_level` | Boolean (compute) | Computed từ `department_id.name` ∈ {"Giảng viên", "Trợ giảng"} |

### 4.2 Constraints

1. **Không trùng tên** trong cùng phòng ban (active=True). Kiểm tra: `name + department_id + active`.
2. **Phòng Giảng viên / Trợ giảng** bắt buộc `x_teaching_level ≠ na`.

### 4.3 Views thêm

- **Form inherit** (`hr.view_hr_job_form`): Nút Đăng tuyển / Ngừng đăng trong header; `recruitment_status` + `jd_google_link` sau `department_id`; group "Học Bá — Yêu cầu giảng dạy" (ẩn nếu không phải phòng giảng dạy)
- **Kanban inherit** (`view_hr_job_kanban`): Badge `PUBLISHED` xanh lá khi `x_published = True`
- **List inherit**: Thêm cột `recruitment_status` (badge), `address_id`, `new_application_count`, `x_published` (toggle), `jd_google_link`
- **Search view** (standalone): Filter Đang tuyển / Dừng tuyển / Đã đăng tuyển; Group by phòng ban / trạng thái

### 4.4 Seed data — 8 vị trí (noupdate=1)

| Vị trí | Phòng | recruitment_status | x_published |
|--------|-------|--------------------|-------------|
| Tư vấn tuyển sinh | Kinh doanh | recruiting | True |
| Giáo viên dạy tiếng Trung | Vận hành | recruiting | True |
| Chuyên viên R&D | R&D sản phẩm | recruiting | True |
| Quản lý học viên | Vận hành | recruiting | True |
| Content Marketing | Marketing | recruiting | True |
| Trợ giảng | Vận hành | stopped | False |
| Giáo vụ | Vận hành | stopped | False |
| Hành chính nhân sự | Kế toán HCNS | stopped | False |

---

## 5. Model: `hr.applicant` (inherit)

### 5.1 Fields thêm — Sheet 7.4 (Danh sách CV)

| Field | Type | Ghi chú |
|-------|------|---------|
| `date_received` | Date | index=True |
| `ctv_tuyen_dung` | Char | Cộng tác viên tuyển dụng |
| `cv_link` | Char | Link Google Drive / tên file |
| `cv_filter_result` | Selection | `pass` / `fail` / `potential` / `contact_later` |
| `cv_note` | Text | Ghi chú CV |
| `call_status` | Selection | `agree` / `refuse` / `potential` / `contact_later` |
| `interview_date` | Date | Ngày hẹn phỏng vấn |
| `interview_time` | Char | VD: 10h, 10h30 |
| `interviewer_name` | Char | Tên người phỏng vấn |

### 5.2 Fields thêm — Sheet 7.5 (Danh sách phỏng vấn)

| Field | Type | Ghi chú |
|-------|------|---------|
| `attendance_status` | Selection | `present` / `absent` |
| `interview_result` | Selection | `pass` / `fail` / `potential` |
| `offer_content` | Text | Nội dung offer (lương, COM...) |
| `start_date` | Date | Ngày nhận việc |
| `offer_note` | Text | Ghi chú nội bộ về offer |
| `candidate_confirmed` | Char | VD: "Đã xác nhận", "Đã phản hồi" |

### 5.3 Views thêm

**List custom 7.4** (`hb_view_applicant_cv_list`): Hiển thị date_received, CTV, tên, SĐT, email, vị trí, CV link, kết quả lọc (badge), gọi điện (badge), ngày/giờ/người PV. Row color: xanh = pass+agree, đỏ = fail, vàng = potential, xám = refuse.

**List custom 7.5** (`hb_view_applicant_interview_list`): Thêm attendance_status, interview_result, offer_content, start_date, offer_note, candidate_confirmed. Row color: xanh = pass, đỏ = fail/absent, vàng = potential.

**Form inherit** (2 tab thêm vào notebook):
- Tab "Lọc CV & Phỏng vấn": cv_filter_result, call_status, interview_date, interview_time, interviewer_name, cv_note
- Tab "Kết quả PV": attendance_status, interview_result, start_date, candidate_confirmed, offer_content, offer_note

**Kanban inherit** (`hr_kanban_view_applicant`): Thêm `source_id` + `create_date` lên card; Việt hóa dropdown menu (Lên lịch phỏng vấn / Gửi email / Từ chối hồ sơ / Lưu trữ / Khôi phục / Xóa).

**Search inherit**: Thêm filter CTV, Người PV, Pass/Fail/Tiềm năng/Liên hệ sau, Đồng ý PV/Từ chối PV, PV hôm nay, kết quả PV, tham gia PV, có offer, UV xác nhận, có ngày nhận việc.

### 5.4 Mail actions (4 nút trên form header)

| Nút | Template | Hiển thị khi |
|-----|----------|-------------|
| Mời phỏng vấn | `email_template_interview_invite` | email_from có giá trị |
| Kết quả phỏng vấn | `email_template_interview_result` | email_from có giá trị |
| Thư mời nhận việc | `email_template_job_offer` | email_from có giá trị |
| Chào mừng Học Bá | `email_template_welcome` | email_from có giá trị |

---

## 6. Model: `hr.recruitment.stage` (inherit)

### 6.1 Fields thêm

| Field | Type | Ghi chú |
|-------|------|---------|
| `success_criteria` | Text | Điều kiện hoàn thành bước |
| `support_person` | Char | BP/người phối hợp |

### 6.2 Seed data — 10 bước quy trình (noupdate=0)

Sequence dùng bước nhảy 10 để dễ chèn stage mới giữa các bước sau này.

| Sequence | Tên | Người hỗ trợ | Tiêu chí thành công |
|----------|-----|-------------|---------------------|
| 10 | Yêu cầu tuyển dụng | BP tuyển dụng | Yêu cầu rõ ràng, JD đầy đủ, có chỉ tiêu SL và thời gian |
| 20 | Đăng tuyển & tổng hợp CV | TBP | Tin đăng trên 3 kênh, CV tổng hợp đủ thông tin |
| 30 | Lọc CV | TBP | TBP nhận đủ hồ sơ, điền Pass/Fail tại cột Lọc CV |
| 40 | Lên lịch phỏng vấn | BP tuyển dụng | TBP điền lịch rảnh trong tuần |
| 50 | Hẹn & mời phỏng vấn | TBP | >80% ứng viên đồng ý và xác nhận lịch |
| 60 | Phỏng vấn | BP tuyển dụng | Đúng giờ, đánh giá đủ năng lực và thái độ |
| 70 | Kết quả phỏng vấn | BP tuyển dụng | BP nhận kết quả + lý do pass/không pass |
| 80 | Gửi Offer | TBP | Offer rõ ràng, ứng viên xác nhận đồng ý qua mail |
| 90 | Onboarding | TBP | Nhân sự nắm quy trình, hoà nhập, ký HĐ đầy đủ |
| 100 | Bàn giao nhân sự | TBP | Nhân sự bắt đầu chính thức, TBP tiếp nhận. `hired_stage=True` |

### 6.3 Cleanup — Xóa stages mặc định của Odoo

Cuối file `hr_recruitment_stages.xml` gọi `<function name="_hocba_cleanup_default_stages"/>`. Method này (trên model `hr.recruitment.stage`) chạy mỗi lần upgrade và:

1. Tìm stages có tên trong danh sách: `New`, `Qualification`, `Initial Qualification`, `First Interview`, `Second Interview`, `Contract Proposal`, `Contract Signed`, `Hồ sơ mới`
2. Reassign toàn bộ `hr.applicant` (kể cả archived — `active_test=False`) đang ở stage đó về `hb_stage_request`
3. Unlink các stage thừa

> **Lưu ý vận hành:** Nếu thêm stage mới vào Odoo mặc định cần xóa, thêm tên vào `_ODOO_DEFAULT_STAGE_NAMES` trong `hr_recruitment_stage.py` rồi upgrade module.

---

## 7. Model: `hb.interview.slot` — Lịch rảnh phỏng vấn (Screen 7.3)

Model mới. Order: `start_datetime`. **Không** inherit mail.thread.

### 7.1 Fields

| Field | Type | Ghi chú |
|-------|------|---------|
| `name` | Char (compute, store) | `"{user} — {dd/mm HH:MM}"` theo timezone user |
| `start_datetime` | Datetime | Required — thời điểm bắt đầu slot (UTC) |
| `stop_datetime` | Datetime | Required — thời điểm kết thúc slot (UTC) |
| `user_id` | Many2one `res.users` | Required, default: current user |
| `department_id` | Many2one `hr.department` | Compute từ `hr.employee.user_id`, store=True |
| `state` | Selection | `available` / `booked`. Default: available |
| `applicant_id` | Many2one `hr.applicant` | Ứng viên được đặt (khi state=booked) |
| `notes` | Text | Ghi chú nội bộ |

### 7.2 Constraint

`stop_datetime > start_datetime` — ValidationError nếu vi phạm.

### 7.3 Methods

| Method | Mô tả |
|--------|-------|
| `action_mark_booked` | Set `state = booked` |
| `action_mark_available` | Set `state = available`, xóa `applicant_id` |

### 7.4 Views

**Calendar view** (`hb_view_interview_slot_calendar`): `mode="week"`, `date_start=start_datetime`, `date_stop=stop_datetime`, `color=user_id`. Đây là màn hình chính — tương đương Weekly Availability Matrix.

**List view** (`hb_view_interview_slot_list`): Decoration xanh = available, muted = booked. Các cột: start/stop datetime, user, department, state (badge), applicant, notes.

**Form view** (`hb_view_interview_slot_form`): Header buttons "Đánh dấu đã đặt" / "Trả về còn trống". Statusbar hiển thị state.

**Search view** (`hb_view_interview_slot_search`): Filter available/booked/tuần này. Group by ngày/người PV/phòng ban/trạng thái.

### 7.5 Wizard: `hb.interview.slot.wizard` (Khai báo batch)

TBP mở wizard từ menu **Phỏng vấn → Khai báo lịch rảnh**, điền danh sách slot:

- `user_id` — người phỏng vấn (default: current user)
- `line_ids` (o2m → `hb.interview.slot.wizard.line`): mỗi dòng gồm `date` + `start_hour` + `end_hour` (Selection từ 09:00–17:00, bước 30 phút)

`action_create_slots` convert giờ local → UTC (dùng `user.tz`, fallback `Asia/Ho_Chi_Minh`) rồi tạo records `hb.interview.slot`. Sau khi tạo, navigate về calendar.

Server action `hb_server_action_slot_wizard` binding vào model `hb.interview.slot` — nút "Khai báo lịch rảnh theo tuần…" xuất hiện trong dropdown Action trên list view.

### 7.6 Security

| Rule | Model | Group | R | W | C | D |
|------|-------|-------|---|---|---|---|
| `access_hb_interview_slot_user` | `hb.interview.slot` | `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `access_hb_interview_slot_interviewer` | `hb.interview.slot` | `group_hr_recruitment_interviewer` | ✓ | ✓ | ✓ | — |
| `access_hb_interview_slot_wizard_*` | wizard + line | cả 2 groups | ✓ | ✓ | ✓ | ✓ |

### 7.7 Đặt lịch PV cho ứng viên (SPA — tab Danh sách PV)

Khép vòng "chọn slot rảnh → đặt cho ứng viên" ngay trên SPA (không cần vào backend Odoo).
Quyền: `_can_manage_slots()` (HR/BP tuyển dụng, trưởng phòng, hoặc interviewer).

| Endpoint | Mô tả |
|----------|-------|
| `POST …/interview-slot/<id>/book` body `{applicantId}` | slot → `booked` + gán `applicant_id`; **đồng thời** điền lịch PV lên hồ sơ ứng viên: `interview_date` = ngày slot, `interview_time` = giờ bắt đầu (HH:MM), `interviewer_name` = tên người PV của slot |
| `POST …/interview-slot/<id>/unbook` | slot → `available` + gỡ `applicant_id`; **giữ nguyên** lịch PV đã ghi trên hồ sơ ứng viên (chỉ giải phóng slot) |

- `_slot_row` trả thêm `applicantId` để FE biết slot đã gán ai.
- UI: slot **Rảnh** có nút **"Đặt UV"** (mở modal chọn ứng viên có tìm kiếm); slot **Đã đặt**
  hiện tên UV + nút **"Hủy đặt"**. Đặt/hủy xong refresh cả lịch tuần lẫn bảng "Ứng viên đang phỏng vấn".
- Nhờ đồng bộ `interview_date/time`, mail **Thư mời phỏng vấn** (biến `{{ object.interview_date }}`)
  tự điền đúng lịch vừa đặt.

---

## 8. Mail Templates (4 templates — model: `hr.applicant`)

| XML ID | Tên | Chủ đề | Dùng khi |
|--------|-----|--------|---------|
| `email_template_interview_invite` | Thư mời phỏng vấn | `[HỌC BÁ] THƯ MỜI THAM GIA PHỎNG VẤN VỊ TRÍ ${job}` | Sau khi call_status = agree |
| `email_template_interview_result` | Thông báo kết quả PV | `[HỌC BÁ] THÔNG BÁO KẾT QUẢ PHỎNG VẤN VỊ TRÍ ${job}` | Khi interview_result = fail |
| `email_template_job_offer` | Thư mời nhận việc | `[HỌC BÁ] THƯ MỜI NHẬN VIỆC VỊ TRÍ ${job} - FULLTIME` | Khi interview_result = pass |
| `email_template_welcome` | Chào mừng Học Bá | `[HỌC BÁ] CHÀO MỪNG BẠN ĐẾN VỚI HỌC BÁ` | Ngày đầu nhận việc |

Tất cả template dùng cú pháp **Jinja2 chuẩn** (Odoo 17+): `{{ object.partner_name }}`, `{{ object.job_id.name }}`, `{{ object.interview_date.strftime('%d/%m/%Y') if object.interview_date else '' }}`.

**Thông tin liên hệ cố định trong template:**
- Địa chỉ: Tầng 2, toà IP3, Imperial 360 Giải Phóng, Thanh Xuân, Hà Nội
- HR: Ms. Ngọc Anh — 0356 960 580
- Email: hocbahcns@gmail.com

---

## 9. Security

| Rule | Model | Group | R | W | C | D |
|------|-------|-------|---|---|---|---|
| `access_hb_recruitment_request_user` | `hb.recruitment.request` | `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `access_hb_recruitment_request_interviewer` | `hb.recruitment.request` | `group_hr_recruitment_interviewer` | ✓ | — | — | — |
| `access_hb_interview_slot_user` | `hb.interview.slot` | `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `access_hb_interview_slot_interviewer` | `hb.interview.slot` | `group_hr_recruitment_interviewer` | ✓ | ✓ | ✓ | — |

> Không có access rule riêng cho `hr.job` và `hr.applicant` — dùng rule từ `hr_recruitment`.

---

## 10. Controller — API domain `recruitment` (cho SPA)

`controllers/main.py` cung cấp REST-ish API prefix `/hocba-hrm/api/recruitment/*`
(`auth='user'`, `type='http'`, JSON camelCase). Thao tác ghi chặn theo
`group_hr_recruitment_user`. **Hợp đồng đầy đủ:** `docs/SPEC_API_RECRUITMENT.md`.

Nhóm endpoint:
- **CV/Ứng viên:** `GET /cv`, `GET /applicant/<id>`, `POST /cv`, `POST /applicant/<id>`,
  `POST /applicant/<id>/cv-file` (upload PDF → `ir.attachment` `description='hb_cv'`),
  `POST /applicant/<id>/stage`.
- **Vị trí/JD:** `GET /jobs` (+ `requests`, `hired`), `GET /job/<id>`, `POST /jobs`, `POST /job/<id>`.
  Ghi `published` đồng bộ `is_published` + `x_published` + `recruitment_status`, và tự
  sinh `website_description` (toàn bộ thông tin) cho trang `/jobs` công khai.
- **Phiếu yêu cầu:** `GET /requests`, `GET /request/<id>`, `POST /requests`, `POST /request/<id>`, `POST /request/<id>/action`.
- **Mail mẫu:** `GET /mail-templates`, `GET /mail-template/<id>`, `POST /mail-templates`,
  `POST /mail-template/<id>`, `POST /mail-template/<id>/preview`, `POST /mail-template/<id>/send`.
  Render bằng **inline_template engine** (vì `body_html` qweb không thay `{{ }}`); send hỗ trợ ghi đè `subject`/`bodyHtml` đã sửa.
- **Lịch sử mail:** `GET /mail-logs` (nguồn `mail.message` + `mail.notification`).
- **Lịch rảnh PV:** `GET /interview-slots`, `POST /interview-slots`, `POST /interview-slot/<id>/delete`,
  `POST /interview-slot/<id>/book` (gán UV + điền lịch PV lên hồ sơ), `POST /interview-slot/<id>/unbook` (xem §7.7).
  Đọc/ghi datetime dùng `_user_tz()` đối xứng (fallback `Asia/Ho_Chi_Minh`) — tránh lệch giờ.

> **Lưu ý môi trường:** Odoo 19 — `hr.applicant` không còn field `name`; gửi mail thật cần cấu hình `ir.mail_server` (hiện hàng đợi, chế độ soạn + xem trước).

---

## 11. Điểm cần xem lại / TODO

### Đã xử lý (cập nhật 2026-06-21)

| # | Việc | Ghi chú |
|---|------|---------|
| ✅ | Tách vai duyệt phiếu (TBP order ≠ BP tuyển dụng duyệt) | §3.4 — gate action: TBP chỉ Gửi duyệt/Về nháp; Duyệt/Từ chối/Đóng chỉ `_is_hr`. Cờ `canApprove`. |
| ✅ | TBP order được phiếu dù không có ACL model | endpoint `create/update/action` ghi `.sudo()` sau khi kiểm vai+phạm vi (§3.4). |
| ✅ | Tạo hồ sơ NV từ ứng viên: map "Ngày nhận việc" | controller set `x_probation_start` = `start_date` của offer → tự seed mốc đánh giá thử việc. |
| ✅ | Đặt lịch PV cho ứng viên (chọn slot → gán UV) | §7.7 — endpoint `book/unbook`, đồng bộ `interview_date/time/interviewer_name` lên hồ sơ; UI nút Đặt UV / Hủy đặt. |
| ✅ | Thêm `depends: hocba_employees` vào manifest | controller dùng `x_employee_code/x_employment_status/x_probation_start`. |
| ✅ | Xoá code legacy | gỡ route `/hocba-tuyen-dung` + 4 file `rec-*.jsx` + `rec-styles.css`. |

### Còn lại

| # | Vấn đề | Mức độ |
|---|--------|--------|
| 1 | **Chưa có test tự động** (`tests/`). Đã có kịch bản kiểm thử thủ công `docs/QUY_TRINH_TUYEN_DUNG.md` (chạy tay 16/06 — đạt). *Quyết định: tạm chưa viết test tự động.* | Trung bình |
| 2 | `jd_google_link` trên `hb_job_positions.xml` bỏ trống — cần điền URL thực | Thấp |
| 3 | Mail templates có thông tin liên hệ hardcode — cần cập nhật khi thay nhân sự | Thấp |
| 4 | Chưa cấu hình `ir.mail_server` (SMTP) — mail gửi nằm hàng đợi; đang chạy chế độ soạn + xem trước | Trung bình |
| 5 | Sample data (`hb_applicant_data*.xml`, `hb_interview_results.xml`) — chưa kiểm tra nội dung | Cần xác nhận |
| 6 | `cv_link` seed là tên file (không phải URL) → cột Link CV chỉ hiện text; dùng upload PDF hoặc URL đầy đủ | Thấp |
| 7 | Tạo hồ sơ NV xong chưa tự điều hướng sang form NV vừa tạo | Thấp (UX) |
| 8 | Action `reset` (mở lại nháp) cho cả TBP trên phiếu closed/refused — cân nhắc giới hạn HR | Thấp (thiết kế) |
