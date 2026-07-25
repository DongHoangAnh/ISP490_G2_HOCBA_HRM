# HƯỚNG DẪN TEST TAY — Nhân viên · Nhận việc · Nghỉ việc

**Ngày:** 10/07/2026 · Phạm vi: 3 module đã hoàn thiện, test **hoàn toàn trên giao diện SPA `/hocba-hrm`** (không thao tác trong backend Odoo).
Đây là kịch bản **bấm tay trên màn hình** để nghiệm thu nghiệp vụ + phân quyền.

---

## 0. Chuẩn bị (5 phút)

1. Chạy hệ thống (mặc định Neon):
   ```bash
   cd D:\DoAnOdooHRM\DoAnHrm\ISP490_G2_HOCBA_HRM
   docker compose -f docker-compose.yml up -d odoo
   ```
2. Mở trình duyệt vào **`http://localhost:8069/hocba-hrm`**.
   - ⚠️ Nếu đăng nhập xong không thấy dữ liệu quen thuộc → máy có 2 Odoo cùng cổng, thử **`http://[::1]:8069/hocba-hrm`**.
   - Phải vào **thẳng** `/hocba-hrm` (đừng dừng ở trang chủ website).
3. SPA có **màn đăng nhập riêng** (logo Học Bá, ô "Tài khoản" + "Mật khẩu"). Đăng nhập tại đây, **không** qua trang Odoo.
4. Đăng xuất: bấm biểu tượng **⎋ (logout)** ở góc dưới-trái sidebar (thẻ tên tài khoản).

**Tài khoản test — mật khẩu chung `Hocba@2026`:**

| Tài khoản | Vai trò | Đăng nhập xong sẽ thấy |
|---|---|---|
| `test_admin@hocba.vn` | Admin | Toàn bộ menu, mọi phòng ban |
| `test_hrmanager@hocba.vn` | HR Manager (**HRM**) | Toàn bộ nghiệp vụ + **cột Lương** + duyệt cổng + HR duyệt nghỉ |
| `test_hr@hocba.vn` | HR officer (**HR**) | Quản lý hồ sơ, **không thấy Lương** |
| `test_giaovu@hocba.vn` | Giáo vụ (**GV**) | Quản lý **giáo viên** (thêm/sửa/xoá + cấp tài sản) + **xem cột Lương**; **không** quyền tài khoản/phòng ban |
| `test_truongphong@hocba.vn` | Trưởng phòng (**TP**) | Quản lý NV **phòng mình** (thêm/sửa/xoá + cấp tài sản) + **xem cột Lương**; **không** quyền tài khoản/phòng ban |
| `test_employee@hocba.vn` | Nhân viên (**NV**) | Menu cá nhân: Chấm công, Nghỉ phép, **Nghỉ việc**, **Hồ sơ của tôi** |
| `test_employee2@hocba.vn` | Nhân viên phụ | Self-service (thuộc Phòng Test QA) |

> **Menu SPA theo vai trò** (sidebar trái):
> - **HRM/HR/Admin/GV/TP** → nhóm *"Quản lý nhân sự"*: **Nhân viên · Nhận việc · Chấm công · Nghỉ phép · Nghỉ việc · Bảng lương · Tuyển dụng** (HR/Admin còn có Tài khoản, Phòng ban). Các tài khoản này **không** có "Hồ sơ của tôi".
> - **Quyền quản lý hồ sơ**: HRM/HR/Admin thao tác **mọi** nhân sự; **TP** giới hạn **phòng mình** (gồm phòng con); **GV** giới hạn **giáo viên**. Trong phạm vi, TP/GV **thêm/sửa/xoá hồ sơ + cấp/thu hồi tài sản + quản lý NPT/chứng chỉ** và **xem** cột Lương CB (**không** sửa mức lương; **không** vào Tài khoản/Phòng ban; thăng tiến do HR Manager). HR officer sửa hồ sơ nhưng **không** thấy Lương.
> - **NV thường** → nhóm *"Cá nhân"*: **Chấm công · Nghỉ phép · Nghỉ việc · Hồ sơ của tôi**.

> Quy ước: ✅ = kết quả mong đợi. ⚠️ = thao tác thay đổi dữ liệu thật.

> ⚠️ **Cảnh báo dữ liệu thật:** đánh giá cổng thử việc và **Hoàn tất** đơn nghỉ việc làm đổi trạng thái thật (khi "Hoàn tất", hồ sơ NV bị lưu trữ và **khoá đăng nhập**). Ưu tiên test trên NV mới tạo hoặc `test_employee`; xem §6 (khôi phục).

---

## 1. Module NHÂN VIÊN — vai trò HR Manager

Đăng nhập `test_hrmanager` → sidebar bấm **Nhân viên**.

### 1.1 Danh sách, lọc, tìm kiếm

| # | Thao tác trên SPA | ✅ Mong đợi |
|---|---|---|
| 1.1.1 | Xem tiêu đề trang | "Nhân viên" + dòng "N nhân sự · M phòng ban · dữ liệu trực tiếp từ Odoo" |
| 1.1.2 | Bấm các **chip phòng ban** (có số đếm) | Lọc đúng theo phòng; số đếm khớp |
| 1.1.3 | Đổi dropdown **Mọi trạng thái** / **Mọi hình thức** | Lọc đúng (Chính thức / Thử việc / Part-time…) |
| 1.1.4 | Gõ ô **tìm kiếm** trên topbar (tên, mã HB, chức danh, phòng) | Bảng lọc ngay; đổi bộ lọc thì tự về **trang 1** |
| 1.1.5 | Bấm nút chuyển **Bảng / Thẻ** | Đổi 2 kiểu hiển thị |
| 1.1.6 | Dùng **phân trang** dưới bảng (20 dòng/trang) | Chuyển trang đúng |
| 1.1.7 | Nhìn cột **Lương CB** | **Có** (vì HRM) |

### 1.2 Xem chi tiết (drawer)

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 1.2.1 | Bấm 1 dòng NV | Mở drawer với tab: **Thông tin · Thử việc · Tài sản (n) · Thăng tiến (n) · Tài khoản** |
| 1.2.2 | Tab **Thông tin** | Thông tin cơ bản; có thêm bảng **Người phụ thuộc** và **Chứng chỉ** |
| 1.2.3 | Tab **Tài sản** | Danh sách tài sản; có nút thêm/thu hồi |
| 1.2.4 | Tab **Thăng tiến** | Lịch sử thăng tiến/đánh giá |
| 1.2.5 | Đóng drawer (chỉ xem) | Danh sách **không** chớp "Đang tải…" |

### 1.3 Thêm nhân viên — có dữ liệu mẫu

Bấm **+ Thêm nhân viên** (góc phải). Form gồm 3 khối: *Thông tin cơ bản · Hồ sơ pháp lý · Lương & bảo hiểm*.

**📋 Dữ liệu mẫu A — NV chính thức (test ràng buộc CCCD):**

| Trường | Giá trị mẫu |
|---|---|
| Họ và tên * | `Nguyễn Văn Kiểm Thử` |
| Mã nhân sự | `HB.QA.T1` |
| Phòng ban | *Kinh doanh* |
| Chức danh | *(chọn theo phòng)* |
| Hình thức làm việc | `Offline` |
| Tình trạng | `Chính thức` |
| Loại vị trí | `Nhân viên` |
| Email công ty | `kiemthu.t1@hocba.edu.vn` |
| Điện thoại | `0900000101` |
| Ngày sinh | `1996-05-20` |
| CCCD (12 số) | `034096001234` *(phải đủ 12 số, không trùng NV khác)* |
| Ngày cấp CCCD | `2021-03-15` |
| Nơi cấp CCCD | `Cục CS QLHC về TTXH` |
| Lương cơ bản (₫) | `9000000` |
| MST TNCN | `8801234567` |
| Số sổ BHXH | `0123456789` |
| Ngân hàng / Số TK | *Vietcombank* / `0123456789` |

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 1.3.1 | Điền mẫu A **nhưng để trống CCCD** → **Tạo nhân viên** | Báo lỗi ràng buộc (NV chính thức phải có CCCD 12 số — BR-010) |
| 1.3.2 | Nhập CCCD `12345` (thiếu số) → Tạo | Báo lỗi định dạng CCCD |
| 1.3.3 | Nhập CCCD đủ `034096001234` → Tạo | Tạo thành công; NV xuất hiện trong danh sách, chip phòng +1 |
| 1.3.4 | Bỏ trống **Họ và tên** → Tạo | Báo "Vui lòng nhập họ tên." |

### 1.4 Sửa nhân viên

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 1.4.1 | Mở NV vừa tạo → (trong drawer) sửa **Điện thoại** → Lưu | Cập nhật đúng; đóng drawer → danh sách refresh ngầm |

---

## 2. Module NHẬN VIỆC — vai trò HR Manager

> Từ 2026-07-15, thử việc chạy theo **quy trình BƯỚC ĐỘNG** admin cấu hình
> được (màn **Cấu hình nhận việc**). Hệ thống seed sẵn 2 quy trình tái hiện
> luồng cũ:
> - **Thử việc Nhân viên văn phòng** (khớp staff/manager + Offline):
>   ĐG tuần-2 → Cấp thiết bị (tự động) → ĐG tháng-1 (*Đạt → chính thức*) →
>   ĐG tháng-2 (*bước gia hạn — chỉ mở khi tháng-1 "Gia hạn"*).
> - **Thử việc Giáo viên** (khớp loại nhân sự Giáo viên): Thử giảng →
>   Ký hợp đồng thỉnh giảng.
> NV thử việc có **Ngày bắt đầu thử việc** sẽ được gán quy trình khớp tự
> động (snapshot — sửa template sau không ảnh hưởng NV đang chạy).

### 2.1 Tạo sẵn dữ liệu để test (dùng lại form Thêm nhân viên ở §1.3)

**📋 Dữ liệu mẫu B — NV thử việc Nhóm B (2 cổng):**

| Trường | Giá trị |
|---|---|
| Họ và tên | `Trần Thử Việc B` |
| Mã nhân sự | `HB.QA.B1` |
| Phòng ban | *Kinh doanh* |
| Hình thức làm việc | **`Offline`** |
| Tình trạng | **`Thử việc`** |
| Loại vị trí | **`Nhân viên`** |
| Ngày bắt đầu thử việc | *hôm nay* |
| Email / ĐT | `thuviec.b1@hocba.edu.vn` / `0900000201` |

**📋 Dữ liệu mẫu C — NV thử việc Nhóm A (thử giảng):**

| Trường | Giá trị |
|---|---|
| Họ và tên | `Lê Giảng Viên A` |
| Phòng ban | *Giảng viên* |
| Hình thức làm việc | **`Online`** |
| Tình trạng | **`Thử việc`** |
| Loại vị trí | `Nhân viên` |
| Ngày bắt đầu thử việc | *hôm nay* |
| Email / ĐT | `giangvien.a1@hocba.edu.vn` / `0900000202` |

> Sau khi tạo 2 NV trên, vào **Nhận việc** — cả hai phải xuất hiện đúng nhóm.

> Lưu ý mẫu C: để khớp quy trình Giáo viên, đặt **Loại nhân sự = Giáo viên**
> trong hồ sơ (không chỉ Hình thức = Online).

### 2.2 Bảng theo dõi

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 2.2.1 | Vào **Nhận việc** | 4 ô thống kê: *Đang thử việc · Đang chạy quy trình · Chờ đánh giá · Quá hạn bước* |
| 2.2.2 | Xem bảng | Cột: Nhân viên · Phòng ban · Ngày bắt đầu · Quy trình · Tiến độ (n/m bước + thanh %) · Bước hiện tại · Trạng thái |
| 2.2.3 | NV mẫu B | Cột Quy trình = "Thử việc Nhân viên văn phòng"; Bước hiện tại = "Đánh giá tuần-2" kèm **hạn** |
| 2.2.4 | NV mẫu C (đã gán Loại nhân sự Giáo viên) | Quy trình = "Thử việc Giáo viên"; Bước hiện tại = "Thử giảng" |
| 2.2.5 | Bước quá hạn (hạn < hôm nay, đang mở) | Hạn hiển thị **đỏ + ⚠**; ô "Quá hạn bước" đếm tăng; cột Trạng thái thêm "⚠ quá hạn" |

### 2.3 Thao tác bước — NV mẫu B (quy trình văn phòng)

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 2.3.1 | Bấm dòng NV mẫu B | Drawer mở thẳng tab **Thử việc**: header quy trình + thanh tiến độ + danh sách bước dọc |
| 2.3.2 | Bước **Đánh giá tuần-2** → **Đạt** | Bước done ✓; bước "Cấp thiết bị làm việc" **tự hoàn thành** (automation cấp tài sản mặc định); bước "Đánh giá tháng-1" chuyển **Đang chờ** |
| 2.3.3 | Bước chưa tới lượt | KHÔNG có nút thao tác (badge "Chưa tới lượt") |
| 2.3.4 | ĐG tháng-1 → **Gia hạn** | Bước done "Gia hạn"; bước **Đánh giá tháng-2** (bước gia hạn) mở |
| 2.3.5 | ĐG tháng-2 → **Đạt** | NV lên **Chính thức** (badge drawer đổi); các bước sau (nếu có) bị bỏ qua; hiện "Chính thức từ <ngày>" |
| 2.3.6 | (NV khác) ĐG tuần-2 → **Gia hạn** | Bước **giữ nguyên Đang chờ** + nhãn "đã gia hạn ×1" (tái đánh giá tại chỗ — vì bước kế không phải bước gia hạn) |
| 2.3.7 | (NV khác) bước bất kỳ → **Không đạt** (bắt buộc nhập nhận xét) | NV chuyển `exiting` + tự tạo đơn Nghỉ việc (source thử việc); các bước còn lại "Bỏ qua"; Trạng thái bảng → "Không đạt thử việc" |
| 2.3.8 | HR Manager: nút ✎ cạnh hạn của bước đang mở | Sửa được hạn (date picker) |
| 2.3.9 | HR Manager: nút **Đổi quy trình** trên header | Chọn template khác → bước chưa làm bị thay bằng chuỗi mới, bước đã xong giữ lịch sử |
| 2.3.10 | Đóng drawer | Bảng Nhận việc cập nhật tiến độ |

> 📋 Ô **Nhận xét** — mẫu: `"Đạt yêu cầu, tinh thần học hỏi tốt."` / `"Chưa đạt KPI onboarding tuần 2."`

### 2.4 NV mẫu C (quy trình Giáo viên)

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 2.4.1 | Drawer NV mẫu C → tab Thử việc | 2 bước: "Thử giảng" (Đánh giá, đang chờ) → "Ký hợp đồng thỉnh giảng" (Việc cần làm) |
| 2.4.2 | Thử giảng → **Đạt** *(nhận xét mẫu: "PP 8.5/10; CM 9/10 — phát âm chuẩn, quản lớp tốt")* | Bước done; "Ký hợp đồng thỉnh giảng" mở; NV **VẪN thử việc** (thử giảng đạt không tự lên chính thức) |
| 2.4.3 | Hoàn thành "Ký hợp đồng thỉnh giảng" | Chuỗi xong; chuông 🔔 báo HR "Hoàn tất quy trình nhận việc — chờ quyết định" |
| 2.4.4 | (NV khác) Thử giảng → **Không đạt** | Như 2.3.7 (offboarding) |

### 2.5 Màn CẤU HÌNH NHẬN VIỆC (chỉ HR Manager/Admin)

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 2.5.1 | Menu **Cấu hình nhận việc** | Chỉ HR Manager/Admin thấy menu; thấy ≥2 card quy trình seed với danh sách bước |
| 2.5.2 | **Thêm quy trình** → đặt tên, tick tiêu chí, thêm 2-3 bước (kéo ↑↓, chọn loại, hạn +N ngày, cờ) → Lưu | Card mới xuất hiện; NV thử việc tạo MỚI khớp tiêu chí sẽ nhận quy trình này |
| 2.5.3 | Bước "Bước gia hạn" đặt ngay sau bước Việc cần làm → Lưu | Bị chặn với thông báo lỗi ("phải đứng ngay sau một bước Đánh giá") |
| 2.5.4 | Sửa template đang có NV chạy giữa chừng | NV đó **không đổi** lộ trình (snapshot) — kiểm tra lại drawer NV |
| 2.5.5 | **Lưu trữ** một quy trình | Card mờ đi "Đã lưu trữ"; không được gán mới nữa |
| 2.5.6 | Đăng nhập `test_giaovu` / `test_truongphong` | KHÔNG thấy menu Cấu hình nhận việc; gọi thẳng API templates trả 403 |

---

## 3. Module NGHỈ VIỆC — luồng đầy đủ (3 vai trò)

> Trạng thái: **Chờ quản lý duyệt → Chờ HR duyệt → Chờ hoàn tất → Đã nghỉ**. Nhánh phụ: **Từ chối** / **Đã huỷ**.
> Giao diện: **NV** thấy *"Đơn của tôi"* (nút Nộp đơn); **HRM/HR/TP/GV** thấy *"Đơn chờ xử lý"* (nút duyệt).
>
> **Duyệt 2 cấp — theo tên nút trên giao diện:**
> 1. **Cấp 1 — nút "Quản lý duyệt"**: do **Trưởng phòng** (đơn của NV phòng mình) hoặc **Giáo vụ** (đơn của giáo viên) bấm → đơn chuyển **"Chờ HR duyệt"**.
> 2. **Cấp 2 — nút "HR duyệt"**: do **HR/HR Manager/Admin** bấm → đơn chuyển **"Chờ hoàn tất"**.
> 3. **Nút "Hoàn tất"**: do **HR** bấm → hồ sơ **lưu trữ + khoá tài khoản đăng nhập** (chặn nếu còn tài sản chưa thu hồi).
> Nút **"Từ chối"** có ở cả hai cấp. TP/GV **không** thấy nút "HR duyệt"; NV **không** có nút duyệt nào.

### 3.1 Nhân viên nộp đơn — đăng nhập `test_employee`

Sidebar (nhóm *Cá nhân*) → **Nghỉ việc**.

**📋 Dữ liệu mẫu D — đơn nghỉ việc:**

| Trường | Giá trị |
|---|---|
| Loại lý do | `Tự nguyện` |
| Lý do chi tiết * | `Chuyển vào TP.HCM sinh sống, xin nghỉ theo nguyện vọng cá nhân.` |
| Ngày nghỉ dự kiến * | *(để mặc định +30 ngày)* |

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 3.1.1 | Xem màn | Bảng "Đơn nghỉ việc của tôi" + nút **+ Nộp đơn nghỉ** |
| 3.1.2 | Bấm **+ Nộp đơn nghỉ** → để trống Lý do → **Nộp đơn** | Báo "Vui lòng nhập lý do chi tiết." |
| 3.1.3 | Điền mẫu D → **Nộp đơn** | Đơn `OFF/2026/xxxx`, trạng thái **Chờ quản lý duyệt** |
| 3.1.4 | Bấm vào dòng đơn | Modal chi tiết: trạng thái, loại lý do, ngày nộp/nghỉ, QL duyệt, HR duyệt, lý do |
| 3.1.5 | Đơn còn "Chờ quản lý duyệt" → nút **Huỷ** → xác nhận | Đơn chuyển **Đã huỷ** *(muốn chạy tiếp §3.2 thì nộp lại 1 đơn mới, đừng huỷ)* |

### 3.2 Duyệt cấp 1 — Trưởng phòng `test_truongphong`

Sidebar → **Nghỉ việc** (thấy bảng "Đơn nghỉ việc — chờ xử lý").

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 3.2.1 | Xem danh sách | Chỉ thấy đơn của NV **phòng mình** (vd `test_employee`, `test_employee2`); **không** có nút "Nộp đơn" |
| 3.2.2 | Cột **Tài sản** | Badge vàng "n chưa thu" nếu NV còn tài sản chưa thu hồi |
| 3.2.3 | Bấm **Quản lý duyệt** | Đơn chuyển **Chờ HR duyệt**; ô "Quản lý duyệt" ghi tên TP |
| 3.2.4 | (Đơn khác) bấm **Từ chối** → xác nhận | Đơn chuyển **Từ chối** |

### 3.3 Duyệt cấp 2 + Hoàn tất — HR Manager `test_hrmanager`

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 3.3.1 | Vào **Nghỉ việc** | Thấy **mọi** đơn (không giới hạn phòng) |
| 3.3.2 | Đơn "Chờ HR duyệt" → **HR duyệt** | Đơn chuyển **Chờ hoàn tất**; ô "HR duyệt" ghi tên HRM |
| 3.3.3 | NV còn tài sản chưa thu → nút **Hoàn tất** | Bị **khoá**, hover báo "Còn n tài sản chưa thu hồi" |
| 3.3.4 | Vào **Nhân viên** → mở NV đó → tab **Tài sản** → thu hồi hết → quay lại Nghỉ việc | Nút **Hoàn tất** mở |
| 3.3.5 | ⚠️ Bấm **Hoàn tất** → xác nhận | Đơn **Đã nghỉ**; hồ sơ NV bị lưu trữ + **khoá đăng nhập** của NV đó |

### 3.4 Thông báo (chuông 🔔 trên topbar)

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 3.4.1 | Sau mỗi lần đổi trạng thái, bấm chuông 🔔 của người liên quan | Nhận thông báo đúng: đơn mới → QL; duyệt/từ chối/hoàn tất → NV… |
| 3.4.2 | Bấm 1 thông báo | Điều hướng tới đúng màn (Nghỉ việc / Hồ sơ) |

### 3.5 Chặn thao tác sai

| # | Thao tác | ✅ Mong đợi |
|---|---|---|
| 3.5.1 | `test_employee` chỉ thấy đơn của mình | Không thấy đơn người khác |
| 3.5.2 | Nút duyệt hiển thị theo đúng bước | Chưa qua QL thì **không** hiện nút "HR duyệt"; NV không có nút duyệt |

---

## 4. Test riêng vai trò TRƯỞNG PHÒNG (`test_truongphong`)

> TP là **tài khoản quản lý theo phòng ban** → thấy nhóm *"Quản lý nhân sự"*, **không** có "Hồ sơ của tôi". Phạm vi = phòng mình (gồm phòng con).

| # | Màn | Thao tác | ✅ Mong đợi |
|---|---|---|---|
| 4.1 | Sidebar | Quan sát menu | Có Dashboard, Nhân viên, Nhận việc, Chấm công, Nghỉ phép, Nghỉ việc, Bảng lương, Tuyển dụng. **Không** có Tài khoản/Phòng ban; **không** có "Hồ sơ của tôi" |
| 4.2 | **Nhân viên** | Xem danh sách | **Chỉ** NV phòng mình; **có** nút "+ Thêm nhân viên"; **có** cột **Lương CB** (chỉ xem) |
| 4.2b | **Nhân viên** | Bấm **+ Thêm nhân viên** rồi lưu (dữ liệu mẫu §1.3, phòng = phòng mình) | Tạo được NV trong phòng mình. Thử chọn phòng khác/ngoài phạm vi → bị chặn ("Ngoài phạm vi quản lý của bạn.") |
| 4.3 | **Nhân viên** | Bấm 1 NV trong phòng | Drawer: tab **Thông tin · Thử việc · Tài sản · Thăng tiến** (**không** tab "Tài khoản"); có nút **Chỉnh sửa**; xem được CCCD/pháp lý/NPT/chứng chỉ + **Lương cơ bản** |
| 4.3b | **Nhân viên** → tab **Tài sản** | Bấm **Cấp phát** rồi **Thu hồi** | Cấp/thu hồi/chuyển tài sản được cho NV trong phòng |
| 4.3c | **Nhân viên** → tab **Thông tin** | Sửa hồ sơ; thử sửa **mức lương** | Sửa hồ sơ được; **không** có ô sửa Lương (chỉ HR Manager) |
| 4.4 | **Nhận việc** | Xem | Chỉ NV thử việc phòng mình; đánh giá cổng được (dù không thuộc nhóm HR) |
| 4.5 | **Nghỉ việc** | Xem | Bảng "chờ xử lý" chỉ đơn phòng mình; có nút **Quản lý duyệt** (cấp 1) / **Từ chối**; **không** có nút "Nộp đơn" |
| 4.6 | **Nghỉ việc** | Đơn đã ở "Chờ HR duyệt" | **Không** có nút "HR duyệt" (cấp 2 do HR/Admin) |

---

## 5. Test riêng vai trò GIÁO VỤ (`test_giaovu`)

> GV là **tài khoản quản lý theo loại nhân sự = giáo viên** → thấy nhóm *"Quản lý nhân sự"*, phạm vi = **chỉ giáo viên**.

| # | Màn | Thao tác | ✅ Mong đợi |
|---|---|---|---|
| 5.1 | Sidebar | Quan sát menu | Giống TP về cấu trúc; **không** có "Hồ sơ của tôi"; **không** có Tài khoản/Phòng ban |
| 5.2 | **Nhân viên** | Xem danh sách | **Chỉ** nhân sự là **giáo viên**; **có** nút "+ Thêm nhân viên"; **có** cột **Lương CB** (chỉ xem) |
| 5.2a | **Nhân viên** | Bấm **+ Thêm nhân viên** → điền + Tạo | Form tải được; NV tạo ra **mặc định là giáo viên** (đúng phạm vi GV) — không cần chọn loại nhân sự |
| 5.2b | **Nhân viên** | Bấm 1 giáo viên → drawer | Tab **Thông tin · Thử việc · Tài sản · Thăng tiến** (**không** "Tài khoản"); có **Chỉnh sửa**; sửa hồ sơ + **cấp/thu hồi tài sản** được; **không** có ô sửa Lương |
| 5.3 | **Nhận việc** | Xem | Chỉ giảng viên đang thử việc (**Nhóm A**); **chấm thử giảng được** (F-008) |
| 5.4 | **Nhận việc** | Với NV Nhóm B (nếu lọt vào phạm vi) | Không thuộc phạm vi GV → không thấy / không đánh giá |
| 5.5 | **Nghỉ việc** | Xem | Bảng "chờ xử lý" chỉ đơn của **giáo viên**; nút **Quản lý duyệt** (cấp 1) trong phạm vi |
| 5.6 | **Nhân viên** | Thử mở 1 NV phòng Kinh doanh (không phải giáo viên) | **Không** xuất hiện trong danh sách của GV; mở trực tiếp → bị chặn (403) |

---

## 6. Kịch bản E2E xuyên suốt + khôi phục

**Chạy 1 lượt hoàn chỉnh:**
1. `test_hrmanager` tạo **NV mẫu B** (§2.1) → xuất hiện ở **Nhân viên** và **Nhận việc**.
2. Ở **Nhận việc**: cổng tuần-2 **Đạt** → tháng-1 **Gia hạn** → tháng-2 **Đạt** → lên **chính thức**.
3. `test_employee` vào **Nghỉ việc** → nộp **đơn mẫu D**.
4. `test_truongphong` → **Quản lý duyệt**.
5. `test_hrmanager` → **HR duyệt** → (Nhân viên → thu hồi tài sản) → **Hoàn tất**.
6. Kiểm tra chuông 🔔 ở từng vai trò khớp từng bước.

**♻️ Khôi phục sau test (quan trọng):**
- NV mẫu tạo mới: có thể để lại (đánh dấu QA) hoặc nhờ Admin lưu trữ.
- Nếu đã bấm **Hoàn tất** cho `test_employee`: tài khoản bị khoá đăng nhập → **nhờ Admin khôi phục** (bỏ lưu trữ hồ sơ + tài khoản) như nhật ký 05/07 trong [`DB_TEST_DATA.md`](DB_TEST_DATA.md). → **Khuyến nghị:** chỉ chạy tới bước Hoàn tất khi đã thống nhất, hoặc dùng NV mẫu mới thay cho `test_employee`.

---

## 7. Bảng ghi kết quả

| Nhóm case | Pass/Fail | Ghi chú / lỗi |
|---|---|---|
| 1. Nhân viên (HRM) |  |  |
| 2. Nhận việc (HRM) |  |  |
| 3. Nghỉ việc (E2E 3 vai trò) |  |  |
| 4. Trưởng phòng |  |  |
| 5. Giáo vụ |  |  |
| 6. E2E xuyên suốt |  |  |

> Người test: __________ · Ngày: __________ · Môi trường (Neon/local): __________
