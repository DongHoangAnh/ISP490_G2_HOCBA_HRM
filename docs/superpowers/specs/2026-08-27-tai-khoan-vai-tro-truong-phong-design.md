# Thiết kế — Tài khoản vai trò trưởng phòng (`x_is_role_account`)

- Ngày: 2026-08-27 · Owner: Vũ/Tân · Nhánh: `feature/dept-bo-loai-nhan-su`
- Nền tảng đã có: form "Thêm phòng ban" (`_dept_new_manager`), quy trình
  [Nhận việc bước động](2026-07-15-onboarding-config-design.md)

## 1. Vấn đề

Form "Thêm phòng ban" bắt buộc tạo kèm một trưởng phòng mới, và để làm được điều
đó nó tạo một bản ghi `hr.employee`. Lý do kỹ thuật: quyền "trưởng phòng" của cả
hệ suy ra từ `hr.department.manager_id`, mà field đó trỏ tới `hr.employee`.

Nhưng theo nghiệp vụ, tài khoản này **không phải nhân viên**. Nó là tài khoản thứ
hai của một người đã có hồ sơ nhân viên riêng, cấp thêm để người đó quản lý đúng
phòng mình — duyệt đơn, xem NV phòng mình. Ví dụ: A có tài khoản nhân viên để
chấm công bình thường, đồng thời A là trưởng phòng Marketing nên được cấp thêm
`test_truongphong@hocba.vn` chỉ để quản lý.

Hệ quả của việc coi nó là nhân viên:

| Hiện tượng | Nguồn |
|---|---|
| Lọt vào hàng đợi **Nhận việc** | `x_employment_status` default `'probation'` (hr_employee.py) + domain `api_onboarding` lọc đúng `'probation'` (main.py) |
| Đếm vào ô "Thử việc" của thống kê phòng ban | cùng field trạng thái |
| Nằm trong **danh sách Nhân viên** như người thật | `_emp_scope_domain` không phân biệt |
| Ghi một mốc "Nhận việc" vào lịch sử thăng tiến | `hr_employee.create()` gọi `_hocba_log_promotion('join', …)` |

Bằng chứng trong DB local: tài khoản `test123` → NV #33107 "Nguyen van a",
`probation`, mã tự sinh `HB.25352`, đang là trưởng phòng phòng "Test" — một tài
khoản vai trò đang nằm trong hàng đợi Nhận việc.

## 2. Phạm vi

**Trong phạm vi:** cờ `x_is_role_account` trên `hr.employee`; `_dept_new_manager`
bật cờ và không đặt trạng thái thử việc; loại tài khoản vai trò khỏi danh sách
Nhân viên, hàng đợi Nhận việc, thống kê phòng ban và "Hồ sơ của tôi"; migration
gỡ `manager_id` của mọi phòng ban; cập nhật `docs/DB_TEST_DATA.md`.

**Ngoài phạm vi:** module của thành viên khác (`hocba_payroll`, `hocba_timeoff`,
`hocba_attendance`, `hocba_reviews`) — xem mục 6; UI cho HR tự bật/tắt cờ; gộp
tài khoản vai trò với hồ sơ nhân viên của cùng một người; áp cờ cho tài khoản
giáo vụ (giáo vụ tạo ở màn Tài khoản, gắn với NV thật, không đi qua form này).

## 3. Quyết định thiết kế

| Câu hỏi | Chốt |
|---|---|
| Cơ chế loại trừ | Cờ tường minh `x_is_role_account`, lọc tại `_emp_scope_domain` |
| Vì sao không archive (`active=False`) | Trong hệ này `active=False` đã mang nghĩa "đã nghỉ việc" (offboarding dùng đúng cờ đó) → sẽ lẫn vào danh sách nhân sự đã nghỉ |
| Vì sao không bỏ `manager_id` | Là field core Odoo, `_managed_department_ids` và cây phòng ban con dựa vào nó; đổi là viết lại toàn bộ lớp phân quyền |
| Màn **Tài khoản** | **Vẫn liệt kê** tài khoản vai trò — đây là chỗ duy nhất HR đổi mật khẩu / khoá nó. `_account_list` không lọc cờ |
| "Hồ sơ của tôi" | **Không hiện** khi tài khoản vai trò đăng nhập — nó không có hồ sơ nhân sự để xem |
| Trạng thái làm việc | `_dept_new_manager` ghi `x_employment_status = False`, không để rơi vào default `'probation'` |
| Dữ liệu cũ | Gỡ `manager_id` của **toàn bộ** phòng ban; HR tạo lại tài khoản vai trò cho từng phòng qua form |
| Thứ tự triển khai | Local trước; lên Neon chỉ khi user báo nhóm và cho phép |

## 4. Backend

### 4.1 `hr.employee` (`hocba_employees`)

```python
x_is_role_account = fields.Boolean(
    string='Tài khoản vai trò', default=False, copy=False,
    help='Tài khoản quản lý (trưởng phòng) — không phải hồ sơ nhân sự. '
         'Không tham gia Nhận việc, danh sách nhân viên, thống kê.')
```

(Không `index=True` — gỡ theo góp ý review Task 1: field chỉ dùng trong domain
kết hợp với các điều kiện khác, không đứng một mình trong truy vấn lớn nào đủ
để cần index riêng.)

Nâng version `hocba_employees` `19.0.6.0.0` → `19.0.7.0.0`.

`create()` của `hr.employee` hiện luôn ghi mốc thăng tiến `'join'` và gọi
`_hocba_maybe_assign_onboarding()`. Cả hai phải **bỏ qua** khi `x_is_role_account`
bật — mốc "Nhận việc" cho một tài khoản không có nghĩa.

`x_employee_code`: **ngược với dự tính ban đầu**, tài khoản vai trò
**KHÔNG** được cấp mã (`hr_employee.py:523`, nhánh
`create()`: `if not vals.get('x_is_role_account') and not vals.get('x_employee_code')`)
— để tránh thủng dãy `HB.xx` mà HR đang dùng làm mã định danh liên tục cho
nhân sự thật. NV thật vẫn tự sinh mã từ sequence như trước.

### 4.2 `_dept_new_manager` (`hocba_hrm/controllers/main.py`)

Thêm vào `emp_vals`:

```python
'x_is_role_account': True,
'x_employment_status': False,
```

### 4.3 Các điểm lọc

| Hàm | Sửa |
|---|---|
| `_emp_scope_domain` | Thêm `('x_is_role_account', '=', False)` vào **mọi** nhánh trả về, kể cả nhánh HR/Admin trả `[]` |
| `api_onboarding` | Domain đã gọi `_emp_scope_domain` → tự khỏi. Xác nhận bằng test |
| Thống kê phòng ban (`dd['probation']`) | Dùng cùng domain → xác nhận bằng test |
| `_emp_in_scope` | **Không sửa gì cả** (main.py:1656-1666) — HR/Admin vẫn short-circuit `return True` ngay đầu hàm, trước khi hỏi `_emp_scope_domain`. Test đã chốt hành vi này (`_emp_in_scope` không cần biết `x_is_role_account`; việc loại tài khoản vai trò khỏi các MÀN HÌNH hoàn toàn nằm ở `_emp_scope_domain`) |
| Payload `/api/me` | Không trả khối "Hồ sơ của tôi" khi `user.employee_id.x_is_role_account` (qua helper `_has_self_profile`) |
| `_account_list` | **Không** sửa — giữ tài khoản vai trò trong màn Tài khoản |
| `_dept_list` (dropdown trưởng phòng màn Sửa) | **Không** sửa — vẫn cho chọn NV có sẵn, đúng như hiện tại |
| `api_employee_update` (main.py:~4646) | **Bổ sung ngoài kế hoạch ban đầu** — guard từ chối HTTP 400 (`error: 'rejected'`) kèm thông báo tiếng Việt khi ai đó POST sửa một bản ghi `x_is_role_account = True` qua form nhân viên. Lý do tồn tại: `_emp_in_scope` short-circuit `e == user.employee_id`, và `_cap_edit_emp` = `True` cho trưởng phòng ⇒ **chính tài khoản vai trò trưởng phòng, đăng nhập bình thường**, cũng vượt được `_can_edit_emp_record` trên bản ghi CỦA CHÍNH NÓ (với `employeeId` do chính FE trao qua `_role_payload`) — không cần vai HR/Postman. Không chặn, `EmployeeForm.jsx` gửi `status: statusKey \|\| 'probation'` sẽ ghi ngược `x_employment_status='probation'` lên một bản ghi đang cố tình để trạng thái rỗng, làm hỏng tính toàn vẹn dữ liệu (bản ghi mang cờ `x_is_role_account=True` nhưng lại có trạng thái thử việc) |

Cạm bẫy: `_emp_scope_domain` là hàm dùng chung cho ~15 điểm gọi, trong đó có
những chỗ ghép domain trên `employee_id.*` (bảng chấm công, đơn phép). Prefix
phải giữ đúng, không hard-code tên field.

## 5. Migration

Migration `hocba_employees/migrations/19.0.7.0.0/post-migrate.py`:

1. Gỡ `manager_id` của mọi `hr.department` (`UPDATE hr_department SET manager_id = NULL`).
2. Không đánh dấu `x_is_role_account` cho bất kỳ bản ghi cũ nào — không có
   heuristic nào phân biệt được "NV thật kiêm trưởng phòng" với "tài khoản vai
   trò" mà không có nguy cơ bắt nhầm một NV thật rồi làm họ biến mất khỏi lương
   và chấm công.

Sau migration, 7 phòng ban trong DB local trống trưởng phòng; HR tạo lại qua
form. Sáu người đang kiêm nhiệm (HB.01, HB.02, HB.06, HB.12, HB.17, HB.23) trở
về nhân viên thuần: vẫn chấm công, vẫn lương, chỉ mất quyền duyệt.

`test_truongphong@hocba.vn` mất vai trò trưởng phòng → **phải** cập nhật
`docs/DB_TEST_DATA.md` (bảng tài khoản + nhật ký), theo quy ước của nhóm.

## 6. Vì sao không sửa module của người khác

`hr.employee` được truy vấn rải rác trong 4 module thuộc sở hữu thành viên
khác — ranh giới không-đụng-`hocba_attendance` đã chốt từ 2026-08-06, và cùng
lý do đó áp dụng cho `hocba_payroll` (Hùng), `hocba_reviews` (Việt),
`hocba_timeoff` (NhậtAnh): **cố ý KHÔNG sửa code của các module này** trong
nhánh này. Đã đọc code từng module để xác nhận mức độ ảnh hưởng thật, **không
phải** giả định "không có dữ liệu nghiệp vụ để lọt vào" như bản nháp trước —
giả định đó sai ở 2/4 module:

| Module | Kết luận | Bằng chứng |
|---|---|---|
| `hocba_payroll` | ✅ An toàn | Mọi đường sinh phiếu bắt đầu từ `hb.contract`; danh sách chuyển khoản (`payroll_api.py`, quanh dòng 1334-1350) lặp `hr.employee` đang active nhưng có `if not slip: continue` — tài khoản vai trò không có hợp đồng nên không có `hb.payslip`, bị bỏ qua |
| `hocba_attendance` | ✅ An toàn | Không điểm nào `search` toàn bộ `hr.employee`; mọi truy vấn đi từ `hocba.attendance` / `hocba.work.shift` |
| `hocba_reviews` | ❌ **LỌT** | `models/hb_performance_review.py:248-249` (`role_group_domain`) — nhóm `'office'` CỐ Ý gộp NV chưa gán loại (`('x_employee_type_id', '=', False)`), mà tài khoản vai trò không có `x_employee_type_id` → rơi vào đó. `controllers/main.py:154-166` (`_employee_domain`) trả `[]` cho HR, ghép với domain trên ở dòng 267-268 → tài khoản vai trò hiện trong màn Đánh giá. Với trưởng phòng còn tệ hơn: `_dept_new_manager` gán `department_id` cho chính tài khoản vai trò, và `_managed_department_ids` (dùng trong `_employee_domain` nhánh trưởng phòng) chỉ lọc theo phòng ban → trưởng phòng thấy CHÍNH MÌNH trong danh sách cần đánh giá |
| `hocba_timeoff` | ❌ **LỌT** | `controllers/main.py:224-228` (`_dept_domain`) trả `[]` khi `scope['seeAll']`, rồi hàm bảng "Số dư phép toàn nhân viên" (dòng 338-341) `Employee.search(emp_domain)` không loại tài khoản vai trò → mỗi tài khoản vai trò thành một dòng "0 ngày phép" và cộng vào KPI `low_balance` (dòng 354-361). Cron nhắc nhở cuối tháng (`hb_timeoff_cron.py:43`) thì AN TOÀN — nó `search` toàn bộ `hr.employee` active nhưng chỉ hành động khi tìm thấy `hr.leave.allocation` đã `validate`, mà tài khoản vai trò không có allocation nào |

**Không tự sửa hai chỗ LỌT** — đó là code của Việt (reviews) và NhậtAnh
(timeoff), ngoài phạm vi nhánh này. Cờ `x_is_role_account` đã public trên
`hr.employee`, hai bạn tự thêm điều kiện khi rảnh. **Cần báo cả hai owner kèm
số dòng cụ thể ở trên** trước khi gộp nhánh này về `main`, để họ biết lỗ đang
tồn tại chứ không bị bất ngờ khi có người hỏi vì sao trưởng phòng thấy tên
mình trong danh sách cần đánh giá.

## 7. Test (TDD, `hocba_hrm/tests/test_role_account.py`)

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | Tạo phòng ban qua API → bản ghi trưởng phòng | `x_is_role_account is True`, `x_employment_status` rỗng |
| 2 | `api_onboarding` sau khi tạo | Tài khoản vai trò **không** trong `items` |
| 3 | Danh sách NV (HR/Admin xem) | Không chứa tài khoản vai trò |
| 4 | Thống kê phòng ban | Ô "Thử việc" không đếm tài khoản vai trò |
| 5 | `/api/accounts` | **Có** tài khoản vai trò, `role == 'truongphong'` |
| 6 | Tài khoản vai trò đăng nhập | Vẫn thấy & duyệt được NV phòng mình (quyền không suy giảm) |
| 7 | `/api/me` của tài khoản vai trò | Không có khối "Hồ sơ của tôi" |
| 8 | Không sinh mốc thăng tiến `'join'` | Lịch sử thăng tiến rỗng |

Chạy: `--test-tags /hocba_hrm:TestRoleAccount`, cần thấy `0 failed, 0 error(s)`
với N > 0.

## 8. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Lọc ở `_emp_scope_domain` làm tài khoản vai trò mất luôn quyền duyệt phòng mình | **Đã kiểm chứng khi soạn spec:** `_managed_department_ids` chỉ `search` trên `hr.department` (`manager_id`, `parent_id`), không đụng `hr.employee` → lọc danh sách NV không ảnh hưởng quyền. Test #6 chốt cứng |
| Migration gỡ `manager_id` làm cả nhóm mất quyền trên Neon | Chỉ chạy local; lên Neon khi user báo nhóm |
| Tài khoản vai trò "vô hình" — HR không sửa được | Vẫn ở màn Tài khoản (quyết định mục 3) |
| Bản ghi cũ như `test123` vẫn kẹt trong Nhận việc | Chấp nhận; dọn tay sau khi migration gỡ `manager_id` |
