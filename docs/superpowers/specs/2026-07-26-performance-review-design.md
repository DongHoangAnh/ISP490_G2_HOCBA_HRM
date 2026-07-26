# Đánh giá nhân viên định kỳ (Performance Review) — thiết kế

- **Ngày**: 2026-07-26 · **Owner**: Việt · **Module mới**: `hocba_reviews` 19.0.1.0.0
- **Tài liệu công thức**: [docs/CONG_THUC_DANH_GIA.md](../../CONG_THUC_DANH_GIA.md)
- **Liên quan**: `hr.promotion.evaluation` (đánh giá THĂNG TIẾN — giữ nguyên, không đụng),
  `hb.onboarding.step` (đánh giá THỬ VIỆC — giữ nguyên).

## Bối cảnh

Học Bá chưa cung cấp bộ tiêu chí đánh giá. Nhóm tự đề xuất dựa trên (a) dữ liệu
hệ thống đang có, (b) tham khảo khung KPI trung tâm ngoại ngữ. Hai nhóm nhân sự
có bản chất công việc khác nhau (169/203 nhân sự là giáo viên) nên **tách 2 bộ
tiêu chí**, không dùng chung một bộ.

Phân biệt nhóm bằng `hr.employee.x_employee_type_id.code`:
`teacher` → bộ Giảng viên; còn lại (`office_staff`, `contractor`) → bộ Văn phòng.

## Phạm vi

**Làm**: kỳ đánh giá theo quý/6 tháng/năm · 2 bộ tiêu chí cấu hình được · chấm
điểm thang 5 có trọng số · tự động tính 4 chỉ số từ dữ liệu vận hành · xếp loại
A/B/C/D · luồng Nháp → Đã chốt → Đã công bố · thông báo cho nhân viên khi công
bố · mở đợt hàng loạt · tab SPA 2 sub-tab.

**Không làm** (thiếu nguồn dữ liệu — xem "Điểm mù"): phản hồi học viên tự động,
KPI doanh số, đánh giá 360 độ, nối kết quả sang bảng lương.

**Điểm mù đã biết**: chất lượng giảng dạy (dự giờ, phản hồi học viên, tỷ lệ
hoàn thành khoá) nằm ở CMS `cms.dangch.tech` — mới dò được API auth, chưa dò
được endpoint dữ liệu lớp. Các tiêu chí này để **chấm tay**, khi nào thông CMS
thì chuyển sang tự động mà không phải đổi cấu trúc (chỉ đổi `auto_source`).

## Model

### `hb.review.criteria` — tiêu chí (cấu hình)

| Field | Kiểu | Ghi chú |
|---|---|---|
| `name` | Char | Tên tiêu chí |
| `code` | Char | Unique |
| `role_group` | Selection | `teacher` / `office` |
| `sequence` | Integer | Thứ tự hiển thị |
| `weight` | Float | Trọng số (%) — tổng mỗi nhóm nên = 100 |
| `max_score` | Integer | Mặc định 5 |
| `auto_source` | Selection | `none` (chấm tay) / `punctuality` / `workload` / `cert` |
| `guideline` | Text | Hướng dẫn chấm cho quản lý |
| `active` | Boolean | Ẩn tiêu chí không dùng nữa (không xoá) |

Constraint: `weight >= 0`, `max_score >= 1`, `code` unique.

### `hb.performance.review` — phiếu đánh giá 1 nhân viên / 1 kỳ

Khoá: **unique (employee_id, period_type, period_year, period_index)** — mỗi NV
chỉ một phiếu mỗi kỳ.

- Định danh kỳ: `period_type` (`quarter`/`half`/`year`), `period_year`,
  `period_index`; `date_from`/`date_to` compute-store từ 3 field trên.
- `role_group` chốt tại thời điểm tạo (snapshot) — NV đổi loại sau không làm
  lệch phiếu cũ.
- Chỉ số snapshot: `metric_total_units`, `metric_ok_units`, `metric_punctual_pct`,
  `metric_late_count`, `metric_leave_days`, `metric_cert_valid/expiring/expired`,
  `metrics_computed_on`. **Đóng băng khi chốt** — không compute field, chỉ tính
  lại khi bấm "Tính lại chỉ số" ở trạng thái Nháp.
- Điểm: `total_score` (compute-store), `grade` (compute-store A/B/C/D).
- Nhận xét: `self_note` (NV tự đánh giá), `manager_note`, `hr_note`.
- `state`: `draft` → `confirmed` → `published`.

### `hb.performance.review.line` — dòng chấm

`review_id`, `criteria_id`, `sequence`, `weight`, `max_score`, `score`,
`auto_score` (readonly, hệ thống tính), `is_auto`, `note`.

Line được sinh tự động từ criteria của `role_group` khi tạo phiếu; `weight` và
`max_score` **snapshot** từ criteria (sửa cấu hình sau không đổi phiếu đã chấm).

## Bộ tiêu chí mặc định (seed)

### Giảng viên — tổng 100

| Mã | Tiêu chí | Trọng số | Nguồn |
|---|---|---|---|
| `t_quality` | Chất lượng giờ dạy | 25 | Chấm tay |
| `t_expertise` | Chuyên môn & chứng chỉ | 20 | **Tự động** (`cert`) |
| `t_punctual` | Chuyên cần & đúng giờ lên lớp | 20 | **Tự động** (`punctuality`) |
| `t_class` | Quản lý lớp & chăm sóc học viên | 15 | Chấm tay |
| `t_workload` | Khối lượng giảng dạy | 10 | **Tự động** (`workload`) |
| `t_teamwork` | Phối hợp & báo cáo | 10 | Chấm tay |

### Nhân viên văn phòng — tổng 100

| Mã | Tiêu chí | Trọng số | Nguồn |
|---|---|---|---|
| `o_result` | Kết quả công việc / KPI | 35 | Chấm tay |
| `o_punctual` | Chuyên cần & kỷ luật giờ giấc | 20 | **Tự động** (`punctuality`) |
| `o_attitude` | Thái độ & tinh thần trách nhiệm | 15 | Chấm tay |
| `o_teamwork` | Phối hợp | 15 | Chấm tay |
| `o_initiative` | Chủ động & cải tiến | 10 | Chấm tay |
| `o_potential` | Tiềm năng phát triển | 5 | Chấm tay |

## Công thức

Chi tiết + ví dụ tính tay: [docs/CONG_THUC_DANH_GIA.md](../../CONG_THUC_DANH_GIA.md).
Tóm tắt: `TOTAL = Σ(score_i / max_i × weight_i) / Σ(weight_i) × 100`, xếp loại
A ≥ 85, B ≥ 70, C ≥ 55, D < 55 (ngưỡng để trong `ir.config_parameter`).

Chỉ số tự động tính trên khoảng `[date_from, date_to]`:

- **`punctuality`** — Giảng viên: `hocba.teaching.attendance` có `check_in`;
  buổi "đạt" = không `out_of_window`, không `out_of_zone`, không `face_suspect`.
  Văn phòng: `hocba.attendance`; ngày "đạt" = `late_minutes = 0` và
  `early_leave_minutes = 0`. Không có dữ liệu trong kỳ → **không tự chấm**
  (`auto_score = 0`, để quản lý chấm tay, tránh phạt oan NV mới).
- **`workload`** — số buổi dạy / chỉ tiêu kỳ (`hocba_reviews.teacher_sessions_target`,
  mặc định 60 buổi/quý, quy đổi theo độ dài kỳ).
- **`cert`** — đếm chứng chỉ đã xác minh (`x_cert_verified`) theo
  `x_cert_status`; hết hạn kéo điểm xuống mạnh nhất.

## Luồng & phân quyền

1. **Mở đợt** — HR/Admin bấm "Mở đợt đánh giá" cho một nhóm + kỳ → tạo phiếu
   Nháp hàng loạt cho mọi NV đang làm việc thuộc nhóm (bỏ qua NV đã có phiếu kỳ
   đó — idempotent), tự tính chỉ số.
2. **Chấm** — quản lý trực tiếp/HR mở phiếu, sửa điểm (dòng tự động đã điền sẵn,
   sửa đè được), ghi nhận xét.
3. **Chốt** (`confirmed`) — cần chấm đủ mọi dòng (score > 0 ở ít nhất 1 dòng) và
   có nhận xét quản lý. Khoá sửa điểm.
4. **Công bố** (`published`) — bắn `hb.notification` cho tài khoản NV.
5. **Mở lại** — chỉ HR/Admin, đưa về Nháp (ghi log chatter).

Phân quyền theo đúng mô hình hệ thống (`docs/QUY_UOC_FRONTEND.md` + pattern
`hocba_recruitments/controllers`):

| Vai trò | Phạm vi |
|---|---|
| Admin / HR Manager / HR officer | Mọi nhân viên, mọi thao tác |
| Trưởng phòng | NV phòng mình (gồm phòng con qua `_managed_department_ids`) — chấm & chốt, **không** công bố |
| Giáo vụ | Chỉ giáo viên |
| NV thường | Không vào tab (giai đoạn này); xem kết quả qua thông báo |

Kiểm phạm vi ở controller rồi mới `.sudo()` — theo gotcha self-service của dự án.

## API (`/hocba-hrm/api/reviews/*`)

| Route | Method | Trả về |
|---|---|---|
| `/reviews` | GET | `{canManage, canPublish, group, period, criteria[], rows[], stats}` — query `group`, `periodType`, `year`, `index` |
| `/reviews/<id>` | GET | Chi tiết phiếu + `lines[]` + `metrics` |
| `/reviews` | POST | Tạo phiếu 1 NV `{employeeId, periodType, year, index}` |
| `/reviews/<id>` | POST | Lưu `{lines:[{id, score, note}], selfNote, managerNote, hrNote}` |
| `/reviews/<id>/action` | POST | `{action: compute\|confirm\|publish\|reset}` |
| `/reviews/bulk-open` | POST | `{group, periodType, year, index}` → `{created, skipped}` |

Quy ước chung: camelCase, ngày ISO, lỗi `{error, message}` — 403 `forbidden`,
400 `rejected`/`bad_request`, 404 `not_found`.

## Frontend

`features/reviews/Reviews.jsx` — tab **Đánh giá** trong mục "Quản lý nhân sự",
2 sub-tab **Giảng viên** / **Nhân viên văn phòng** (nhớ tab qua localStorage như
màn Tuyển dụng). Mỗi sub-tab: chọn kỳ (loại + năm + quý), 4 thẻ KPI (đã chấm /
chờ chấm / điểm TB / số loại A), bảng NV kèm badge xếp loại và trạng thái, nút
"Mở đợt đánh giá". Click dòng → `ReviewDrawer` chấm điểm: từng tiêu chí có
thanh chọn 1–5, badge "Tự động" + ghi chú nguồn cho dòng auto, khối chỉ số
tham chiếu, ô nhận xét, nút Lưu / Chốt / Công bố / Mở lại theo trạng thái.

## Test (`hocba_reviews/tests/test_review.py`)

- Công thức tổng điểm có trọng số + 4 ngưỡng xếp loại.
- `punctuality` giảng viên (buổi vi phạm bị trừ) và văn phòng (đi trễ/về sớm).
- `cert`: không chứng chỉ / hết hạn / sắp hết hạn / 1 còn hạn / ≥2 còn hạn.
- `workload` theo chỉ tiêu quy đổi độ dài kỳ.
- Không có dữ liệu chấm công → không tự chấm (auto_score = 0).
- Sinh line theo đúng `role_group`; snapshot weight không đổi khi sửa criteria.
- Unique 1 phiếu/NV/kỳ; chốt thiếu điểm bị chặn; công bố sinh thông báo;
  bulk-open idempotent.

## Quyết định thiết kế

- **Model mới, không nhồi vào `hr.promotion.evaluation`**: đánh giá thăng tiến có
  ngữ nghĩa riêng (kết luận Đủ/Cân nhắc/Chưa đủ, gắn `hr.promotion.history`),
  chu kỳ bất thường. Đánh giá định kỳ chạy theo kỳ cố định, có 2 bộ tiêu chí và
  chỉ số tự động. Gộp sẽ làm bẩn cả hai.
- **Module mới `hocba_reviews`**: tránh đụng `hocba_employees` (owner Tân) đang
  có nhánh riêng; ownership rõ, merge ít xung đột.
- **Chỉ số là snapshot, không phải compute field**: phiếu đã chốt phải giữ nguyên
  con số tại thời điểm đánh giá, dù dữ liệu chấm công sau đó bị sửa.
- **Dòng tự động vẫn sửa được**: máy đề xuất, người quyết định — quản lý sửa đè
  kèm ghi chú, tránh tình huống dữ liệu chấm công lỗi làm oan nhân viên.
- **Thang 5 mức** thống nhất với `hr.promotion.criteria` sẵn có → nhân sự chỉ
  phải học một cách chấm.
- **Không nối lương** giai đoạn này: cần khách chốt chính sách thưởng trước.
