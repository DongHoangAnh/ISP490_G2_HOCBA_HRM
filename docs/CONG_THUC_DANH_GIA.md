# Công thức tính đánh giá nhân viên — Học Bá HRM

> Tài liệu nghiệp vụ cho module `hocba_reviews`. Mọi con số dưới đây là **cấu
> hình được** (`ir.config_parameter`), không hard-code trong công thức.
> Thiết kế tổng thể: [spec đánh giá định kỳ](superpowers/specs/2026-07-26-performance-review-design.md).
>
> **Bản cho người chấm:** tab **Hướng dẫn chấm điểm** trong màn Đánh giá nhân
> viên trình bày lại đúng nội dung này ngay trong app, số liệu đọc động từ API
> `GET /hocba-hrm/api/reviews/guide` (ngưỡng xếp loại, trọng số tiêu chí, bảng
> quy đổi lấy thẳng từ cấu hình + hằng số model). Sửa công thức/tham số ở đây
> thì phải sửa cả endpoint đó nếu nguồn số thay đổi — đừng chép cứng vào SPA.

---

## 1. Ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| `n` | Số tiêu chí của bộ đang dùng (Giảng viên: 6, Văn phòng: 6) |
| `score_i` | Điểm quản lý chấm cho tiêu chí `i` (số nguyên 0…`max_i`) |
| `max_i` | Điểm tối đa của tiêu chí `i` (mặc định **5**) |
| `weight_i` | Trọng số tiêu chí `i` (%) — tổng mỗi bộ = 100 |
| `ratio_i` | Tỷ lệ đạt của tiêu chí `i` |
| `TOTAL` | Tổng điểm quy về thang 100 |
| `[T₁, T₂]` | Khoảng thời gian của kỳ đánh giá (`date_from`, `date_to`) |

---

## 2. Công thức tổng điểm

**Bước 1 — tỷ lệ đạt từng tiêu chí:**

```
ratio_i = score_i / max_i            (0 ≤ ratio_i ≤ 1)
```

**Bước 2 — tổng điểm có trọng số, quy về thang 100:**

```
          Σ (ratio_i × weight_i)
TOTAL =  ───────────────────────── × 100
              Σ weight_i
```

Chia cho `Σ weight_i` thay vì cho 100 cố định để công thức vẫn đúng khi HR bật/tắt
bớt tiêu chí (tổng trọng số không còn tròn 100). Tiêu chí có `max_i = 0` bị loại
khỏi cả tử và mẫu.

**Bước 3 — xếp loại:**

| Xếp loại | Điều kiện | Ý nghĩa | Tham số |
|---|---|---|---|
| **A — Xuất sắc** | `TOTAL ≥ 85` | Vượt mong đợi, xét thưởng/thăng tiến | `hocba_reviews.grade_a` |
| **B — Tốt** | `70 ≤ TOTAL < 85` | Hoàn thành tốt | `hocba_reviews.grade_b` |
| **C — Đạt** | `55 ≤ TOTAL < 70` | Hoàn thành, cần cải thiện vài điểm | `hocba_reviews.grade_c` |
| **D — Cần cải thiện** | `TOTAL < 55` | Lập kế hoạch cải thiện, tái đánh giá kỳ sau | — |

---

## 2b. Chọn điểm nào trên thang 0–5 (thang mô tả hành vi)

Công thức ở §2 chỉ nói cách **cộng** điểm, không nói cách **chọn** điểm. Với các
tiêu chí chấm tay, mỗi tiêu chí có ba mốc hành vi quan sát được lưu trên
`hb.review.criteria`:

| Trường | Mức | Vai trò |
|---|---|---|
| `anchor_top` | `max_score` (mặc định 5) | Hành vi vượt hẳn yêu cầu vị trí |
| `anchor_mid` | `(max_score + 1) // 2` = 3 | **Mốc chuẩn** — làm đúng những gì vị trí cần |
| `anchor_low` | 1 | Chưa đạt yêu cầu cơ bản |

Hai mức xen giữa (4 và 2) **cố ý không có mô tả riêng**: chúng là "nằm giữa hai
mốc liền kề". Mức **0 không phải một bậc đánh giá** mà là "chưa chấm" — nhưng
vẫn được tính là 0 điểm trong công thức §2, nên bỏ sót một dòng sẽ âm thầm kéo
tổng điểm xuống.

Tiêu chí **tự động** không có mốc hành vi: thang của chúng là bảng quy đổi ở §4.

Nội dung mốc mặc định nằm trong `DEFAULT_ANCHORS`
(`models/hb_review_criteria.py`), được nạp vào DB bằng `post_init_hook` (cài
mới) và migration `19.0.2.0.0` (nâng cấp). Cả hai **chỉ điền ô đang rỗng** nên
HR sửa lại mốc cho phù hợp trung tâm thì không bị ghi đè ở lần nâng cấp sau.

Người chấm đọc mốc ở hai chỗ: tab **Hướng dẫn chấm điểm** (mục 4 và 5) và ngay
trong phiếu chấm (mục "Mốc chấm điểm" của từng tiêu chí).

---

## 3. Khoảng thời gian của kỳ

| Loại kỳ | `period_index` | `date_from` → `date_to` |
|---|---|---|
| Quý (`quarter`) | 1 → 4 | 01/01–31/03 · 01/04–30/06 · 01/07–30/09 · 01/10–31/12 |
| Nửa năm (`half`) | 1 → 2 | 01/01–30/06 · 01/07–31/12 |
| Năm (`year`) | 1 | 01/01–31/12 |

`months_in_period` = 3 (quý) · 6 (nửa năm) · 12 (năm) — dùng để quy đổi chỉ tiêu
khối lượng ở §4.3.

---

## 4. Chỉ số tự động

Hệ thống tính 4 chỉ số dưới đây trên `[T₁, T₂]` rồi **quy đổi ra điểm 1–5**.
Điểm này chỉ là **đề xuất**: quản lý sửa đè được, khi sửa thì dòng chuyển sang
"chấm tay" và nên ghi lý do vào ô ghi chú.

### 4.1. Tỷ lệ chuyên cần / đúng giờ (`punctuality`)

**Giảng viên** — nguồn `hocba.teaching.attendance` (chấm công theo buổi dạy):

```
N_total = số buổi có check-in trong [T₁, T₂]
N_ok    = số buổi KHÔNG vi phạm, tức là:
          out_of_window = false  (chấm công đúng cửa sổ giờ buổi học)
      AND out_of_zone   = false  (đúng vị trí lớp)
      AND face_suspect  = false  (ảnh khuôn mặt không bị nghi ngờ)

punctual_pct = N_ok / N_total × 100
```

**Nhân viên văn phòng** — nguồn `hocba.attendance` (chấm công ngày):

```
N_total = số ngày công có bản ghi trong [T₁, T₂]
N_ok    = số ngày có late_minutes = 0 VÀ early_leave_minutes = 0

punctual_pct = N_ok / N_total × 100
```

**Quy đổi ra điểm:**

| `punctual_pct` | Điểm |
|---|---|
| ≥ 98% | 5 |
| ≥ 95% | 4 |
| ≥ 90% | 3 |
| ≥ 80% | 2 |
| < 80% | 1 |

> **Quy tắc chống phạt oan:** `N_total = 0` (nhân viên mới, nghỉ thai sản, chưa
> có dữ liệu chấm công) → hệ thống **không tự chấm**, để trống cho quản lý chấm
> tay. Không quy về 0 điểm.

### 4.2. Số lần đi trễ (`metric_late_count`) — chỉ hiển thị

```
Giảng viên : số buổi có out_of_window = true
Văn phòng  : số ngày có late_minutes > 0
```

Không tham gia công thức tính điểm, chỉ hiện trong khối "Chỉ số tham chiếu" để
quản lý có căn cứ khi chấm các tiêu chí định tính.

### 4.3. Khối lượng giảng dạy (`workload`) — chỉ giảng viên

```
target_period = teacher_sessions_target × (months_in_period / 3)
workload_pct  = N_total_sessions / target_period × 100
```

`teacher_sessions_target` = chỉ tiêu **60 buổi/quý** (tham số
`hocba_reviews.teacher_sessions_target`). Ví dụ kỳ nửa năm → chỉ tiêu 120 buổi.

| `workload_pct` | Điểm |
|---|---|
| ≥ 100% | 5 |
| ≥ 85% | 4 |
| ≥ 70% | 3 |
| ≥ 50% | 2 |
| < 50% | 1 |

### 4.4. Chuẩn chứng chỉ (`cert`) — chỉ giảng viên

Đếm chứng chỉ **đã xác minh** (`x_cert_verified = true`) trên hồ sơ, phân loại
theo `x_cert_status` tại thời điểm tính:

```
cert_valid    = số chứng chỉ còn hạn (valid) hoặc không có hạn (none)
cert_expiring = số chứng chỉ sắp hết hạn (mặc định trong 60 ngày tới)
cert_expired  = số chứng chỉ đã hết hạn
```

Quy đổi theo thứ tự ưu tiên từ trên xuống, gặp điều kiện đúng đầu tiên thì dừng:

| Điều kiện | Điểm | Diễn giải |
|---|---|---|
| Không có chứng chỉ nào đã xác minh | 1 | Chưa đạt chuẩn hồ sơ |
| `cert_expired > 0` | 2 | Có chứng chỉ hết hạn — phải gia hạn ngay |
| `cert_expiring > 0` | 3 | Sắp hết hạn — nhắc gia hạn |
| `cert_valid = 1` | 4 | Đủ chuẩn tối thiểu |
| `cert_valid ≥ 2` | 5 | Vượt chuẩn |

### 4.5. Ngày nghỉ phép (`metric_leave_days`) — chỉ hiển thị

Tổng `number_of_days` của các đơn `hr.leave` trạng thái đã duyệt (`validate`)
giao với `[T₁, T₂]`. Không tính điểm — nghỉ phép là quyền lợi, chỉ dùng làm ngữ
cảnh khi quản lý đọc chỉ số khối lượng.

---

## 5. Ví dụ tính tay

### 5.1. Giảng viên — cô Nguyễn Thị A, Quý 3/2026 (01/07 – 30/09)

**Dữ liệu hệ thống trong kỳ:**
- 58 buổi dạy có chấm công; 3 buổi `out_of_window`, 1 buổi `out_of_zone` (trùng
  1 buổi đã trễ) → số buổi vi phạm riêng biệt = 3
- 2 chứng chỉ đã xác minh: HSK 5 còn hạn, Chứng chỉ sư phạm còn hạn

**Chỉ số tự động:**

```
N_total = 58, N_ok = 58 − 3 = 55
punctual_pct = 55 / 58 × 100 = 94.8%   → 90% ≤ 94.8% < 95%  → điểm 3

target_period = 60 × (3/3) = 60 buổi
workload_pct  = 58 / 60 × 100 = 96.7%  → 85% ≤ 96.7% < 100% → điểm 4

cert_valid = 2, cert_expiring = 0, cert_expired = 0        → điểm 5
```

**Bảng chấm:**

| Tiêu chí | Trọng số | Điểm | `ratio` | `ratio × weight` |
|---|---|---|---|---|
| Chất lượng giờ dạy | 25 | 4 (tay) | 0.80 | 20.00 |
| Chuyên môn & chứng chỉ | 20 | 5 (auto) | 1.00 | 20.00 |
| Chuyên cần & đúng giờ | 20 | 3 (auto) | 0.60 | 12.00 |
| Quản lý lớp & học viên | 15 | 4 (tay) | 0.80 | 12.00 |
| Khối lượng giảng dạy | 10 | 4 (auto) | 0.80 | 8.00 |
| Phối hợp & báo cáo | 10 | 5 (tay) | 1.00 | 10.00 |
| **Tổng** | **100** | | | **82.00** |

```
TOTAL = 82.00 / 100 × 100 = 82.0  →  70 ≤ 82.0 < 85  →  Xếp loại B (Tốt)
```

**Đọc kết quả:** điểm kéo xuống chủ yếu do chuyên cần (3/5 — 3 buổi chấm công
ngoài cửa sổ giờ). Đây là điểm cải thiện cụ thể, đo được, để trao đổi với giáo
viên ở kỳ sau.

### 5.2. Nhân viên văn phòng — anh Trần Văn B, Nửa năm 2/2026 (01/07 – 31/12)

**Dữ liệu hệ thống:** 118 ngày công, trong đó 4 ngày đi trễ và 2 ngày về sớm
(không trùng nhau) → `N_ok = 118 − 6 = 112`.

```
punctual_pct = 112 / 118 × 100 = 94.9%  → 90% ≤ 94.9% < 95% → điểm 3
```

| Tiêu chí | Trọng số | Điểm | `ratio` | `ratio × weight` |
|---|---|---|---|---|
| Kết quả công việc / KPI | 35 | 5 (tay) | 1.00 | 35.00 |
| Chuyên cần & kỷ luật | 20 | 3 (auto) | 0.60 | 12.00 |
| Thái độ & trách nhiệm | 15 | 4 (tay) | 0.80 | 12.00 |
| Phối hợp | 15 | 4 (tay) | 0.80 | 12.00 |
| Chủ động & cải tiến | 10 | 5 (tay) | 1.00 | 10.00 |
| Tiềm năng phát triển | 5 | 4 (tay) | 0.80 | 4.00 |
| **Tổng** | **100** | | | **85.00** |

```
TOTAL = 85.00 / 100 × 100 = 85.0  →  85.0 ≥ 85  →  Xếp loại A (Xuất sắc)
```

### 5.3. Trường hợp tổng trọng số ≠ 100

Giả sử HR tắt tiêu chí "Tiềm năng phát triển" (weight 5) → `Σ weight = 95`. Giữ
nguyên các điểm khác của ví dụ 5.2:

```
Σ (ratio × weight) = 35 + 12 + 12 + 12 + 10 = 81.00
TOTAL = 81.00 / 95 × 100 = 85.26  →  Xếp loại A
```

Nếu chia cứng cho 100 thì kết quả là 81.0 (loại B) — nhân viên bị thiệt chỉ vì
công ty bỏ bớt một tiêu chí. Đó là lý do mẫu số là `Σ weight_i`.

---

## 6. Bảng tham số cấu hình

| Tham số (`ir.config_parameter`) | Mặc định | Ý nghĩa |
|---|---|---|
| `hocba_reviews.grade_a` | 85 | Ngưỡng xếp loại A |
| `hocba_reviews.grade_b` | 70 | Ngưỡng xếp loại B |
| `hocba_reviews.grade_c` | 55 | Ngưỡng xếp loại C |
| `hocba_reviews.teacher_sessions_target` | 60 | Chỉ tiêu buổi dạy mỗi quý |
| `hoc_ba.cert_alert_days` | 60 | Số ngày coi là "sắp hết hạn" (dùng chung toàn hệ thống) |

Trọng số từng tiêu chí sửa trực tiếp trên bản ghi `hb.review.criteria`.

---

## 7. Nguyên tắc khi vận hành

1. **Máy đề xuất, người quyết định.** Chỉ số tự động chỉ điền sẵn; quản lý sửa
   đè được và nên ghi lý do.
2. **Chỉ số là ảnh chụp.** Khi phiếu đã chốt, con số giữ nguyên dù dữ liệu chấm
   công sau đó được sửa. Muốn tính lại phải mở lại phiếu (chỉ HR).
3. **Trọng số và điểm tối đa được sao chép vào phiếu lúc tạo.** Sửa cấu hình
   tiêu chí không làm thay đổi các phiếu đã chấm.
4. **Không có dữ liệu thì không chấm.** Thiếu dữ liệu chấm công không đồng nghĩa
   với làm việc kém.
