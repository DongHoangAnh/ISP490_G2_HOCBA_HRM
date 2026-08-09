# Thiết kế: Khóa tài khoản + bộ lọc màn Tài khoản, và bước nhận việc "không ràng buộc thứ tự"

- **Ngày**: 2026-08-08
- **Module**: `hocba_employees` (model + migration) · `hocba_hrm` (controller + SPA)
- **Owner**: Tân — nhánh `feature/account-lock-independent-step`
- **Nguồn yêu cầu**:
  - Yêu cầu trực tiếp của nhóm: màn Tài khoản thiếu chức năng khóa và thiếu bộ lọc.
  - Họp khách hàng 2026-08-07 (bản ghi `UpdateISPEmployee.mp4`), đoạn 00:52–02:07.

## 1. Bối cảnh

### 1.1 Màn Tài khoản

`features/accounts/Accounts.jsx` hiện chỉ liệt kê nhân viên đã có tài khoản và
cho cấp lại mật khẩu. Cột Trạng thái đã hiển thị `Hoạt động / Khóa` từ
`res.users.active`, nhưng **không có cách nào đổi trạng thái đó từ SPA** — HR
phải vào backend Odoo archive user. Danh sách cũng không có bộ lọc, chỉ có ô
tìm kiếm chung ở thanh header.

Một chi tiết ảnh hưởng thiết kế: `_account_list` (`main.py:1594`) search
`hr.employee` **không** kèm `active_test=False`. Offboarding khi hoàn tất lại
archive cả hồ sơ NV lẫn user (`hocba_offboarding.py:182-185`). Hệ quả: người đã
nghỉ việc — nhóm có tài khoản bị khóa đông nhất — hiện không xuất hiện trên màn
này, nên bộ lọc "đang khóa" sẽ gần như rỗng nếu giữ nguyên phạm vi.

### 1.2 Quy trình nhận việc

Từ spec `2026-07-15-onboarding-config-design.md`, quy trình thử việc là chuỗi
bước động (`hb.onboarding.step`) chạy **tuần tự**: một bước xong mới mở bước kế
(`_advance` → `_next_waiting` → `_open`).

Template mặc định "Thử việc Nhân viên văn phòng"
(`data/hb_onboarding_template_data.xml`) xếp:

| # | Bước | Loại |
|---|---|---|
| 1 | Đánh giá tuần-2 | evaluation, hạn +14 ngày |
| 2 | **Cấp thiết bị làm việc** | task, `auto_action=grant_assets` |
| 3 | Đánh giá tháng-1 | evaluation, +30 ngày, `pass_completes` |
| 4 | Đánh giá tháng-2 | evaluation, +60 ngày, `is_extension`, `pass_completes` |

Vì tuần tự, thiết bị chỉ cấp được **sau khi** Đánh giá tuần-2 đạt. Khách phản
đối đúng điểm này:

> "Bỏ cái việc cấp thiết bị nó ra khỏi [luồng], nó tách ra nhưng đừng bắt buộc
> theo cái luồng kia… chị vẫn muốn nó có ở trong cái bảng này nhưng nó sẽ không
> bị ràng buộc, riêng cái việc cấp thiết bị nó sẽ là một luồng riêng." (01:09)
>
> "Còn tách cấp thiết bị thì cấp lúc nào cũng được nhé." (02:03)

Đồng thời khách khẳng định các bước **đánh giá vẫn phải tuần tự**:

> "Còn đánh giá thì rõ ràng là phải đánh giá 2 tuần thì mới được đánh giá 1
> tháng… đạt thì tiếp tục sang 1 tháng, 1 tháng đạt thì sang 2 tháng." (01:38)

## 2. Mục tiêu

1. HR/Admin khóa và mở khóa tài khoản đăng nhập ngay trên SPA; màn Tài khoản
   lọc được theo phòng ban và theo trạng thái đang dùng / đang khóa.
2. Một bước nhận việc có thể được đánh dấu "không ràng buộc thứ tự": nó hiện
   trong bảng quy trình nhưng làm được bất cứ lúc nào, không chặn và không bị
   chặn bởi chuỗi.

**Ngoài phạm vi** (các ý khác của cùng cuộc họp, sẽ có spec riêng): gom nhập
liệu đánh giá về màn Đánh giá, trang dashboard lịch sử cho từng nhân viên,
bảng vinh danh/leaderboard trên dashboard chung.

## 3. Quyết định thiết kế

| Quyết định | Phương án chọn | Vì sao không chọn phương án kia |
|---|---|---|
| Cơ chế khóa | Dùng `res.users.active` sẵn có | Thêm field khóa riêng tạo hai nguồn sự thật — offboarding đã ghi `active`, Odoo đã chặn đăng nhập theo `active` |
| Nơi lọc | Lọc client-side | Danh sách cỡ vài trăm dòng và API đã trả toàn bộ; thêm tham số server chỉ tăng round-trip |
| Phạm vi danh sách | Gồm cả NV đã nghỉ (archived) | Giữ nguyên thì bộ lọc "đang khóa" gần như rỗng (§1.1) |
| Bước độc lập | Cờ cấu hình trên bước mẫu | Hard-code riêng "Cấp thiết bị" đi ngược spec 2026-07-15 vốn đã bỏ 3 cổng cứng |
| Automation của bước độc lập | Ép `auto_action = 'none'` | Bước độc lập mở ngay từ đầu; để `grant_assets` thì nó tự cấp tài sản ngày đầu, mất quyền chọn thời điểm của HR |

## 4. Phần 1 — Khóa tài khoản + bộ lọc

### 4.1 Backend (`hocba_hrm/controllers/main.py`)

**`_account_set_active(env, emp_id, active)`** — hàm mới, đặt cạnh
`_account_reset`:

- `AccessError` nếu không phải HR (`_is_hr`, tức `hr.group_hr_user`) — cùng mức
  quyền với tạo tài khoản và cấp lại mật khẩu.
- `ValidationError` riêng cho "không tìm thấy nhân viên" và "chưa có tài
  khoản" — hai tình huống khác nhau, `_account_create` đã phân biệt.
- `ValidationError` nếu `emp.user_id == env.user` — không cho tự khóa chính
  mình (tự khóa xong là mất đường vào).
- `ValidationError` nếu tài khoản là quản trị hệ thống — kiểm `SUPERUSER_ID`
  **và** `base.group_system`, không chỉ uid 1/2: chặn mỗi admin gốc thì một HR
  thường vẫn khóa được mọi sysadmin khác. Thông điệp phải trung tính về hướng
  vì guard này chặn cả chiều mở khóa.
- `ValidationError` khi **mở khóa** nhân viên đã nghỉ (`hr.employee.active =
  False`). Offboarding archive cả hồ sơ lẫn user; mở lại user trong khi hồ sơ
  vẫn archived sẽ tạo "ma đăng nhập" — `env.user.employee_id` là computed
  search nên trả rỗng, và hàng chục chỗ trong `main.py` làm
  `emp = env.user.employee_id` sẽ âm thầm thấy "không có nhân viên". Chiều
  **khóa** vẫn phải cho phép (đó là lý do danh sách gồm NV đã nghỉ).
- Ghi `emp.user_id.sudo().write({'active': bool(active)})` và `message_post`
  lên hồ sơ NV — chỉ khi trạng thái thực sự đổi, để log không đầy dòng vô
  nghĩa. Body **phải nhúng `env.user.name`**: post chạy qua `emp.sudo()` nên
  Odoo gán tác giả là OdooBot, mà "ai khóa" đúng là thứ duy nhất log này cần
  ghi. Trả `_account_payload(emp)`.

**Route mới**, theo đúng khuôn 2 route account hiện có:

```
POST /hocba-hrm/api/employee/<int:emp_id>/account/active
body: {"active": true|false}
403 forbidden (AccessError) · 400 rejected (ValidationError, kèm rollback)
```

**`_account_list`** sửa 2 chỗ:

- `search` đổi sang `env['hr.employee'].sudo().with_context(active_test=False)`
  để gồm NV đã nghỉ.
- Mỗi row thêm `depId` (`e.department_id.id or 0` — giữ kiểu JSON luôn là số)
  cho bộ lọc phòng ban, và `empActive` (`e.active`) để SPA phân biệt "khóa vì
  nghỉ việc" với "khóa thủ công".
- Mỗi row thêm `isSystem` (`SUPERUSER_ID` hoặc `base.group_system`) — cùng
  điều kiện guard của `_account_set_active`, để FE ẩn nút thay vì bày ra chỉ
  để nhận lỗi.
- Vòng lặp KHÔNG được `search_count` từng nhân viên để tìm trưởng phòng: hàm đã
  search toàn bộ phòng ban ở cuối, kéo lên trước rồi tra `set(...ids)`. Danh
  sách giờ gồm cả NV đã nghỉ nên tập chỉ có phình ra, mà DB production là Neon
  cloud — mỗi count là một round-trip mạng.
- Danh mục `departments` giữ `active_test` mặc định (chỉ phòng ban còn hiệu
  lực). Hệ quả đã biết, chấp nhận được: NV đã nghỉ thuộc phòng ban sau đó bị
  archive sẽ có `depId` không khớp mục nào trong dropdown lọc — dòng vẫn hiện
  (có `depName`), chỉ là không lọc tới được. Đừng coi "mọi `depId` đều có trong
  `departments`" là bất biến.

### 4.2 Frontend

**`api/employees.js`**: `setAccountActive(empId, active)` →
`hbPost('/hocba-hrm/api/employee/${empId}/account/active', { active })`.

**`features/accounts/Accounts.jsx`**:

- Hai `<select>` trên đầu bảng: **Phòng ban** (đổ từ `departments` API đã trả
  sẵn, thêm mục "Tất cả phòng ban") và **Trạng thái** (Tất cả / Đang sử dụng /
  Đang khóa). Kết hợp AND với ô tìm kiếm sẵn có.
- Dòng đếm `{rows.length} người` giữ nguyên, phản ánh kết quả sau lọc.
- Cột Trạng thái: `active` → badge xanh "Hoạt động", ngược lại badge xám
  "Khóa"; thêm badge phụ `Đã nghỉ` khi `empActive === false`.
- Cột thao tác: nút **Khóa** (khi đang hoạt động) / **Mở khóa** (khi đang khóa)
  cạnh "Cấp lại MK", đi qua `ConfirmModal` — quy ước SPA, không dùng
  `window.confirm`. Thành công thì `load()` lại danh sách.
- Ẩn hẳn nút khi dòng đã khóa **và** `empActive === false` (NV đã nghỉ):
  backend từ chối mở khóa họ, nên bày nút chỉ để báo lỗi là bẫy người dùng.
- Dòng có `isSystem` không hiện nút nào, chỉ ghi nhãn "Quản trị hệ thống" —
  backend từ chối cả khóa lẫn mở khóa những tài khoản này.
- Ẩn luôn **Cấp lại MK** khi `empActive === false`. `_account_reset` không có
  guard `emp.active`, nên đặt lại mật khẩu cho người đã nghỉ chạy trót lọt
  nhưng vô nghĩa (tài khoản đang khóa, Odoo chặn đăng nhập) — một thao tác
  trông như có tác dụng mà không có.

### 4.3 Kiểm thử

Test Odoo trong `hocba_employees/tests` (hoặc test controller sẵn có của
`hocba_hrm`):

1. User thường gọi `_account_set_active` → `AccessError`.
2. HR khóa NV có tài khoản → `res.users.active` thành `False`; mở lại → `True`.
3. HR tự khóa tài khoản của chính mình → `ValidationError`.
4. NV chưa có tài khoản → `ValidationError`.
5. HR khóa tài khoản quản trị hệ thống → `ValidationError`.
6. HR khóa NV **đã archive** → thành công (đây là lý do danh sách gồm họ).
7. HR **mở khóa** NV đã archive → `ValidationError`.
8. `_account_list` trả cả NV đã archive, và mỗi row có `depId`, `empActive`.

Mỗi test dùng `assertRaisesRegex` chứ không `assertRaises` trần: bốn guard đều
ném `ValidationError`, `assertRaises` trần sẽ xanh cả khi guard SAI bắn.

## 5. Phần 2 — Bước "không ràng buộc thứ tự"

### 5.1 Model

Thêm `is_independent = fields.Boolean(string='Không ràng buộc thứ tự')` vào
**cả hai** model, vì bước trên NV là snapshot của bước mẫu:

- `hb.onboarding.template.step` (`hb_onboarding_template.py`)
- `hb.onboarding.step` (`hb_onboarding_step.py`)

Ràng buộc phải có ở **cả hai** model. Bước mẫu dùng `_check_step_flags`; bản
snapshot cần `_check_independent_flags` riêng, vì `ir.model.access` cho
`hr.group_hr_user` quyền ghi thẳng `hb.onboarding.step` — thiếu nó thì mọi bất
biến dưới đây vá được bằng một lệnh `write`.

Nội dung ràng buộc:

- `is_independent` chỉ dùng cho `step_type = 'task'` — khách khẳng định các bước
  đánh giá vẫn tuần tự.
- `is_independent` và `is_extension` loại trừ lẫn nhau.
- `is_independent` ⇒ `auto_action = 'none'` (§3).

### 5.2 Máy trạng thái (`hb_onboarding_step.py`)

Bước độc lập nằm **ngoài** chuỗi. Các điểm sửa:

| Chỗ | Hành vi mới |
|---|---|
| Gán quy trình (`_hocba_assign_onboarding`, `hr_employee.py:724`) | Dict `create` copy thêm `is_independent` từ bước mẫu. Chỗ mở bước đầu (`steps.sorted(...)[0]._open()`) đổi thành: mở **mọi** bước độc lập, cộng bước **không độc lập** đầu tiên |
| `_next_waiting()` | Bỏ qua bước `is_independent` → `_advance()` không bao giờ mở hay skip nó |
| `_advance()` | Thoát ngay nếu chính nó là bước độc lập — nếu không, hoàn thành bước độc lập sẽ bị hiểu nhầm là "hết chuỗi" và bắn chuông *Hoàn tất quy trình nhận việc* sai |
| `_advance()` khi hết chuỗi | Chỉ xét bước trong chuỗi; bước độc lập chưa xong không cản thông báo "hoàn tất quy trình" |
| `action_evaluate` kết quả `pass` + `pass_completes` | Chỉ skip bước `waiting` **không độc lập**; bước độc lập đang mở giữ nguyên `open` |
| `action_evaluate` kết quả `fail` | Tương tự — bước độc lập không bị chuyển `skipped` |

Nghĩa là NV có thể lên Chính thức trong khi bước "Cấp thiết bị làm việc" vẫn
mở, và HR hoàn thành nó sau. Đây là lựa chọn có ý thức, đúng ý "luồng riêng,
không bị ràng buộc" của khách.

Tiến độ `progress.done/total` vẫn đếm cả bước độc lập — đó là việc thật, cần
hiện trong "x/y bước".

### 5.3 Giao diện

- `features/onboarding/OnboardingConfig.jsx`: checkbox "Không ràng buộc thứ tự"
  ở nhánh `stepType === 'task'`, cạnh ô Automation; khi tick thì khóa/ẩn ô
  Automation cho khớp ràng buộc §5.1. Dòng tóm tắt bước thêm hậu tố `· ↗độc lập`.
- `features/employees/OnboardingStepsPanel.jsx`: badge `Không ràng buộc` trên
  bước độc lập để HR hiểu vì sao bấm được ngay dù chưa tới lượt.
- Payload bước (`_onb_emp_item` trong `main.py`) thêm `isIndependent`.

### 5.4 Dữ liệu sẵn có — migration

Seed template khai `noupdate="1"` nên nâng cấp module **không** đè bước cũ.
Cần migration `custom-addons/hocba_employees/migrations/19.0.4.0.0/post-migrate.py`
(kèm nâng `version` trong `__manifest__.py`):

1. Với template step xmlid `hocba_employees.onb_tpl_vp_step2` (Cấp thiết bị làm
   việc): đặt `is_independent = True`, `auto_action = 'none'`.
2. Với các `hb.onboarding.step` sinh từ bước mẫu đó trên NV đang chạy dở: đặt
   `is_independent = True`, `auto_action = 'none'`; bước nào đang `waiting` thì
   chuyển `open` để HR bấm được ngay.
3. Bước đã `done` / `skipped` giữ nguyên — là lịch sử.

Migration phải chịu được trường hợp xmlid không tồn tại (DB được seed khác đi)
— tra `ir.model.data` và thoát êm nếu không thấy, không raise.

Sửa luôn `data/hb_onboarding_template_data.xml` cho DB cài mới: bước 2 khai
`is_independent` `True` và bỏ `auto_action`.

### 5.5 Kiểm thử

1. Gán quy trình cho NV mới → bước "Cấp thiết bị" ở `open` đồng thời với
   "Đánh giá tuần-2" cũng `open`.
2. Hoàn thành bước độc lập → chuỗi **không** nhảy bước (Đánh giá tuần-2 vẫn là
   bước đang chờ).
3. Đánh giá tuần-2 `pass` → mở Đánh giá tháng-1, **không** đụng bước độc lập.
4. Đánh giá tháng-1 `pass` (`pass_completes`) → NV lên Chính thức, bước độc lập
   chưa làm vẫn `open` (không bị `skipped`).
5. Đánh giá `fail` → bước độc lập vẫn `open`.
6. Constraint: `is_independent` trên bước `evaluation` → `ValidationError`;
   `is_independent` + `auto_action='grant_assets'` → `ValidationError`.

Chạy theo lệnh trong `CLAUDE.md`:

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees,hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

## 6. Rủi ro

- **BR-010**: nhân viên `official` trong test phải có `identification_id` 12 chữ
  số duy nhất, nếu không `ValidationError` ngay `setUp`. Kịch bản test §5.5 mục 4
  đẩy NV lên Chính thức nên chắc chắn chạm luật này.
- **Neon**: migration là DDL + upgrade module, phải chạy qua endpoint trực tiếp
  (bỏ `-pooler` trong host), theo gotcha trong `CLAUDE.md`.
- **SPA build artifacts** (`static/spa/`) được commit — build lại từ source sau
  khi gộp, không merge tay bundle.
