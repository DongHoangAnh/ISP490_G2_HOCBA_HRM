# Thiết kế: Rút gọn F-006 Quản lý tài sản — "Ai đang giữ tài sản nào"

- **Ngày**: 2026-07-24
- **Module**: `hocba_employees` (+ `hocba_hrm` controller/SPA)
- **Owner**: Tân — nhánh `Tan/Employee`
- **Nguồn yêu cầu**: Góp ý của giảng viên hướng dẫn — quản lý tài sản chi tiết (thu hồi + bàn giao) quá lằng nhằng so với phạm vi đồ án; chỉ cần biết **ai đang giữ tài sản nào**.

## 1. Bối cảnh & mục tiêu

Hiện tại F-006 cài đặt vòng đời tài sản đầy đủ: mỗi bản ghi có trạng thái
`Đang giữ / Đã thu hồi / Đã chuyển giao`, có ngày thu hồi, người nhận chuyển giao,
ghi chú tình trạng khi thu, không cho xoá bản ghi, và chuyển giao tự sinh bản ghi
mới cho người nhận (BR-050). Vòng đời này còn khoá 2 nghiệp vụ khác:
hoàn tất đơn nghỉ việc và lưu trữ hồ sơ nhân viên đều bị chặn khi còn tài sản
chưa thu hồi.

**Mục tiêu**: hạ F-006 xuống mức "sổ tay cấp phát" — một danh sách phẳng
*nhân viên ↔ tài sản đang giữ*. Thu hồi và bàn giao không còn là nghiệp vụ có
trạng thái; chúng trở thành thao tác sửa danh sách.

**Ngoài phạm vi**: kho tài sản (tồn kho, giá trị, khấu hao), lịch sử luân chuyển,
biên bản bàn giao. Đây là quyết định có ý thức, không phải thiếu sót.

## 2. Đánh đổi đã chấp nhận

Bỏ trạng thái đồng nghĩa với **mất lịch sử**: hệ thống không trả lời được
"laptop LAP-007 trước đây ai giữ". Người dùng đã cân nhắc và chấp nhận —
với phạm vi đồ án, thông tin hiện trạng là đủ.

## 3. Thiết kế

### 3.1 Model `hr.employee.asset`

Giữ 5 trường: `employee_id`, `asset_type_id`, `asset_code`, `grant_date`,
`condition_in`.

Bỏ:

| Thành phần bỏ | Lý do |
|---|---|
| `state` (assigned/returned/transferred) | Không còn vòng đời |
| `return_date`, `condition_out_note` | Thuộc nghiệp vụ thu hồi |
| `transferred_to` | Thuộc nghiệp vụ bàn giao |
| `action_mark_returned()`, `action_mark_transferred()` | Nghiệp vụ đã bỏ (BR-050 gỡ) |
| `unlink()` chặn xoá | Xoá dòng chính là cách biểu diễn "đã thu hồi" |
| `_check_dates()` ràng buộc `grant_date >= x_eval_2w_date` | Luật gây tắc, không phục vụ mục tiêu "biết ai giữ gì" |

Đổi: ràng buộc mã tài sản duy nhất chuyển từ `@api.constrains` (chỉ xét dòng
`assigned`) sang **SQL constraint unique toàn bảng** trên `asset_code`.
Đơn giản hơn và vẫn chống nhập trùng.

Giữ nguyên: `hocba.asset.type` (kể cả cờ `x_is_default`) và bước onboarding
`auto_action = 'grant_assets'` — tự cấp tài sản mặc định cho nhân viên mới vẫn
hữu ích, đã có test, không thuộc phần "lằng nhằng".

Ngữ nghĩa mới:

- **Thu hồi** = xoá dòng của người đang giữ.
- **Bàn giao** = xoá dòng người cũ, thêm dòng cho người mới (cùng mã tài sản).

### 3.2 Migration `hocba_employees` 19.0.2.0.0 → 19.0.3.0.0

Bắt buộc có migration **pre-** vì Odoo không tự dọn dữ liệu khi bỏ trường:
các dòng đang ở trạng thái `returned` / `transferred` phải bị **xoá**. Nếu để
lại, sau khi cột `state` biến mất chúng sẽ được hiểu là "đang giữ" — vừa sai dữ
liệu, vừa đụng ràng buộc unique `asset_code` mới (một mã có thể có nhiều dòng
lịch sử).

```sql
DELETE FROM hr_employee_asset WHERE state IN ('returned', 'transferred');
```

Sau bước xoá, nếu vẫn còn `asset_code` trùng (dữ liệu bẩn có sẵn) thì giữ dòng
`id` nhỏ nhất, xoá phần còn lại, và ghi log cảnh báo — để việc tạo unique index
không làm hỏng lần upgrade.

Các cột cũ (`state`, `return_date`, ...) để Odoo bỏ khỏi ORM; cột vật lý còn lại
trong bảng là vô hại, không cần drop tay.

### 3.3 Gỡ 2 chỗ chặn nghiệp vụ

- `hocba.offboarding.action_done()` — bỏ `raise ValidationError` khi còn tài sản.
  Trường `asset_pending_count` đổi tên thành `asset_count`, đếm **toàn bộ** dòng
  tài sản của nhân viên, chỉ dùng để hiển thị.
- `hr.employee.write()` — bỏ hẳn đoạn chặn `active = False` khi còn tài sản.

Bù lại bằng **thông tin**, không phải bằng khoá: đơn nghỉ việc hiển thị
"Đang giữ N tài sản: LAP-007, KEY-12" để HR biết mà đòi.

### 3.4 ACL

`ir.model.access.csv`: bật quyền `unlink` cho `hr.employee.asset` ở cả
`hr.group_hr_user` và `hr.group_hr_manager` (hiện đang là 0) — vì xoá dòng nay là
thao tác nghiệp vụ hợp lệ.

### 3.5 API (`hocba_hrm/controllers/main.py`)

| Route | Thay đổi |
|---|---|
| `POST /api/employee/<emp_id>/asset` | Giữ. `ASSET_FIELDS` bỏ các khoá thuộc vòng đời |
| `POST /api/asset/<asset_id>/return` | **Xoá** |
| `POST /api/asset/<asset_id>/transfer` | **Xoá** |
| `POST /api/asset/<asset_id>/delete` | **Mới** — gỡ dòng tài sản; kiểm quyền bằng `_can_edit_emp_record` như 2 route cũ; trả `_detail_response(employee)` |

Payload chi tiết nhân viên: `assets[]` bỏ `state`, `stateLabel`, `returnDate`;
còn `id`, `type`, `code`, `grantDate`, `conditionLabel`.
`formMeta` bỏ khoá `asset_state`; giữ `assetTypes`, `assetCondition`.
Danh sách nghỉ việc: `assetPending` đổi thành `assetCount` + thêm `assetCodes`
(chuỗi mã, để hiển thị cảnh báo).

### 3.6 SPA

- `AssetForm.jsx`: bỏ chế độ `return` và `transfer`; còn một form "Cấp phát tài sản"
  với 4 ô (loại, mã, ngày cấp, tình trạng). Bỏ luôn phần tải danh sách nhân viên
  để chọn người nhận.
- `EmployeeDrawer.jsx > AssetsTab`: bảng 4 cột (Mã · Loại · Ngày cấp · Tình trạng),
  bỏ 2 cột Trạng thái/Ngày thu hồi; 2 nút "Thu hồi"/"Chuyển" thay bằng một nút
  **Gỡ** có hộp xác nhận ("Gỡ LAP-007 khỏi hồ sơ Nguyễn Văn A?").
- `api/employees.js`: bỏ `returnAsset`, `transferAsset`; thêm `deleteAsset`.
- `Offboarding.jsx`: bỏ biến `doneBlocked` và điều kiện vô hiệu hoá nút Hoàn tất;
  badge "N chưa thu" đổi thành badge thông tin "Đang giữ N" kèm tooltip liệt kê mã.

### 3.7 Kiểm thử

| Test | Xử lý |
|---|---|
| `test_offboarding.test_done_blocked_when_asset_assigned` | Đảo ngược: hoàn tất đơn nghỉ việc **thành công** dù nhân viên còn tài sản |
| `test_onboarding_step` (grant_assets) | Giữ nguyên; bỏ mọi assert vào `state` |
| Mới: unique `asset_code` | Cấp 2 dòng cùng mã cho 2 nhân viên → lỗi |
| Mới: xoá dòng tài sản | HR xoá được bản ghi (trước đây `unlink` raise) |
| Mới: lưu trữ hồ sơ | `write({'active': False})` thành công khi còn tài sản |

Chạy: `-u hocba_employees --test-tags /hocba_employees` (Docker local, có
`MSYS_NO_PATHCONV=1`).

### 3.8 Tài liệu

- `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md`: viết lại mục F-006, gỡ BR-050
  (chuyển giao) và ghi rõ lý do rút gọn theo góp ý giảng viên.
- `docs/DB_TEST_DATA.md`: thêm dòng nhật ký khi upgrade module lên Neon.

## 4. Thứ tự triển khai

Backend trước, UI sau (theo quy ước dự án):

1. Model + ACL + migration (đỏ → xanh theo test).
2. Sửa/bổ sung test, chạy xanh.
3. Controller API.
4. SPA + build.
5. Cập nhật tài liệu; upgrade Neon bằng endpoint trực tiếp (không dùng `-pooler`).

## 5. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Dữ liệu lịch sử bị xoá không lấy lại được | Chỉ chạy trên DB đồ án; nêu rõ trong nhật ký DB |
| Trùng `asset_code` sẵn có làm hỏng upgrade | Migration khử trùng trước khi tạo unique index |
| Bundle SPA (`static/spa/`) xung đột khi merge | Build lại từ source đã gộp, không merge tay |
