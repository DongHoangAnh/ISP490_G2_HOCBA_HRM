# HƯỚNG DẪN TEST TAY TRÊN GIAO DIỆN ODOO

**Ngày:** 12/06/2026 · Dùng kèm [TEST_BACKEND_2026-06-12.md](TEST_BACKEND_2026-06-12.md) (test máy) — tài liệu này là kịch bản **bấm tay trên UI** để nghiệm thu nghiệp vụ + phân quyền.

---

## 0. Chuẩn bị (5 phút)

1. Bật Docker Desktop → `docker compose up -d` trong thư mục dự án.
2. Mở trình duyệt vào **`http://[::1]:8069`** ⚠️ KHÔNG dùng `localhost`/`127.0.0.1` — máy dev còn 1 Odoo native chiếm IPv4, sẽ vào nhầm db `tan`. Kiểm tra nhanh: màn login phải hiện db `hocba_hrm`.
3. Tài khoản test (mật khẩu chung **`Hocba@2026`**):

| Tài khoản | Role | Dùng để test |
|---|---|---|
| `test_admin@hocba.vn` | Admin | toàn quyền, Settings, chạy CRON tay |
| `test_hrmanager@hocba.vn` | HR Manager | nghiệp vụ F-001..009, field nhạy cảm |
| `test_employee@hocba.vn` | Employee | bị chặn gì — phần phân quyền |
| `test_ctv@hocba.vn` | Contractor | như Employee |

4. Dữ liệu mẫu: nhân viên **`HB.TEST` — Nguyễn Văn Test** (có đủ CCCD/MST/BHXH).
5. Bật developer mode khi cần chạy CRON: thêm `?debug=1` vào URL, hoặc Settings → Developer Tools.

**Vị trí menu chính** (đăng nhập HR Manager):
- App **Nhân viên** (Employees) → form nhân viên có 2 tab mới: **"Thông tin Học Bá"** và **"Pháp lý & Người phụ thuộc"**, cùng 3 smart button: **Tài sản / CC sắp hết hạn / Thăng tiến**.
- Menu **Nhân viên → Học Bá** → *Tài sản nhân viên*, *Loại tài sản*, *Lịch sử thăng tiến*.
- App **HOCBA HRM** (mở từ menu apps góc trên-trái — app riêng, KHÔNG nằm trong app Nhân viên) → menu ngang **User Management** → *Users*, *User Roles*, *Employee Types*, *Access Control*, *Department Managers*. Chỉ hiện với Admin/HR Manager.

> Quy ước dưới đây: ✅ = kết quả mong đợi. Làm tuần tự — kịch bản sau dùng dữ liệu của kịch bản trước.

---

## 1. Đăng nhập & phân quyền cơ bản (15 phút)

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 1.1 | Vào `/hocba/login`, đăng nhập `test_hrmanager` | Form custom hiện; login xong redirect vào `/web` |
| 1.2 | `/hocba/login` với mật khẩu sai | Quay lại form + báo "Invalid credentials", KHÔNG nói rõ sai gì |
| 1.3 | `/hocba/dashboard` lần lượt bằng 4 tài khoản | Mỗi role thấy dashboard tương ứng; Employee/CTV **không bị lỗi 403** (bug đã fix 12/06) |
| 1.4 | Vào `/hocba-hrm` | Redirect về `/odoo` (SPA đã ngắt); KHÔNG còn menu gốc "Học Bá HRM" |
| 1.5 | Đăng nhập `test_admin` → User Management → Users → mở user của `test_ctv` → tắt **Active** (nút khóa) | Lưu OK |
| 1.6 | Logout, thử login `test_ctv` ở CẢ `/web/login` và `/hocba/login` | Cả 2 cổng đều từ chối |
| 1.7 | Mở khóa lại `test_ctv` rồi login | Vào được bình thường; mở hocba.user thấy **Last Login** vừa cập nhật |
| 1.8 | Đăng nhập `test_employee` → mở app Nhân viên → mở hồ sơ bất kỳ | Chỉ thấy hồ sơ công khai (ảnh, tên, phòng ban, chức vụ); **KHÔNG có tab "Thông tin Học Bá" / "Pháp lý"** (user thường đi qua hr.employee.public) |
| 1.9 | Vẫn `test_employee`: thử mở menu User Management | Không thấy menu / bị chặn truy cập |
| 1.10 | Đăng nhập `test_hrmanager` → mở `HB.TEST` → tab Pháp lý | Thấy đủ **MST TNCN + Số sổ BHXH** |
| 1.11 | Tạo thêm 1 user role HR Officer nếu muốn test mức giữa (User Management → Users, role Employee + thêm nhóm "Nhân sự / Cán bộ" trong Settings) → mở tab Pháp lý | Thấy BHYT/CCCD nhưng **KHÔNG thấy MST/BHXH** (field chỉ dành manager) |

## 2. Role = quyền thật (User Management) (10 phút)

Đăng nhập `test_admin`:

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 2.1 | User Management → User Roles | Đủ 4 role: Admin / HR Manager / Employee / Contractor, mỗi role có cột ODOO Groups |
| 2.2 | Users → Create: chọn 1 ODOO User chưa có hocba.user, role **HR Manager** → Save | Tên tự điền theo res.users. Mở Settings → Users → user đó: đã nằm trong nhóm **HR / Administrator** |
| 2.3 | Đổi role bản ghi vừa tạo thành **Employee** → Save | Vào lại Settings → Users: nhóm HR Administrator **đã bị gỡ** |
| 2.4 | Thử tạo hocba.user thứ 2 cho cùng ODOO User | Báo lỗi unique "Each ODOO user can have only one HOCBA user!" |

## 3. F-001 — Hồ sơ & mã nhân sự (10 phút)

Đăng nhập `test_hrmanager`, app Nhân viên:

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 3.1 | Create nhân viên "Trần Test Manual", chọn phòng ban → Save | Tab Thông tin Học Bá: **Mã nhân sự tự sinh `HB.xx`**; statusbar đầu form: Thử việc → Chính thức → Nghỉ việc, đang ở **Thử việc** |
| 3.2 | Sửa mã thành `HB.TEST` (trùng) → Save | Báo lỗi "Mã nhân sự phải là duy nhất!" → đổi lại mã cũ |
| 3.3 | Đặt: Hình thức = **Offline**, Loại vị trí = **Nhân viên**, Loại NV = NV văn phòng | Khối "Dòng thời gian thử việc (2 cổng — Nhóm B)" + **mini-timeline 5 chấm** xuất hiện |
| 3.4 | Đổi Hình thức = **Online** | Khối 2 cổng ẩn đi, khối "Đánh giá thử giảng (Nhóm A)" hiện ra → trả về Offline |
| 3.5 | Xem list nhân viên | Có cột Mã NV + badge Hình thức/Tình trạng; dòng thử việc tô xanh info |
| 3.6 | Thử kéo statusbar lên **Chính thức** ngay | Bị chặn: hoặc lỗi BR-010 (thiếu MST/BHXH) — đúng; với HR Manager đủ pháp lý thì cho phép, user thường thì không |

## 4. F-002/F-003 — Pháp lý & Người phụ thuộc (10 phút)

Vẫn ở "Trần Test Manual", tab **Pháp lý & Người phụ thuộc**:

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 4.1 | MST TNCN = `12345` → Save | Lỗi "MST TNCN phải gồm 10 hoặc 13 chữ số." |
| 4.2 | MST = `0123456789`, BHXH = `0123456789` → Save | OK |
| 4.3 | Tab HR Settings/Thông tin riêng tư: CCCD = `123456789` → Save | Lỗi "Số CCCD phải gồm đúng 12 chữ số" |
| 4.4 | CCCD = `012345678901`; Ngày cấp CCCD = ngày mai | Lỗi "không được sau hôm nay" → đặt 01/06/2021 |
| 4.5 | Tích "Tạm trú giống thường trú" + nhập thường trú | Khối tạm trú ẩn; bỏ tích → hiện lại để nhập riêng |
| 4.6 | Thêm NPT dòng 1: Con, sinh 2020, bắt đầu giảm trừ 01/01/2026, không ngày kết thúc | Save OK; **Số NPT đang hiệu lực = 1** |
| 4.7 | Thêm NPT dòng 2: Cha/Mẹ, kết thúc giảm trừ 01/05/2026 (quá khứ) | Save OK; số NPT đang hiệu lực **vẫn = 1** |
| 4.8 | Thêm NPT ngày kết thúc ≤ ngày bắt đầu | Lỗi "Ngày kết thúc phải sau ngày bắt đầu" |

## 5. F-004/F-005 — Thử việc 2 cổng + automation (20 phút, quan trọng nhất)

Vẫn "Trần Test Manual" (Offline + Nhân viên = Nhóm B), gán **Quản lý** (parent) nếu muốn test quyền TBP:

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 5.1 | Ngày bắt đầu thử việc = **hôm nay − 20 ngày** → Save | Hạn tuần-2 tự = start+14, hạn tháng-2 = start+60; mini-timeline chấm 1 xanh |
| 5.2 | Sửa hạn tuần-2 = start+5 | Lỗi "trong khoảng 7–21 ngày" |
| 5.3 | Kết quả tháng-2 = Đạt (khi tuần-2 còn Chưa đánh giá) | Lỗi "Chỉ đánh giá cổng tháng-2 sau khi cổng tuần-2 đã Đạt" |
| 5.4 | Kết quả tuần-2 = **Đạt**, ngày đánh giá = hôm nay−6 → Save | ✅ **Ngày cấp thiết bị tự điền hôm nay**; chatter có "✅ Cổng tuần-2 ĐẠT…"; **2 Activity**: "Cấp thiết bị văn phòng…" + "Đánh giá thử việc tháng-2…"; timeline chấm 2+3 xanh ✓ |
| 5.5 | Kết quả tháng-2 = **Đạt**, ngày = hôm nay → Save | ✅ Statusbar nhảy **Chính thức**; Ngày chính thức = hôm nay; Activity "Tạo hợp đồng chính thức…"; chatter "🎉 Cổng tháng-2 ĐẠT…"; timeline 5/5 xanh |
| 5.6 | Tạo NV Nhóm B thứ 2 "Lê Test Fail", ngày thử việc −20, tuần-2 = **Không đạt** → Save | Tình trạng nhảy **Đang offboarding** (badge đỏ ở list); Activity "Offboarding nghỉ thử việc…" |
| 5.7 | (HR Manager) bật **Bỏ qua tự động hóa cổng** trên 1 NV mới rồi chấm Đạt | KHÔNG có activity/ngày cấp thiết bị; chatter ghi "Auto trigger bị bỏ qua bởi…" |
| 5.8 | Đăng nhập user HR Officer KHÔNG phải quản lý trực tiếp → chấm cổng | Lỗi "Chỉ HR Manager hoặc quản lý trực tiếp được điền kết quả thử việc." |
| 5.9 | (Admin, debug mode) Settings → Technical → **Scheduled Actions** → "HOCBA: Nhắc đánh giá thử việc (2 cổng)" → Run Manually. Trước đó tạo 1 NV probation có hạn tuần-2 trong ≤2 ngày tới | NV đó có Activity "Sắp đến hạn đánh giá tuần-2…"; chạy lại lần 2 **không nhân đôi** activity (BR-041) |

## 6. F-006 — Tài sản (10 phút)

Menu **Nhân viên → Học Bá → Tài sản nhân viên** (hoặc smart button "Tài sản" trên form):

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 6.1 | Create: NV = Trần Test Manual, Loại = Laptop, Mã = `LT-DEMO-01`, ngày cấp hôm nay → Save | OK, statusbar **Đang giữ**; smart button Tài sản trên form NV = 1 |
| 6.2 | Tạo bản ghi khác cùng mã `LT-DEMO-01` cho NV khác | Lỗi "đang được người khác giữ" |
| 6.3 | Thử ngày cấp < ngày đánh giá tuần-2 của NV | Lỗi "phải từ ngày đánh giá tuần-2 trở đi" |
| 6.4 | Action → Delete bản ghi tài sản | Lỗi "Không được xóa bản ghi tài sản" |
| 6.5 | Trên form NV: Archive nhân viên đang giữ tài sản | Lỗi "còn 1 tài sản chưa thu hồi: LT-DEMO-01" |
| 6.6 | Mở tài sản → nút **Thu hồi** | State = Đã thu hồi, ngày thu hồi tự điền hôm nay |
| 6.7 | Cấp tài sản mới `LT-DEMO-02`, chọn "Chuyển giao cho" = HB.TEST → nút **Chuyển giao** | Bản ghi cũ = Đã chuyển giao; **tự sinh bản ghi mới `LT-DEMO-02` Đang giữ** cho HB.TEST, ngày cấp = ngày chuyển |

## 7. F-007 — Thăng tiến (10 phút)

Menu **Học Bá → Lịch sử thăng tiến** (hoặc smart button):

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 7.1 | Create: NV = Trần Test Manual, chức vụ mới (khác hiện tại), lương cũ 10tr → mới 12tr, **bỏ trống Lý do** | Lỗi "Cần nhập Lý do / Căn cứ khi thay đổi mức lương." |
| 7.2 | Nhập lý do + số QĐ → Save | OK; mở form NV: **Chức vụ đã đổi** sang chức vụ mới; chatter có "📈 Cập nhật chức vụ…" |
| 7.3 | Lương mới = 0 | Lỗi "Lương mới phải lớn hơn 0." |
| 7.4 | Ngày hiệu lực = hôm nay + 45 | Lỗi "không được quá 30 ngày trong tương lai." |
| 7.5 | Delete bản ghi thăng tiến | Lỗi "Không được xóa lịch sử thăng tiến (audit trail)." |

## 8. F-008 — Thử giảng Nhóm A (10 phút)

Tạo NV "Phạm Test GV", Hình thức = **Online** (khối thử giảng hiện ra):

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 8.1 | Điểm phương pháp = 11 | Lỗi "Điểm thử giảng phải trong thang 1–10." |
| 8.2 | Ngày thử giảng = ngày mai | Lỗi "không được sau hôm nay" |
| 8.3 | Kết quả = Không đạt, bỏ trống nhận xét | Lỗi "Cần nhập Nhận xét thử giảng khi kết quả Không đạt." |
| 8.4 | Ngày = hôm nay, lớp `C1`, điểm 8.5/9.0, kết quả **Đạt** → Save | Chatter "✅ Thử giảng ĐẠT (PP 8.5 / CM 9.0)…"; Activity "Ký HĐ thỉnh giảng cho…" hạn +3 ngày |

## 9. F-009 — Chứng chỉ & CRON cảnh báo (10 phút)

Trên form "Phạm Test GV" → tab Resume/Kỹ năng (hr_skills):

| # | Bước | ✅ Mong đợi |
|---|---|---|
| 9.1 | Thêm kỹ năng HSK cấp bất kỳ; mở bản ghi skill đặt: Ngày cấp = 1 năm trước, **Ngày hết hạn = hôm nay + 10**, tích **Đã xác minh** | Tình trạng chứng chỉ = **Sắp hết hạn** (≤60 ngày); smart button **"CC sắp hết hạn" = 1** trên form NV |
| 9.2 | Đặt ngày hết hạn ≤ ngày cấp | Lỗi "Ngày hết hạn chứng chỉ phải sau ngày cấp." |
| 9.3 | (Admin, debug) Scheduled Actions → "HOCBA: Cảnh báo chứng chỉ sắp hết hạn" → **Run Manually** | NV có Activity "Chứng chỉ sắp hết hạn: HSK…". Cert chưa tích "Đã xác minh" thì KHÔNG được cảnh báo |
| 9.4 | Smart button CC sắp hết hạn → mở list | List chứng chỉ tô màu theo tình trạng (đỏ hết hạn / vàng sắp) |

## 10. Dọn dữ liệu sau khi test

Các NV "… Test Manual / Test Fail / Test GV" + tài sản `LT-DEMO-*`: tài sản & thăng tiến **không xóa được** (audit – chủ đích). Cách dọn: thu hồi hết tài sản → **Archive** nhân viên (không Delete). Giữ lại `HB.TEST` + 4 tài khoản test cho lần demo sau.

## 11. Checklist tổng (tick khi nghiệm thu)

- [ ] 1. Đăng nhập 2 cổng + khóa/mở + dashboard 4 role
- [ ] 2. Role sync quyền thật (gán/đổi/unique)
- [ ] 3. F-001 mã HB + statusbar + badge
- [ ] 4. F-002/3 validate pháp lý + NPT
- [ ] 5. F-004/5 hai cổng + automation + CRON nhắc hạn + quyền chấm
- [ ] 6. F-006 vòng đời tài sản + chặn archive
- [ ] 7. F-007 thăng tiến + audit
- [ ] 8. F-008 thử giảng + activity
- [ ] 9. F-009 chứng chỉ + CRON cảnh báo
- [ ] 10. Phân quyền: Employee không thấy tab Học Bá / MST; HR Officer không thấy MST
