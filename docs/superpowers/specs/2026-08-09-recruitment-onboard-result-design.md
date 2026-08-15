# Kết quả nhận việc — xử lý ứng viên nhận offer rồi không đến

- **Ngày:** 2026-08-09 · **Owner:** Việt · **Module:** `hocba_recruitments`
- **Trạng thái:** chờ duyệt
- **Liên quan:** sheet **7.6** của khách (cột *Kết quả nhận việc*), tab
  *Offer & Nhận việc*, phễu 8 mốc ở tab *Theo dõi tuyển dụng*

## 1. Vấn đề

Tab *Offer & Nhận việc* hiện chỉ có **một đường đi tiếp**: nhập offer → điền
ngày nhận việc → bấm **Tạo hồ sơ nhân viên** → bước Onboarding. Không có chỗ nào
ghi nhận ứng viên **nhận offer rồi không đến**.

Hệ quả:

- Ứng viên bùng nằm lại vô thời hạn ở bước *Gửi Offer*, lẫn với người đang chờ
  đến ngày đi làm — nhìn bảng không phân biệt được.
- **Không đo được tỷ lệ nhận offer rồi bùng** — chỉ số khách quan tâm, và là
  cột `Kết quả nhận việc` (danh mục *Đã đến / Không nhận việc*) đã có sẵn trong
  file Excel 7.6 của khách mà hệ thống chưa làm.
- Ô **Nhận việc** trong phễu đang suy đoán từ *bước Onboarding trở đi HOẶC đã
  điền ngày nhận việc*, nên **đếm cả người đã bùng** (ngày nhận việc vẫn còn
  trên hồ sơ).

Không phải vấn đề — đã kiểm và loại khỏi phạm vi:

> Phiếu yêu cầu **không** bị đóng nhầm vì ứng viên bùng.
> `_hb_auto_close_if_filled` (`models/hr_applicant.py:275`) chỉ chạy khi ứng
> viên vào **bước có cờ `hired_stage`** (Bàn giao nhân sự — bước 10, sau thử
> việc). Người bùng ở khâu offer chưa từng chạm bước đó, phiếu vẫn đang mở.

## 2. Phạm vi

**Làm:**

1. Field mới `hr.applicant.onboard_result` — *Kết quả nhận việc*.
2. Tab *Offer & Nhận việc*: ô chọn kết quả + badge, chặn tạo hồ sơ khi bùng.
3. Ô **Nhận việc** của phễu loại người bùng ra khỏi phép đếm.

**Không làm (ghi lại để khỏi hỏi lại):**

- Nút *Hủy ứng viên* dùng chung mọi bước (fail CV, bùng PV…) — đợt sau nếu cần.
- Thêm ô thứ 9 "Không nhận việc" vào phễu — chưa ai yêu cầu; số liệu đã đủ để
  tính tỷ lệ bùng bằng báo cáo về sau.
- Tách `Ngày hẹn đi làm` khỏi `Ngày nhận việc`, và `Thử việc 2 tuần` — hai chỗ
  thiếu còn lại của sheet 7.6, không thuộc lần này.
- Tự mở lại / đổi trạng thái phiếu yêu cầu (xem §1 — không cần).

## 3. Thiết kế

### 3.1 Model

```python
# models/hr_applicant.py — cạnh start_date / candidate_confirmed (nhóm sheet 7.6)
onboard_result = fields.Selection([
    ('arrived', 'Đã đến'),
    ('no_show', 'Không nhận việc'),
], string='Kết quả nhận việc', tracking=True)
```

- **Bỏ trống = chưa xác định** (đã gửi thư mời, đang chờ tới ngày). Đây là trạng
  thái mặc định, không cần giá trị riêng.
- `tracking=True` để chatter ghi lại ai đổi, khi nào — người bùng là dữ liệu hay
  bị hỏi lại.
- Chỉ **thêm cột nullable**, không cần migration script.

### 3.2 Quy tắc nghiệp vụ

| Mã | Quy tắc | Lý do |
|---|---|---|
| BR-OB-01 | Chọn **Không nhận việc** → hồ sơ **vẫn ở tab Offer**, hiện badge đỏ, **ẩn nút Tạo hồ sơ nhân viên**. Không lưu trữ hồ sơ. | Chốt theo yêu cầu của Việt 2026-08-09: cần nhìn thấy để theo dõi, không giấu đi. |
| BR-OB-02 | Backend **từ chối** `create-employee` khi `onboard_result = 'no_show'` (400, thông báo rõ). | Ẩn nút ở UI là lớp mềm; API vẫn gọi thẳng được. |
| BR-OB-03 | **Không** cho đặt `no_show` khi ứng viên đã ở bước có `hired_stage`. | Đã bàn giao nhân sự mà đánh "không nhận việc" là mâu thuẫn, đồng thời phá bất biến phễu (`hired ⊆ Nhận việc`). |
| BR-OB-04 | Đổi từ `no_show` → `arrived` (hoặc về trống) được bình thường. | UV đổi ý / HR chọn nhầm là chuyện thường, không khoá một chiều. |
| BR-OB-05 | Chọn **Đã đến** **không** tự đẩy bước. Bước vẫn do nút *Tạo hồ sơ nhân viên* đẩy sang Onboarding như hiện nay. | Giữ đúng luồng Việt mô tả: đến rồi thì người tuyển bấm tạo hồ sơ; hai hành động tách nhau. |

### 3.3 Đếm lại ô "Nhận việc" của phễu

Chốt **cách C** (Việt chọn 2026-08-09): giữ luật suy đoán cũ nhưng **trừ người
bùng**, và công nhận thêm ai đã được đánh *Đã đến*.

```python
'onboard': ['&', ('onboard_result', '!=', 'no_show'),
            '|', '|',
            ('stage_id.sequence', '>=', _STAGE_ONBOARD_SEQ),
            ('start_date', '!=', False),
            ('onboard_result', '=', 'arrived')],
```

- Không chọn "chỉ đếm `arrived`" (cách A) vì 16 CV cũ trên Neon chưa ai điền ô
  mới → ô Nhận việc sẽ tụt về 0 cho tới khi HR điền bù.
- Bất biến `hired ⊆ Nhận việc` vẫn giữ nhờ BR-OB-03.

### 3.4 API

| Chỗ sửa | Nội dung |
|---|---|
| `APPLICANT_FIELDS` (`controllers/main.py:29`) | thêm `'onboardResult': ('onboard_result', 'str')` — validate thuộc selection, sai thì 400. |
| `_cv_row` | trả `onboardResult` + payload `/cv` mang thêm `onboardResultLabels` (SPA không hard-code chuỗi tiếng Việt). |
| `api_recruitment_create_employee` (`:527`) | thêm guard BR-OB-02, đặt **trước** nhánh chống tạo trùng. |
| `APPLICANT_GROUPS['onboard']` | domain mới ở §3.3. |

### 3.5 UI — tab Offer & Nhận việc

- Thêm cột **Kết quả nhận việc** ngay sau *Ngày nhận việc*: ô `select` ba lựa
  chọn — *Chưa xác định* / *Đã đến* / *Không nhận việc*, lưu ngay như các ô khác
  (`saveField`), chỉ recruiter sửa được.
- `no_show` → badge đỏ **Không nhận việc** trên dòng, nút *Tạo hồ sơ NV* biến
  mất; `arrived` → badge xanh **Đã đến**.
- Bổ sung một bước vào `GuideNote` của tab: gửi thư mời xong thì **chờ tới ngày
  hẹn**, đến thì đánh *Đã đến* rồi bấm tạo hồ sơ, không đến thì đánh *Không
  nhận việc*.
- Tooltip ô **Nhận việc** ở tab Theo dõi cập nhật: đã trừ người bùng.

## 4. Ảnh hưởng triển khai

- `__manifest__.py`: **19.0.2.7.0 → 19.0.2.8.0**.
- **Có DDL** (cột mới) ⇒ Neon phải `-u hocba_recruitments` qua **endpoint trực
  tiếp** (bỏ `-pooler`), dừng container serving trước. Chạy từ Git Bash nhớ
  `MSYS_NO_PATHCONV=1`.
- Dữ liệu cũ: mọi ứng viên `onboard_result` **NULL** — đúng nghĩa "chưa xác
  định", không cần backfill. Số của phễu **không đổi** ngay sau upgrade.
- Ghi `docs/DB_TEST_DATA.md` sau khi deploy.

## 5. Test (đỏ trước, xanh sau)

Thêm vào `tests/test_offer_onboard_result.py`:

1. Ghi nhận `Đã đến` / `Không nhận việc` qua `PATCH /recruitment/applicant/<id>`;
   giá trị lạ → 400.
2. BR-OB-02: `no_show` rồi gọi `create-employee` → 400, **không** tạo `hr.employee`.
3. BR-OB-03: ứng viên ở bước hired, đặt `no_show` → `ValidationError`.
4. BR-OB-04: `no_show` → `arrived` chạy được, sau đó `create-employee` OK.
5. Phễu: UV có `start_date` nhưng bị đánh `no_show` **không** vào ô Nhận việc;
   UV đánh `arrived` mà chưa có ngày **có** vào ô Nhận việc; bất biến
   `hired ≤ Nhận việc ≤ PV` vẫn đúng.

Chạy local: `0 failed, 0 error(s)` với tổng số test > 159 (mốc hiện tại).

## 6. Điểm còn treo

- Tỷ lệ bùng hiện chỉ tra được bằng tay (lọc `no_show`). Nếu khách cần con số
  trên màn hình thì làm ở màn báo cáo tuyển dụng — sheet 7.9 của khách **rỗng
  hoàn toàn**, phải hỏi khách muốn xem gì trước khi dựng.
