# SPEC — Module `hocba_tuyen_dung` (v19.0.2.0.0)

> **Trạng thái:** Đã implement — branch `Viet/Recruitment`  
> **Cập nhật:** 2026-06-12  
> **Depends:** `hr_recruitment` (Odoo 19 core)

Module mở rộng tuyển dụng Odoo cho Học Bá Education. Không có SPA riêng — toàn bộ UI nằm trong menu **Recruitment** của Odoo. (Controller `/hocba-tuyen-dung` vẫn tồn tại nhưng là legacy React app chưa dùng.)

---

## 1. Cấu trúc file

```
hocba_tuyen_dung/
├── __manifest__.py
├── __init__.py
├── controllers/
│   └── main.py               # Legacy React shell (chưa dùng)
├── models/
│   ├── hb_recruitment_request.py   # Model mới
│   ├── hr_applicant.py             # Inherit
│   ├── hr_job.py                   # Inherit
│   └── hr_recruitment_stage.py     # Inherit
├── views/
│   ├── menu.xml                         # Toàn bộ menu items + window actions
│   ├── hb_recruitment_request_views.xml # Screen 7.2
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
| 20.1 | → Lịch rảnh PV | `hr.applicant` | calendar, list, form |
| 20.2 | → Danh sách phỏng vấn | `hr.applicant` | **list custom**, calendar, form — domain: `interview_date != False` |
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
                    ┌──────────────────────────────┐
                    │                              │
          draft ──► submitted ──► manager_approved ──► hr_approved ──► recruiting ──► closed
            ▲           │                │                  │
            │         refused          refused            refused
            │           │
            └───── reset_draft
```

| State | Label | Màu badge |
|-------|-------|-----------|
| `draft` | Nháp | — |
| `submitted` | Chờ TBP duyệt | info (xanh dương) |
| `manager_approved` | TBP đã duyệt | warning (vàng) |
| `hr_approved` | HR đã duyệt | success (xanh lá) |
| `recruiting` | Đang tuyển | success |
| `closed` | Đã đóng | muted (xám) |
| `refused` | Từ chối | danger (đỏ) |

### 3.3 Buttons trên form header

| Nút | Hiển thị khi | Action |
|-----|-------------|--------|
| Gửi duyệt | state = draft | `action_submit` |
| TBP Duyệt | state = submitted | `action_manager_approve` |
| HR Duyệt | state = manager_approved | `action_hr_approve` |
| Bắt đầu tuyển | state = hr_approved | `action_start_recruiting` |
| Đóng phiếu | state = recruiting | `action_close` |
| Từ chối | state ∉ (draft, recruiting, closed, refused) | `action_refuse` |
| Trả về nháp | state = refused | `action_reset_draft` |

**Smart button Job Position:** Nếu chưa có `job_id` → tạo mới `hr.job` từ `job_title + department_id`. Nếu đã có → mở xem.

### 3.4 Security

| Group | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `group_hr_recruitment_interviewer` | ✓ | — | — | — |

> **Lưu ý:** Nút TBP Duyệt và HR Duyệt đều dùng `group_hr_recruitment_user` — chưa tách role riêng.

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

| # | Tên | Người hỗ trợ | Tiêu chí thành công |
|---|-----|-------------|---------------------|
| 1 | Yêu cầu tuyển dụng | BP tuyển dụng | Yêu cầu rõ ràng, JD đầy đủ, có chỉ tiêu SL và thời gian |
| 2 | Đăng tuyển & tổng hợp CV | TBP | Tin đăng trên 3 kênh, CV tổng hợp đủ thông tin |
| 3 | Lọc CV | TBP | TBP nhận đủ hồ sơ, điền Pass/Fail tại cột Lọc CV |
| 4 | Lên lịch phỏng vấn | BP tuyển dụng | TBP điền lịch rảnh trong tuần |
| 5 | Hẹn & mời phỏng vấn | TBP | >80% ứng viên đồng ý và xác nhận lịch |
| 6 | Phỏng vấn | BP tuyển dụng | Đúng giờ, đánh giá đủ năng lực và thái độ |
| 7 | Kết quả phỏng vấn | BP tuyển dụng | BP nhận kết quả + lý do pass/không pass |
| 8 | Gửi Offer | TBP | Offer rõ ràng, ứng viên xác nhận đồng ý qua mail |
| 9 | Onboarding | TBP | Nhân sự nắm quy trình, hoà nhập, ký HĐ đầy đủ |
| 10 | Bàn giao nhân sự | TBP | Nhân sự bắt đầu chính thức, TBP tiếp nhận. `hired_stage=True` |

---

## 7. Mail Templates (4 templates — model: `hr.applicant`)

| XML ID | Tên | Chủ đề | Dùng khi |
|--------|-----|--------|---------|
| `email_template_interview_invite` | Thư mời phỏng vấn | `[HỌC BÁ] THƯ MỜI THAM GIA PHỎNG VẤN VỊ TRÍ ${job}` | Sau khi call_status = agree |
| `email_template_interview_result` | Thông báo kết quả PV | `[HỌC BÁ] THÔNG BÁO KẾT QUẢ PHỎNG VẤN VỊ TRÍ ${job}` | Khi interview_result = fail |
| `email_template_job_offer` | Thư mời nhận việc | `[HỌC BÁ] THƯ MỜI NHẬN VIỆC VỊ TRÍ ${job} - FULLTIME` | Khi interview_result = pass |
| `email_template_welcome` | Chào mừng Học Bá | `[HỌC BÁ] CHÀO MỪNG BẠN ĐẾN VỚI HỌC BÁ` | Ngày đầu nhận việc |

Tất cả template dùng biểu thức `${object.partner_name}`, `${object.job_id.name}`, `${object.interview_date.strftime('%d/%m/%Y')}`.

**Thông tin liên hệ cố định trong template:**
- Địa chỉ: Tầng 2, toà IP3, Imperial 360 Giải Phóng, Thanh Xuân, Hà Nội
- HR: Ms. Ngọc Anh — 0356 960 580
- Email: hocbahcns@gmail.com

---

## 8. Security

| Rule | Model | Group | R | W | C | D |
|------|-------|-------|---|---|---|---|
| `access_hb_recruitment_request_user` | `hb.recruitment.request` | `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `access_hb_recruitment_request_interviewer` | `hb.recruitment.request` | `group_hr_recruitment_interviewer` | ✓ | — | — | — |

> Không có access rule riêng cho `hr.job` và `hr.applicant` — dùng rule từ `hr_recruitment`.

---

## 9. Controller (legacy)

**Route:** `GET /hocba-tuyen-dung` (auth=user)

Trả về HTML shell chứa React app (CDN React 18.3.1 + Babel standalone). Load 4 file JS/JSX:
- `rec-data.jsx` — data layer
- `rec-shell.jsx` — layout shell
- `rec-dashboard.jsx` — dashboard component
- `rec-app.jsx` — root app

> **Trạng thái:** Chưa dùng trong flow hiện tại. Menu `menu_hocba_tuyen_dung_root` đã bị `active=False`.

---

## 10. Điểm cần xem lại / TODO

| # | Vấn đề | Mức độ |
|---|--------|--------|
| 1 | Nút TBP Duyệt và HR Duyệt đều dùng `group_hr_recruitment_user` — chưa tách role | Trung bình |
| 2 | `jd_google_link` trên `hb_job_positions.xml` bỏ trống — cần điền URL thực | Thấp |
| 3 | Mail templates có thông tin liên hệ hardcode — cần cập nhật khi thay nhân sự | Thấp |
| 4 | Controller React legacy còn tồn tại nhưng chưa dùng — quyết định giữ hay xóa | Thấp |
| 5 | Sample data (`hb_applicant_data*.xml`, `hb_interview_results.xml`) — chưa kiểm tra nội dung | Cần xác nhận |
