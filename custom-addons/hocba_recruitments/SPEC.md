# SPEC — Module `hocba_recruitments` (v19.0.2.8.0)

> **Trạng thái:** Đã implement — branch `Viet/Recruitment`
> **Cập nhật:** 2026-08-16 (đối chiếu lại toàn bộ với code; bổ sung: cấu hình quy trình + SLA, gắn CV vào đợt tuyển & phễu 8 mốc, kết quả nhận việc, slot nhiều ứng viên + khung giờ cấu hình được, tự chuyển bước, 2 cron, 4 migration, 13 file test)
> **Odoo version:** 19.0-20260810
> **Depends:** `hr_recruitment` (Odoo 19 core) · `hocba_employees` (dùng `x_employee_code` / `x_employment_status` / `x_probation_start` khi tạo hồ sơ NV từ ứng viên, và hook lên Chính thức) · `hocba_notify` (chuông thông báo)

Module mở rộng tuyển dụng Odoo cho Học Bá Education. UI có **2 lớp**:
1. **Backend Odoo** — menu **Recruitment** (models/views mô tả §1–§10 bên dưới).
2. **SPA Tuyển dụng** (React, trong `frontend/` build vào `hocba_hrm`) — **8 tab** + màn
   **Cấu hình tuyển dụng** riêng, gọi **API domain `recruitment`**
   (`/hocba-hrm/api/recruitment/*`) do controller `controllers/main.py` cung cấp.
   Chi tiết hợp đồng API: **`docs/SPEC_API_RECRUITMENT.md`**.

> Controller React legacy `/hocba-tuyen-dung` đã bỏ; `controllers/main.py` giờ là controller API thật cho SPA.

---

## 1. Cấu trúc file

```
hocba_recruitments/
├── __manifest__.py                 # v19.0.2.8.0
├── controllers/
│   └── main.py                     # ~1.900 dòng — API JSON cho SPA
├── models/
│   ├── hb_recruitment_request.py   # Model mới — Phiếu yêu cầu (§3)
│   ├── hb_interview_slot.py        # Model mới — Slot PV + wizard (§7)
│   ├── hr_applicant.py             # Inherit (§5)
│   ├── hr_job.py                   # Inherit (§4)
│   ├── hr_recruitment_stage.py     # Inherit (§6)
│   └── hr_employee.py              # Inherit — nối kết quả thử việc về bước tuyển (§8)
├── views/
│   ├── menu.xml                          # Window actions + menu items
│   ├── hb_recruitment_request_views.xml  # Sheet 7.2
│   ├── hb_interview_slot_views.xml       # Sheet 7.3
│   ├── hb_cv_list_views.xml              # Sheet 7.4
│   ├── hb_interview_list_views.xml       # Sheet 7.5
│   ├── hb_offer_views.xml                # Sheet 7.6
│   ├── hr_applicant_kanban.xml           # Sheet 7.1
│   ├── hr_job_form_inherit.xml           # Sheet 7.8
│   └── hr_recruitment_stage_views.xml    # Cấu hình bước
├── data/
│   ├── hr_recruitment_stages.xml         # 10 bước + SLA mặc định (noupdate=1)
│   ├── hb_recruitment_request_sequence.xml
│   ├── hb_job_positions.xml              # 8 vị trí (noupdate=1)
│   ├── hb_recruitment_request_data.xml   # Sample phiếu
│   ├── hb_applicant_data.xml             # Sample ứng viên
│   ├── hb_interview_results.xml          # Sample kết quả PV
│   ├── hb_mail_templates.xml             # 4 mail template
│   └── ir_cron_data.xml                  # CRON-REC-001 (§12)
├── migrations/                     # 19.0.2.2.0 · 2.5.0 · 2.6.0 · 2.7.0 · 2.9.0 (§13)
├── tests/                          # 19 file · 218 test (§14)
└── security/
    └── ir.model.access.csv         # 8 dòng ACL
```

> ⚠️ `hb_applicant_data2.xml` / `hb_applicant_data3.xml` đã gỡ khỏi manifest lẫn repo (bản spec cũ còn ghi).

---

## 2. Menu & Navigation (backend Odoo)

Tất cả nằm dưới root menu `hr_recruitment.menu_hr_recruitment_root`.

| Seq | Menu | Model | View mode |
|-----|------|-------|-----------|
| 5 | **Vị trí / JD** | `hr.job` | list, kanban, form |
| 10 | **Ứng viên** | `hr.applicant` | list, kanban, form |
| 15 | **Phiếu yêu cầu** | `hb.recruitment.request` | list, form |
| 20 | **Phỏng vấn** _(parent)_ | — | — |
| 20.1 | → Khai báo lịch rảnh | `hb.interview.slot.wizard` | form dialog (wizard) |
| 20.2 | → Lịch rảnh PV | `hb.interview.slot` | **calendar week**, list, form |
| 20.3 | → Danh sách phỏng vấn | `hr.applicant` | list custom, calendar, form — domain `stage_id.name = 'Phỏng vấn'` |
| 25 | **Offer & Nhận việc** | `hr.applicant` | list custom, kanban, form — domain `stage_id.name in ('Gửi Offer','Onboarding')` |
| 30 | **Báo cáo** | `hr.applicant` | pivot, graph, list |
| Config.45 | **Mail mẫu** | `mail.template` | list, form — domain `model = hr.applicant` |

**Access groups trên menu:** `group_hr_recruitment_user` thấy tất cả; `group_hr_recruitment_interviewer` thấy Ứng viên + Phỏng vấn.

> ⚠️ Hai action backend 20.3 / 25 lọc theo **TÊN bước** — admin đổi tên bước trên màn Cấu hình là menu rỗng. SPA đã chuyển hết sang lọc theo **mã bước** (`stageRef`); backend còn nợ (xem §15).

---

## 3. Model: `hb.recruitment.request` — Phiếu Yêu Cầu Tuyển Dụng

Model mới. Inherit `mail.thread`, `mail.activity.mixin`. Order: `create_date desc`.

### 3.1 Fields

| Field | Type | Ghi chú |
|-------|------|---------|
| `name` | Char | Auto-sequence `hb.recruitment.request`, readonly, copy=False, tracking |
| `date_request` | Date | Default: today |
| `requester_id` | Many2one `res.users` | Default: current user, readonly |
| `department_id` | Many2one `hr.department` | Required |
| `job_id` | Many2one `hr.job` | Domain theo `department_id`, tuỳ chọn |
| `job_title` | Char | Required |
| `jd_link` | Char | Link Google Drive hoặc tên file |
| `qty_expected` | Integer | Default 1, required |
| `reason` | Selection | `new` / `replacement` / `expansion`, required |
| `level` | Selection | intern / fresher / junior / mid / senior / lead / manager |
| `education` | Selection | none / intermediate / college / bachelor / master / doctor |
| `experience_years` | Float | digits(5,1) |
| `skill_description` | Text | |
| `language_requirement` | Char | |
| `expected_start_date` | Date | **Ngày cần onboard** = deadline ở tab Theo dõi tuyển dụng |
| `salary_range` | Char | Mô tả dạng text |
| `salary_from` / `salary_to` | Float | digits(15,0) |
| `work_type` | Selection | onsite / remote / hybrid |
| `manager_id` / `hr_manager_id` / `director_id` | Many2one `res.users` | Chỉ **ghi nhận** ai ký duyệt, KHÔNG làm cổng workflow |
| `refuse_reason` | Text | |
| `note` | Html | sanitize=True |
| `headcount_synced` | Boolean | Cờ chống cộng trùng chỉ tiêu (§3.3) |
| `state` | Selection | Xem §3.2 |

**Onchange:** đổi `department_id` → bỏ `job_id` không thuộc phòng mới; chọn `job_id` → tự điền `job_title` + `jd_link`.

### 3.2 State machine

```
  draft ──► submitted ──► recruiting ──► closed
    ▲           │
    │         refused
    └───── reset_draft (từ draft/refused/closed)
```

| State | Label | Badge |
|-------|-------|-------|
| `draft` | Nháp | — |
| `submitted` | Chờ BP duyệt | info |
| `recruiting` | Đang tuyển | success |
| `closed` | Đã đóng | muted |
| `refused` | Từ chối | danger |

### 3.3 Hệ quả của `action_approve`

1. `state → recruiting`.
2. **Cộng `qty_expected` vào `job_id.no_of_recruitment`** — một lần duy nhất mỗi phiếu (`headcount_synced`).
3. Vị trí đang `stopped` (do đợt trước tuyển đủ) → mở lại `recruiting`. **Không** tự publish: đăng tin là quyết định của HR.

`action_close` chỉ chạy khi đang `recruiting`. Tuyển đủ chỉ tiêu thì phiếu **tự đóng** — xem §5.5.

### 3.6 Trạng thái tuyển của VỊ TRÍ bám theo vòng đời PHIẾU (2026-08-29)

Kho JD là kho **dùng lại**: đợt trước tuyển đủ thì vị trí về `stopped` nhưng JD vẫn nằm đó
cho đợt sau. Bất biến: **"Đang tuyển" ⇔ vị trí còn ít nhất một phiếu ĐANG MỞ.**

`OPEN_STATES = ('draft', 'submitted', 'recruiting')` — "đang mở" gồm cả **nháp / chờ duyệt**,
vì phiếu vừa tạo (còn Nháp) đã mở lại vị trí; chỉ đếm `recruiting` thì chốt đợt cũ sẽ dập tắt
luôn đợt mới đang soạn.

| Cửa | Hook | Hệ quả cho `hr.job` |
|---|---|---|
| Tạo phiếu / gắn phiếu sang vị trí khác (`create`, `write` đổi `job_id`) | `_resume_job_recruiting()` | `stopped` → **`recruiting`** ngay, không chờ duyệt |
| Duyệt phiếu (`action_approve`) | `_hb_resume_recruiting()` | như trên (giữ cho phiếu cũ) |
| Đóng phiếu — tự động khi tuyển đủ hoặc đóng tay | `_stop_jobs_without_open_request()` | hết phiếu mở ⇒ **`stopped`** + gỡ tin |
| **Từ chối** phiếu (`action_refuse`) | nt | nt |
| **Xoá** phiếu (`unlink`) | nt | nt |

Hai helper trên `hr.job` đều **idempotent** và chỉ ghi khi có thay đổi thật, nên không post
chatter trùng: `_hb_resume_recruiting()` (chỉ đổi `recruitment_status`, **không** tự bật đăng
tin — đăng tuyển là quyết định của HR) và `_hb_stop_recruiting()` (hạ trạng thái **và** gỡ
`x_published` / `is_published`).

Test: `test_job_reuse.py` (11 ca, cả hai chiều) · `test_auto_close.py` (ca tuyển đủ).

### 3.4 Thông báo chuông (`hb.notification`, category `recruitment`)

| Sự kiện | Người nhận | Level |
|---------|-----------|-------|
| `submit` | `_hr_approver_users()` = nhóm tuyển dụng ∪ HR Manager | warning |
| `approve` | `requester_id` | success |
| `refuse` | `requester_id` (kèm lý do) | danger |

- Người vừa bấm nút luôn bị loại khỏi danh sách nhận — không ai tự báo mình.
- `dedup_key = rec_request_<id>_<event>`; bấm chuông mở SPA đúng tab `requests` + drawer đúng phiếu.
- Tìm theo `all_group_ids` để bắt cả `group_hr_recruitment_manager` kế thừa. **Lệch có chủ ý:** user chỉ có `base.group_system` không nhận chuông.

### 3.5 Security & tách vai duyệt

| Group | R | W | C | D |
|-------|---|---|---|---|
| `group_hr_recruitment_user` | ✓ | ✓ | ✓ | ✓ |
| `group_hr_recruitment_interviewer` | ✓ | — | — | — |

Sheet quy trình chỉ có 2 vai nên workflow chỉ cần **một** lần duyệt (BP tuyển dụng tiếp nhận
order), không phải chuỗi "TBP → HR → BGĐ". Quyền chia **theo từng action**, enforce ở
controller `api_recruitment_request_action`:

| Action | Trạng thái | Ai được làm |
|--------|-----------|-------------|
| `submit`, `reset` | draft / refused / closed | `_is_recruiter()` = **TBP** (trưởng phòng) **hoặc** BP tuyển dụng/HR |
| `approve`, `refuse`, `close` | submitted / recruiting | **chỉ `_is_hr()`** |

- API list trả cờ **`canApprove = _is_hr()`**; `RequestDrawer.jsx` ẩn nút Duyệt/Từ chối/Đóng nếu không có cờ.
- ⚙️ **Ghi qua `.sudo()` SAU khi kiểm vai + phạm vi:** ACL model chỉ cho `group_hr_recruitment_user` ghi, nên endpoint `create/update/action` dùng `.sudo()` để **TBP order được phiếu** dù không có ACL. `requester_id` vẫn = người đăng nhập.
- ⚠️ **TBP không được gán `group_hr_recruitment_user`** — gán là mất tách vai.

---

## 4. Model: `hr.job` (inherit)

### 4.1 Fields thêm

| Field | Type | Ghi chú |
|-------|------|---------|
| `x_published` | Boolean | Badge PUBLISHED xanh trên kanban. Default False, tracking |
| `recruitment_status` | Selection | `recruiting` / `stopped`. Default recruiting, tracking |
| `jd_google_link` | Char | Link JD Google Drive |
| `x_teaching_level` | **Char** | Trình độ tiếng Trung — **nhập tự do**, `HB_TEACHING_LEVELS` chỉ là danh sách **gợi ý** (HSK1–9, HSK7-9, HSKK, TOCFL) đổ vào `<datalist>` |
| `x_required_sessions_per_week` | Integer | Default 0 |

> `x_requires_teaching_level` (compute) trong bản spec cũ **đã bỏ**.

### 4.2 `write()` — gương publish ↔ trạng thái tuyển

Đổi `is_published` **hoặc** `x_published` từ **bất kỳ đâu** (SPA, form backend, công tắc
Publish của website) đều: gương hai cờ với nhau, và set `recruitment_status` = `recruiting`
nếu bật / `stopped` nếu tắt. Trạng thái truyền tường minh trong cùng `write` vẫn được tôn trọng.

### 4.3 Constraint

**Chỉ còn một:** không trùng `name` trong cùng `department_id` (với `active = True`).

> **Ràng buộc "phòng Giảng viên/Trợ giảng bắt buộc điền Trình độ" đã BỎ (2026-08-07).** Lý do
> ghi đầy đủ trong `hr_job.py`: đối chiếu file quy trình gốc của khách (59 sheet) thì cụm 7.x
> không có cột trình độ ở bất kỳ sheet nào; "Trình độ tiếng Trung" chỉ nằm ở sheet 2.1 (hồ sơ
> nhân viên) và 165/168 nhân sự để trống. Ràng buộc cũ còn so **tên** phòng ban với
> 'Giảng viên'/'Trợ giảng' — hai phòng không có trong 6 phòng chuẩn nên nó chưa từng chạy trên
> dữ liệu thật. Muốn thêm lại thì đọc ghi chú ở cuối `hr_job.py` trước.

### 4.4 Seed data — 8 vị trí (`noupdate=1`)

Tư vấn tuyển sinh · Giáo viên dạy tiếng Trung · Chuyên viên R&D · Quản lý học viên ·
Content Marketing · Trợ giảng · Giáo vụ · Hành chính nhân sự.

### 4.5 Views

- **Form inherit**: nút Đăng tuyển / Ngừng đăng ở header; `recruitment_status` + `jd_google_link` sau `department_id`; nhóm yêu cầu giảng dạy.
- **Kanban inherit**: badge `PUBLISHED` khi `x_published`.
- **List inherit**: thêm `recruitment_status`, `address_id`, `new_application_count`, `x_published`, `jd_google_link`.
- **Search view**: filter Đang tuyển / Dừng tuyển / Đã đăng tuyển; group by phòng ban / trạng thái.

### 4.6 Chỉ tiêu tuyển (`no_of_recruitment`) đến từ PHIẾU, không nhập tay lúc tạo JD

Chỉ tiêu là của **đợt tuyển**: duyệt phiếu cộng `qty_expected` vào vị trí, đóng phiếu trả lại
phần chưa tuyển (`_release_headcount`, §3). Vì vậy từ 2026-08-29:

- Form vị trí (Kho JD) **bỏ hẳn** ô "Số lượng cần tuyển" và "Số buổi/tuần tối thiểu" — **cả
  lúc Thêm lẫn lúc Sửa**; form không gửi `expected` / `sessionsPerWeek` nên sửa JD không đụng
  hai số này. Số "còn cần tuyển" vẫn xem được ở drawer chi tiết vị trí.
- `api_recruitment_job_create` chốt `no_of_recruitment = 0` khi payload không gửi `expected`:
  default của core `hr.job` là **1**, để nguyên thì JD vừa tạo đã "còn thiếu 1 người" trong
  khi chưa có phiếu nào — chỉ tiêu ma đó khiến vị trí không bao giờ về 0 để tự ngừng đăng.
- Test: `test_job_create_quota.py`.

### 4.7 Mô tả công việc (JD) — DB giữ HTML, người dùng chỉ thấy text

`hr.job.description` là field **Html** (`sanitize=True`). Quy ước chốt 2026-08-29 để không
ai phải nhìn thấy thẻ:

| Nơi | Xử lý |
|---|---|
| Ô "Mô tả công việc (JD)" trên SPA | `JobForm` hiện **text thuần** (`htmlToText` của `mailSend.js`) — HR không thấy `<p>…</p>` |
| Lưu từ SPA | `_job_vals` gọi `plaintext2html` khi giá trị **chưa có thẻ** ⇒ DB luôn là HTML, xuống dòng không mất |
| Drawer chi tiết JD | render bằng `dangerouslySetInnerHTML` (vốn đã đúng) |
| Trang tuyển dụng công khai | `_as_html()` — **giữ nguyên thẻ thật**, chỉ escape + `nl2br` phần text thuần |

> 🐞 Lỗi đã sửa: `_build_website_description` trước đây `escape(j.description)` một field Html
> ⇒ trang `/jobs` in ra đúng chữ `<p>…</p>` cho ứng viên đọc. Nhận diện "đã là HTML chưa" bằng
> `_HTML_TAG_RE` (cố ý chặt: `<` + chữ cái) để câu như "Lương < 10 triệu" vẫn được escape.
> Test: `test_job_description_html.py`.
>
> **Phần mail đã rà cùng đợt và KHÔNG dính lỗi này:** `/preview` trả HTML thật, 3 chỗ hiển thị
> (`MailSendModal`, `MailTemplateForm`, `MailTemplateImport`) đều render HTML, và thân thư gửi
> qua Gmail được `htmlToText` hoá text thuần trước khi điền.

Cùng đợt, **đăng / ngừng đăng tuyển gom về đúng MỘT chỗ: tab Theo dõi tuyển dụng.**
Form Thêm/Sửa vị trí bỏ ô tích **"Đăng tuyển lên website công khai (/jobs)"** và `JobDrawer`
(Kho JD) bỏ nút toggle **Đăng tuyển / Ngừng đăng** — cả hai **không gửi khoá `published`**
nữa, nên sửa nội dung JD không còn vô tình gỡ tin đang chạy. Kho JD vẫn HIỆN trạng thái đăng
(badge + link trang công khai) để tra cứu. Nút toggle ở `RequestTracking` chỉ gửi
`{published}` và trạng thái tuyển suy theo cờ đăng (§4.2); luật `setdefault` ở `_job_vals`
giữ nguyên cho payload nào gửi cả hai.

---

## 5. Model: `hr.applicant` (inherit)

### 5.1 Đợt tuyển — `hb_request_id`

Spec: `docs/superpowers/specs/2026-08-08-recruitment-request-tracking-design.md`.

| Field | Type | Ghi chú |
|-------|------|---------|
| `hb_request_id` | Many2one `hb.recruitment.request` | index, `ondelete='set null'`, tracking |

Trước đây số liệu theo dõi phải bắc cầu qua JD (`job_id`) nên **hai đợt tuyển cùng một vị trí
thấy CHUNG một bộ số**. Nay CV gắn thẳng vào phiếu:

- `_hb_open_request()` — phiếu **đang tuyển** mới nhất của vị trí; cố ý **không** lùi về phiếu đã đóng/nháp/từ chối (CV nộp lúc không có đợt nào mở thì thật sự không thuộc đợt nào).
- `_hb_fill_request()` — điền cho CV còn trống ô này, chạy ở `create()` và khi `write()` đổi `job_id`. **Không bao giờ ghi đè** giá trị HR đã gán tay.
- Dữ liệu cũ được đoán lại bằng migration 19.0.2.7.0 (§13).

### 5.2 Fields thêm — Sheet 7.4 (Danh sách CV)

| Field | Type | Ghi chú |
|-------|------|---------|
| `date_received` | Date | index, default today |
| `ctv_tuyen_dung` | Char | CTV tuyển dụng |
| `cv_link` | Char | Link Drive / tên file |
| `cv_filter_result` | Selection | `pass` / `fail` / `potential` / `contact_later`, tracking |
| `cv_note` | Text | |
| `call_status` | Selection | `agree` / `refuse` / `potential` / `contact_later`, tracking |
| `interview_date` | Date | |
| `interview_time` | Char | VD: 10h, 10h30 |
| `interviewer_name` | Char | |

### 5.3 Fields thêm — Sheet 7.5 / 7.6 (Phỏng vấn · Offer & Nhận việc)

Spec `onboard_result`: `docs/superpowers/specs/2026-08-09-recruitment-onboard-result-design.md`.

| Field | Type | Ghi chú |
|-------|------|---------|
| `attendance_status` | Selection | `present` / `absent`, tracking |
| `interview_result` | Selection | `pass` / `fail` / `potential`, tracking |
| `offer_content` | Text | |
| `start_date` | Date | Ngày nhận việc |
| `offer_note` | Text | |
| `candidate_confirmed` | Char | |
| **`onboard_result`** | Selection | **`arrived` / `no_show`** — cột "Kết quả nhận việc" của sheet 7.6, tracking |

**`onboard_result` bỏ trống = CHƯA XÁC ĐỊNH** (đã gửi thư mời, đang chờ tới ngày hẹn) — đó là
trạng thái mặc định nên không cần giá trị riêng. Thiếu ô này thì ứng viên bùng nằm lẫn với
người đang chờ và không đo được tỷ lệ nhận offer rồi bùng.

**Constraint `_check_onboard_result_vs_stage`:** đã ở bước `hired_stage` thì không đánh
`no_show` được — vừa mâu thuẫn dữ liệu, vừa phá bất biến của phễu ("Đã tuyển" sẽ lớn hơn
"Nhận việc").

**Guard `_check_hired_regression` (ở `write`, không phải `constrains`):** không kéo hồ sơ RA
KHỎI bước Bàn giao khi nhân viên đã `official`. Hook đẩy bước chỉ chạy một lần lúc lên chính
thức nên kéo lùi sau đó là hỏng vĩnh viễn, mà chỉ tiêu tuyển thì được cộng lại và tin đã đóng
có thể mở lại. Chỉ chặn khi NV đã chính thức — kéo nhầm lúc còn thử việc vẫn sửa được.

### 5.4 SLA theo bước

`_hb_sla_state()` → `(số ngày ở bước, sla_days của bước, có trễ không)`. Mốc vào bước =
`date_last_stage_update`, fallback `create_date`. Bước `hired_stage` hoặc `sla_days = 0` →
không tính trễ. API trả `daysInStage` / `slaDays` / `slaOverdue`; SPA hiện badge
"Quá hạn N ngày" trên card kanban.

### 5.5 Tự động đóng phiếu / ngừng đăng khi tuyển đủ

`_hb_auto_close_if_filled()` chạy khi ứng viên vào stage `hired_stage` (qua kéo kanban SPA,
backend, hay import — đều đi qua `create`/`write`). Hook xét **hai mức**, theo đúng thứ tự:

1. **Vị trí** — chỉ tiêu **tổng** của `hr.job` về 0 ⇒ ngừng đăng (+ đóng mọi phiếu đang tuyển
   ở chế độ `full`).
2. **Phiếu** — đóng khi số ứng viên của chính phiếu (`hb_request_id`) đã vào bước Bàn giao
   đạt `qty_expected`. Chỉ chạy ở chế độ `full`.

Tách hai mức từ 2026-08-29: `no_of_recruitment` là **tổng** (số có sẵn trên JD + mọi phiếu đã
duyệt), nên chờ tổng về 0 mới đóng thì một phiếu đã tuyển đủ người vẫn treo "Đang tuyển" chỉ
vì vị trí còn chỉ tiêu của phiếu khác. Đi kèm: form Thêm vị trí không còn ô "Số lượng cần
tuyển" và controller chốt `no_of_recruitment = 0` lúc tạo (§4.6).

**Chốt phiếu cuối cùng ⇒ vị trí về Dừng tuyển.** `_stop_jobs_without_open_request()` chạy ở
cả ba cửa chốt phiếu — **đóng** (tự động khi tuyển đủ hoặc đóng tay), **từ chối**, **xoá**:
vị trí không còn phiếu nào ở `OPEN_STATES` thì hạ `recruitment_status` về `stopped` và gỡ tin
đăng (`hr.job._hb_stop_recruiting()`, idempotent, cũng là chỗ vòng lặp vị trí ở trên dùng).
Nhờ vậy "Đang tuyển" trên Kho JD luôn có nghĩa **còn đợt tuyển đang mở** — kể cả với vị trí
mang chỉ tiêu dư của dữ liệu cũ. Còn phiếu khác đang mở thì KHÔNG đụng: đợt kia vẫn cần tin
chạy. Chiều ngược (dùng lại JD cũ) ở §3.6.

Core Odoo 19 coi `no_of_recruitment` là số **còn thiếu** (tự trừ 1 khi vào hired) ⇒ hook chạy
sau `super().write()` nên "đủ chỉ tiêu" ⇔ `no_of_recruitment <= 0`.

| `auto_close_mode` | Hành vi |
|---|---|
| `full` *(mặc định)* | Đóng phiếu đủ số của nó · vị trí hết chỉ tiêu thì ngừng đăng **+ đóng** mọi phiếu đang tuyển còn lại |
| `stop` | Chỉ ngừng đăng tuyển, giữ phiếu |
| `warn` | Chỉ ghi cảnh báo lên chatter |
| `off` | Không làm gì |

Cấu hình ở `ir.config_parameter` `hocba_recruitments.auto_close_mode` (màn Cấu hình tuyển dụng).

### 5.6 Tự chuyển bước (auto-stage)

Tất cả đi qua `_hb_advance_stage(from_ref, to_ref, reason)`:
**bám xmlid chứ không bám tên bước** (admin đổi tên là chuyện thường), **chỉ đẩy tới không kéo
lùi**, bước bị xoá/ẩn thì im lặng bỏ qua, và **ghi chatter** để lần được ai/khi nào bị máy đổi bước.

| Kích hoạt | Bước nguồn → đích | Nơi cài |
|---|---|---|
| `cv_filter_result = pass` | Lọc CV → Lên lịch phỏng vấn | `hr_applicant.write` |
| Điền `interview_date` | Lên lịch PV → Hẹn & mời PV | `hr_applicant.write` |
| Điền `interview_result` (bất kỳ giá trị) | Phỏng vấn → Kết quả phỏng vấn | `hr_applicant.write` |
| Xếp UV vào slot | Hẹn & mời PV → Phỏng vấn | `hb_interview_slot.create/write` |
| Gửi mail **Thư mời phỏng vấn** | Hẹn & mời PV → Phỏng vấn | `controllers.MAIL_STAGE_RULES` |
| Gửi mail **Thư mời nhận việc** | Phỏng vấn / Kết quả PV → Gửi Offer | `controllers.MAIL_STAGE_RULES` |
| NV lên `official` | Onboarding → Bàn giao nhân sự | `hr_employee.write` (§8) |

> **Pass PV KHÔNG tự nhảy sang Gửi Offer** — quyết định offer là của HR, không phải của máy.
> Luật mail áp cho **cả hai** đường gửi (`/send` qua SMTP và `/mail/log-sent` qua Gmail);
> SPA đang dùng đường Gmail nên đừng chỉ vá một chỗ.

### 5.7 Nhắc CV quá hạn xử lý (CRON-REC-001)

Spec: `docs/superpowers/specs/2026-08-03-recruitment-overdue-notification-design.md`.

Ứng viên bị nhắc khi thoả **cả 4**: `active` · `stage_id.sla_days > 0` ·
`stage_id.hired_stage = False` · `interview_result != 'fail'` — khớp 1-1 với luật hiện badge
trên card kanban, cố ý để "có badge" ⇔ "có thông báo".

| `overdue_notify_mode` | Người nhận |
|---|---|
| `both` *(mặc định)* | Nhóm tuyển dụng + Trưởng phòng của vị trí |
| `hr_only` | Chỉ nhóm tuyển dụng |
| `manager_only` | Chỉ Trưởng phòng |
| `off` | Tắt hẳn |

`dedup_key = rec_overdue_<id>`: còn một dòng **chưa đọc** cùng khoá thì bỏ qua ⇒ chạy 30 ngày
liền vẫn 1 dòng; đọc rồi mà chưa xử lý thì hôm sau nhắc lại.

> Phải tắt được mà không cần sửa code: phòng Giảng viên có ~169 NV, ngày gán Trưởng phòng cho
> phòng đó thì người này nhận chuông cho **mọi** CV giáo viên quá hạn.

### 5.8 Views

- **List custom 7.4** (`hb_view_applicant_cv_list`), **7.5** (`hb_view_applicant_interview_list`), **7.6** (`hb_view_applicant_offer_list`).
- **Form inherit**: 2 tab thêm — "Lọc CV & Phỏng vấn", "Kết quả PV".
- **Kanban inherit**: thêm `source_id` + `create_date`; Việt hoá dropdown.
- **Search inherit**: filter CTV, người PV, kết quả lọc CV, trạng thái gọi, PV hôm nay, kết quả PV, tham gia PV, có offer, UV xác nhận, có ngày nhận việc.

### 5.9 Mail actions (4 nút trên form header)

Mời phỏng vấn · Kết quả phỏng vấn · Thư mời nhận việc · Chào mừng Học Bá — hiện khi `email_from` có giá trị.

---

## 6. Model: `hr.recruitment.stage` (inherit)

### 6.1 Fields thêm

| Field | Type | Ghi chú |
|-------|------|---------|
| `success_criteria` | Text | Điều kiện hoàn thành bước |
| `support_person` | Char | BP/người phối hợp |
| `sla_days` | Integer | Hạn xử lý; 0 = không áp. Constraint: không âm |
| `active` | Boolean | Ẩn bước khỏi kanban & form chọn, không xoá dữ liệu |

### 6.2 Guard

| Hàm | Chặn |
|-----|------|
| `_check_can_hide` (khi `active = False`) | Phải còn ≥ 1 bước hiển thị; không ẩn bước còn ứng viên **đang hoạt động** |
| `_unlink_except_in_use` (`@api.ondelete`) | Không xoá bước còn ứng viên **kể cả đã lưu trữ**; phải còn ≥ 1 bước |
| `action_reorder(ordered_ids)` | Ghi lại `sequence` 10/20/30… theo thứ tự kéo-thả từ SPA (`check_access('write')`) |

### 6.3 Seed data — 10 bước (`noupdate=1`)

Bước nhảy 10 để dễ chèn bước mới.

| Seq | Tên | xmlid | SLA | Người hỗ trợ |
|-----|-----|-------|-----|--------------|
| 10 | Yêu cầu tuyển dụng | `hb_stage_request` | — | BP tuyển dụng |
| 20 | Đăng tuyển & tổng hợp CV | `hb_stage_sourcing` | — | TBP |
| 30 | Lọc CV | `hb_stage_screening` | 1 | TBP |
| 40 | Lên lịch phỏng vấn | `hb_stage_schedule` | 1 | BP tuyển dụng |
| 50 | Hẹn & mời phỏng vấn | `hb_stage_invite` | 1 | TBP |
| 60 | Phỏng vấn | `hb_stage_interview` | — | BP tuyển dụng |
| 70 | Kết quả phỏng vấn | `hb_stage_result` | 1 | BP tuyển dụng |
| 80 | Gửi Offer | `hb_stage_offer` | 1 | TBP |
| 90 | Onboarding | `hb_stage_onboarding` | 2 | TBP |
| 100 | Bàn giao nhân sự | `hb_stage_hired` | — | TBP · `hired_stage=True` |

> `noupdate="1"` từ v19.0.2.2.0: admin sửa bước trên màn Cấu hình sẽ **không** bị upgrade ghi đè.
> Hai sequence 60 và 90 được controller dùng làm mốc phễu (`_STAGE_INTERVIEW_SEQ` / `_STAGE_ONBOARD_SEQ`).

### 6.4 Cleanup stage mặc định của Odoo

`<function name="_hocba_cleanup_default_stages"/>` cuối `hr_recruitment_stages.xml`, chạy mỗi
lần upgrade: tìm stage tên trong `_ODOO_DEFAULT_STAGE_NAMES` → reassign toàn bộ applicant (kể
cả archived, `active_test=False`) về `hb_stage_request` → unlink.

---

## 7. Model: `hb.interview.slot` — Lịch rảnh phỏng vấn (Sheet 7.3)

Model mới. Order `start_datetime`. **Không** inherit `mail.thread`.

### 7.1 Fields

| Field | Type | Ghi chú |
|-------|------|---------|
| `name` | Char (compute, store) | `"{user} — {dd/mm HH:MM}"` theo tz user |
| `start_datetime` / `stop_datetime` | Datetime | Required (UTC) |
| `user_id` | Many2one `res.users` | Required, default current user |
| `department_id` | Many2one `hr.department` | Compute từ `hr.employee.user_id`, store |
| **`applicant_ids`** | **Many2many** `hr.applicant` | Bảng `hb_interview_slot_applicant_rel` — **một slot phỏng vấn được NHIỀU ứng viên** (PV nhóm / hội đồng gọi lần lượt) |
| `applicant_count` | Integer (compute, store) | |
| `state` | Selection (**compute**, store, readonly) | `available` / `booked` — **suy ra từ `applicant_ids`**, tránh 2 nguồn sự thật lệch nhau |
| `notes` | Text | |

> Đổi từ `applicant_id` (many2one) sang `applicant_ids` ở v19.0.2.5.0 — xem migration §13.
> `action_mark_booked` cũ đã bỏ (state không set tay được nữa); còn `action_mark_available` = gỡ hết ứng viên.

### 7.2 Constraint

`stop_datetime > start_datetime` → ValidationError.

### 7.3 Khung giờ khai slot — **cấu hình được**

Spec: `docs/superpowers/specs/2026-08-11-interview-hours-config-design.md`.

| `ir.config_parameter` | Mặc định |
|---|---|
| `hocba_recruitments.slot_hour_open` | 9.0 |
| `hocba_recruitments.slot_hour_close` | 17.0 |
| `hocba_recruitments.slot_step_minutes` | 30 (chỉ nhận 15 / 30 / 60) |

`_hb_slot_hour_config()` luôn trả giá trị dùng được: tham số hỏng thì rơi về mặc định thay vì
nổ lỗi giữa lúc TBP đang khai lịch. `_hb_hour_slots()` cộng dồn **theo chỉ số** chứ không
`cur += inc` — cộng float 121 lần thì 17.0 thành 16.999999 và mốc cuối biến mất.

> Selection của wizard là **callable**, không phải list: list bị đóng băng lúc load module ⇒ đổi cấu hình phải restart Odoo mới thấy.

### 7.4 Wizard `hb.interview.slot.wizard`

TBP mở từ menu **Phỏng vấn → Khai báo lịch rảnh**: chọn `user_id` + các dòng
`date` / `start_hour` / `end_hour`. `action_create_slots` convert giờ local → UTC
(`user.tz`, fallback `Asia/Ho_Chi_Minh`) rồi tạo `hb.interview.slot`, sau đó về calendar.

### 7.5 Views

Calendar `mode="week"` (màn chính) · List (xanh = available, muted = booked) · Form · Search
(filter available/booked/tuần này; group by ngày/người PV/phòng ban/trạng thái).

### 7.6 Đặt lịch PV cho ứng viên (SPA — tab Danh sách PV)

Quyền: `_can_manage_slots()` = HR **hoặc** trưởng phòng **hoặc** interviewer.

| Endpoint | Mô tả |
|----------|-------|
| `POST …/interview-slot/<id>/book` `{applicantId}` | Nối UV vào `applicant_ids` (slot → `booked`); **đồng thời** điền lên hồ sơ: `interview_date` = ngày slot, `interview_time` = giờ bắt đầu, `interviewer_name` = người PV. Đẩy bước Hẹn & mời PV → Phỏng vấn |
| `POST …/interview-slot/<id>/unbook` | Gỡ UV khỏi slot; **giữ nguyên** lịch PV đã ghi trên hồ sơ, **không** kéo bước về |

Nhờ đồng bộ `interview_date`, mail **Thư mời phỏng vấn** (`{{ object.interview_date }}`) tự điền đúng lịch vừa đặt.

---

## 8. Model: `hr.employee` (inherit) — nối thử việc về bước tuyển dụng

Ứng viên nhận việc đứng ở bước **Onboarding** cho tới khi hết thử việc. Người chốt "đạt thử
việc" làm ở module Nhân sự chứ không mở tab Tuyển dụng ⇒ không tự đẩy thì hồ sơ nằm mãi ở
Onboarding và **chỉ tiêu tuyển không bao giờ được trừ**.

`write()` bắt `x_employment_status = 'official'` → `_hb_advance_applicant_to_handover()`:
tra ngược qua `hr.applicant.employee_id` (`active_test=False` vì hồ sơ ứng viên hay bị lưu trữ)
→ đẩy Onboarding → Bàn giao nhân sự. Bước này là `hired_stage` nên **trừ chỉ tiêu** và có thể
kích hoạt tự ngừng đăng tin (§5.5) — đúng ý đồ, không phải tác dụng phụ.

> Đặt ở `hocba_recruitments` (đã depends `hocba_employees`) chứ không nhét ngược vào
> `hocba_employees`: tuyển dụng biết về nhân sự, chiều ngược lại thì không.

---

## 9. Mail Templates (4 — model `hr.applicant`)

| XML ID | Tên | Dùng khi |
|--------|-----|---------|
| `email_template_interview_invite` | Thư mời phỏng vấn | Sau khi `call_status = agree` — **đẩy bước** Hẹn & mời PV → Phỏng vấn |
| `email_template_interview_result` | Thông báo kết quả PV | Khi `interview_result = fail` |
| `email_template_job_offer` | Thư mời nhận việc | Khi `interview_result = pass` — **đẩy bước** → Gửi Offer |
| `email_template_welcome` | Chào mừng Học Bá | Ngày đầu nhận việc |

Cú pháp **Jinja2 chuẩn** (Odoo 17+): `{{ object.partner_name }}`,
`{{ object.interview_date.strftime('%d/%m/%Y') if object.interview_date else '' }}`.

**Thông tin liên hệ hardcode trong template:** Tầng 2, toà IP3, Imperial 360 Giải Phóng,
Thanh Xuân, Hà Nội · HR Ms. Ngọc Anh — 0356 960 580 · hocbahcns@gmail.com.

---

## 10. Security & phân quyền

### 10.1 ACL model (`ir.model.access.csv` — 8 dòng)

| Model | `group_hr_recruitment_user` | `group_hr_recruitment_interviewer` |
|-------|---|---|
| `hb.recruitment.request` | R W C D | R |
| `hb.interview.slot` | R W C D | R W C |
| `hb.interview.slot.wizard` (+ line) | R W C D | R W C D |

> Không có rule riêng cho `hr.job` / `hr.applicant` — dùng rule của `hr_recruitment`.

### 10.2 Vai ở tầng controller

| Hàm | Định nghĩa | Dùng cho |
|-----|-----------|----------|
| `_is_hr()` | `base.group_system` ∪ `hr.group_hr_manager` ∪ nhóm tuyển dụng (user/manager) | Xem & thao tác **mọi phòng ban**; duyệt/từ chối/đóng phiếu |
| `_is_dept_manager()` | Đứng `manager_id` của ít nhất 1 phòng | Trưởng phòng (TBP) |
| `_is_recruiter()` | `_is_hr()` ∪ `_is_dept_manager()` | Thêm/sửa/đổi bước (trong phạm vi) |
| `_can_manage_slots()` | `_is_recruiter()` ∪ interviewer | Khai/đặt/huỷ slot PV |
| `_can_config()` | `base.group_system` ∪ `hr.group_hr_manager` | Màn Cấu hình tuyển dụng (spec v1.2 nới từ chỉ-Admin) |
| `_is_admin()` | `base.group_system` | Thêm/xoá/sắp bước quy trình |

**Phạm vi phòng ban** (`_dept_scope_ids()`): `None` = không giới hạn (HR) · `list` = các phòng
mình quản lý **gồm phòng con** (duyệt cây `parent_id`) · `[]` = không có quyền. Áp cho danh
sách CV / vị trí / phiếu, **và cả các ô chọn** (`_meta`, `_job_meta`, `_req_meta`) — chặn ngay
từ ô chọn thay vì để user chọn rồi mới ăn 403 lúc lưu.

---

## 11. Controller — API domain `recruitment` (cho SPA)

`controllers/main.py`, prefix `/hocba-hrm/api/recruitment/*` (`auth='user'`, `type='http'`,
JSON camelCase). **Hợp đồng đầy đủ:** `docs/SPEC_API_RECRUITMENT.md`.

### 11.1 Nhóm endpoint

- **CV/Ứng viên:** `GET /cv`, `GET /applicant/<id>`, `POST /cv`, `POST /applicant/<id>`,
  `POST /applicant/<id>/cv-file` (PDF → `ir.attachment` `description='hb_cv'`; fallback file
  mới nhất cho CV nộp từ form công khai `/jobs/apply`), `POST /applicant/<id>/stage`,
  `POST /applicant/<id>/create-employee`.
- **Vị trí/JD:** `GET /jobs` (kèm `requests` + thống kê phễu), `GET /job/<id>`, `POST /jobs`,
  `POST /job/<id>`. Ghi `published` đồng bộ `is_published` + `x_published` +
  `recruitment_status`, và tự sinh `website_description` (Thông tin tuyển dụng · Yêu cầu ứng
  viên · Mô tả công việc · link JD) cho trang `/jobs` công khai.
- **Theo dõi đợt tuyển:** `GET /request/<id>/applicants?group=<key>` — danh sách ứng viên theo
  nhóm phễu + thông tin JD.
- **Phiếu yêu cầu:** `GET /requests`, `GET /request/<id>`, `POST /requests`,
  `POST /request/<id>`, `POST /request/<id>/action`.
- **Mail mẫu:** `GET|POST /mail-templates`, `GET|POST /mail-template/<id>`,
  `POST /mail-template/<id>/preview|send|delete`. Render bằng **inline_template engine**
  (`body_html` qweb không thay `{{ }}`); `send` cho ghi đè `subject`/`bodyHtml` đã sửa.
- **Lịch sử mail:** `GET /mail-logs` (`mail.message` + `mail.notification`),
  `POST /mail/log-sent` (ghi lịch sử mail gửi qua Gmail — cũng chạy luật đẩy bước).

**Quyền cụm mail — HAI cờ khác nhau, đừng gộp** (bug C1 #5, QA 2026-08-07):

| Endpoint | Gate |
|----------|------|
| `GET /mail-templates`, `GET /mail-template/<id>`, `POST …/preview`, `GET /mail-logs` | `_is_recruiter()` — payload kèm họ tên · email ứng viên nên user thường không được đọc; `recipients` và `/preview` còn lọc theo phạm vi phòng ban |
| `POST /mail-templates`, `POST /mail-template/<id>`, `…/delete` | `_is_hr()` → cờ **`canEdit`** — mail mẫu là cấu hình email **toàn hệ thống**, không theo phòng ban |
| `POST /mail-template/<id>/send` (SMTP) | `_is_hr()` |
| `POST /mail/log-sent` (đường Gmail — SPA đang dùng) | `_is_recruiter()` → cờ **`canSend`**: trưởng phòng được gửi, nhưng chỉ tới ứng viên phòng mình |
- **Lịch rảnh PV:** `GET|POST /interview-slots`, `POST /interview-slot/<id>/delete|book|unbook`.
  Đọc/ghi datetime dùng `_user_tz()` đối xứng (fallback `Asia/Ho_Chi_Minh`).
- **Cấu hình:** `GET /config`, `POST /config/slot-hours`, `POST /config/stages`,
  `POST /config/stage/<id>`, `POST /config/stage/<id>/delete`, `POST /config/stages/reorder`,
  `POST /config/settings`.

### 11.2 Phễu tuyển dụng theo phiếu (`APPLICANT_GROUPS`)

Thứ tự đúng bằng thứ tự khách đọc bảng — **dùng chung cho cả đếm lẫn popup danh sách**, để con
số bấm vào và danh sách hiện ra không bao giờ lệch nhau. Query chạy trên
`hr.applicant` với `active_test=False` (hồ sơ hay bị lưu trữ sau khi nhận việc).

| Nhóm | Định nghĩa |
|------|-----------|
| `cv` | Tổng CV của đợt |
| `cv_pass` / `fail_cv` | `cv_filter_result = pass` / `fail` |
| `pv` | Bước ≥ 60 **HOẶC** có `interview_date` / `attendance_status` / `interview_result` |
| `pv_pass` / `fail_pv` | `interview_result = pass` / `fail` |
| `onboard` | (bước ≥ 90 **HOẶC** có `start_date` **HOẶC** `onboard_result = arrived`) **VÀ** `onboard_result != no_show` |
| `hired` | `stage_id.hired_stage = True` |

> Hai mốc `pv` và `onboard` không có trường riêng nên phải suy ra, và suy theo kiểu **HỢP (OR)**
> để phễu không bao giờ hụt: nhóm sau luôn nằm trong nhóm trước. Chỉ lấy stage thì ứng viên đã
> có kết quả PV mà chưa ai kéo thẻ sẽ rơi ra ngoài "PV" ⇒ "PV fail" nhiều hơn "PV", người xem
> tưởng số liệu sai. `onboard` trừ hẳn người `no_show` vì `start_date` vẫn nằm trên hồ sơ sau
> khi ứng viên bùng.

### 11.3 Cấu hình lưu ở `ir.config_parameter`

| Khoá | Giá trị |
|------|---------|
| `hocba_recruitments.auto_close_mode` | `full` / `stop` / `warn` / `off` |
| `hocba_recruitments.overdue_notify_mode` | `both` / `hr_only` / `manager_only` / `off` |
| `hocba_recruitments.slot_hour_open` · `slot_hour_close` · `slot_step_minutes` | 9.0 · 17.0 · 30 |

### 11.4 Quy ước SPA

- Wire format camelCase, ngày ISO, lỗi `{error, message}` — `docs/QUY_UOC_FRONTEND.md`.
- **Lọc theo MÃ bước (`stageRef`), không theo tên bước.** Tên sửa được trên màn Cấu hình nên so
  tên là màn rỗng ngay khi ai đó đổi chữ (đã dính ở tab Offer, xem `OFFER_STAGE_REFS`).
- **Số trên chip lọc đếm theo kiểu faceted** (2026-08-16): mọi màn gom về **một** hàm lọc dùng
  chung cho cả bảng lẫn chip, cho phép ghi đè từng tiêu chí ⇒ số trên chip luôn là "bấm chip
  này thì thấy bao nhiêu dòng". Đếm trên tập chưa lọc thì bật bộ lọc thứ hai (kể cả ô tìm kiếm)
  là chip ghi một đằng, bảng ra một nẻo. Áp cho `Offers` · `RequestTracking` · `JdLibrary` ·
  `Requests` · `MailLogs` · `CvList`.

**Màn SPA của module** (`frontend/src/features/recruitment/`): `CvList` · `InterviewSlots` ·
`Offers` · `RequestTracking` · `Requests` · `JdLibrary` · `MailTemplates` · `MailLogs`,
điều phối bởi `Recruitment.jsx`. Màn "Vị trí tuyển dụng" gộp cũ (`Jobs.jsx`) **đã tách thành
`RequestTracking` (theo dõi tiến độ) + `JdLibrary` (tra cứu JD)** và file gốc đã xoá 2026-08-16.

---

## 12. Cron

| Mã | Tên | Chu kỳ | Việc |
|----|-----|--------|------|
| CRON-REC-001 | HOCBA: Nhắc CV quá hạn xử lý | 1 ngày, `nextcall` 01:00 UTC (08:00 VN) | §5.7 |

~~CRON-REC-002 (Qua giờ PV → Kết quả phỏng vấn, 30 phút)~~ **đã gỡ 2026-08-26**
theo yêu cầu: không cần cron quét slot nữa. Bước Phỏng vấn → Kết quả phỏng vấn
nay chỉ chạy khi HR điền Kết quả PV. Bản ghi cũ trong DB được migration
`19.0.2.9.0/post-migrate.py` xoá — `noupdate="1"` nên upgrade KHÔNG tự dọn.

`noupdate="1"` — admin đổi giờ chạy không bị upgrade ghi đè.
⚠️ Odoo 19: `ir.cron` **không còn** `numbercall`, và `nextcall` không theo timezone.

---

## 13. Migrations

| Version | Việc |
|---------|------|
| `19.0.2.2.0` | Set cờ `noupdate` cho 10 stage xmlid (admin sửa không bị ghi đè) + seed `sla_days` mặc định |
| `19.0.2.5.0` | `hb.interview.slot`: `applicant_id` (m2o) → `applicant_ids` (m2m). Odoo tạo bảng quan hệ nhưng **không** chuyển dữ liệu ⇒ chép sang rồi bỏ cột cũ. Idempotent |
| `19.0.2.6.0` | `hr.job.x_teaching_level`: Selection → Char. Ghi lại mã cũ thành nhãn; `na` → rỗng |
| `19.0.2.7.0` | Gán ngược CV cũ vào đợt tuyển (`hb_request_id`): lấy phiếu mở gần nhất **trước** ngày nhận CV, không có thì lấy phiếu sớm nhất của vị trí |

---

## 14. Test tự động

`tests/` — **19 file · 218 test** (bản spec cũ ghi "chưa có test", đã lỗi thời).

| File | Tests | Phủ |
|------|-------|-----|
| `test_auto_stage.py` | 48 | Toàn bộ luật tự chuyển bước (§5.6) |
| `test_request_tracking.py` | 26 | Phễu 8 mốc, gắn CV vào đợt, thống kê theo phiếu |
| `test_offer_onboard_result.py` | 15 | `onboard_result`, constraint bàn giao, chặn kéo lùi |
| `test_overdue_notify.py` | 15 | CRON-REC-001 + 4 chế độ người nhận |
| `test_mail_stage.py` | 13 | Đẩy bước theo mail mẫu (cả `/send` lẫn `/log-sent`) |
| `test_mail_acl.py` | 11 | Cổng quyền cụm endpoint mail — trước đây 4 route chỉ có `auth='user'` nên mọi tài khoản đăng nhập đọc được họ tên · email · bước của **toàn bộ** ứng viên |
| `test_slot_hours.py` | 11 | Khung giờ cấu hình được, tham số hỏng, mốc cuối |
| `test_stage_config.py` | 11 | Sửa/ẩn/xoá/sắp bước + guard |
| `test_auto_close.py` | 10 | 4 chế độ tự đóng khi tuyển đủ |
| `test_request_notify.py` | 9 | Chuông vòng duyệt phiếu |
| `test_meta_scope.py` | 7 | Phạm vi phòng ban ở các ô chọn |
| `test_job_teaching_level.py` | 7 | `x_teaching_level` nhập tự do, trùng tên vị trí |
| `test_interview_slot.py` | 5 | Slot xếp được nhiều ứng viên; `state` suy từ `applicant_ids` nên không còn nguồn sự thật thứ hai |

Chạy (Docker local):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_recruitments,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_recruitments --stop-after-init --log-level=test
```

Kịch bản kiểm thử thủ công: `docs/QUY_TRINH_TUYEN_DUNG.md`.

---

## 15. Điểm cần xem lại / TODO

### Đã xử lý từ bản spec trước (2026-06-21 → 2026-08-16)

| Việc | Ghi chú |
|------|---------|
| ✅ Test tự động | 19 file / 218 test (§14) — mục "Chưa có test" của bản cũ đã hết hiệu lực |
| ✅ Màn Cấu hình tuyển dụng | Sửa/thêm/ẩn/xoá/kéo-thả bước, SLA từng bước, chế độ tự đóng, chế độ nhắc quá hạn, khung giờ PV (§11.3) |
| ✅ Gắn CV vào ĐỢT TUYỂN | `hb_request_id` + migration 2.7.0 — hai đợt cùng vị trí không còn dùng chung số (§5.1) |
| ✅ Phễu 8 mốc theo phiếu | `APPLICANT_GROUPS` dùng chung cho đếm và popup (§11.2) |
| ✅ Kết quả nhận việc (sheet 7.6) | `onboard_result` + constraint + trừ khỏi mốc "Nhận việc" (§5.3) |
| ✅ Slot PV nhiều ứng viên | `applicant_ids` m2m + `state` compute + migration 2.5.0 (§7.1) |
| ✅ Khung giờ PV cấu hình được | Không còn hardcode 09:00–17:00 (§7.3) |
| ✅ Tự chuyển bước | 8 luật, bám xmlid, chỉ đẩy tới, ghi chatter (§5.6) |
| ✅ Tự ngừng đăng khi tuyển đủ | 4 chế độ (§5.5) |
| ✅ Nhắc CV quá hạn | CRON-REC-001 + chuông `hocba_notify` (§5.7) |
| ✅ Link tuyển dụng công khai | `website_description` tự sinh từ phiếu + vị trí (§11.1) |
| ✅ Gửi mail qua Gmail | `/mail/log-sent` — không phụ thuộc `ir.mail_server` |
| ✅ Bỏ ràng buộc Trình độ giảng dạy | Đối chiếu file quy trình gốc của khách (§4.3) |
| ✅ Chặn kéo hồ sơ lùi khỏi Bàn giao | Khi NV đã lên chính thức (§5.3) |
| ✅ Chỉ tiêu tuyển chỉ cộng không trừ | 2026-08-26 — đóng phiếu (kể cả tự đóng khi tuyển đủ) trả lại phần chưa tuyển qua `_release_headcount()`; "Mở lại nháp" siết còn HR + chỉ từ Từ chối. Test: `test_request_headcount.py` |
| ✅ Nút Đăng tuyển vỡ HTTP 500 khi thiếu `website_hr_recruitment` | 2026-08-26 — controller chỉ ghi `x_published`, model tự mirror; 3 chỗ đọc dùng chung `_job_published()`; stack nginx cài thêm module. Test: `test_job_publish.py` |
| ✅ Xếp lịch PV không kiểm phạm vi phòng ban | 2026-08-26 — book/unbook/xoá slot kiểm `_applicants_out_of_scope()` + `_slot_in_scope()`; GET lịch cắt theo phòng (trước đó mọi user đọc được tên ứng viên + danh bạ NV). Test: `test_slot_scope.py` |
| ✅ Phễu bám số sequence cứng 60/90 | 2026-08-26 — `_stage_seq()` đọc sequence theo xmlid lúc chạy; thêm bước + kéo-thả không còn đếm nhầm PV/Nhận việc. Test: `test_funnel_stage_seq.py` |
| ✅ Action backend lọc theo XMLID bước | 2026-08-26 — `hb_action_interview_list` / `hb_action_offer_hire` dùng `eval="[('stage_id','=',ref(...))]"`; đổi tên bước không còn làm menu rỗng. Test: `test_backend_actions.py` |
| ✅ Gỡ CRON-REC-002 | 2026-08-26 — bỏ cron quét slot quá khứ (quét không giới hạn thời gian, càng chạy càng nặng); migration `19.0.2.9.0` xoá bản ghi cũ trong DB |
| ✅ Xoá `Jobs.jsx` dead code | 2026-08-16 — màn gộp cũ đã tách thành `RequestTracking` + `JdLibrary`, file không còn được import (§11.4) |

### Còn lại

| # | Vấn đề | Mức độ |
|---|--------|--------|
| 2 | Chưa cấu hình `ir.mail_server` (SMTP) — mail qua `/send` nằm hàng đợi; luồng thật đang đi đường Gmail + `/log-sent` | Trung bình |
| 3 | `jd_google_link` trên `hb_job_positions.xml` bỏ trống — cần điền URL thực | Thấp |
| 4 | Mail template hardcode thông tin liên hệ HR — cập nhật khi thay nhân sự | Thấp |
| 5 | Sample data (`hb_applicant_data.xml`, `hb_interview_results.xml`) chưa rà lại nội dung | Cần xác nhận |
| 6 | `cv_link` seed là tên file (không phải URL) → cột Link CV chỉ hiện text | Thấp |
| 7 | Tạo hồ sơ NV xong chưa tự điều hướng sang form NV vừa tạo | Thấp (UX) |
| 9 | Dữ liệu CTV tuyển dụng trên Neon còn bẩn (đã hoãn xử lý) | Cần xác nhận |
| 10 | Hai tên modal mail dễ nhầm: `SendMailModal` (1 mẫu → nhiều UV) vs `MailSendModal` (1 UV → chọn mẫu) — đảo chữ của nhau, nên đổi thành `MultiMailModal` / `SingleMailModal` | Thấp |
