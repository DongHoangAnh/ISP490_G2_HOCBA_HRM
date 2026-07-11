# Đặc tả API domain — `recruitment` (Tuyển dụng)

**Domain:** `recruitment`
**Owner:** Việt · **Module backend:** `hocba_recruitments` · **Màn FE:** `features/recruitment/`
**Phiên bản:** 1.0 · **Ngày:** 16/06/2026 · **Trạng thái:** Đã implement (branch `Viet/Recruitment`)

---

## 1. Phạm vi

Màn Tuyển dụng (SPA) gồm **7 tab**, dữ liệu lấy trực tiếp từ Odoo (DB Neon) qua API. SPA
**đọc và ghi** (không còn chỉ đọc như v0.1): thêm/sửa CV, kéo-thả đổi stage, chỉnh
inline ngày/giờ/người PV/kết quả/offer, upload file CV PDF, quản lý vị trí & phiếu yêu
cầu, tạo lịch rảnh PV, soạn/xem trước/chỉnh sửa & gửi mail mẫu.

| # | Tab | Component | Endpoint chính |
|---|-----|-----------|----------------|
| 1 | **Danh sách CV** | `CvList` | `GET /cv` (+ create/update/stage/cv-file) |
| 2 | **Vị trí tuyển dụng / JD** | `Jobs` | `GET /jobs` (+ job CRUD) |
| 3 | **Phiếu yêu cầu** | `Requests` | `GET /requests` (+ CRUD + action) |
| 4 | **Danh sách PV** | `InterviewSlots` | `GET /interview-slots` + `GET /cv` (lọc stage Phỏng vấn) |
| 5 | **Offer & Nhận việc** | `Offers` | `GET /cv` (lọc stage Offer/Onboarding) + mail |
| 6 | **Mail mẫu tuyển dụng** | `MailTemplates` | `GET /mail-templates` (+ CRUD + send/preview) |
| 7 | **Lịch sử gửi mail** | `MailLogs` | `GET /mail-logs` |

## 2. Nguồn dữ liệu (model Odoo)

| Dữ liệu | Model | Ghi chú |
|---|---|---|
| Ứng viên / CV | `hr.applicant` (mở rộng) | `date_received`, `ctv_tuyen_dung`, `cv_link`, `cv_filter_result`, `call_status`, `interview_*`, `attendance_status`, `interview_result`, `offer_content`, `start_date`… |
| File CV (PDF) | `ir.attachment` | `res_model=hr.applicant`, `res_id`, `description='hb_cv'` (đánh dấu phân biệt) |
| Vị trí | `hr.job` (mở rộng) | `x_published`, `recruitment_status`, `jd_google_link`, `is_published`/`website_description` (module `website_hr_recruitment`) |
| Phiếu yêu cầu | `hb.recruitment.request` | mỗi phiếu = 1 vị trí cần tuyển |
| Bước quy trình | `hr.recruitment.stage` | 10 bước; `Bàn giao nhân sự` có `hired_stage=True` |
| Lịch rảnh PV | `hb.interview.slot` | datetime lưu UTC |
| Mail mẫu | `mail.template` (model `hr.applicant`) | render bằng inline_template engine |
| Lịch sử mail | `mail.message` + `mail.notification` | bền vững (template `auto_delete=True` xoá `mail.mail`) |

## 3. Quy ước chung

- Prefix `/hocba-hrm/api/recruitment/...`, `auth='user'`, `type='http'`, `csrf=False` cho POST.
- JSON key **camelCase**; ngày ISO `YYYY-MM-DD`; datetime trả về đã quy về **giờ user** (fallback `Asia/Ho_Chi_Minh`).
- Lỗi: `{"error": "<code>", "message": "..."}` + HTTP status (400/403/404).
- Thao tác **ghi** chặn theo nhóm: trả `403 forbidden` nếu không phải `hr_recruitment.group_hr_recruitment_user` (cờ `isRecruiter`); riêng slot PV dùng `_can_manage_slots` (cờ `canManage`).

---

## 4. Endpoints — CV / Ứng viên (`hr.applicant`)

### 4.1 `GET /cv`
Trả toàn bộ ứng viên active + meta (nhãn select, danh sách stages/jobs) + cờ `isRecruiter`.

**Response 200 (rút gọn):**
```json
{
  "isRecruiter": true,
  "stages": [{ "id": 1, "name": "Lọc CV", "sequence": 30 }],
  "jobs": [{ "id": 3, "name": "Giảng viên Tiếng Trung" }],
  "cvResultLabels": { "pass": "Pass", "fail": "Fail", "potential": "Tiềm năng", "contact_later": "Liên hệ sau" },
  "callStatusLabels": { "agree": "Đồng ý PV", "...": "..." },
  "attendanceLabels": { "present": "Có mặt", "absent": "Vắng" },
  "interviewResultLabels": { "pass": "Đạt", "fail": "Không đạt", "potential": "Tiềm năng" },
  "rows": [ { /* _cv_row, xem 4.2 */ } ]
}
```

### 4.2 Wire format `_cv_row`
```json
{
  "id": 12, "dateReceived": "2026-06-10", "ctv": "Huonglt",
  "name": "Nguyễn Văn A", "phone": "0901234567", "email": "a@example.com",
  "jobId": 3, "jobName": "Giảng viên Tiếng Trung",
  "cvLink": "CV_A.pdf",
  "cvFileId": 945, "cvFileName": "CV_A.pdf", "cvFileUrl": "/web/content/945?download=false",
  "cvResult": "pass", "cvNote": "...", "callStatus": "agree",
  "interviewDate": "2026-06-14", "interviewTime": "10h30", "interviewer": "Dunglt",
  "stageId": 6, "stage": "Phỏng vấn",
  "attendanceStatus": "present", "interviewResult": "pass",
  "offerContent": "Lương cứng 8tr…", "startDate": "2026-07-01",
  "offerNote": "", "candidateConfirmed": "Đã xác nhận"
}
```
- `cvFileUrl`: link mở file PDF đã upload (rỗng nếu chưa có). Lấy attachment `description='hb_cv'` mới nhất.

### 4.3 `GET /applicant/<id>` — chi tiết 1 ứng viên (`_cv_row`).

### 4.4 `POST /cv` *(recruiter)* — tạo CV thủ công
- Body: whitelist `APP_FORM_FIELDS` (camelCase). Bắt buộc `name` (tên ứng viên).
- **Lưu ý Odoo 19:** model `hr.applicant` **không còn field `name`** (tiêu đề đơn); BE chỉ set `name` khi field tồn tại (tương thích bản cũ). Tên ứng viên = `partner_name`.
- Trả `_cv_row` bản ghi mới.

### 4.5 `POST /applicant/<id>` *(recruiter)* — cập nhật
- Body: các key trong `APP_FORM_FIELDS` (gửi key nào cập nhật key đó). Dùng cho **chỉnh inline** ngày/giờ/người PV (`interviewTime`, `interviewer`), tham gia PV (`attendanceStatus`), kết quả PV (`interviewResult`), vị trí (`jobId`), offer (`offerContent`), ngày nhận việc (`startDate`).
- Trả `_cv_row` đã cập nhật.

### 4.6 `POST /applicant/<id>/cv-file` *(recruiter)* — upload file CV PDF
- **multipart/form-data**, field `file`. Giới hạn 15MB.
- Lưu `ir.attachment` (`raw`, `res_model=hr.applicant`, `res_id`, `description='hb_cv'`); **xoá file CV cũ** (giữ 1 file mới nhất).
- Trả `_cv_row` (đã có `cvFileUrl`).

### 4.7 `POST /applicant/<id>/stage` *(recruiter)* — đổi stage (kéo-thả kanban)
- Body `{ "stageId": <int> }`. Trả `_cv_row`.

---

## 5. Endpoints — Vị trí / JD (`hr.job`)

- `GET /jobs` — `rows` (mỗi `_job_row`) + `requests` + meta (`departments`, `teachingLevels`, `statusLabels`) + `isRecruiter`.
- `GET /job/<id>` — `_job_row(detail=True)` (kèm `description`).
- `POST /jobs` *(recruiter)* — tạo. `POST /job/<id>` *(recruiter)* — sửa / toggle đăng.

**`_job_row` (rút gọn):** `id, name, depId, depName, status, published, expected, hired, applications, newApplications, location, teachingLevel, requiresTeaching, sessionsPerWeek` (+ `description` khi detail).
- `hired` = `no_of_hired_employee` của vị trí.

**`requests` (vị trí đang tuyển từ phiếu — dùng cho view "Phòng ban"):** các phiếu `state='recruiting'`, mỗi item: `id, code, jobTitle, depId, depName, qty, hired, jobId, jobName, published, levelLabel, jdLink`.
- `hired` = số ứng viên ở **stage hired** (`stage_id.hired_stage=True`) của JD gắn với phiếu (đếm thực tế, kể cả hồ sơ archive).

**Trường `published` — đồng bộ 3 nơi (quan trọng):**
- `published` đọc từ **`is_published`** (trạng thái thật trên website công khai `/jobs` — nguồn sự thật), không còn đọc `x_published`.
- Khi ghi `published`: BE set **`is_published`** (web) + **`x_published`** (badge kanban) + **`recruitment_status`** (`recruiting` nếu bật / `stopped` nếu tắt).
- Mỗi lần lưu job, BE **tự sinh `website_description`** (qua `_build_website_description`) tổng hợp **toàn bộ** thông tin: Phòng ban · Số lượng cần tuyển · Trạng thái tuyển · Trình độ giảng dạy · Số buổi/tuần · Mô tả JD · link JD → trang `/jobs/<slug>` hiển thị đầy đủ. Nội dung đã escape an toàn.

---

## 6. Endpoints — Phiếu yêu cầu (`hb.recruitment.request`)

- `GET /requests` · `GET /request/<id>`
- `POST /requests` *(recruiter)* — tạo · `POST /request/<id>` *(recruiter)* — sửa
- `POST /request/<id>/action` body `{ "action": "submit|approve|close|refuse|reset_draft", ... }` — chuyển state.

State machine: `draft → submitted → recruiting → closed`; `submitted → refused → (reset_draft) → draft`.
Khi `approve` (→ recruiting): nếu phiếu có `job_id` thì **cộng dồn `qty_expected` vào `no_of_recruitment`** của vị trí (cờ `headcount_synced`, 1 lần/phiếu).

---

## 7. Endpoints — Mail mẫu (`mail.template`, model `hr.applicant`)

- `GET /mail-templates` — `rows` (mẫu) + `recipients` (ứng viên có email) + `isRecruiter`.
- `GET /mail-template/<id>` — kèm `bodyHtml`.
- `POST /mail-templates` *(recruiter)* — tạo (BE tự set `model_id=hr.applicant`, `email_to={{ object.email_from }}`).
- `POST /mail-template/<id>` *(recruiter)* — sửa.
- `POST /mail-template/<id>/preview` *(recruiter)* — **xem trước** render theo 1 ứng viên:
  - Body `{ "applicantId": <int> }` → `{ subject, bodyHtml, emailTo }`.
- `POST /mail-template/<id>/send` *(recruiter)* — gửi:
  - Body `{ "applicantIds": [...], "subject"?: "...", "bodyHtml"?: "..." }`.
  - Nếu có `subject`/`bodyHtml` (nội dung đã sửa ở màn xem trước) → gửi nội dung đó; nếu không → BE tự render mẫu.
  - Trả `{ sent, skipped }` (skip ứng viên thiếu email). Mail vào hàng đợi (`force_send=False`).

**⚠️ Render engine (quan trọng):** `mail.template.body_html` mặc định render bằng **qweb** → KHÔNG thay cú pháp `{{ }}`. BE dùng helper `_render_tmpl` render `subject`/`body_html`/`email_to` bằng **`inline_template` engine** (đúng cú pháp `{{ object.partner_name }}` mà template dùng) cho **cả preview lẫn send**, rồi ghi đè qua `email_values` khi `send_mail`.

**Placeholder hay dùng:** `{{ object.partner_name }}`, `{{ object.job_id.name }}`, `{{ object.email_from }}`, `{{ object.start_date }}`, `{{ object.offer_content }}`, `{{ object.interview_date }}`.

**Gửi thật cần SMTP:** chưa cấu hình `ir.mail_server` nên mail nằm hàng đợi (trạng thái outgoing/exception, lỗi `111`). Hiện vận hành ở chế độ **"soạn + xem trước"**. Khi cấu hình SMTP + `mail.default.from`/`mail.catchall.domain`, cron "Mail: Email Queue Manager" sẽ gửi.

---

## 8. Endpoint — Lịch sử gửi mail

`GET /mail-logs` — nguồn `mail.message` (bền vững). Trả `{ isRecruiter, rows }`, mỗi row:
```json
{ "id": 1484, "applicantId": 597, "applicant": "Nguyen Van A", "email": "a@gmail.com",
  "subject": "[HỌC BÁ] THƯ MỜI NHẬN VIỆC…", "date": "2026-06-15T18:57:45+07:00",
  "status": "sent|outgoing|failed", "failure": "" }
```
- Lọc `message_type in ('email','email_outgoing')`, `model='hr.applicant'`. `status` suy từ `mail.notification` (exception/bounce → failed; ready → outgoing; còn lại → sent).

---

## 9. Endpoints — Lịch rảnh PV (`hb.interview.slot`)

- `GET /interview-slots?from=YYYY-MM-DD&to=YYYY-MM-DD` — `{ canManage, meId, meName, interviewers, rows }`. Mỗi row có `applicantId` (slot đã đặt cho ai).
- `POST /interview-slots` *(canManage)* — tạo batch: `{ userId, slots:[{date, startHour, endHour}] }`.
- `POST /interview-slot/<id>/delete` *(canManage)*.
- `POST /interview-slot/<id>/book` *(canManage)* — `{ applicantId }`: slot → `booked` + gán ứng viên; đồng thời điền `interview_date/interview_time/interviewer_name` lên hồ sơ ứng viên. Trả về slot row.
- `POST /interview-slot/<id>/unbook` *(canManage)* — slot → `available`, gỡ ứng viên (giữ lịch PV trên hồ sơ). Trả về slot row.

**⚠️ Múi giờ (đã fix):** create dùng `_user_tz()` (fallback `Asia/Ho_Chi_Minh`) chuyển local→UTC; **đọc** (`_slot_row`) cũng dùng `_user_tz()` (không dùng `context_timestamp` vì nó để nguyên UTC khi user chưa set timezone → lệch -7h). Hai chiều đối xứng.

---

## 10. Ma trận phân quyền

| Thao tác | Điều kiện |
|---|---|
| Đọc (mọi GET) | mọi user đăng nhập |
| Ghi CV/ứng viên, upload file, đổi stage | `group_hr_recruitment_user` (`isRecruiter`) |
| Ghi vị trí/JD, phiếu yêu cầu, mail mẫu, gửi/xem trước mail | `group_hr_recruitment_user` |
| Tạo/xoá slot PV | `_can_manage_slots` (`canManage`) |

FE ẩn nút/ô chỉnh khi không phải recruiter; BE vẫn chặn 403 (không tin client).

---

## 11. Ghi chú test

- [ ] `GET /cv` → 200, có `rows`, `isRecruiter`, `cvFileUrl` đúng khi đã upload.
- [ ] Tạo CV (Odoo 19) không lỗi 500 (`name` không còn) — đã fix.
- [ ] Upload PDF → `cvFileUrl` trả về, mở `/web/content/<id>` xem được file.
- [ ] Slot PV: chọn 09:00 → hiển thị 09:00 (không lệch -7h).
- [ ] Job: bật published → live `/jobs`, `recruitment_status=recruiting`, `/jobs/<slug>` có đủ thông tin; tắt → `stopped`.
- [ ] Mail preview/send: body thay đúng `{{ }}` (inline engine), không còn placeholder thô.
- [ ] Sửa nội dung ở màn xem trước → gửi đúng nội dung đã sửa.
- [ ] `GET /mail-logs` liệt kê mail đã phát sinh + trạng thái.

## 12. TODO / phụ thuộc

- Cấu hình `ir.mail_server` (SMTP) để mail gửi thật (hiện chỉ soạn + xem trước).
- `cv_link` seed hiện là **tên file** (không phải URL) → cột "Link CV" hiển thị text; dùng upload PDF hoặc nhập URL đầy đủ để mở được.
- Cân nhắc ẩn SĐT/email ứng viên với user ngoài nhóm tuyển dụng (hiện chưa ẩn).
