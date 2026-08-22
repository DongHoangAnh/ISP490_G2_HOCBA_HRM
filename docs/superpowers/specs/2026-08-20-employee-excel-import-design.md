# Nhập hồ sơ nhân viên từ Excel (màn Nhân viên)

- Ngày: 2026-08-20
- Owner: Việt (nhánh `Viet/Recruitment`) — chạm `hocba_hrm` + 1 sửa nhỏ ở `hocba_employees`
- Trạng thái: đã duyệt thiết kế, chờ viết plan

## 1. Bối cảnh

Trung tâm đã có sẵn danh sách nhân sự trong file Excel nghiệp vụ
(`Học bá education.xlsx`, sheet **2.1. Quản lý nhân sự** — 168 dòng, 53 cột).
Nhập tay từng hồ sơ qua form là không khả thi, nên cần một đường nhập hàng loạt
ngay trên màn Nhân viên.

Đã có khuôn mẫu chạy thật để bám: **Nhập lịch làm việc từ Excel** của module Nghỉ
phép (`hocba_timeoff/controllers/workday_xlsx.py` + 2 route `workdays/template`,
`workdays/import`) — tách parser thành hàm thuần để test không cần dựng HTTP, và
**đọc-kiểm tách rời khỏi ghi** (upload chỉ trả preview, người dùng bấm Lưu mới ghi).

### 1.1 Số liệu khảo sát dữ liệu thật (2026-08-20)

Đối chiếu sheet 2.1 + 2.3 với model hiện tại:

| Hạng mục | Kết quả |
|---|---|
| Số dòng có mã nhân sự | 168, **không trùng mã** |
| Họ tên | đủ 100% |
| Danh mục **Hình thức** (Offline/Online) | trùng khít `x_work_form` |
| Danh mục **Loại vị trí** (Quản lý/Nhân viên/CTV) | trùng khít `x_position_type` |
| Cột **Tình trạng** | 31 Chính thức · 56 Nghỉ việc · 24 Thử việc · 2 TTS · 2 Parttime · **52 ghi "Online"** (giá trị của cột Hình thức lọt sang) · 1 trống |
| CCCD | 12 dòng trống, 1 dòng sai định dạng 12 số |
| MST TNCN (sheet 2.3) | **0/30 dòng** có dữ liệu |
| Số sổ BHXH (sheet 2.3) | 18/30 dòng |
| Số NV không có dòng nào ở sheet 2.3 | **138/168** |
| Chức danh | 48 giá trị khác nhau (danh mục hệ thống chỉ ~16) |
| Phòng ban | 6 giá trị, lệch cách viết so với danh mục |
| Email | 167 dòng có, trong đó 7 dòng trùng nhau |

Hai kết luận quyết định thiết kế:

1. **BR-010 chặn toàn bộ.** NV `official` bắt buộc CCCD + MST TNCN + số sổ BHXH
   (`_check_official_required_fields`). Không ai trong file có MST ⇒ nhập thẳng thì
   31 dòng "Chính thức" hỏng hết.
2. **Cột Tình trạng bẩn.** 52 dòng ghi "Online". Nếu để rơi về mặc định của model
   (`probation`) thì 52 người bị `_hocba_maybe_assign_onboarding()` gán quy trình
   nhận việc — sai nghiêm trọng với nhân sự cũ.

## 2. Quyết định đã chốt với người dùng

| # | Câu hỏi | Chốt |
|---|---|---|
| Q1 | Nguồn file | **File có sẵn của trung tâm**, hệ thống tự dò cột theo tên tiêu đề (không bắt dùng file mẫu) |
| Q2 | NV "Chính thức" thiếu MST/BHXH | **Cho nhập**, giữ nguyên trạng thái thật, hồ sơ thiếu được đánh dấu "cần hoàn thiện" |
| Q3 | Phòng ban / chức danh không khớp danh mục | Phòng ban: bảng bí danh, không khớp → lỗi dòng. Chức danh: khớp thì gắn `job_id`, không khớp thì **giữ nguyên văn vào `job_title`** |
| Q4 | Dòng đã có trong hệ thống | **Bỏ qua**, chỉ nhập dòng mới (import lại nhiều lần không sinh bản sao) |
| Q5 | Nhánh làm việc | `Viet/Recruitment` (không tách nhánh riêng) |

## 3. Nguyên tắc

1. **Đọc-kiểm và ghi là hai lần gọi API.** Upload chỉ trả preview; không ghi một
   byte nào cho tới khi người dùng bấm Nhập. (Bê từ luồng `workdays/import`.)
2. **Không đoán thay người dùng ở chỗ mơ hồ.** Giá trị danh mục lạ (Tình trạng,
   Phòng ban) → báo lỗi dòng kèm số dòng Excel, HR sửa file. Chỉ ô *thông tin*
   (CCCD, email, SĐT) sai định dạng mới được bỏ trống kèm cảnh báo.
3. **Ghi trọn gói.** Một transaction; lỗi bất kỳ → rollback sạch, không nhập nửa vời.
4. **Parser là hàm thuần.** Nhận `bytes` + dict danh mục, trả dữ liệu; không đụng
   `request`, không đụng ORM ⇒ test đủ nhánh mà không dựng HTTP.

## 4. Luồng người dùng

Nút **"Nhập từ Excel"** trên toolbar màn Nhân viên (cạnh nút thêm NV), chỉ hiện với
HR Manager / Admin. Modal 2 bước:

**Bước 1 — Chọn file.** Kéo/thả hoặc chọn `.xlsx` (≤ 10 MB). File nhiều sheet → hiện
ô chọn sheet, mặc định chọn sheet đầu tiên dò được header hợp lệ.

**Bước 2 — Xem trước.** Bảng chia 3 nhóm, mỗi dòng kèm **số dòng trong file Excel**:

| Nhóm | Nội dung |
|---|---|
| Sẽ nhập | họ tên · mã NV · phòng ban · chức danh · tình trạng, kèm chip cảnh báo ô bị bỏ trống |
| Bỏ qua vì đã có | mã NV / CCCD đã tồn tại trong hệ thống |
| Lỗi phải sửa | thiếu họ tên · tình trạng lạ · phòng ban không khớp |

Dưới bảng: dòng "Các cột trong file không nhận diện được: …" để HR biết mình mất gì,
và cảnh báo tổng "N hồ sơ sẽ thiếu MST/BHXH — cần hoàn thiện sau".

Nút **Nhập** bị khoá khi nhóm "Sẽ nhập" rỗng. Vài dòng lỗi **không** chặn phần còn
lại: SPA chỉ gửi lên nhóm "Sẽ nhập", các dòng lỗi bị loại từ bước preview và HR sửa
file rồi nhập bổ sung sau (đợt sau không sinh bản sao nhờ luật bỏ qua ở Q4). Lỗi *cả
file* ở mục 6.3 thì không có gì để nhập.

Cần phân biệt với mục 6.2: rollback trọn gói ở đó nói về lỗi phát sinh **trong lúc
ghi** (ORM từ chối, ràng buộc chưa lường trước) — lúc đó cả mẻ bị huỷ để không nhập
nửa vời.

## 5. Kiến trúc & file

| File | Vai trò |
|---|---|
| `custom-addons/hocba_hrm/controllers/employee_xlsx.py` *(mới)* | Parser thuần hàm: `parse_employees_xlsx(content, sheet, catalogs, existing) → {rows, errors, unknownCols}` |
| `custom-addons/hocba_hrm/controllers/employee_import.py` *(mới)* | 2 route REST |
| `custom-addons/hocba_hrm/controllers/__init__.py` | đăng ký 2 file trên |
| `custom-addons/hocba_employees/models/hr_employee.py` | thêm cửa thoát context cho BR-010 (mục 8) |
| `frontend/src/features/employees/ImportEmployeesModal.jsx` *(mới)* | modal 2 bước |
| `frontend/src/features/employees/Employees.jsx` | thêm nút |
| `frontend/src/api/employees.js` | 2 hàm gọi API |
| `custom-addons/hocba_hrm/tests/test_employee_import.py` *(mới)* | test parser + controller |

Route đặt ở file riêng, **không** nhét thêm vào `hocba_hrm/controllers/main.py`
(file đó đã hơn 4.400 dòng).

## 6. Backend

### 6.1 `POST /hocba-hrm/api/employees/import/preview`

`type="http"`, `auth="user"`, `csrf=False`, nhận `multipart/form-data`:
`file` (bắt buộc), `sheet` (tuỳ chọn).

Quyền: **HR Manager hoặc Admin**. Khác → `403 {"error":"forbidden"}`.
(Giáo vụ / Trưởng phòng bị loại: phạm vi của họ hẹp, nhập cả file sẽ đẻ hồ sơ ngoài
phạm vi rồi bị `_emp_in_scope` chặn giữa chừng.)

**Không ghi bất cứ gì.** Trả:

```json
{
  "sheets": ["2.1. Quản lý nhân sự", "..."],
  "sheet": "2.1. Quản lý nhân sự",
  "headerRow": 1,
  "rows":    [{"excelRow": 2, "name": "...", "code": "HB.01", "depName": "Marketing",
               "jobName": "...", "status": "official", "warnings": ["CCCD không đủ 12 số — để trống"],
               "missingOfficial": ["MST TNCN"], "values": { ... }}],
  "skipped": [{"excelRow": 9, "code": "HB.08", "reason": "code_exists"}],
  "errors":  [{"excelRow": 14, "code": "bad_status", "message": "Tình trạng \"Online\" không thuộc danh mục."}],
  "unknownCols": ["Tài khoản Lark", "Màn máy tính", "..."],
  "summary": {"total": 168, "ok": 137, "skipped": 24, "error": 7, "needCompletion": 31}
}
```

### 6.2 `POST /hocba-hrm/api/employees/import/commit`

`type="http"`, `auth="user"`, `csrf=False`, body JSON `{"rows": [...]}` — chính các
phần tử `rows` mà preview trả về (SPA gửi lại nguyên vẹn).

Cùng kiểm quyền như 6.1. Xử lý:

1. Kiểm lại toàn bộ ở server (**không tin payload client**): danh mục hợp lệ, mã NV /
   CCCD chưa tồn tại, họ tên không rỗng. Dòng nào hỏng → `400` kèm số dòng.
2. Tạo bản ghi với context `hocba_no_onb_assign=True` (cờ **đã có sẵn** trong model)
   + `hocba_legacy_import=True` (cờ mới, mục 8).
3. `hr.employee.create()` → ghi tiếp `hr.version` cho `identification_id`.
4. Lỗi bất kỳ → `request.env.cr.rollback()`, trả `400 {"error":"rejected", "excelRow": n, "message": ...}`.
5. Thành công → **không bắn thông báo**. Hồ sơ thiếu giấy tờ được đánh dấu
   thường trực (mục 8b) chứ không qua chuông — chuông trôi đi thì HR không tìm
   lại được ai còn thiếu. *(Đổi 2026-08-21 theo yêu cầu: chuyển sang badge.)*

Trả `{"created": 137, "needCompletion": 31, "employeeIds": [...]}`.

### 6.3 Mã lỗi

| Phạm vi | `error` | Khi nào |
|---|---|---|
| Cả file | `no_file` | không đính kèm file |
| Cả file | `bad_ext` | không phải `.xlsx` |
| Cả file | `too_large` | > 10 MB |
| Cả file | `no_header` | không dò được dòng header trong 10 dòng đầu |
| Cả file | `no_name_col` | không tìm thấy cột Họ và tên |
| Dòng | `empty_name` | thiếu họ tên |
| Dòng | `bad_status` | Tình trạng không thuộc danh mục |
| Dòng | `bad_department` | Phòng ban không khớp danh mục cả sau khi tra bí danh |
| Dòng (bỏ qua) | `code_exists` / `cccd_exists` | đã có hồ sơ |

## 7. Dò cột & chuẩn hoá

### 7.1 Tìm header

Quét 10 dòng đầu; dòng nào có **≥ 3 ô** khớp bảng bí danh thì là header, dữ liệu bắt
đầu từ dòng kế. Không thấy → `no_header`.

Chuẩn hoá tên cột trước khi tra: bỏ dấu tiếng Việt, hạ hoa-thường, gộp khoảng trắng,
bỏ ký tự `_` và đuôi `text`. Nhờ vậy "Họ và tên", "Họ tên nhân sự_text",
"Họ và tên nhân viên" cùng trúng một khoá.

### 7.2 Bảng bí danh cột (22 cột nhận diện)

| Khoá | Field | Bí danh |
|---|---|---|
| `code` | `x_employee_code` | mã nhân sự · mã nhân viên · mã nv |
| `name` | `name` | họ và tên · họ tên · họ tên nhân sự · họ và tên nhân viên |
| `status` | `x_employment_status` | tình trạng · trạng thái |
| `workForm` | `x_work_form` | hình thức · hình thức làm việc |
| `posType` | `x_position_type` | loại vị trí |
| `dep` | `department_id` | phòng ban · phòng |
| `job` | `job_id` / `job_title` | chức danh · vị trí |
| `probStart` | `x_probation_start` | ngày thử việc |
| `bday` | `birthday` | ngày tháng năm sinh · ngày sinh |
| `cccd` | `identification_id` *(hr.version)* | số căn cước công dân · cccd · số cccd |
| `idIssue` | `x_id_date_issue` | ngày cấp |
| `idPlace` | `x_id_place_issue` | nơi cấp |
| `phone` | `work_phone` | số điện thoại · sđt |
| `email` | `work_email` | email công ty *(ưu tiên)* · email cá nhân · email |
| `bankAccountNo` | `x_bank_account_no` | số tài khoản |
| `bankCode` | `x_bank_code` | ngân hàng |
| `pit` | `x_pit_code` | mã số thuế tncn · mst |
| `si` | `x_social_insurance_no` | số sổ bhxh |
| `hi` | `x_health_insurance_no` | số thẻ bhyt |
| `hiPlace` | `x_health_care_place` | nơi đăng ký bhyt |
| `permStreet` | `x_permanent_street` | địa chỉ thường trú · địa chỉ thường chú *(lỗi chính tả trong file thật)* |
| `currStreet` | `x_current_street` | địa chỉ hiện tại |

Cột không khớp → bỏ qua, gom vào `unknownCols` để hiển thị.

### 7.3 Chuẩn hoá giá trị

- **Tình trạng**: `Chính thức→official` · `Thử việc→probation` · `TTS→intern` ·
  `Parttime`/`Part-time`→`parttime` · `CTV→ctv` · `Cố vấn→advisor` ·
  `Nghỉ việc→resigned`. Khác → **lỗi dòng** `bad_status`.
- **Hình thức**: `Offline→offline` · `Online→online`. Khác → cảnh báo, để trống.
- **Loại vị trí**: theo nhãn Selection. Khác → cảnh báo, để trống.
- **Phòng ban**: chuẩn hoá rồi tra bảng bí danh cố định —
  `phòng r&d_sp` → *Sản phẩm (R&D_SP)* · `kế toán` → *Kế toán_HCNS* ·
  `kinh doanh` · `vận hành` · `marketing` khớp sau khi hạ hoa-thường.
  Không khớp → **lỗi dòng** `bad_department`.

  ⚠️ **Còn treo, cần hỏi Học Bá:** `Phòng Nhân sự` (3 dòng trong file) không có danh
  mục tương ứng. Mô tả seed của *Kế toán_HCNS* là "Thu chi, quyết toán, HR, hành
  chính" nên nhiều khả năng là nó, nhưng đây là quyết định nghiệp vụ — **không tự
  ánh xạ**. Trước khi có câu trả lời thì 3 dòng này rơi vào `bad_department`, HR sửa
  file hoặc tự thêm phòng ban rồi nhập lại.
- **Chức danh**: so tên đã chuẩn hoá với `hr.job` → khớp thì `job_id`; luôn ghi
  nguyên văn vào `job_title`.
- **Ngày**: nhận ô kiểu ngày của Excel + chuỗi `dd/mm/yyyy`, `yyyy-mm-dd`, `dd-mm-yyyy`.
  Không đọc được → cảnh báo, để trống.
- **CCCD**: bỏ khoảng trắng/chấm; phải đúng 12 chữ số, giữ số 0 đầu. Sai → cảnh báo,
  để trống ô (không chặn dòng).
- **Email**: kiểm dạng tối thiểu `x@y.z`; sai → cảnh báo, để trống. Trùng với email đã
  có trong hệ thống hoặc trùng trong chính file → cảnh báo, vẫn ghi.
- **SĐT**: giữ nguyên chuỗi, chỉ bỏ khoảng trắng.

## 8. Sửa BR-010 ở `hocba_employees`

`_check_official_required_fields` thêm cửa thoát ngay đầu hàm:

```python
if self.env.context.get('hocba_legacy_import'):
    return
```

Chỉ controller import bật cờ này. Hệ quả **cố ý**: hồ sơ đã nhập mà thiếu MST/BHXH
thì lần sau HR mở ra sửa trên UI vẫn bị BR-010 chặn cho tới khi điền đủ — đúng ý đồ
ép hoàn thiện dần. Preview có cảnh báo trước cho HR biết điều này.

Không thêm field mới: "hồ sơ cần hoàn thiện" tính bằng
`_hocba_missing_official_fields()` đã có sẵn.

## 8b. Đánh dấu hồ sơ cần hoàn thiện *(bổ sung 2026-08-21)*

Không dùng chuông. Dấu là **thường trực**, tính cho **mọi NV** thiếu CCCD/MST/BHXH
(không riêng người nhập từ Excel — NV tuyển mới mà HR quên đòi giấy tờ cũng hiện):

| Chỗ | Thể hiện |
|---|---|
| Model `hr.employee` | `x_needs_profile_completion` (Boolean) + `x_profile_missing` (Char) — compute **store=True** để lọc/đếm bằng domain SQL |
| Menu **Nhân viên** | Badge số, nguồn `GET /hocba-hrm/api/employees/incomplete-count`. Không quyền → `200 {count: 0}` (khuôn của `/api/timeoff/pending-count`) |
| Dòng NV trong bảng | Icon `alertTriangle` cạnh tên, tooltip *"Cần hoàn thiện hồ sơ — thiếu MST TNCN, Số sổ BHXH"*; nguồn là khoá `missingDocs` trong payload `/api/employees` |

Quyền xem badge = quyền nhập (`_cap_import_emp`): HR Manager / Admin.

## 9. Test (TDD — đỏ trước)

**Parser (hàm thuần, không HTTP):**
1. Dò được header dù nằm ở dòng 3.
2. Không có dòng header hợp lệ → `no_header`.
3. Thiếu cột Họ và tên → `no_name_col`.
4. Mỗi bí danh cột trong bảng 7.2 đều trúng đúng khoá.
5. Ngày đọc được cả 3 định dạng chuỗi lẫn ô kiểu ngày.
6. CCCD `"038098029187"` giữ nguyên số 0 đầu; `"12345"` → cảnh báo + để trống.
7. Tình trạng `"Online"` → `bad_status` (không rơi về `probation`).
8. Phòng ban `"Phòng R&D_SP"` → khớp *Sản phẩm (R&D_SP)*; `"Phòng ma"` → `bad_department`.
9. Chức danh lạ → `job_id` trống, `job_title` giữ nguyên văn.
10. Cột lạ được gom vào `unknownCols`, không làm hỏng dòng.

**Controller:**
11. NV thường và Giáo vụ gọi preview → 403.
12. Preview **không tạo bản ghi nào** (đếm `hr.employee` trước/sau bằng nhau).
13. Commit tạo đúng số hồ sơ, `identification_id` xuống `hr.version`.
14. Dòng trùng mã NV / trùng CCCD bị bỏ qua, không tạo bản sao.
15. NV `official` thiếu MST/BHXH **vẫn tạo được** qua import.
16. **BR-010 vẫn chặn** ở luồng tạo/sửa bình thường (không có cờ context).
17. Một dòng hỏng giữa chừng → rollback, không hồ sơ nào được tạo.
18. NV `probation` nhập qua import **không** bị gán quy trình nhận việc.

Lệnh chạy (theo CLAUDE.md, bắt buộc `MSYS_NO_PATHCONV=1` trên Git Bash):

```
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

## 10. Ngoài phạm vi (YAGNI)

- Không có màn ánh xạ cột thủ công.
- Không nhập lương / phụ cấp (sheet 2.2) — `wage` để trống.
- Không tạo tài khoản đăng nhập cho NV được nhập.
- Không nhập người phụ thuộc, tài sản, hợp đồng.
- Không sinh file mẫu để tải về (đã chốt dùng file có sẵn của trung tâm).
