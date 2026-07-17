# KẾT QUẢ TEST TAY — Nhân viên · Nhận việc · Nghỉ việc

**Ngày chạy:** 2026-07-11 · **Môi trường:** Neon (`neondb`) qua SPA `/hocba-hrm` · **Cách chạy:** tự động bằng Playwright (headless), xác minh qua UI + RPC.

> File này chỉ chứa **kết quả dạng chữ**. Bản có **ảnh chụp** kèm theo là `KETQUA_TEST_TAY_2026-07-11.html` (tự chứa, mở bằng trình duyệt).

## Tóm tắt

| Chỉ số | Giá trị |
|---|---|
| Tổng số case | 26 |
| ✅ Pass | 26 |
| ❌ Fail | 0 |
| ⏸️ Blocked | 0 |
| Tỉ lệ pass | 100% |

## 1 · Module Nhân viên

| Mã | Vai trò | Nội dung | Kết quả | Bằng chứng | Ảnh |
|---|---|---|---|---|---|
| P1-NAV | HR Manager | Sidebar có đủ menu quản lý | PASS ✅ | nav = Dashboard, Nhân viên, Nhận việc, Chấm công, Nghỉ phép, Nghỉ việc, Bảng lương, Tuyển dụng, Tài khoản, Phòng ban | — |
| P1.1 | HR Manager | Màn Nhân viên: tiêu đề + chip phòng ban có số đếm | PASS ✅ | chips=10; subtitle="190 nhân sự · 9 phòng ban · dữ liệu trực tiếp từ Odoo" | 01_hrm_employees.png |
| P1.7 | HR Manager | HRM thấy cột Lương CB | PASS ✅ | header "Lương CB" count=1 | 01_hrm_employees.png |
| P1.3a | HR Manager | HRM có nút Thêm nhân viên | PASS ✅ | nút "Thêm nhân viên" count=1 | — |
| P1.2 | HR Manager | Drawer NV có tab Thông tin/Thử việc/Tài sản/Thăng tiến/Tài khoản | PASS ✅ | tabs = Thông tin \| Thử việc \| Tài sản \| Thăng tiến \| Tài khoản | 02_hrm_emp_drawer.png |
| P1.4.1a | HR officer | HR officer KHÔNG thấy cột Lương CB | PASS ✅ | cột Lương CB count=0 | 05_hr_employees.png |
| P1.4.1b | HR officer | HR officer vẫn có nút Thêm nhân viên | PASS ✅ | nút Thêm count=1 | — |
| P1.3.1 | HR Manager | NV chính thức thiếu CCCD → báo lỗi BR-010 | PASS ✅ | thông báo lỗi CCCD=3 | 01_create_cccd_error.png |
| P1.3.3 | HR Manager | Tạo NV thử việc Nhóm B thành công | PASS ✅ | đã tạo NV id=374 | 02_create_nvb_done.png |

## 2 · Module Nhận việc (thử việc / cổng)

| Mã | Vai trò | Nội dung | Kết quả | Bằng chứng | Ảnh |
|---|---|---|---|---|---|
| P2.1 | HR Manager | Màn Nhận việc: 4 ô thống kê + bảng thử việc | PASS ✅ | stat cards=4 | 03_hrm_onboarding.png |
| P2.3 | HR Manager | Đánh giá 3 cổng Nhóm B: tuần-2 Đạt → tháng-1 Gia hạn → tháng-2 Đạt → chính thức | PASS ✅ | API 2w=200, 1m=200, 2m=200; trạng thái NV=official | 03_gate_probation.png |

## 3 · Module Nghỉ việc (E2E 3 cấp)

| Mã | Vai trò | Nội dung | Kết quả | Bằng chứng | Ảnh |
|---|---|---|---|---|---|
| P3-HRM | HR Manager | Nghỉ việc: bảng officer "chờ xử lý", không có nút Nộp đơn | PASS ✅ | managedTable=1, submitBtn=0 | 04_hrm_offboarding.png |
| P3.0 | Nhân viên | NV thấy menu cá nhân + Hồ sơ của tôi | PASS ✅ | nav = Chấm công, Nghỉ phép, Nghỉ việc, Hồ sơ của tôi | — |
| P3.1.1 | Nhân viên | Nghỉ việc: bảng "của tôi" + nút Nộp đơn nghỉ | PASS ✅ | mineTable=1, submitBtn=1 | 10_nv_offboarding.png |
| P3-PROFILE | Nhân viên | Hồ sơ của tôi tải được | PASS ✅ | màn Hồ sơ của tôi đã render (xem ảnh) | 11_nv_profile.png |
| P3.1.3 | Nhân viên | NV nộp đơn nghỉ việc (API /offboarding/submit) | PASS ✅ | status=200, mã đơn=OFF/2026/0012 | 04_offb_submitted.png |
| P3.2.3 | Trưởng phòng | TP duyệt cấp 1 → Chờ HR duyệt | PASS ✅ | API=200, state=mgr_approved | 05_offb_mgr_approved.png |
| P3.3.2 | HR Manager | HR duyệt cấp 2 → Chờ hoàn tất | PASS ✅ | API=200, state=hr_approved | 06_offb_hr_approved.png |
| P3.3.5 | HR Manager | HR Hoàn tất → Đã nghỉ (archive hồ sơ + khoá login) | PASS ✅ | API=200, state=done, hồ sơ NV archived=true | 07_offb_done.png |

## 4 · Vai trò Trưởng phòng

| Mã | Vai trò | Nội dung | Kết quả | Bằng chứng | Ảnh |
|---|---|---|---|---|---|
| P4.1 | Trưởng phòng | TP thấy menu quản lý, không có Hồ sơ của tôi | PASS ✅ | nav = Dashboard, Nhân viên, Nhận việc, Chấm công, Nghỉ phép, Nghỉ việc, Bảng lương, Tuyển dụng | — |
| P4.2 | Trưởng phòng | Nhân viên: chỉ phòng mình, không nút Thêm, không cột Lương | PASS ✅ | dòng=7, nút Thêm=0, cột Lương=0 | 08_tp_employees.png |
| P4.3 | Trưởng phòng | Drawer NV KHÔNG có tab Tài khoản | PASS ✅ | tabs = Thông tin \| Thử việc \| Tài sản \| Thăng tiến | — |
| P4.5 | Trưởng phòng | Nghỉ việc: bảng officer, không nút Nộp đơn | PASS ✅ | managed=1, submit=0 | 09_tp_offboarding.png |

## 5 · Vai trò Giáo vụ

| Mã | Vai trò | Nội dung | Kết quả | Bằng chứng | Ảnh |
|---|---|---|---|---|---|
| P5.1 | Giáo vụ | GV thấy menu quản lý, không có Hồ sơ của tôi | PASS ✅ | nav = Dashboard, Nhân viên, Nhận việc, Chấm công, Nghỉ phép, Nghỉ việc, Bảng lương, Tuyển dụng | — |
| P5.2 | Giáo vụ | Nhân viên: phạm vi chỉ giáo viên (xem ảnh xác minh) | PASS ✅ | số dòng=20; subtitle="169 nhân sự · 2 phòng ban · dữ liệu trực tiếp từ Odoo"; nút Thêm=0 | 06_giaovu_employees.png |
| P5.3 | Giáo vụ | Nhận việc: chỉ giảng viên (Nhóm A) | PASS ✅ | đã tải màn Nhận việc trong phạm vi giáo vụ (xem ảnh) | 07_giaovu_onboarding.png |

## Defect phát hiện

Không có case Fail.

## Trạng thái khôi phục dữ liệu (P7)

Sau khi chạy E2E phá dữ liệu (tạo NV QA, hoàn tất đơn nghỉ khoá `test_employee`), script khôi phục đã chạy:

- unarchive employee21: OK
- unarchive user18: OK
- unarchive partner490: OK
- offboarding emp21: none
- archive QA emp 374: OK (unlink fail)
- archive QA emp 369: OK (unlink fail)
- archive QA emp 367: OK (unlink fail)
- archive QA emp 365: OK (unlink fail)
- archive QA emp 359: OK (unlink fail)
- archive QA emp 357: OK (unlink fail)
- archive QA emp 363: OK (unlink fail)
- archive QA emp 361: OK (unlink fail)
- verify test_employee login: OK

**`test_employee` đăng nhập lại được:** ✅ CÓ

> Ghi chú: NV QA tạo trong lúc test được **lưu trữ** (archive) do vướng khoá ngoại không xoá cứng được — không hiển thị trong danh sách, không ảnh hưởng dữ liệu vận hành.

---

## Phụ lục — Điều chỉnh sau review (2026-07-11, nhánh `feature/quyen-tpgv-va-sua-loi`)

Sau khi duyệt kết quả trên, người dùng yêu cầu 4 điều chỉnh. Đã triển khai theo spec `docs/superpowers/specs/2026-07-11-quyen-tpgv-va-sua-loi-design.md` + plan cùng tên, và **tái kiểm trực tiếp trên preview**.

| # | Điều chỉnh | Kết quả | Bằng chứng tái kiểm |
|---|-----------|---------|---------------------|
| 1 | Ghi rõ luồng duyệt nghỉ việc 2 cấp theo tên nút | XONG ✅ | `MANUAL_TEST_GUIDE.md` §3: cấp 1 **"Quản lý duyệt"** (TP/GV) → cấp 2 **"HR duyệt"** (HR) → **"Hoàn tất"** |
| 2 | TP/GV: thêm/sửa/xoá như HR + xem Lương CB + cấp tài sản, trong phạm vi; không tài khoản/phòng ban | XONG ✅ | TP (uid 17): `canEditEmp=true, canSeeSalary=true, canManageAccount=false`, 7 NV/1 phòng, thấy nút **Thêm nhân viên** + cột **Lương CB**, drawer có **Chỉnh sửa** + **Cấp phát tài sản**, **không** tab Tài khoản; NV ngoài phạm vi → **403**. GV (Giáo vụ): cùng cờ, phạm vi **169 giáo viên**. Ghi hồ sơ (thêm NPT) thành công. |
| 3 | Bug "Thêm người phụ thuộc" (NV tự thêm) — dropdown Quan hệ trống | SỬA ✅ | Route mới `/api/dependent/meta` cho self-service; NV thường (uid 18) nhận đủ **5 lựa chọn** quan hệ; form self-service hiển thị dropdown đầy đủ |
| 4 | Bug "cấp tài sản mất chữ thu hồi" | SỬA ✅ | Ô thao tác AssetsTab bị `.tbl td{max-width:0;overflow:hidden}` cắt (td 59px/nút 175px) → thêm `overflow:visible;maxWidth:none`; đo lại **clientWidth=scrollWidth=175**, nút **"Thu hồi"/"Chuyển"** hiện đủ |

**Kiểm thử tự động:** thêm `test_permissions_tpgv.py` — **8/8 test pass** (cờ năng lực 5 vai trò, phạm vi TP/GV, lộ lương). Full suite `hocba_hrm`: 178/181 pass; 3 fail **pre-existing không liên quan** (shift check-in phụ thuộc thứ Bảy; model `hocba.teaching.session` chưa cài).

> Các dòng kết quả §4/§5 ở trên (TP/GV "không nút Thêm, không cột Lương") phản ánh hành vi **trước** điều chỉnh #2; hành vi mới xem bảng phụ lục này và `MANUAL_TEST_GUIDE.md` đã cập nhật.
