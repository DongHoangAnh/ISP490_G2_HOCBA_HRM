# Spec — Dashboard Đánh giá Thăng tiến (Promotion Evaluation Dashboard)

- **Ngày:** 2026-06-25
- **Module:** `hocba_employees` (backend) + `hocba_hrm` (API + SPA)
- **Owner:** Vũ/Tân — nhánh `Tan/Employee`
- **Liên quan:** FUNC-EMP-007 (Lịch sử Thăng tiến), `hr.promotion.history`, tab "Thăng tiến" trong hồ sơ NV.

## 1. Bối cảnh & Vấn đề

Hiện tab "Thăng tiến" chỉ là **timeline lịch sử** (`hr.promotion.history`) + form thêm mốc thủ công (chức vụ/lương/lý do/bằng chứng). Khách đánh giá là **sơ sài**: không có cơ sở dữ liệu/định lượng để quyết định một NV có **xứng đáng thăng tiến** hay không.

Khách yêu cầu: một **dashboard đánh giá cụ thể** theo từng NV, tổng hợp dữ liệu hệ thống + cho quản lý chấm các tiêu chí định tính → ra kết luận hỗ trợ quyết định thăng tiến.

> **Lưu ý:** Bộ tiêu chí/điểm chính thức bên khách **chưa chốt**. Spec này đề xuất một bộ mặc định hợp lý nhưng để dạng **cấu hình được trong DB** (model `hr.promotion.criteria` + ngưỡng `ir.config_parameter`), nên khi khách gửi rubric thật chỉ cần chỉnh **dữ liệu**, không sửa code.

## 2. Phạm vi (Scope)

**Trong phạm vi (v1):**
- Góc nhìn **theo từng nhân viên**, gắn vào tab "Thăng tiến" của hồ sơ NV.
- Tổng hợp **chỉ số tự động** (read-only) + **form chấm tiêu chí định tính** (chấm tay) → tổng điểm % có trọng số → gợi ý trạng thái → quản lý chốt kết luận.
- Lưu **lịch sử nhiều đợt đánh giá** (audit trail).
- Trực quan kiểu "Career & Growth Analytics": biểu đồ lộ trình chức vụ + lương theo thời gian (có mốc), radar tiêu chí (hiện tại vs ngưỡng mục tiêu), bảng mốc/thành tích, sidebar kết luận + chỉ số.
- Nối liền: khi kết luận "Đủ điều kiện" → mở `PromotionForm` hiện có để tạo bản ghi thăng tiến, đính `evaluation_id` làm bằng chứng.

**Ngoài phạm vi (v1) — có thể làm sau:**
- **Phản hồi nhiều nguồn** (quản lý / đồng nghiệp / tự đánh giá) — cần cơ chế multi-rater, đội scope.
- **Lộ trình nghề nghiệp & khóa học gợi ý** — cần model/dữ liệu mới.
- **Auto-scoring** chỉ số tự động vào tổng điểm (map raw→điểm) — v1 chỉ hiển thị tham khảo.
- NV thường tự xem kết quả đánh giá của mình.

## 3. Quyết định đã chốt (từ brainstorm)

| # | Quyết định |
|---|---|
| Phạm vi | Theo từng NV, trong tab "Thăng tiến" |
| Bản chất | Kết hợp: data tự động (read-only) + form chấm tay |
| Chấm điểm | Thang điểm/tiêu chí + trọng số → tổng % → tự gợi ý verdict; quản lý chốt cuối. Bộ tiêu chí cấu hình được (rubric khách chưa chốt) |
| NV tự xem | **Không** — chỉ người quản lý thấy tab đánh giá |
| Panel ⚠ | **Bỏ** ở v1: phản hồi nhiều nguồn, lộ trình/khóa học gợi ý |
| Theme | Theo app: đỏ Học Bá + nền sáng |
| Biểu đồ | **recharts** (`^2.x`, tương thích React 18.3) |

## 4. Mô hình dữ liệu (Backend — `hocba_employees`)

### 4.1 `hr.promotion.criteria` — bộ tiêu chí (config, seed sẵn)
| Field | Kiểu | Ghi chú |
|---|---|---|
| `name` | Char (required) | VD "Năng lực chuyên môn / KPI" |
| `code` | Char (required, unique) | slug định danh |
| `sequence` | Integer | thứ tự hiển thị |
| `weight` | Float (required) | trọng số (VD 30/25/20…) |
| `max_score` | Integer (default 5) | thang điểm tối đa |
| `guideline` | Text | mô tả cách chấm |
| `active` | Boolean (default True) | bật/tắt tiêu chí |

Tiêu chí là **chấm tay**. Seed mặc định (sửa được): Năng lực/KPI (w=35), Thái độ & kỷ luật (w=25), Phối hợp & teamwork (w=20), Tiềm năng phát triển (w=20). *(Sẽ thay khi khách chốt rubric.)*

### 4.2 `hr.promotion.evaluation` — một đợt đánh giá
| Field | Kiểu | Ghi chú |
|---|---|---|
| `employee_id` | M2o `hr.employee` (required, index) | NV được đánh giá |
| `eval_date` | Date (default today) | ngày đánh giá |
| `evaluator_id` | M2o `res.users` (default current) | người đánh giá |
| `state` | Selection `draft`/`confirmed` (default draft) | |
| `line_ids` | O2m `hr.promotion.evaluation.line` | các dòng chấm |
| `total_score` | Float (computed, store) | **% có trọng số** |
| `verdict_auto` | Selection `qualified`/`consider`/`not_yet` (computed) | gợi ý theo ngưỡng |
| `verdict_final` | Selection (cùng tập) | quản lý chốt — **bắt buộc khi confirm** |
| `conclusion_note` | Text | nhận xét/kết luận |
| `promotion_id` | M2o `hr.promotion.history` | nối nếu đã tạo thăng tiến từ đợt này |
| `snapshot_tenure_months` | Float | chụp thâm niên lúc đánh giá |
| `snapshot_months_since_promo` | Float | tháng từ lần thăng tiến gần nhất |
| `snapshot_job_id` | M2o `hr.job` | chức vụ tại thời điểm |

### 4.3 `hr.promotion.evaluation.line` — dòng chấm từng tiêu chí
| Field | Kiểu | Ghi chú |
|---|---|---|
| `evaluation_id` | M2o (required, ondelete cascade) | |
| `criteria_id` | M2o `hr.promotion.criteria` (required) | |
| `score` | Float | 0..`max_score` (validate) |
| `weight` | Float | **copy từ criteria lúc tạo** — đổi config sau không phá lịch sử |
| `max_score` | Integer | copy từ criteria lúc tạo |
| `note` | Text | |

### 4.4 Logic tính điểm & ngưỡng
- `total_score = Σ(line.score / line.max_score × line.weight) / Σ(line.weight) × 100`.
- Ngưỡng (lưu `ir.config_parameter`, chỉnh được):
  - `hocba_employees.promo_eval_qualified` (default 80) → `qualified`
  - `hocba_employees.promo_eval_consider` (default 60) → `consider`
  - < consider → `not_yet`
- `verdict_auto` chỉ là gợi ý; `verdict_final` là quyết định của quản lý.

### 4.5 Chỉ số tự động (read-only, không cộng vào điểm)
| Chỉ số | Nguồn |
|---|---|
| Thâm niên (tháng/năm) | ngày vào làm; `x_official_date` / `x_official_months` (đã có) |
| Tháng từ thăng tiến gần nhất | `date_effective` mới nhất trong `hr.promotion.history` |
| Chức vụ & lương hiện tại | `hr.employee` |
| Kết quả thử việc | `x_eval_2w_result` / `x_eval_1m_result` / `x_eval_2m_result` (đã có trong payload `probation`) |
| Chấm công 3 tháng (ngày công/đi muộn/nghỉ) | `hocba_attendance` — **best-effort**: bọc guard, thiếu model/khóa → ẩn block, không vỡ hồ sơ |

### 4.6 Ràng buộc & Audit
- `score` trong `[0, max_score]`, không âm.
- Confirm yêu cầu có `verdict_final` và ≥1 line.
- Đợt `confirmed` **không được xóa** (audit). Sửa sau 24h: chỉ HR Manager (giống `hr.promotion.history`).
- `message_post` log khi tạo/confirm đợt.

## 5. Phân quyền

| Hành động | Ai |
|---|---|
| Xem & chấm đợt đánh giá | `canManage` với NV đó (HR/Admin; TBP phòng mình + phòng con; Giáo vụ với giáo viên) |
| Chốt `verdict_final` / confirm | `canManage` |
| Tạo bản ghi thăng tiến từ kết luận | **Chỉ HR Manager** (giữ nguyên rule hiện hành — tách "đánh giá" khỏi "thẩm quyền") |
| Sửa đợt > 24h | Chỉ HR Manager |
| NV thường | **Không** thấy tab đánh giá |

`ir.model.access.csv` + record rules theo pattern hiện có. Truy cập dữ liệu ngoài ACL của user thường (nếu có) qua `.sudo()` sau khi đã kiểm phạm vi.

## 6. API (`hocba_hrm/controllers/main.py`)

Tách riêng để payload `_employee_detail` không phình:
- `GET /hocba-hrm/api/promotion/eval/<int:emp_id>` → `{ criteria[], autoMetrics{}, evaluations[] }` (kiểm `canManage`).
- `POST /hocba-hrm/api/promotion/eval/save` → tạo/cập nhật đợt (kèm `lines`, `state`, `verdict_final`, `conclusion_note`).
- Tái dùng `createPromotion` sẵn có cho bước tạo thăng tiến; truyền `evaluation_id` để đính làm bằng chứng (map vào `x_evidence_url`/ghi chú).

Mọi response theo format chuẩn của controller hiện tại. Kiểm quyền + phạm vi NV trước khi `.sudo()`.

## 7. Frontend (`frontend/src/features/employees/`)

- Tab "Thăng tiến" (`PromoTab` trong `EmployeeDrawer.jsx`) nâng cấp thành dashboard.
- **Theme:** đỏ Học Bá + nền sáng, dùng biến CSS hiện có (`--red-*`, `--ink`, `--muted`, `--border*`).
- **recharts**: 
  - `LineChart` — lộ trình: lương (+ điểm đánh giá nếu có) theo thời gian, mốc chú thích (nhận việc / lên chính thức / thăng chức) từ `hr.promotion.history`.
  - `RadarChart` — tiêu chí: điểm hiện tại vs ngưỡng mục tiêu.
- **Bảng mốc & thành tích**: gộp thăng tiến + đợt đánh giá + chứng chỉ theo thời gian.
- **Sidebar**: kết luận %/badge (Đủ/Cân nhắc/Chưa đủ) + chỉ số tự động.
- **Form "Đánh giá mới"** (component mới, VD `EvaluationForm.jsx`): danh sách tiêu chí + ô nhập điểm (0..max) + ghi chú; hiển thị tổng % realtime + verdict gợi ý; nút Lưu nháp / Xác nhận.
- Nút **"Tạo thăng tiến"** (chỉ HR Manager, hiện khi verdict đủ) → mở `PromotionForm` đính `evaluation_id`.
- API client: thêm hàm vào `frontend/src/api/employees.js`.
- **Build SPA** ra `custom-addons/hocba_hrm/static/spa/` (đừng merge tay bundle).

## 8. Kế hoạch test (TDD — backend trước)

Backend (`--test-tags /hocba_employees`, chạy Docker local, nhớ `MSYS_NO_PATHCONV=1`):
- Tính `total_score` đúng với trọng số & max_score khác nhau.
- `verdict_auto` đúng theo ngưỡng (biên 60/80).
- `verdict_final` bắt buộc khi confirm; thiếu line → lỗi.
- `score` ngoài `[0, max_score]` → `ValidationError`.
- Confirmed không xóa được; sửa > 24h chỉ HR Manager.
- Phân quyền: TBP ngoài phòng / giáo vụ với NV không phải giáo viên / NV thường → bị chặn.
- Chấm công guard: không có module/khóa → autoMetrics trả gọn, không lỗi.
- Lưu ý BR-010: NV `official` trong test phải có `identification_id` 12 số.

UI: kiểm thủ công qua preview (`/hocba-hrm`) với tài khoản HR/TBP/giáo vụ/NV thường.

## 9. Mở rộng tương lai (đã ghi nhận, không làm v1)
- Phản hồi nhiều nguồn (multi-rater), tự đánh giá.
- Lộ trình nghề nghiệp + khóa đào tạo gợi ý.
- Auto-scoring chỉ số tự động vào tổng điểm.
- Kỳ đánh giá định kỳ + nhắc tự động (CRON).
