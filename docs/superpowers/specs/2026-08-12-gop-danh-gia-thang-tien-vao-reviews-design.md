# Gộp nhập liệu đánh giá + thăng tiến về màn Đánh giá (hocba_reviews)

- Ngày: 2026-08-12
- Owner: Tân. Đã được Việt (owner `hocba_reviews`) đồng ý.
- Trạng thái: chờ duyệt spec

## 1. Vấn đề

Hiện có **hai hệ đánh giá song song**:

| | Đợt đánh giá thăng tiến (cũ) | Phiếu đánh giá định kỳ (Việt) |
|---|---|---|
| Model | `hr.promotion.evaluation` | `hb.performance.review` |
| Bộ tiêu chí | `hr.promotion.criteria` — 4 tiêu chí | `hb.review.criteria` — 8 tiêu chí, 2 nhóm |
| Nhập liệu | popup trong hồ sơ NV | màn Đánh giá |
| Chỉ số tự động | 1 (chấm công 3 tháng) | 7 (chuyên cần, đúng giờ, nghỉ phép, chứng chỉ…) |
| Luồng | nháp → xác nhận | nháp → chốt → công bố (+ báo NV) |

Khách chốt sau họp: **chỉ giữ một bộ tiêu chí — bộ của Việt**, và dồn toàn
bộ nhập liệu (cả đánh giá lẫn thăng tiến) về màn Đánh giá. Hồ sơ nhân viên
chỉ còn **kết quả và biểu đồ**. Dashboard sự nghiệp lấy dữ liệu từ nguồn mới.

## 2. Ràng buộc kiến trúc (quyết định chỗ đặt FK)

`hr.promotion.history` nằm trong `hocba_employees`, mà `hocba_reviews` **đã
depends** vào `hocba_employees`. Thêm trường trỏ `hb.performance.review`
ngay trên model gốc → **vòng phụ thuộc**, Odoo không load được.

**Giải:** thêm `hocba_hrm/models/hr_promotion_history.py` với
`_inherit = 'hr.promotion.history'`, khai `review_id`, và thêm
`hocba_reviews` vào `depends` của `hocba_hrm`.
Chuỗi `hocba_hrm → hocba_reviews → hocba_employees` không có vòng, và
**module của Việt không phải sửa dòng nào**.

## 3. Nhập liệu thăng tiến chuyển vào ReviewDrawer

- Nút **"Tạo thăng tiến"** hiện trong `ReviewDrawer` khi:
  `state ∈ {confirmed, published}` **và** user là HR Manager.
  (Trưởng phòng/giáo vụ chấm được phiếu nhưng không tạo được thăng tiến —
  giữ đúng quyền hiện hành của `PromotionForm`.)
- Bấm → mở `PromotionForm` prefill: nhân viên, phòng ban/chức vụ hiện tại,
  ngày hiệu lực = hôm nay, lý do gợi ý `"Đánh giá <kỳ> — xếp loại <grade>"`.
- `POST /api/employee/<emp_id>/promotion` nhận thêm `reviewId`, ghi vào
  `review_id`. Ba ràng buộc phía server (không tin FE):
  1. Phiếu phải tồn tại và `employee_id` **trùng** `emp_id`.
  2. Phiếu phải đã chốt (`confirmed`/`published`) — không gắn vào phiếu nháp.
  3. Một phiếu chỉ gắn **một** bản ghi thăng tiến; phiếu đã có thì FE hiện
     liên kết thay vì nút, server trả lỗi rõ nếu vẫn cố tạo.

## 4. Hồ sơ nhân viên chỉ còn kết quả

- `PromoTab`: bỏ nút "Đánh giá mới" **và** "Tạo thăng tiến"; xoá
  `EvaluationForm.jsx` + `saveEvaluation`.
- `PromoTab` đọc **một nguồn duy nhất** là `/api/career/<empId>` (bỏ nhánh
  `fetchEvaluations`) → hết cảnh Giáo vụ bị 403 rồi hiển thị "0 đợt đánh
  giá" dù NV có đánh giá.
- Xoá cả hai route `/api/promotion/eval/<emp_id>` (GET) và
  `/api/promotion/eval/save` (POST) — không còn ai gọi.
- Thẻ "Chấm công 3T" trên `PromoTab` bỏ: chỉ số vận hành nay nằm trong phiếu
  của Việt (7 chỉ số, đầy đủ hơn).

## 5. Dashboard sự nghiệp đọc nguồn mới

`_career_payload` lấy mốc "Đánh giá" từ `hb.performance.review`:

- **Phạm vi trạng thái theo người xem:** tự xem hồ sơ mình → chỉ
  `published`; vai trò quản lý → `confirmed` + `published`.
  Việt chỉ bắn thông báo cho NV khi công bố, để NV thấy phiếu vừa chốt là
  lộ kết quả trước khi HR công bố.
- `scoreTrend`: cả hai nguồn đều quy về thang %, vẽ chung một đường; mỗi
  điểm mang nhãn nguồn để không ai đọc nhầm.
- `criteriaRadar` + "Tiến bộ từng tiêu chí": **chỉ** dựng từ
  `hb.review.criteria` (bộ của Việt). Không trộn 2 bộ tiêu chí.
- `stats.evalCount / lastScore / avgScore`: đếm theo phiếu mới.

## 6. Bộ tiêu chí cũ

Chỉ giữ **một** bộ tiêu chí đang dùng: `hb.review.criteria`.

- `hr.promotion.criteria` (4 record data XML) **không xuất hiện ở bất kỳ màn
  nào nữa**. Model + data **giữ nguyên trong DB**: dòng chấm cũ tham chiếu
  nó với `ondelete='restrict'`, xoá đi là gãy lịch sử.
- Mốc đánh giá cũ vẫn nằm trên timeline dưới dạng lịch sử: ngày, tổng điểm,
  kết luận, nhận xét — **không** hiện chip điểm từng tiêu chí cũ, vì đó
  chính là chỗ gây loạn giữa hai bộ.
- Không migrate dữ liệu cũ sang model mới: 4 tiêu chí ≠ 8 tiêu chí, thang
  điểm khác nhau, ép sang nhau sẽ bịa ra lịch sử điểm không có thật.

## 7. Test

`hocba_hrm/tests/test_promotion_review_link.py`:

1. Gắn thăng tiến vào phiếu **nháp** → bị chặn.
2. Gắn phiếu của **NV khác** → bị chặn.
3. Phiếu đã có thăng tiến → tạo lần hai bị chặn.
4. Tạo hợp lệ → `review_id` được ghi, `hr.promotion.history` cập nhật chức
   vụ/lương như cũ.
5. Quyền: trưởng phòng/giáo vụ **không** tạo được thăng tiến.

`hocba_hrm/tests/test_career.py` (bổ sung):

6. NV thường xem career của mình: thấy phiếu `published`, **không** thấy
   `confirmed`.
7. Quản lý xem career NV trong phạm vi: thấy cả `confirmed`.
8. Timeline có đủ mốc từ cả nguồn cũ lẫn nguồn mới.
9. `criteriaRadar` chỉ chứa tiêu chí của `hb.review.criteria`.

Lệnh chạy:

```
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees,hocba_reviews --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

## 8. Rủi ro

- **Thêm depends là thay đổi cấu trúc module**: `hocba_hrm` từ nay cần
  `hocba_reviews` cài trước. Trên Neon phải upgrade theo đúng thứ tự; DB nào
  chưa cài `hocba_reviews` sẽ không load được `hocba_hrm`.
- **Hai nguồn trên cùng một timeline** trong giai đoạn chuyển tiếp. Chấp
  nhận: dữ liệu cũ ít và sẽ lùi dần về quá khứ.
- Sau đợt này **không còn chỗ nào tạo `hr.promotion.evaluation` mới** —
  đúng ý đồ; model tồn tại chỉ để đọc lịch sử.
