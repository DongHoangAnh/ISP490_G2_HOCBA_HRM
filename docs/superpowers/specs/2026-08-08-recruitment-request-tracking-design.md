# Theo dõi tiến độ theo Phiếu yêu cầu tuyển dụng

- **Ngày**: 2026-08-08
- **Owner**: Việt (`hocba_recruitments`)
- **Nhánh**: `Viet/Recruitment`
- **Trạng thái**: Chờ duyệt

## 1. Bối cảnh & yêu cầu khách hàng

Khách muốn theo dõi **từng phiếu yêu cầu tuyển dụng** chứ không chỉ theo vị trí:

> xem, theo dõi chi tiết từng phiếu yêu cầu: tuyển vị trí gì, phòng ban nào, trạng
> thái, cần tuyển mấy, đã tuyển mấy, thiếu mấy, đã có CV nào nộp vào mấy, ứng viên
> nào pass, ứng viên nào fail, Deadline (lấy từ trường *Ngày cần onboard*).

Lưu ý chữ **"ứng viên nào"** — khách cần **danh sách tên**, không chỉ con số. Do đó
màn hình phải có 2 tầng: bảng tổng hợp (số) → drawer chi tiết (danh sách ứng viên).

### Hiện trạng

- Tab `jobs` (**"Theo dõi tuyển dụng"**, `frontend/src/features/recruitment/Jobs.jsx`)
  đã có view **Phòng ban** liệt kê các phiếu `state = recruiting` với **Cần tuyển /
  Đã tuyển / Còn thiếu / Đăng tuyển**. Đây là chỗ mở rộng (khách chọn phương án này).
- **Chưa có** liên kết CV ↔ phiếu: `hr.applicant` chỉ gắn `job_id` (`hr.job`).
  Số "đã tuyển" hiện đếm qua `job_id` nên **1 JD có nhiều đợt tuyển sẽ đếm chồng**.
- `expected_start_date` ("Ngày cần onboard") đã có trên `hb.recruitment.request`
  nhưng chưa lộ ra danh sách (chỉ có ở `_req_row(detail=True)`).

## 2. Quyết định thiết kế (đã chốt với khách)

| Vấn đề | Quyết định |
|---|---|
| Đặt ở đâu | Mở rộng tab **"Theo dõi tuyển dụng"** hiện có |
| Gắn CV vào phiếu | **Thêm M2O `hb_request_id`** trên `hr.applicant` + tự gán + backfill dữ liệu cũ |
| Pass | Ứng viên **đã hoàn thành thử việc** (NV lên `official`) |
| Fail | **Fail lọc CV** *hoặc* **Fail phỏng vấn** |

### 2.1. Diễn giải Pass/Fail sang dữ liệu hiện có

Chuỗi đã có sẵn trong code, không cần thêm trường:

`hr.employee.x_employment_status = 'official'`
→ `hocba_recruitments/models/hr_employee.py::_hb_advance_applicant_to_handover()`
→ applicant chuyển `hb_stage_onboarding` → **`hb_stage_hired`** ("Bàn giao nhân sự",
`hired_stage = True`).

Vậy:

- **Pass** = applicant ở `stage_id.hired_stage = True` (⇔ đã qua thử việc, lên chính thức).
- **Fail** = `cv_filter_result = 'fail'` **OR** `interview_result = 'fail'` (đếm 1 lần/ứng viên).

**Hệ quả cần nói rõ**: cột "Đã tuyển" hiện tại đang đếm đúng tập này ⇒ *Đã tuyển ≡ Pass*.
Để không hiện 2 cột cùng số, bảng mới tách thành:

- **Đang thử việc** = applicant ở `hb_stage_onboarding` (đã nhận việc, chưa qua thử việc).
- **Đạt (Pass)** = `hired_stage` — cũng là số dùng để tính **Còn thiếu**.

Giữ "Còn thiếu = Cần tuyển − Pass" là **cố ý**: khớp với logic chỉ tiêu của core Odoo
(`no_of_recruitment` bị trừ khi vào `hired_stage`) và với `_hb_auto_close_if_filled()`.
Nếu tính theo "đã nhận việc" thì phiếu tự đóng khi người còn đang thử việc — sai nghiệp vụ.

## 3. Thay đổi Backend

### 3.1. Model — `hr.applicant.hb_request_id`

```python
hb_request_id = fields.Many2one(
    'hb.recruitment.request', string='Phiếu yêu cầu tuyển dụng',
    index=True, ondelete='set null', tracking=True)
```

**Tự gán** (trong `create` / `write` đã có sẵn của `hr_applicant.py`), khi và chỉ khi
applicant có `job_id` và `hb_request_id` còn trống:

- Chọn phiếu `job_id = <job của applicant>` **và** `state = 'recruiting'`, mới nhất (`id desc`).
- Không có phiếu đang tuyển ⇒ **để trống** (không gắn vào phiếu đã đóng/nháp/từ chối).
- Không bao giờ **ghi đè** giá trị HR đã chọn tay.

Áp dụng cho mọi đường vào: SPA (`api_recruitment_cv_create`), form website `/jobs/apply`,
import, backend Odoo — vì tất cả đều đi qua `create`/`write`.

Trường được thêm vào form phiếu/CV (`views/hb_cv_list_views.xml`) để HR sửa tay khi
máy đoán sai.

### 3.2. Backfill dữ liệu cũ — `migrations/19.0.2.7.0/post-migrate.py`

Bump manifest `19.0.2.6.0` → `19.0.2.7.0`.

Với mỗi applicant có `job_id` và `hb_request_id IS NULL`, gán phiếu của cùng JD theo
quy tắc **phiếu mở gần nhất trước khi nhận CV**:

1. Phiếu cùng `job_id` có `date_request <= COALESCE(date_received, create_date::date)`,
   lấy `date_request` lớn nhất (tie-break `id desc`).
2. Không có ⇒ lấy phiếu cùng `job_id` có `date_request` **nhỏ nhất** (đợt đầu tiên).
3. Vẫn không có ⇒ để `NULL`.

Chạy bằng SQL thuần (1 `UPDATE ... FROM LATERAL`), idempotent (chỉ đụng dòng `NULL`).

### 3.3. API — mở rộng `GET /hocba-hrm/api/recruitment/jobs`

Mỗi phần tử `data['requests'][*]` thêm:

| Khoá | Nguồn |
|---|---|
| `state`, `stateLabel` | `state` của phiếu |
| `cvCount` | số applicant có `hb_request_id = phiếu` |
| `inProgress` | `cvCount − pass − fail − onboarding` (tối thiểu 0) |
| `onboarding` | applicant ở `hb_stage_onboarding` |
| `pass` (`passed`) | applicant ở `stage_id.hired_stage = True` |
| `fail` (`failed`) | `cv_filter_result='fail' OR interview_result='fail'` |
| `missing` | `max(0, qty − passed)` |
| `deadline` | `expected_start_date` |
| `daysLeft` | `deadline − hôm nay` (âm = trễ); `null` khi chưa đặt deadline |
| `deadlineState` | `none` / `ok` / `soon` (≤7 ngày) / `late` (quá hạn **và** `missing > 0`) |

**Phạm vi phiếu trả về đổi**: hiện chỉ `state = 'recruiting'` → trả **mọi trạng thái trừ
`draft`** (phiếu nháp chưa phải việc tuyển dụng). SPA lọc mặc định "Đang tuyển" để
view Phòng ban giữ nguyên hành vi cũ.

**Hiệu năng** (bắt buộc): thay N+1 `search_count` bằng **3 lần `read_group`** trên
`hr.applicant` gom theo `hb_request_id` (tổng / theo stage / fail), rồi tra dict.
Hiện tại mỗi phiếu 1 query; thêm 4 chỉ số nữa mà giữ cách cũ là 5×N query.

### 3.4. API mới — `GET /hocba-hrm/api/recruitment/request/<int:req_id>/pipeline`

Trả danh sách ứng viên của phiếu (khách cần biết **ai** pass / fail):

```json
{ "request": { "id", "name", "jobTitle", "depName", "state", "qty",
               "deadline", "cvCount", "passed", "failed", "onboarding", "inProgress" },
  "rows": [ { "id", "name", "phone", "email", "dateReceived", "stage", "stageRef",
              "cvResult", "interviewResult", "startDate", "employeeName",
              "outcome": "pass|fail|onboarding|progress" } ] }
```

- `outcome` tính ở backend theo đúng luật §2.1 để SPA khỏi lặp logic.
- ACL: dùng lại `_dept_scope_ids()` / `_dep_in_scope(r.department_id.id)` → 403 khi
  trưởng phòng mở phiếu phòng khác. `active_test=False` để giữ cả ứng viên đã lưu trữ
  (nhất quán với cách đếm `hired` hiện tại).

## 4. Thay đổi Frontend

`Jobs.jsx` — view **Phòng ban** (`DepartmentView`):

- Header phòng ban: giữ Cần tuyển / Đã tuyển → đổi nhãn **Đạt thử việc**; thêm badge
  **CV nộp** và **Trễ deadline: N phiếu** (đỏ) khi có phiếu `deadlineState = 'late'`.
- Bảng phiếu, cột mới: `CV nộp` · `Đang xử lý` · `Đang thử việc` · `Đạt` · `Fail` ·
  `Deadline` (kèm "còn N ngày" / "trễ N ngày", tô đỏ khi trễ) · `Trạng thái` (badge).
- Bấm dòng phiếu → **`RequestTrackDrawer`** (component mới): thẻ tóm tắt + bảng ứng viên
  nhóm theo `outcome` (Đạt / Fail / Đang thử việc / Đang xử lý), có link mở CV.
- Thêm bộ lọc trạng thái phiếu (mặc định **Đang tuyển**) và chip **Chỉ phiếu trễ deadline**.

`frontend/src/api/recruitment.js`: thêm `fetchRequestPipeline(reqId)`.

## 5. Test (viết trước, đỏ → xanh)

`custom-addons/hocba_recruitments/tests/test_request_tracking.py`:

| # | Ca | Kỳ vọng |
|---|---|---|
| 1 | Tạo CV vào JD đang có phiếu `recruiting` | `hb_request_id` = phiếu đó |
| 2 | Tạo CV vào JD chỉ có phiếu `closed`/`draft` | `hb_request_id` trống |
| 3 | HR gán tay phiếu rồi đổi `job_id` | không bị ghi đè |
| 4 | JD có 2 phiếu (đợt 1 đóng, đợt 2 đang tuyển) | CV mới thuộc đợt 2; số liệu 2 đợt **không** cộng chồng |
| 5 | Bộ đếm | 1 pass (hired) + 1 fail CV + 1 fail PV + 1 onboarding + 1 đang xử lý → `cvCount=5, passed=1, failed=2, onboarding=1, inProgress=1, missing=qty−1` |
| 6 | Ứng viên vừa fail CV vừa fail PV | đếm **1** ở `failed` |
| 7 | NV lên `official` | applicant sang `hired_stage` ⇒ `passed` +1, `onboarding` −1 |
| 8 | `deadlineState` | quá hạn + còn thiếu → `late`; quá hạn + đủ người → `ok` |
| 9 | Scope | trưởng phòng gọi `/pipeline` phiếu phòng khác → **403** |

Chạy:

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_recruitments,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_recruitments --stop-after-init --log-level=test
```

## 6. Ngoài phạm vi

- Không đổi cách core Odoo trừ `no_of_recruitment`.
- Không đổi luật tự đóng phiếu (`_hb_auto_close_if_filled`).
- Không thêm biểu đồ/thống kê theo thời gian (funnel, time-to-hire) — đợt sau nếu khách cần.
- Không đụng tab "Phiếu yêu cầu" (`Requests.jsx`) ngoài việc dùng chung API meta.

## 7. Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Backfill đoán sai phiếu cho CV cũ | Quy tắc "phiếu mở gần nhất trước ngày nhận CV" + HR sửa tay được trên form CV |
| Neon DDL: thêm cột + index qua pooler | Chạy `-u` bằng **endpoint trực tiếp** (bỏ `-pooler`) theo CLAUDE.md |
| Đổi phạm vi `requests` (thêm state) làm lệch view cũ | SPA lọc mặc định `recruiting`; test #4 khoá số liệu |
