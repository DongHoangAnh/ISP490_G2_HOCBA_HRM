# Spec — Thông báo CV quá hạn xử lý (tuyển dụng) · v1.0

**Ngày**: 2026-08-03 · **Owner**: Việt (`hocba_recruitments`) · **Nhánh**: `Viet/Recruitment`

Nối tiếp [2026-07-23-recruitment-config-design.md](2026-07-23-recruitment-config-design.md)
(hạn xử lý từng bước) — spec đó mới dừng ở **badge đỏ trên card kanban**, tức là chỉ ai
đang mở màn Tuyển dụng mới thấy. Spec này biến nó thành **thông báo chủ động**.

## Bối cảnh

Hiện trạng: `hr.recruitment.stage.sla_days` cấu hình được, `hr.applicant._hb_sla_state()`
tính được `(số ngày ở bước, hạn, quá hạn)`, card kanban hiện badge `Quá hạn N ngày`.

Vấn đề: badge **thụ động**. Ứng viên kẹt ở bước "Lọc CV" 5 ngày mà HR không mở màn
Tuyển dụng thì không ai biết. Đúng ca cần nhắc thì lại là ca không ai nhìn.

## Phạm vi (đã chốt với user 2026-08-03)

1. Cron quét ứng viên **đã quá hạn** ở bước hiện tại → bắn thông báo chuông.
2. Người nhận: **HR tuyển dụng** + **Trưởng phòng** của phòng ban gắn với vị trí đó.
3. **1 thông báo / 1 ứng viên quá hạn** (bấm vào mở đúng ứng viên), chống trùng bằng
   `dedup_key`.
4. Bấm thông báo → nhảy về màn Tuyển dụng, tab **Danh sách CV**, mở drawer ứng viên.

**Ngoài phạm vi** (chốt là KHÔNG làm): nhắc trước khi tới hạn; gửi email; thông báo
tổng hợp kiểu digest; nhắc cho `hr.job.user_id` (nhiều vị trí đang bỏ trống field này).

## Thiết kế

### 1. `hocba_notify` — thêm nhóm thông báo

`hb.notification.CATEGORY_SEL` thêm `('recruitment', 'Tuyển dụng')`.

⚠️ Đây là **module dùng chung** (owner khác). Có tiền lệ: commit `dfc20df`
thêm `('service', 'Dịch vụ nhân sự')`. Chỉ thêm một dòng vào Selection, không đụng
logic → không ảnh hưởng module khác. Cần báo nhóm và bump version `hocba_notify`.

### 2. `hocba_recruitments/__manifest__.py`

- `depends`: thêm `'hocba_notify'`.
- `data`: thêm `'data/ir_cron_data.xml'`.
- `version`: `19.0.2.3.0` → `19.0.2.4.0`.

### 3. `hr.applicant` (extend) — `models/hr_applicant.py`

#### `_hb_overdue_recipients()` → `res.users`

```
HR   = res.users có group hr_recruitment.group_hr_recruitment_user
       (tìm bằng all_group_ids nên bắt luôn group_hr_recruitment_manager kế thừa),
       active = True
TP   = self.department_id.manager_id.user_id   (bỏ qua nếu trống/inactive)
→ trả HR | TP  (union, res.users tự khử trùng)
```

Ghi nhận lệch có chủ ý — bám đúng cách `hocba_service._notif_handlers()` đã làm:
user chỉ có `base.group_system` mà không thuộc nhóm tuyển dụng thì **không** nhận
chuông. Sysadmin không phải người xử lý nghiệp vụ.

#### `_cron_overdue_reminder()` — CRON-REC-001

```python
apps = self.sudo().search([
    ('active', '=', True),                    # loại ứng viên đã lưu trữ / bị từ chối
    ('stage_id.sla_days', '>', 0),            # bước không áp hạn thì bỏ
    ('stage_id.hired_stage', '=', False),     # bước đích không bao giờ quá hạn
    ('interview_result', '!=', 'fail'),       # Fail PV = đã dừng, giục vô nghĩa
])
for a in apps:
    days, sla, overdue = a._hb_sla_state()
    if not overdue:
        continue
    ...  _notify(...)
```

Bốn điều kiện loại trừ **khớp 1-1 với quy tắc hiển thị badge trên card kanban** —
cố ý, để "có badge" ⇔ "có thông báo", không có ca người dùng thấy badge mà không
được nhắc hoặc ngược lại.

**Về `interview_result != 'fail'` và giá trị NULL** — đã kiểm chứng trên source
Odoo 19 (`odoo/orm/fields.py:1298`), KHÔNG cần viết dạng `'|' ... '=', False`:

```
if (operator == 'in') == null_in_condition:
    # field not in {val} => field NOT IN vals OR field IS NULL
```

Odoo quy `!=` về `not in ['fail']`; danh sách giá trị không chứa `False` nên ORM
tự sinh `(interview_result NOT IN ('fail') OR interview_result IS NULL)`. Ứng viên
**chưa PV (NULL) vẫn được quét**. Bảng hành vi với 4 giá trị đang có trên dữ liệu:

| Kết quả PV | Nhắc? | Lý do |
|---|---|---|
| Chưa PV (NULL) | ✅ | đang chờ xử lý — nhóm cần giục nhất |
| Pass | ✅ | có thể kẹt ở bước Offer / Nhận việc |
| Tiềm năng (`potential`) | ✅ | chưa chốt, vẫn trong quy trình |
| Fail | ❌ | đã dừng |

Test BR-4b khoá hành vi NULL này lại như một regression guard — nếu bản Odoo sau
đổi cách sinh SQL thì test đỏ ngay chứ không âm thầm bỏ sót ứng viên.

#### Payload thông báo

| Trường | Giá trị |
|---|---|
| `category` | `recruitment` |
| `kind` | `recruitment_overdue` |
| `level` | `warning` |
| `title` | `CV quá hạn xử lý` |
| `body` | `<tên UV> · <vị trí> · bước "<tên bước>" · quá hạn N ngày` |
| `target_view` | `recruitment` |
| `target_tab` | `cv` |
| `target_ref` | `applicant.id` |
| `dedup_key` | `rec_overdue_<applicant.id>` |

`dedup_key` cho hành vi: mỗi ứng viên chỉ 1 dòng **chưa đọc**; cron chạy 30 ngày
liền vẫn 1 dòng. Đọc rồi mà chưa xử lý → hôm sau nhắc lại. Đây là cơ chế có sẵn
trong `hb.notification._notify()`, không phải viết mới.

Gọi qua `.sudo()` là đủ (không cần `with_user(SUPERUSER_ID)` như module Dịch vụ —
tuyển dụng không có yêu cầu ẩn danh nên `create_uid` không phải dữ liệu nhạy cảm).

### 4. `data/ir_cron_data.xml`

Cron `Tuyển dụng — nhắc CV quá hạn xử lý`, `interval_type=days`, `interval_number=1`,
`nextcall` 01:00 UTC (= 08:00 giờ VN), `model_id` = `hr.applicant`,
`code`: `model._cron_overdue_reminder()`. `noupdate="1"` để admin đổi giờ không bị
upgrade ghi đè.

### 5. SPA

- `frontend/src/app/App.jsx` — `openNotification()`: thêm `'recruitment'` vào nhánh
  đang `setFocus` (hiện chỉ có `timeoff` và `service`).
- `frontend/src/features/recruitment/Recruitment.jsx` — nhận prop `focus`; có
  `focus.targetTab === 'cv'` thì `select('cv')` và truyền `focus` xuống `CvList`.
- `frontend/src/features/recruitment/CvList.jsx` — `useEffect` theo `focus.nonce`:
  tìm row theo `focus.requestId`, thấy thì `setSel(row)` (mở drawer). Nếu row bị
  chip lọc hiện tại giấu đi thì **reset `cvFilter` về `all`** trước, không thì bấm
  thông báo xong màn hình trống trơn.

## Kiểm thử (TDD — `tests/test_overdue_notify.py`)

| # | Ca | Kỳ vọng |
|---|---|---|
| BR-1 | UV quá hạn, phòng có TP | HR **và** TP mỗi người đúng 1 dòng |
| BR-2 | Chạy cron 2 lần liên tiếp | vẫn 1 dòng / người (dedup) |
| BR-3 | Đánh dấu đã đọc rồi chạy lại | sinh dòng thứ 2 (nhắc lại) |
| BR-4a | UV `interview_result = fail` | **không** gửi |
| BR-4b | UV `interview_result` NULL (chưa PV), quá hạn | **có** gửi (regression guard §3) |
| BR-4c | UV `interview_result = potential` / `pass`, quá hạn | **có** gửi |
| BR-5 | Bước `sla_days = 0` / `hired_stage` | **không** gửi |
| BR-6 | Phòng ban không gán `manager_id` | chỉ HR nhận, cron không lỗi |
| BR-7 | UV `active = False` | **không** gửi |
| BR-8 | UV chưa quá hạn (đúng ngày hạn) | **không** gửi (`>` chứ không `>=`) |

Chạy: `-u hocba_recruitments,hocba_employees --test-tags /hocba_recruitments`,
cần thấy `0 failed, 0 error(s) of N tests` với N > 0.

## Rủi ro / lưu ý vận hành

- **Phòng Giảng viên (169 NV) chưa gán `manager_id`** (ghi nhận trong
  `docs/DB_TEST_DATA.md` khi deploy `hocba_service`) ⇒ vị trí thuộc phòng này chỉ
  HR nhận được nhắc. Không phải bug của spec này; muốn TP nhận thì gán TP cho phòng.
  User đã xác nhận (2026-08-03) sẽ **chỉnh dữ liệu phòng ban cho khớp sau** — code
  không chờ việc này, BR-6 đã khoá ca "phòng không có TP thì chỉ HR nhận, không lỗi".
- Deploy Neon: `-u hocba_notify,hocba_recruitments` qua **endpoint trực tiếp**
  (bỏ `-pooler`).
- Cron chỉ chạy khi có worker cron — stack Docker mặc định có.
- Đếm theo **ngày lịch** (kể cả T7/CN) vì `_hb_sla_state()` đã vậy. CV nhận chiều
  thứ Sáu, bước hạn 1 ngày → sáng thứ Hai đã báo quá hạn. Muốn đếm ngày làm việc
  là một thay đổi khác, không nằm trong spec này.
