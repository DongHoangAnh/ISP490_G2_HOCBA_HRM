# Badge "việc cần xử lý" trên menu — Nhận việc & Nghỉ việc

- Ngày: 2026-08-12
- Owner: Tân (module `hocba_employees` + `hocba_hrm`)
- Trạng thái: đã duyệt, chờ implement

## 1. Bối cảnh

Menu **Nghỉ phép** đã có badge số đơn chờ duyệt cạnh tên mục
(`Sidebar` đọc `badges[viewId]`, nạp từ `GET /api/timeoff/pending-count`).
Khách xem demo và yêu cầu: các module do nhóm mình đảm nhiệm, mục nào có
"việc cần xử lý" thì làm badge giống vậy.

Trong phạm vi mình phụ trách (`hocba_employees` + `hocba_hrm`) có 2 hàng đợi
thực sự cần người hành động:

| Mục menu | View id | Hàng đợi |
|---|---|---|
| Nhận việc | `onboarding` | `hb.onboarding.step` đang chờ xử lý |
| Nghỉ việc | `offboarding` | `hocba.offboarding` đang chờ duyệt/hoàn tất |

**Ngoài phạm vi:** Yêu cầu dịch vụ (`hocba_service`) không thuộc nhóm mình.
Chấm công / Nghỉ phép / Bảng lương / Đánh giá / Tuyển dụng là module của
thành viên khác — không đụng.

## 2. Nguyên tắc

1. **Badge đếm đúng thứ người đang đăng nhập bấm được**, không phải tồn đọng
   toàn hệ thống. Số trên menu phải khớp số bản ghi có nút hành động trên
   chính màn danh sách — hai chỗ lệch nhau là bug.
2. **Route riêng, chỉ `search_count`.** Badge được gọi ở mọi màn nên không
   được dựng payload danh sách.
3. **Không quyền → `200 {count: 0}`**, không 403. SPA khỏi phải bắt lỗi cho
   một chi tiết trang trí.

(3 điểm trên bê nguyên từ `/api/timeoff/pending-count` — khuôn đã chạy thật.)

## 3. Backend

### 3.1 `GET /hocba-hrm/api/onboarding/pending-count`

Đếm `hb.onboarding.step` có `state = 'open'`, phạm vi bám sát `_onb_can_act`:

| Vai trò | Đếm |
|---|---|
| Admin / HR Manager | tất cả bước `open` |
| Trưởng phòng | bước của NV thuộc phòng mình (gồm phòng con) |
| Quản lý trực tiếp | bước của NV có `parent_id` là mình |
| Giáo vụ | chỉ bước `step_type = 'task'` của NV là giáo viên |
| HR officer / NV thường | 0 |

Giáo vụ và trưởng phòng có thể trùng vai — hợp bằng domain `OR`, đếm một
lần, không cộng dồn thành số ảo.

Trả `{'canAct': bool, 'count': int}`.

### 3.2 `GET /hocba-hrm/api/offboarding/pending-count`

Đếm `hocba.offboarding` mà user có nút bấm, khớp `_offb_json`:

| Trạng thái | Ai đếm được | Nút tương ứng |
|---|---|---|
| `submitted` | NV thuộc `_offb_managed_employee_ids` | Duyệt (quản lý) |
| `mgr_approved` | HR Manager | HR duyệt |
| `hr_approved` | HR Manager | Hoàn tất |

`hr_approved` **được tính** vì vẫn là việc HR phải bấm mới xong.

Trả `{'canAct': bool, 'count': int}`.

### 3.3 Vị trí code

Đặt mỗi route cạnh nhóm route cùng miền trong
`hocba_hrm/controllers/main.py` (onboarding ~2950-3170, offboarding
~3350-3450), không dồn xuống cuối file — file đã hơn 4500 dòng.

## 4. Frontend

- `App.jsx`: thay `setTimeoffBadge` riêng lẻ bằng helper
  `setBadge(key)(n)`; gọi 2 route mới song song với `fetchPendingCount`
  sẵn có sau khi biết vai trò.
- `Onboarding` và `Offboarding` nhận thêm prop `onQueueChanged()` — gọi sau
  mỗi thao tác duyệt để App **hỏi lại server**, không phải F5.
  Khác `TimeOff.onPendingCount(n)` (nhận thẳng số): phạm vi đếm ở đây là
  quyền duyệt phía server (phòng ban con, cấp dưới `parent_id`, giáo vụ),
  tự trừ ở client chắc chắn lệch.
- API client: thêm `fetchOnboardingPendingCount`, `fetchOffboardingPendingCount`.
- **`Shell.jsx` không sửa.** `Sidebar` đã đọc `badges[it.id]`, mà key trùng
  luôn với view id `onboarding` / `offboarding`.

## 5. Test

`custom-addons/hocba_hrm/tests/test_nav_badges.py` — viết đỏ trước:

1. HR Manager: đếm đủ mọi bước `open` / mọi đơn ở 3 trạng thái actionable.
2. Trưởng phòng: chỉ đếm phòng mình, không thấy phòng khác.
3. Giáo vụ: chỉ đếm bước `task` của giáo viên; bước `gate`/`eval` không tính.
4. NV thường: cả 2 route trả `count = 0`, HTTP 200 (không 403).
5. **Không lệch:** với cùng một user, `count` bằng đúng số bản ghi có
   `canMgrApprove|canHrApprove|canDone` trên `/api/offboarding/list`.

Lệnh chạy:

```
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

## 6. Rủi ro

- **Giá phải trả cho mỗi lần tải app:** thêm 2 request. Đều là `search_count`
  có index trên `state`, chấp nhận được; nếu sau này thêm badge nữa thì gộp
  thành một route `/api/nav/badges` trả cả cụm.
- **Lệch số** giữa badge và màn danh sách nếu sau này ai đó đổi điều kiện
  `can*` mà quên route đếm. Test mục 5 chính là chốt chặn cho việc đó.
