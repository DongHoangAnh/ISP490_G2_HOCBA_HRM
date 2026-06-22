# Bản test thủ công — Chức năng Tài khoản đăng nhập

> Mục tiêu: kiểm tra tay toàn bộ chức năng + luồng nghiệp vụ của tính năng quản lý tài khoản (HR cấp/cấp lại tài khoản, không tự đăng ký). Dùng để nghiệm thu trước khi giao.

- **Module:** `hocba_hrm` (controller + SPA), liên kết `hr.employee.user_id ↔ res.users`
- **Spec:** `docs/superpowers/specs/2026-06-21-account-management-design.md`
- **Ngày soạn:** 2026-06-21

---

## 1. Chuẩn bị môi trường

| Việc | Chi tiết |
|---|---|
| Chạy app | Odoo + SPA tại `/hocba-hrm` (preview proxy `http://localhost:8169/hocba-hrm`, hoặc URL thật của bạn) |
| Mật khẩu chung | `Hocba@2026` |
| TK HR (người cấp TK) | `test_hrmanager@hocba.vn` |
| TK Giáo vụ | `test_giaovu@hocba.vn` |
| TK Trưởng phòng | `test_truongphong@hocba.vn` |
| TK Nhân viên thường | `test_employee@hocba.vn` |

**Cần có sẵn để test:**
- **Ít nhất 1 nhân viên CHƯA có tài khoản** (để test "Tạo tài khoản"). Cách tìm: vào *Nhân viên*, mở hồ sơ → tab *Tài khoản* hiện "Nhân viên chưa có tài khoản đăng nhập". (Các NV `test_giaovu/truongphong/employee` ĐÃ có TK — không dùng để test tạo.)
- **1 phòng ban đã có trưởng phòng** (vd "Phòng Test (QA)" đang có Test Trưởng Phòng) để test luồng xác nhận ghi đè.

> ⚠️ Lưu ý: test "Tạo tài khoản" và "Cấp lại MK" sẽ thay đổi DB. Nên test trên DB local `hocba_hrm`, và sau khi seed/đổi thì cập nhật `docs/DB_TEST_DATA.md`.

---

## 2. Luồng nghiệp vụ (business flow)

```
[NV mới vào]
     │
     ▼
HR/Admin mở hồ sơ NV ─► tab "Tài khoản" ─► (chưa có TK) ─► [Tạo tài khoản]
     │                                                          │
     │                          nhập: login, mật khẩu, xác nhận, LOẠI TK
     │                                                          │
     │                       ┌──────────────┬──────────────────┴───────────────┐
     │                       ▼              ▼                                   ▼
     │                  Nhân viên       Giáo vụ                           Trưởng phòng
     │                  (chỉ login)   (+ nhóm giáo vụ)              (chọn phòng → làm trưởng phòng)
     │                       └──────────────┴──────────────────┬───────────────┘
     │                                                          ▼
     │                                              Tạo res.users + gắn vào NV
     │                                                          ▼
     └────────────────────────────────────► NV đăng nhập được bằng login + MK
                                                                │
[NV quên mật khẩu]                                              │
     │                                                          │
     ▼                                                          │
HR/Admin mở hồ sơ NV (hoặc trang "Tài khoản") ─► [Cấp lại mật khẩu]
     │                                                          │
     │                       nhập: mật khẩu mới + xác nhận       │
     │                                                          ▼
     └────────────────────────────────────► NV đăng nhập bằng MK mới

KHÔNG có luồng tự đăng ký. Chỉ HR/Admin thao tác.
```

**Nguyên tắc cốt lõi cần đúng:**
1. Chỉ HR/Admin cấp & cấp lại tài khoản.
2. Nhân viên KHÔNG tự đăng ký.
3. Login do HR tự nhập, phải duy nhất.
4. Mật khẩu ≥ 8 ký tự, phải khớp ô xác nhận.
5. 2 loại TK: thường / giáo vụ (gán nhóm) / trưởng phòng (đặt làm `manager_id` của phòng).

---

## 3. Ca test chi tiết

Ký hiệu kết quả: ✅ Pass · ❌ Fail · ⬜ Chưa test. Điền cột **Thực tế**.

### Nhóm A — Phân quyền & hiển thị

| ID | Mục tiêu | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| A1 | HR thấy mục Tài khoản | Đăng nhập `test_hrmanager` → nhìn sidebar | Có menu **"Tài khoản"** trong nhóm "Quản lý nhân sự" | ⬜ |
| A2 | HR thấy tab Tài khoản | Mở *Nhân viên* → mở 1 hồ sơ | Có tab **"Tài khoản"** trong drawer | ⬜ |
| A3 | Giáo vụ KHÔNG thấy | Đăng nhập `test_giaovu` → xem sidebar & mở hồ sơ NV | KHÔNG có menu "Tài khoản"; KHÔNG có tab "Tài khoản" | ⬜ |
| A4 | Trưởng phòng KHÔNG thấy | Đăng nhập `test_truongphong` → tương tự A3 | Không có menu/tab "Tài khoản" | ⬜ |
| A5 | Nhân viên thường KHÔNG thấy | Đăng nhập `test_employee` | Chỉ thấy phần cá nhân; không có "Tài khoản" | ⬜ |
| A6 | Chặn API trực tiếp | Đăng nhập `test_employee`, mở DevTools Console gõ:`fetch('/hocba-hrm/api/accounts').then(r=>console.log(r.status))` | In ra **403** (forbidden) | ⬜ |

### Nhóm B — Tạo tài khoản (trong hồ sơ NV, vai trò HR)

| ID | Mục tiêu | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| B1 | Tạo TK nhân viên thường | Mở hồ sơ NV **chưa có TK** → tab Tài khoản → **Tạo tài khoản** → login mới (vd `nv.test01`), MK `Test1234`, xác nhận `Test1234`, Loại = **Nhân viên thường** → Tạo | Báo thành công; khu TK chuyển sang hiện **login + Trạng thái: Hoạt động** + nút *Cấp lại mật khẩu* | ⬜ |
| B2 | Tạo TK Giáo vụ | NV chưa có TK khác → Tạo, Loại = **Giáo vụ** → Tạo | Tạo thành công. (Kiểm chứng B2b) | ⬜ |
| B2b | Giáo vụ có quyền đúng | Đăng xuất → đăng nhập bằng TK vừa tạo ở B2 | Vào được app, thấy menu giáo vụ (chỉ giáo viên), KHÔNG thấy mục quản trị HR | ⬜ |
| B3 | Tạo TK Trưởng phòng | NV chưa có TK → Tạo, Loại = **Trưởng phòng** → chọn 1 phòng **chưa có trưởng phòng** → Tạo | Tạo thành công. Vào *Nhân viên* / cấu hình phòng ban → NV này là **trưởng phòng** của phòng đã chọn | ⬜ |
| B4 | Trưởng phòng — xác nhận ghi đè | NV chưa có TK → Tạo, Loại = Trưởng phòng → chọn phòng **đã có trưởng phòng** (vd "Phòng Test (QA)") → Tạo | Hiện hộp xác nhận "Phòng … đã có trưởng phòng (…). Xác nhận để ghi đè." → bấm OK → tạo thành công, NV mới thành trưởng phòng phòng đó | ⬜ |
| B4b | Trưởng phòng — huỷ ghi đè | Lặp B4 nhưng bấm **Cancel** ở hộp xác nhận | Không tạo TK; phòng giữ nguyên trưởng phòng cũ | ⬜ |

### Nhóm C — Validation khi tạo

| ID | Mục tiêu | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| C1 | Thiếu login | Tạo TK, để trống ô login → Tạo | Báo lỗi "Vui lòng nhập tên đăng nhập."; không tạo | ⬜ |
| C2 | Login trùng | Tạo TK với login = `test_giaovu@hocba.vn` (đã tồn tại) → Tạo | Báo lỗi "Tên đăng nhập đã tồn tại."; không tạo | ⬜ |
| C3 | Mật khẩu quá ngắn | Tạo TK, MK = `123` (xác nhận `123`) → Tạo | Báo lỗi "Mật khẩu phải có ít nhất 8 ký tự."; không tạo | ⬜ |
| C4 | Xác nhận không khớp | Tạo TK, MK = `Test1234`, xác nhận = `Khac1234` → Tạo | Báo lỗi "Xác nhận mật khẩu không khớp."; không tạo | ⬜ |
| C5 | Trưởng phòng thiếu phòng | Tạo TK, Loại = Trưởng phòng, KHÔNG chọn phòng → Tạo | Báo lỗi "Trưởng phòng cần chọn phòng ban."; không tạo | ⬜ |
| C6 | Tạo khi đã có TK | Mở hồ sơ NV **đã có TK** → tab Tài khoản | KHÔNG hiện nút "Tạo tài khoản" (chỉ hiện login + "Cấp lại mật khẩu") | ⬜ |

### Nhóm D — Cấp lại mật khẩu

| ID | Mục tiêu | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| D1 | Cấp lại từ hồ sơ NV | Mở hồ sơ NV đã có TK → tab Tài khoản → **Cấp lại mật khẩu** → MK mới `Reset1234` + xác nhận → Cấp lại | Báo thành công; modal chỉ có 2 ô (MK mới + xác nhận), KHÔNG có ô login/loại TK | ⬜ |
| D1b | MK mới hoạt động | Đăng xuất → đăng nhập NV đó với MK `Reset1234` | Đăng nhập thành công | ⬜ |
| D2 | Cấp lại từ trang Tài khoản | Vào menu *Tài khoản* → bấm **Cấp lại MK** ở 1 dòng → đổi MK | Thành công; danh sách load lại | ⬜ |
| D3 | Validation cấp lại — MK ngắn | Cấp lại với MK `12` | Báo lỗi MK ≥ 8 ký tự; không đổi | ⬜ |
| D4 | Validation cấp lại — không khớp | Cấp lại, 2 ô khác nhau | Báo lỗi xác nhận không khớp; không đổi | ⬜ |

### Nhóm E — Trang danh sách Tài khoản

| ID | Mục tiêu | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| E1 | Hiển thị danh sách | Đăng nhập HR → menu *Tài khoản* | Bảng liệt kê các NV **đã có TK**, cột: Nhân viên, Mã, Phòng ban, Đăng nhập, Loại, Trạng thái; header ghi "N tài khoản · M phòng ban" | ⬜ |
| E2 | Loại hiển thị đúng | Xem cột "Loại" | Giáo vụ → "Giáo vụ"; trưởng phòng → "Trưởng phòng"; còn lại → "Nhân viên" (khớp đúng quyền thực tế) | ⬜ |
| E3 | Tìm kiếm | Gõ vào ô tìm trên topbar (tên / login / mã) | Bảng lọc đúng theo từ khoá | ⬜ |
| E4 | Trạng thái | Xem cột Trạng thái | Hiện "Hoạt động" (badge) cho TK đang bật | ⬜ |

### Nhóm F — Luồng nghiệp vụ end-to-end

| ID | Kịch bản | Các bước | Kết quả mong đợi | Thực tế |
|---|---|---|---|---|
| F1 | NV mới được cấp TK rồi đăng nhập | (HR) Tạo NV mới hoặc chọn NV chưa có TK → tạo TK thường → đăng xuất → đăng nhập bằng login+MK vừa cấp | NV đăng nhập được, vào đúng phần cá nhân (Hồ sơ của tôi, Chấm công…) | ⬜ |
| F2 | Quên mật khẩu → HR cấp lại | (HR) Cấp lại MK cho NV ở F1 → báo NV MK mới → đăng nhập lại | NV đăng nhập được bằng MK mới; MK cũ không còn dùng được | ⬜ |
| F3 | Không có tự đăng ký | Ở màn đăng nhập Odoo, kiểm tra không có luồng tạo tài khoản tự phục vụ cho người dùng thường (chỉ HR cấp trong app) | Không có cách NV tự tạo tài khoản | ⬜ |
| F4 | Tách quyền sau khi cấp | Sau B3 (tạo trưởng phòng), đăng nhập TK trưởng phòng đó | Thấy phạm vi quản lý phòng mình (theo phân quyền trưởng phòng), không thấy "Tài khoản" | ⬜ |

---

## 4. Ngoài phạm vi (KHÔNG test — đã thống nhất để sau)

- Khoá / vô hiệu hoá tài khoản khi nhân viên nghỉ việc.
- Đổi vai trò (loại TK) sau khi đã tạo.
- Cấp lại mật khẩu qua email / link tự đặt lại.

---

## 5. Ghi chú khi test

- Lỗi nghiệp vụ hiển thị bằng tiếng Việt ngay trong modal (đỏ).
- Sau mỗi lần tạo/cấp lại thành công: dữ liệu trên màn cập nhật ngay (không cần F5).
- Nếu tạo TK test mới trong DB → ghi vào `docs/DB_TEST_DATA.md` (bảng tài khoản + nhật ký) cho cả nhóm.
- Tổng kết: ___ / ___ ca Pass. Người test: __________ Ngày: ________
