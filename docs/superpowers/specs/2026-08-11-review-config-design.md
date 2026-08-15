# Spec — Cấu hình đánh giá nhân viên

> Module: `hocba_reviews` · Owner: Việt · Nhánh: `Viet/Recruitment`
> Ngày: 2026-08-11 · Trạng thái: **Chờ duyệt**
> Liên quan: [thiết kế đánh giá định kỳ](2026-07-26-performance-review-design.md) ·
> [công thức tính điểm](../../CONG_THUC_DANH_GIA.md)

---

## 1. Vấn đề

Bộ tiêu chí đánh giá và các ngưỡng xếp loại hiện do **nhóm dev tự đặt** (seed
trong `data/hb_review_criteria_data.xml`). Khi bàn giao, Học Bá Education phải tự
điều chỉnh được: đổi trọng số theo định hướng từng năm, thêm/bớt tiêu chí, sửa
ngưỡng xếp loại — **không cần lập trình viên và không cần vào backend Odoo**.

Tầng model đã sẵn sàng: `hb.review.criteria` có đủ trường cấu hình, ngưỡng nằm
trong `ir.config_parameter` và được đọc động ở mỗi lần tính điểm. **Cái thiếu
duy nhất là API + màn hình.**

## 2. Phạm vi

### Trong phạm vi

| Nhóm | Cấu hình được |
|---|---|
| **Bộ tiêu chí** (`hb.review.criteria`) | Tên, mã, trọng số, điểm tối đa, nguồn chấm, thứ tự, hướng dẫn chấm, bật/tắt hiệu lực — tách riêng 2 nhóm Giảng viên / Văn phòng |
| **Ngưỡng xếp loại** (`ir.config_parameter`) | `grade_a` (85), `grade_b` (70), `grade_c` (55) |
| **Chỉ tiêu khối lượng** | `teacher_sessions_target` (60 buổi/quý) |

### Ngoài phạm vi (ghi nhận, chưa làm)

- Bảng quy đổi chỉ số → điểm (`PCT_TABLE`, `WORKLOAD_TABLE`, luật chứng chỉ) vẫn
  hardcode trong [hb_performance_review.py:248](../../../custom-addons/hocba_reviews/models/hb_performance_review.py).
  Đưa ra cấu hình cần thêm model mới + sửa `_auto_score_for` — tách thành đợt sau.
- Áp lại cấu hình mới cho phiếu **Nháp** đã tạo trước đó (xem §6.2).
- Bộ tiêu chí theo từng phòng ban (hiện chỉ tách theo 2 nhóm vai trò).

## 3. Phân quyền

Màn hình dùng `need: 'hrm'` — **HR Manager + Admin**, giống *Cấu hình tuyển dụng*
và *Cấu hình nhận việc*. Trưởng phòng và Giáo vụ chấm điểm được nhưng **không**
thấy mục cấu hình.

Kiểm quyền ở controller bằng `_can_configure()`:

```python
u.has_group('base.group_system') or u.has_group('hr.group_hr_manager')
```

Không dùng `_is_hr()` sẵn có vì hàm đó bao gồm cả `hr.group_hr_user` (HR officer)
— nhân sự cấp officer không nên đổi trọng số toàn hệ thống. Sai quyền → `403
{error: 'forbidden'}`.

> ACL model hiện tại đã khớp: `hr.group_hr_manager` có đủ `write/create/unlink`
> trên `hb.review.criteria`, không phải sửa `ir.model.access.csv`.

## 4. API

Đặt trong `custom-addons/hocba_reviews/controllers/main.py`, `type='http'`, GET
để đọc / POST để ghi (theo đúng quy ước sẵn có của controller này — không dùng
PUT/DELETE). Payload camelCase theo `docs/QUY_UOC_FRONTEND.md`.

### 4.1. `GET /hocba-hrm/api/reviews/config`

```json
{
  "criteria": {
    "teacher": [{
      "id": 3, "name": "Chất lượng giờ dạy", "code": "t_quality",
      "sequence": 10, "weight": 25.0, "maxScore": 5,
      "autoSource": "none", "guideline": "…",
      "active": true, "inUse": true
    }],
    "office": [ … ]
  },
  "weightSum": { "teacher": 100.0, "office": 100.0 },
  "params": { "gradeA": 85, "gradeB": 70, "gradeC": 55, "teacherSessionsTarget": 60 },
  "autoSources": [["none", "Chấm tay"], ["punctuality", "…"], …],
  "canConfigure": true
}
```

- Trả **cả tiêu chí đã tắt** (`active: false`) để HR bật lại được → truy vấn với
  `active_test=False`.
- `weightSum` tính trên tiêu chí **đang bật**, để UI cảnh báo khi ≠ 100.
- `inUse` = đã có dòng chấm `hb.performance.review.line` tham chiếu → UI ẩn nút
  xoá cứng (xem §5.3).
- `autoSources` lấy từ `AUTO_SOURCE_SEL` để frontend không hard-code lại nhãn.

### 4.2. `POST /hocba-hrm/api/reviews/config/criteria` — tạo

Body: `{ roleGroup, name, code, weight, maxScore, autoSource, sequence, guideline }`
→ `201 { id }`. `code` trùng → `409 {error: 'duplicate'}`.

### 4.3. `POST /hocba-hrm/api/reviews/config/criteria/<int:crit_id>` — sửa

Body chỉ chứa trường cần đổi (partial update). **`roleGroup` và `code` không cho
sửa** khi tiêu chí đã dùng ở phiếu nào đó — đổi nhóm sẽ làm phiếu cũ tham chiếu
sang nhóm khác, làm hỏng ý nghĩa lịch sử.

### 4.4. `POST /hocba-hrm/api/reviews/config/criteria/<int:crit_id>/archive`

Body `{ active: false | true }` → bật/tắt hiệu lực. Đây là cách "xoá" mặc định.

### 4.5. `POST /hocba-hrm/api/reviews/config/criteria/<int:crit_id>/delete`

Xoá cứng, **chỉ khi chưa dùng ở phiếu nào**. `criteria_id` khai
`ondelete='restrict'` nên Odoo sẽ chặn; controller bắt trước và trả
`409 {error: 'in_use', message: 'Tiêu chí đã dùng ở N phiếu — hãy tắt hiệu lực thay vì xoá.'}`.

### 4.6. `POST /hocba-hrm/api/reviews/config/params`

Body `{ gradeA, gradeB, gradeC, teacherSessionsTarget }` → ghi
`ir.config_parameter` qua `.sudo()` sau khi đã kiểm quyền.

## 5. Quy tắc nghiệp vụ

### 5.1. Ngưỡng xếp loại

- `0 < gradeC < gradeB < gradeA ≤ 100`, nếu không → `400 {error: 'invalid'}` kèm
  thông báo tiếng Việt.
- `teacherSessionsTarget > 0`.

### 5.2. Trọng số

Tổng trọng số mỗi nhóm ≠ 100 → **cảnh báo trên UI, không chặn lưu**. Công thức
chia cho `Σ weight_i` nên vẫn đúng về mặt toán học
([công thức §5.3](../../CONG_THUC_DANH_GIA.md)); chặn cứng sẽ khiến HR không sửa
được trọng số từng dòng một (phải đi qua trạng thái trung gian ≠ 100).

Ràng buộc cứng giữ nguyên như model đang có: `weight ≥ 0`, `maxScore ≥ 1`.

### 5.3. Xoá vs tắt hiệu lực

Mặc định là **tắt hiệu lực** (`active = False`). Lý do: `ondelete='restrict'` +
phiếu đánh giá cũ phải giữ được nguyên vẹn để đối chiếu lịch sử. Nút xoá cứng chỉ
hiện với tiêu chí `inUse = false` (thường là tiêu chí vừa tạo nhầm).

Tiêu chí đã tắt: không xuất hiện ở phiếu tạo **mới**, phiếu cũ giữ nguyên dòng.

## 6. Ảnh hưởng tới phiếu đã có

### 6.1. Phiếu đã chốt / đã công bố — không đổi

`weight` và `max_score` được **snapshot** vào `hb.performance.review.line` lúc tạo
phiếu ([hb_performance_review.py:479](../../../custom-addons/hocba_reviews/models/hb_performance_review.py)).
Sửa cấu hình không đụng tới điểm đã chấm. Đây là hành vi đúng và spec này **không
thay đổi nó**.

### 6.2. Phiếu Nháp — cũng không đổi (rủi ro đã biết)

Phiếu Nháp tạo trước khi đổi trọng số vẫn giữ trọng số cũ → hai người cùng kỳ có
thể được tính theo hai bộ trọng số khác nhau. Xử lý ở đợt này: **cảnh báo trên
UI** khi lưu cấu hình mà đang có phiếu Nháp trong kỳ hiện tại
("Có N phiếu nháp đang dùng trọng số cũ"). Nút "Áp dụng lại cho phiếu nháp" để
đợt sau.

> `sequence` là `related=... store=True` nên đổi thứ tự tiêu chí **có** sắp xếp
> lại dòng của phiếu cũ. Chỉ ảnh hưởng thứ tự hiển thị, không ảnh hưởng điểm.

## 7. Giao diện

Màn mới `reviews-config` — *Cấu hình đánh giá*, icon `settings`, nhóm "Hệ thống"
trong `Shell.jsx`, đặt cạnh *Cấu hình chấm công*.

```
frontend/src/features/reviews-config/
  ReviewsConfig.jsx    — khung 2 tab, giống TimeoffConfig.jsx
  CriteriaTab.jsx      — bảng tiêu chí (2 nhóm), sửa tại chỗ
  CriteriaForm.jsx     — modal thêm/sửa tiêu chí
  GradesTab.jsx        — form ngưỡng xếp loại + chỉ tiêu buổi dạy
frontend/src/api/reviewsConfig.js
```

**Tab "Bộ tiêu chí"** — hai bảng xếp chồng (Giảng viên / Văn phòng), mỗi bảng có
dòng tổng trọng số ở chân bảng, tô đỏ khi ≠ 100. Cột: Thứ tự · Tiêu chí (+ hướng
dẫn dạng phụ đề) · Trọng số · Điểm tối đa · Nguồn chấm · Hiệu lực · thao tác.
Tiêu chí có `autoSource ≠ none` gắn `Badge` "Tự động" để HR biết điểm do hệ thống
đề xuất.

**Tab "Ngưỡng & chỉ tiêu"** — 4 ô số kèm thanh xem trước dải A/B/C/D, hiển thị
đúng khoảng vừa nhập để HR thấy ngay hệ quả trước khi lưu.

## 8. Kế hoạch test (TDD — đỏ trước)

`custom-addons/hocba_reviews/tests/test_review_config.py`

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `test_get_config_requires_hrm` | Trưởng phòng / giáo vụ / user thường → 403 |
| 2 | `test_get_config_shape` | HR manager: đủ 2 nhóm, có cả tiêu chí đã tắt, `weightSum` chỉ cộng dòng bật |
| 3 | `test_create_criteria` | Tạo được, xuất hiện ở phiếu tạo **sau** đó |
| 4 | `test_create_duplicate_code` | → 409 `duplicate` |
| 5 | `test_update_weight` | Đổi trọng số không đụng phiếu đã chốt (snapshot còn nguyên) |
| 6 | `test_cannot_change_role_group_in_use` | → 400 khi tiêu chí đã dùng |
| 7 | `test_archive_criteria` | Tắt rồi tạo phiếu mới → không có dòng đó; phiếu cũ vẫn còn |
| 8 | `test_delete_in_use_rejected` | → 409 `in_use`, bản ghi vẫn còn |
| 9 | `test_delete_unused_ok` | Xoá được tiêu chí chưa dùng |
| 10 | `test_save_params_ok` | Ghi `ir.config_parameter`, tính lại phiếu nháp cho ra grade mới |
| 11 | `test_save_params_invalid_order` | `gradeB > gradeA` → 400 |

Chạy:

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_reviews,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_reviews --stop-after-init --log-level=test
```

> Nhớ BR-010: nhân viên `official` trong test phải có `identification_id` đúng 12
> chữ số, mỗi người một giá trị.

## 9. Thứ tự triển khai

1. Test đỏ (§8) → controller `_can_configure` + 6 route → xanh → commit
2. `reviewsConfig.js` + 4 file UI → commit
3. Đăng ký màn trong `Shell.jsx` (`need: 'hrm'`) → commit
4. Cập nhật `docs/CONG_THUC_DANH_GIA.md` §6: nói rõ sửa ở đâu trên giao diện
5. Build SPA, kiểm thật trên Neon bằng `test_hrmanager@hocba.vn`

## 10. Câu hỏi mở

- Có cần ghi **nhật ký thay đổi cấu hình** (ai đổi trọng số, lúc nào) không? Bật
  `tracking=True` trên `weight` / `max_score` là rẻ, nhưng `hb.review.criteria`
  hiện chưa kế thừa `mail.thread`. Đề xuất: **chưa làm** đợt này.
