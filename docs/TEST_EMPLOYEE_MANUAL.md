# Bản test thủ công — Module EMPLOYEE (Hồ sơ & Vòng đời nhân sự)

> Dùng cho giai đoạn **test tay – tìm bug – khắc phục**. Tick từng ca, ghi bug vào §cuối.
> Bám đặc tả: `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md` (v2.2, F-001…F-009, M-01…M-11).

- **Phạm vi:** SPA Employees tại `/hocba-hrm` + API `/hocba-hrm/api/*` (`hocba_hrm` controller), model `hr.employee` (`hocba_employees`).
- **Ngày soạn:** 2026-06-21
- Ký hiệu: ✅ Pass · ❌ Fail · ⚠️ Pass có lưu ý · ⬜ Chưa test.

---

## 0. Chuẩn bị

| Việc | Chi tiết |
|---|---|
| URL | `/hocba-hrm` (preview: `http://localhost:8169/hocba-hrm`) |
| MK chung | `Hocba@2026` |
| HR Manager | `test_hrmanager@hocba.vn` |
| Giáo vụ | `test_giaovu@hocba.vn` |
| Trưởng phòng | `test_truongphong@hocba.vn` |
| Nhân viên thường | `test_employee@hocba.vn` |

**Dữ liệu nên có sẵn** (DB local `hocba_hrm` đã có 11 NV / 6 phòng — xem `docs/DB_TEST_DATA.md`):
- ≥1 NV **Thử việc Nhóm B** (offline) để test 3 cổng.
- ≥1 NV **Nhóm A** (hình thức *online*, hoặc tình trạng parttime/ctv/advisor) để test thử giảng.
- ≥1 NV **Chính thức** đã có lương để test bảo mật lương & thăng tiến.
- ≥1 NV có **chứng chỉ sắp/đã hết hạn** để test cảnh báo.

> ⚠️ Test sẽ thay đổi DB → ưu tiên DB local; sau khi đổi cập nhật `docs/DB_TEST_DATA.md`.

---

## 1. Bảng phân quyền tham chiếu (để đối chiếu khi test)

| Vai trò | Phạm vi danh sách NV | Xem lương | Xem CCCD/MST/BHXH | Duyệt cổng thử việc | Thấy "Hồ sơ của tôi" |
|---|---|---|---|---|---|
| **HR Manager / Admin** | Tất cả | Tất cả | Tất cả (Manager) | Có | Không (tài khoản vai trò) |
| **HR User** | Tất cả | Không* | CCCD có / MST-BHXH ẩn | — | Không |
| **Trưởng phòng** | Phòng mình (+ phòng con) | Của NV phòng mình (theo cấu hình) | Theo quyền | NV phòng mình | Không (M-10) |
| **Giáo vụ** | Chỉ giáo viên | Không | Không | — | Không (M-10) |
| **Nhân viên thường** | Chỉ mình | Của mình | Của mình | — | **Có** |

\* Lương chỉ HR Manager (+admin) thấy của mọi người (M-05/BR-011).

---

## 2. NHÓM A — Truy cập & phân quyền theo vai trò

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| A1 | HR thấy đủ menu quản lý | Login HR → sidebar | Có "Nhân viên", "Nhận việc", … (nhóm Quản lý nhân sự); KHÔNG có "Hồ sơ của tôi" | ⬜ |
| A2 | HR xem toàn bộ NV | Vào *Nhân viên* | Thấy tất cả NV mọi phòng; có chip thống kê theo phòng | ⬜ |
| A3 | Giáo vụ chỉ thấy giáo viên | Login Giáo vụ → *Nhân viên* | Danh sách chỉ gồm giáo viên (không thấy NV phòng khác) | ⬜ |
| A4 | Trưởng phòng chỉ thấy phòng mình | Login Trưởng phòng → *Nhân viên* | Chỉ NV thuộc phòng mình (gồm phòng con); không thấy phòng khác | ⬜ |
| A5 | NV thường không vào màn quản lý | Login `test_employee` | Chỉ thấy phần cá nhân ("Hồ sơ của tôi", Chấm công…); không có danh sách NV | ⬜ |
| A6 | Chặn API ngoài phạm vi | (NV thường) Console: `fetch('/hocba-hrm/api/employees').then(r=>r.json()).then(d=>console.log(d.employees?.length))` | Trả rỗng/0 NV (hoặc 403) — không lộ NV khác | ⬜ |
| A7 | Xem hồ sơ ngoài phạm vi bị chặn | (Trưởng phòng) Console: `fetch('/hocba-hrm/api/employee/<id NV phòng khác>').then(r=>console.log(r.status))` | **403** | ⬜ |

---

## 3. NHÓM B — Danh sách, tìm kiếm, hồ sơ tổng quan (F-001)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| B1 | Danh sách hiển thị đúng | (HR) *Nhân viên* | Mỗi NV có ảnh/tên/mã/chức danh/phòng/tình trạng (badge màu theo trạng thái) | ⬜ |
| B2 | Chip thống kê phòng | Xem khối phòng ban | Tổng / chính thức / thử việc đếm đúng theo từng phòng | ⬜ |
| B3 | Tìm kiếm | Gõ tên / mã NS / phòng ở ô tìm | Lọc đúng kết quả | ⬜ |
| B4 | Mở hồ sơ | Click 1 NV | Mở drawer; header có tên + badge tình trạng + mã·chức danh·phòng; tab: Thông tin / Thử việc / Tài sản(n) / Thăng tiến(n) [+ Tài khoản nếu HR] | ⬜ |
| B5 | Badge tình trạng đúng màu | Xem nhiều NV trạng thái khác nhau | Thử việc / Chính thức / Nghỉ… màu khác nhau, đúng nhãn | ⬜ |

---

## 4. NHÓM C — Tạo nhân viên mới (HR)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| C1 | Mở form thêm | (HR) *Nhân viên* → nút Thêm | Hiện form: họ tên, mã NS, phòng, chức danh, 4 trục (hình thức/tình trạng/loại vị trí), email, sđt… | ⬜ |
| C2 | Tạo NV hợp lệ tối thiểu | Nhập họ tên + các trường bắt buộc → Lưu | Tạo thành công, xuất hiện trong danh sách | ⬜ |
| C3 | Thiếu họ tên | Bỏ trống tên → Lưu | Báo "Vui lòng nhập họ tên."; không tạo | ⬜ |
| C4 | Mã NS trùng | Nhập mã NS đã tồn tại → Lưu | Báo "Mã nhân sự đã tồn tại…"; không tạo | ⬜ |
| C5 | 4 trục lưu đúng | Tạo NV với hình thức=Online, loại vị trí=CTV… | Mở lại hồ sơ thấy đúng các trục đã chọn | ⬜ |
| C6 | CCCD sai định dạng | Nhập CCCD ≠ 12 số → Lưu | Báo lỗi định dạng (regex 12 số); không lưu | ⬜ |
| C7 | Quyền tạo | (Giáo vụ / NV thường) thử gọi tạo | Không có nút tạo / API trả 403 | ⬜ |

---

## 5. NHÓM D — Sửa hồ sơ & dữ liệu pháp lý VN (F-002)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| D1 | Sửa thông tin cơ bản | (HR) mở hồ sơ → Chỉnh sửa → đổi chức danh/sđt → Lưu | Lưu thành công, hiển thị cập nhật ngay | ⬜ |
| D2 | Nhập pháp lý VN | Nhập CCCD (12 số), ngày/nơi cấp, BHYT, nơi KCB, địa chỉ thường trú | Lưu đúng; tab Thông tin hiển thị các trường này (với HR) | ⬜ |
| D3 | Địa chỉ tạm trú | Bỏ tick "Giống thường trú" → nhập tạm trú khác | Lưu & hiển thị tạm trú riêng; khi tick lại → "Giống thường trú" | ⬜ |
| D4 | MST/BHXH định dạng | Nhập MST (10/13 số), BHXH (10 số) sai định dạng | Báo lỗi regex; nhập đúng thì lưu | ⬜ |
| D5 | Ngày cấp CCCD hợp lệ | Nhập ngày cấp > hôm nay | Báo lỗi (≤ hôm nay) | ⬜ |

---

## 6. NHÓM E — Người phụ thuộc (F-003)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| E1 | Thêm NPT (HR) | Hồ sơ → tab Thông tin → "Thêm NPT" → nhập họ tên, quan hệ, ngày sinh, giảm trừ từ → Lưu | Dòng NPT xuất hiện trong bảng | ⬜ |
| E2 | Sửa NPT | Bấm sửa 1 NPT → đổi → Lưu | Cập nhật đúng | ⬜ |
| E3 | Xoá NPT | Bấm xoá → xác nhận | NPT biến mất | ⬜ |
| E4 | Ngày kết thúc hợp lệ | Nhập "Đến" < "Giảm trừ từ" | Báo lỗi; không lưu | ⬜ |
| E5 | NV tự thêm NPT (M-11) | Login NV thường → "Hồ sơ của tôi" → tự thêm NPT | Thêm được, không cần HR duyệt | ⬜ |

---

## 7. NHÓM F — Thử việc & 3 cổng đánh giá (F-004/005, M-01/M-02)

> 3 cổng: **tuần-2 (2w)**, **tháng-1 (1m)**, **tháng-2 (2m)**. Mỗi cổng 3 kết quả: **Đạt / Không đạt / Gia hạn**.
> Người duyệt: HR Manager / quản lý trực tiếp / trưởng phòng của NV.

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| F1 | Xem dòng thời gian | (HR) hồ sơ NV Thử việc Nhóm B → tab Thử việc | Hiện mốc tuần-2 / tháng-1 / tháng-2 với ngày đến hạn (due) | ⬜ |
| F2 | Cổng tuần-2 = Đạt | Điền kết quả tuần-2 = **Đạt** + nhận xét → lưu | Ghi kết quả + ngày + người đánh giá; mở cổng tháng-1 (AUT) | ⬜ |
| F3 | Cổng tuần-2 = Không đạt | NV khác: tuần-2 = **Không đạt** | Ghi nhận; (theo AUT-001) gợi ý luồng nghỉ thử việc | ⬜ |
| F4 | Cổng tuần-2 = Gia hạn | NV khác: tuần-2 = **Gia hạn** | Tiếp tục thử việc, KHÔNG kết thúc; hẹn tái đánh giá | ⬜ |
| F5 | Tháng-1 = Đạt → chính thức sớm | NV đã qua tuần-2: tháng-1 = **Đạt** | Trạng thái chuyển **Chính thức** sớm; ghi ngày chính thức | ⬜ |
| F6 | Cổng tháng-2 = Đạt | NV: tháng-2 = **Đạt** | (AUT-002) trạng thái = Chính thức, set ngày chính thức | ⬜ |
| F7 | Quyền duyệt — trưởng phòng | (Trưởng phòng) duyệt cổng cho NV **phòng mình** | Cho phép (dù không thuộc nhóm HR) | ⬜ |
| F8 | Chặn duyệt ngoài phạm vi | (Trưởng phòng) duyệt NV **phòng khác** | **403** "Bạn không có quyền duyệt nhân viên này." | ⬜ |
| F9 | NV thường không duyệt được | (NV thường) gọi API gate | 403 | ⬜ |

---

## 8. NHÓM G — Thử giảng giảng viên Nhóm A (F-008)

> Hiện với NV hình thức **online** hoặc tình trạng **parttime/ctv/advisor**.

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| G1 | Khối thử giảng xuất hiện | (HR) hồ sơ NV Nhóm A → tab Thử việc | Có khối "Thử giảng": ngày, lớp, điểm phương pháp, điểm nội dung, kết quả | ⬜ |
| G2 | Ghi kết quả Đạt | Nhập ngày ≤ hôm nay, lớp, 2 điểm (1–10), kết quả=Đạt → lưu | Lưu thành công | ⬜ |
| G3 | Điểm ngoài 1–10 | Nhập điểm = 0 hoặc 11 | Báo lỗi ràng buộc | ⬜ |
| G4 | Fail cần nhận xét | Kết quả=Không đạt nhưng bỏ trống nhận xét | Báo lỗi yêu cầu nhận xét | ⬜ |
| G5 | Ngày tương lai | Nhập ngày > hôm nay | Báo lỗi | ⬜ |

---

## 9. NHÓM H — Tài sản (F-006, M-06)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| H1 | Cấp tài sản | (HR) hồ sơ → tab Tài sản → Cấp → chọn loại, mã, ngày cấp → lưu | Dòng tài sản trạng thái "assigned" | ⬜ |
| H2 | Thu hồi | Bấm Thu hồi 1 tài sản → nhập ngày | Trạng thái "returned" | ⬜ |
| H3 | Chuyển giao | Chuyển giao tài sản cho NV khác | Trạng thái "transferred"; tài sản gắn NV mới | ⬜ |
| H4 | Loại tài sản mới | (HR) thêm loại tài sản chưa có | Tạo & chọn được loại mới | ⬜ |
| H5 | Đếm Smart count | Tab "Tài sản (n)" | n = số tài sản đang giữ (assigned) | ⬜ |

---

## 10. NHÓM I — Thăng tiến & lương (F-007, M-03/M-04/M-05)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| I1 | Xem lịch sử thăng tiến | (HR Mgr) hồ sơ → tab Thăng tiến | Danh sách mốc: ngày, chức danh từ→đến, phòng, lý do | ⬜ |
| I2 | Thêm mốc thăng tiến | Thêm mốc: ngày, chức danh mới, lương từ→đến, **lý do + link bằng chứng** → lưu | Lưu thành công; bắt buộc lý do + evidence (M-04) | ⬜ |
| I3 | Thiếu lý do/bằng chứng | Bỏ trống lý do hoặc link | Báo lỗi bắt buộc | ⬜ |
| I4 | Lương chỉ HR Mgr thấy (M-05) | (HR **User** thường, không Manager) xem tab Thăng tiến | Cột lương **ẩn**; (HR Manager) thấy lương | ⬜ |
| I5 | Tự sinh mốc khi lên chính thức | Cho 1 NV lên chính thức (cổng tháng-2 Đạt) rồi xem Thăng tiến | Có mốc tự sinh "lên chính thức" (M-03) | ⬜ |

---

## 11. NHÓM J — Chứng chỉ & cảnh báo hết hạn (F-008/009, M-07)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| J1 | Thêm chứng chỉ | (HR) hồ sơ → tab Thông tin → "Thêm chứng chỉ" → chọn nhóm bằng (Ngôn ngữ/Chuyên môn), cấp độ, ngày cấp, hết hạn → lưu | Dòng chứng chỉ xuất hiện | ⬜ |
| J2 | Xác minh | Bật/tắt "xác minh" 1 chứng chỉ | Badge đổi "Đã xác minh"/"Chưa" | ⬜ |
| J3 | Trạng thái hết hạn | Chứng chỉ có hạn quá khứ | Badge cảnh báo "hết hạn" (đỏ) | ⬜ |
| J4 | Xoá chứng chỉ | Xoá → xác nhận | Biến mất | ⬜ |
| J5 | Cảnh báo sắp hết hạn | Console: `fetch('/hocba-hrm/api/employees/cert-alerts').then(r=>r.json()).then(console.log)` | Trả các chứng chỉ sắp/đã hết hạn (≤60 ngày) | ⬜ |

---

## 12. NHÓM K — Nhận việc / Onboarding (M-09)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| K1 | Trang Nhận việc | (HR) menu *Nhận việc* | Danh sách NV đang onboarding/thử việc với tiến độ | ⬜ |
| K2 | Thuật ngữ | Kiểm nhãn | Dùng "Nhận việc" (không phải "Nhập việc") | ⬜ |

---

## 13. NHÓM L — Self-service "Hồ sơ của tôi" (M-10/M-11)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| L1 | Xem hồ sơ mình | (NV thường) "Hồ sơ của tôi" | Thấy đầy đủ hồ sơ của CHÍNH MÌNH (gồm pháp lý/lương của bản thân) | ⬜ |
| L2 | Tự sửa liên hệ/địa chỉ | Sửa sđt/email cá nhân/địa chỉ → lưu | Lưu được (chỉ field self-service); KHÔNG sửa được lương/trạng thái/chức vụ | ⬜ |
| L3 | Tự đổi ảnh | Upload ảnh đại diện | Ảnh cập nhật | ⬜ |
| L4 | Không leo thang | (NV) thử gọi `POST /api/employee/<id người khác>` | 403 / không tác động | ⬜ |
| L5 | Vai trò quản lý ẩn cá nhân (M-10) | Login Trưởng phòng / Giáo vụ | KHÔNG có "Hồ sơ của tôi" (dùng tài khoản cá nhân riêng) | ⬜ |

---

## 14. NHÓM M — Bảo mật dữ liệu nhạy cảm (M-05, BR-011)

| ID | Mục tiêu | Bước | Kết quả mong đợi | KQ |
|---|---|---|---|---|
| M1 | Lương — HR Manager | (HR Mgr) xem hồ sơ NV khác | Thấy lương | ⬜ |
| M2 | Lương — HR User | (HR User, không Manager) xem NV khác | KHÔNG thấy lương người khác | ⬜ |
| M3 | CCCD/MST/BHXH ẩn ngoài HR Mgr | (HR User) xem hồ sơ | CCCD hiển thị nhưng MST/BHXH chỉ HR Manager (đối chiếu InfoTab) | ⬜ |
| M4 | NV xem lương của mình | (NV thường) "Hồ sơ của tôi" | Thấy lương CHÍNH MÌNH | ⬜ |
| M5 | NV không xem người khác | (NV) cố xem hồ sơ người khác | Không truy cập được | ⬜ |

---

## 15. Kiểm thử hồi quy nhanh (sau mỗi lần sửa bug)

- [ ] Backend test Employees còn xanh:
  `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees,hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test`
- [ ] SPA build lại không lỗi: `cd frontend && npm run build`
- [ ] Đăng nhập lại 4 vai trò, smoke test danh sách + mở 1 hồ sơ.

---

## 16. NHẬT KÝ BUG (điền khi test)

| Bug ID | Nhóm/Ca | Mô tả lỗi | Bước tái hiện | Mong đợi | Thực tế | Mức độ (Cao/TB/Thấp) | Trạng thái | Người gặp |
|---|---|---|---|---|---|---|---|---|
| BUG-001 |  |  |  |  |  |  | Mới |  |
| BUG-002 |  |  |  |  |  |  | Mới |  |
| BUG-003 |  |  |  |  |  |  | Mới |  |

> Quy ước mức độ: **Cao** = sai nghiệp vụ/lộ dữ liệu/crash; **TB** = sai hiển thị/validation thiếu; **Thấp** = UI/nhãn/cosmetic.

---

## 17. Tổng kết

- Tổng số ca: ~60. Pass: ___ / ___ · Fail: ___ · Lưu ý: ___
- Người test: __________ · Ngày: ________ · Môi trường: local `hocba_hrm` / Neon
- Kết luận nghiệm thu module Employee: ☐ Đạt ☐ Cần sửa (xem nhật ký bug)
