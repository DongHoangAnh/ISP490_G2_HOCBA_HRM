# Thiết kế — Màn Cấu hình đánh giá (`hocba_reviews`)

- Ngày: 2026-08-21 · Owner: Việt · Nhánh: `Viet/Recruitment`
- Nền tảng đã có: [spec đánh giá định kỳ](2026-07-26-performance-review-design.md),
  công thức [docs/CONG_THUC_DANH_GIA.md](../../CONG_THUC_DANH_GIA.md)

## 1. Vấn đề

Bộ tiêu chí đánh giá (`hb.review.criteria`), trọng số, thang điểm và ngưỡng xếp
loại A/B/C/D hiện chỉ sửa được bằng cách vào giao diện Odoo gốc hoặc sửa data
XML. HR của trung tâm chỉ dùng SPA nên trên thực tế **không tự đổi được câu hỏi
đánh giá**. Cần một màn cấu hình trong SPA.

## 2. Phạm vi

**Trong phạm vi:** HR thêm / sửa / tắt / sắp xếp câu hỏi đánh giá của hai nhóm
(Giảng viên, Nhân viên văn phòng); sửa trọng số từng câu (tổng mỗi nhóm = 100),
điểm tối đa từng câu (1–10), hướng dẫn chấm và 3 mốc mô tả hành vi; sửa ngưỡng
xếp loại A/B/C/D và chỉ tiêu buổi dạy; một tab hướng dẫn cách cấu hình.

**Ngoài phạm vi:** công thức tổng điểm (giữ nguyên trung bình có trọng số quy về
thang 100), bảng quy đổi của tiêu chí tự động (% đúng giờ → điểm, khối lượng,
chứng chỉ), tab "Hướng dẫn chấm điểm" của màn Đánh giá, và mọi thay đổi trên
phiếu đã tồn tại.

## 3. Quyết định thiết kế

| Câu hỏi | Chốt |
|---|---|
| HR sửa "công thức" tới đâu | Chỉ ngưỡng A/B/C/D + tham số chỉ tiêu buổi dạy. Công thức tổng cố định. |
| Sửa câu hỏi tới đâu | Thêm / sửa / tắt / sắp xếp. Không xoá cứng. |
| Tổng trọng số ≠ 100 | Chặn cứng khi lưu, rollback cả lô. |
| Phiếu đang Nháp | Giữ nguyên cấu hình cũ. Cấu hình mới chỉ ăn vào phiếu tạo sau đó; màn cấu hình nhắc "còn N phiếu Nháp dùng cấu hình cũ — mở đợt mới để áp dụng". |
| Quyền | HR Manager + Admin (`need: 'hrm'`), như các màn cấu hình khác. |

## 4. Backend

### 4.1 `hb.review.criteria`

- `max_score`: ràng buộc **1–10** (trước đây chỉ ≥ 1). `anchor_levels()` tự giãn
  mốc cao/giữa/thấp theo thang nên hướng dẫn không lệch khi đổi thang.
- `weight`: 0–100.
- `code`: HR không nhập. Câu hỏi mới tự sinh `t_*` / `o_*` + hậu tố số, đảm bảo
  unique (`_code_unique` đang có).
- Bỏ câu hỏi = `active = False`. Không xoá cứng vì `hb.performance.review.line`
  giữ `criteria_id` với `ondelete='restrict'` — phiếu cũ phải tra được tên tiêu
  chí.
- Thứ tự do `sequence`.

**Tổng trọng số = 100 KHÔNG đặt bằng `@api.constrains`**: lúc cài module / nạp
data XML, bản ghi vào từng cái một nên tổng chưa đủ 100 sẽ làm hỏng install.
Thay bằng method `check_group_weight(role_group)` gọi **sau khi áp toàn bộ
payload trong cùng transaction**; lệch thì `ValidationError` → rollback cả lô.

Method `apply_group(role_group, rows)` nhận cả bộ tiêu chí của một nhóm, tạo /
ghi / tắt / đánh lại `sequence`, rồi gọi `check_group_weight`.

### 4.2 Ngưỡng & tham số

Giữ nguyên `ir.config_parameter` (`hocba_reviews.grade_a/_b/_c`,
`hocba_reviews.teacher_sessions_target`) — engine chấm điểm đã đọc từ đó, không
phải sửa `_compute_total`. Validate `0 < C < B < A ≤ 100`, chỉ tiêu buổi dạy > 0.

### 4.3 API (`hocba_reviews/controllers/main.py`)

Cả ba route chỉ cho HR Manager / Admin, người khác **403**.

| Method | Route | Việc |
|---|---|---|
| GET | `/hocba-hrm/api/reviews/config` | 2 bộ tiêu chí (kể cả đã tắt), ngưỡng, tham số, `weightSum`, `draftCount` từng nhóm, danh mục `autoSource` |
| POST | `/hocba-hrm/api/reviews/config/criteria` | Lưu **cả bộ của một nhóm** trong 1 transaction rồi kiểm tổng 100 |
| POST | `/hocba-hrm/api/reviews/config/grading` | Lưu ngưỡng A/B/C + chỉ tiêu buổi dạy |

Lưu cả bộ thay vì PATCH từng dòng là điều kiện để chặn cứng tổng 100 — sửa lẻ
thì gần như lúc nào tổng cũng tạm lệch.

## 5. Frontend

Mục **"Cấu hình đánh giá"** trong section Hệ thống của `Shell.jsx`
(id `reviewsConfig`, `need: 'hrm'`), thư mục `frontend/src/features/reviews-config/`:

- `ReviewsConfig.jsx` — khung 3 tab + tải/lưu; thanh dưới hiện **"Tổng trọng số
  100/100 ✓"** hoặc cảnh báo đỏ; nút Lưu chỉ bật khi đủ 100 và có thay đổi.
- `CriteriaTab.jsx` — dùng chung cho tab Giảng viên và Nhân viên văn phòng. Mỗi
  dòng: tên · trọng số · điểm tối đa · nguồn chấm · lên/xuống · bật/tắt · mở
  rộng để sửa hướng dẫn + 3 mốc hành vi. Nút "+ Thêm câu hỏi".
- `ConfigGuide.jsx` — tab **Hướng dẫn cấu hình**: ngưỡng A/B/C/D + chỉ tiêu buổi
  dạy (đặt ở đây vì dùng chung cả hai nhóm), giải thích công thức kèm ví dụ tính
  tay theo đúng bộ tiêu chí đang cấu hình, ý nghĩa từng nguồn chấm tự động, quy
  tắc viết mốc hành vi, và cảnh báo "còn N phiếu Nháp dùng cấu hình cũ".

POST trả về state mới → màn tự cập nhật, không reload.

## 6. Test (`tests/test_review_config.py`)

1. Lưu bộ tổng 100 → OK; sửa thành 95 → `ValidationError` và **DB không đổi**.
2. `max_score` 0 và 11 → lỗi; 10 → OK, `anchor_levels()` ra mốc 10/5/1.
3. Thêm câu hỏi → `code` tự sinh unique; tắt câu hỏi → `active=False`, phiếu cũ
   vẫn đọc được tên tiêu chí.
4. Đổi trọng số: phiếu Nháp cũ giữ nguyên `weight`/`max_score`/tổng điểm; phiếu
   tạo mới lấy cấu hình mới.
5. Ngưỡng nghịch (`A=70, B=80`) → lỗi; `A=90,B=75,C=60` → phiếu 76 điểm ra loại B.
6. Trưởng phòng / giáo vụ / nhân viên gọi API config → 403; HR Manager → 200.
