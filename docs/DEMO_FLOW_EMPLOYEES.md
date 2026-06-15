# Kịch bản Demo — Module Nhân sự (Employees)

> Owner: Tân · Cập nhật: 15/06/2026
> Phạm vi: domain **Employees** (Hồ sơ, Nhập việc, Hồ sơ của tôi) trên SPA Học Bá HRM.
> Toàn bộ thao tác đã **inline trong SPA** — không cần mở Odoo backend.

---

## 0. Chuẩn bị trước buổi demo

### 0.1. Môi trường
- **DB demo:** Neon (`neondb`) — DB chung của team.
- **URL SPA:** `http://<host>:8069/hocba-hrm` (mở bằng tài khoản đã đăng nhập Odoo).
- Đảm bảo container Odoo đang chạy (`docker compose up -d odoo`) và đã build FE mới nhất (`cd frontend && npm run build`).

### 0.2. Tài khoản demo (mật khẩu chung: `hocba@123`)
| Đăng nhập | Vai trò | Dùng để demo |
|---|---|---|
| `hr.manager` | HR Manager | Luồng chính — thấy lương, đủ quyền (cổng, thăng tiến, lương) |
| `hr.user` | HR User | So sánh quyền — ẩn lương, ẩn một số nút |
| `nv.test` | Nhân viên chính thức (non-HR) | Màn "Hồ sơ của tôi" (self-service) |
| `nv.thuviec` | Nhân viên thử việc (non-HR) | Self-service góc nhìn NV thử việc |

### 0.3. Dữ liệu demo có sẵn (Neon)
- **10 nhân viên / 6 phòng ban** (Marketing, Sản phẩm R&D_SP, Kinh doanh, Vận hành, Kế toán_HCNS, BOD).
- **Nguyễn Thị Thu Hà (HB.01, Kinh doanh):** đã qua 2 cổng → Chính thức, có **1 mốc thăng tiến** (→ Chuyên viên R&D, 18tr) + **2 bản ghi tài sản** (đã chuyển giao/thu hồi). → Demo hồ sơ "đầy đủ vòng đời".
- **Lý Gia Hân (HB.02, R&D_SP, giảng viên Online part-time):** **thử giảng đang chờ (draft)** + **chứng chỉ HSK 5 (đã xác minh, sắp hết hạn)**. → Demo chấm thử giảng (F-008) trực tiếp + cảnh báo hết hạn chứng chỉ (F-009).
- **Trần Quốc Việt (HB.03), Lê Minh Khôi (HB.04), Vũ Thị Mai (HB.05), Nguyễn Hoàng Nam (HB.06):** nhóm B (Offline), 2 cổng chưa đánh giá (draft) → có thể demo đánh giá cổng.

> ⚠️ **Lưu ý dữ liệu (xem mục 6):** Màn **Nhập việc hiện trống** vì tất cả NV đang ở trạng thái "Chính thức". Để demo trọn vẹn luồng thử việc 2 cổng trên màn Nhập việc, cần 1–2 NV ở trạng thái "Thử việc" (xem mục 6.1).

---

## 1. Mở đầu — Dashboard & tổng quan (1 phút)
**Tài khoản:** `hr.manager`

1. Đăng nhập → SPA mở ở **Dashboard**.
2. Giới thiệu: số liệu nhân sự tổng quan, **widget Cảnh báo chứng chỉ sắp hết hạn (F-009)** — sẽ thấy HSK 5 của Lý Gia Hân nếu trong ngưỡng 60 ngày.
3. Giới thiệu menu trái: **Nhân viên**, **Nhập việc**, **Hồ sơ của tôi** là phạm vi module nhân sự.

**Điểm nhấn:** mọi dữ liệu là thật từ Odoo, không phải mock.

---

## 2. Màn Nhân viên — Hồ sơ tổng quan (F-001) (2 phút)
**Tài khoản:** `hr.manager` → menu **Nhân viên**

1. Danh sách 10 NV: cột Phòng ban, Chức danh, Hình thức, Trạng thái, Ngày vào, **Lương CB** (chỉ HR Manager thấy).
2. **Filter** theo phòng ban (chips) + dropdown trạng thái/hình thức; chuyển **xem Bảng / Thẻ**.
3. Tìm kiếm nhanh theo tên/mã.

**Điểm nhấn:** lọc, tìm, phân loại theo 4 trục (phòng ban, hình thức, trạng thái, loại vị trí).

---

## 3. Thêm / Sửa nhân viên ngay trong SPA (2 phút)
**Tài khoản:** `hr.manager`

1. Bấm **Thêm nhân viên** → form 3 nhóm:
   - **Thông tin cơ bản:** họ tên, mã, phòng ban, chức danh (lọc theo phòng ban), hình thức, tình trạng, loại vị trí, ngày bắt đầu thử việc, email, điện thoại.
   - **Hồ sơ pháp lý (F-002):** ngày sinh, CCCD, ngày/nơi cấp, BHYT, nơi KCB.
   - **Lương & bảo hiểm (chỉ HR Manager):** lương cơ bản, MST TNCN, số sổ BHXH.
2. Lưu → NV mới xuất hiện trong danh sách.
3. Mở 1 NV → **Chỉnh sửa** (cùng form, prefill sẵn).

**Điểm nhấn:** trước đây phải "mở Odoo", nay làm trực tiếp; phân tầng quyền (lương chỉ Manager).

> Gợi ý: dùng NV nháp để thêm, tránh sửa dữ liệu mẫu đẹp. Mã NV phải duy nhất (hệ thống báo lỗi nếu trùng).

---

## 4. Hồ sơ chi tiết — các tab (5–6 phút)
**Tài khoản:** `hr.manager` → mở **Nguyễn Thị Thu Hà (HB.01)** (hồ sơ đầy đủ nhất)

### 4.1. Tab Thông tin
- Thông tin cơ bản + **pháp lý (F-002)** + địa chỉ 2 cấp.
- **Người phụ thuộc (F-003):** bấm **Thêm NPT** → form (quan hệ, ngày sinh, ngày giảm trừ…) → lưu → bảng cập nhật. Demo **Sửa / Xoá** từng dòng.
- **Chứng chỉ (F-008):** bấm **Thêm chứng chỉ** → cascade **Loại → Chứng chỉ → Cấp độ** (Tiếng Trung: HSK/HSKK/TOCFL; Sư phạm) + ngày cấp/hết hạn + xác minh. Demo **toggle Xác minh 1 chạm**, **Sửa**, **Xoá**.

### 4.2. Tab Tài sản (F-006)
- Bảng tài sản đã cấp. Với NV đang giữ: nút **Thu hồi** / **Chuyển** (chuyển giao tự tạo bản ghi cho người nhận).
- Bấm **Cấp phát** → chọn loại (11 loại), mã, ngày, tình trạng.

### 4.3. Tab Thăng tiến (F-007) — chỉ HR Manager
- Timeline mốc thăng tiến (HB.01 đã có 1 mốc → Chuyên viên R&D, +lương).
- Bấm **Thêm mốc** → phòng ban/chức vụ/lương mới/quyết định → lưu → **chức danh NV tự cập nhật**.

**Điểm nhấn:** một hồ sơ thể hiện đầy đủ vòng đời NV chính thức.

---

## 5. Luồng Nhập việc — Thử việc 2 cổng & Thử giảng (4 phút)

### 5.1. Thử việc 2 cổng — Nhóm B (F-004/005)
**Tài khoản:** `hr.manager` → mở **Trần Quốc Việt (HB.03)** → tab **Thử việc**

1. Xem **timeline 5 mốc** (Thử việc → ĐG tuần-2 → Cấp thiết bị → ĐG tháng-2 → Chính thức).
2. Ở thẻ **Cổng tuần-2**: bấm **Đạt** → hệ thống tự **cấp thiết bị (AUT-001)** + ghi ngày đánh giá.
3. Ở thẻ **Cổng tháng-2**: bấm **Đạt** → hệ thống tự **chuyển NV sang Chính thức (AUT-002)**.
4. (Tuỳ chọn) Demo **Không đạt** → cảnh báo offboarding (không gia hạn).

**Điểm nhấn:** đánh giá ngay trong SPA, automation chạy nền (cấp thiết bị / lên chính thức).

### 5.2. Thử giảng — Nhóm A / giảng viên (F-008)
**Tài khoản:** `hr.manager` → mở **Lý Gia Hân (HB.02)** → tab **Thử việc**

1. Thấy mục **Đánh giá thử giảng (Nhóm A)** đang **Chưa đánh giá**.
2. Điền **ngày, lớp, điểm phương pháp, điểm chuyên môn, nhận xét** → bấm **Đạt** (hoặc **Không đạt**).
3. Kết quả ghi nhận + hệ thống tạo nhắc HR (ký HĐ thỉnh giảng nếu Đạt).

**Điểm nhấn:** ràng buộc điểm 1–10, "Không đạt" bắt buộc nhận xét.

---

## 6. Phân quyền & Self-service (3 phút)

### 6.1. Hồ sơ của tôi (self-service)
**Tài khoản:** `nv.test` (đăng xuất hr.manager, đăng nhập lại)

1. Vào **Hồ sơ của tôi** → xem hồ sơ **của chính mình** (thông tin, thử việc, tài sản, thăng tiến — chỉ đọc).
2. Bấm **Cập nhật thông tin** → NV chỉ tự sửa **điện thoại + địa chỉ thường trú/tạm trú** (không sửa lương/trạng thái/pháp lý).

### 6.2. So sánh quyền HR User vs HR Manager
- `hr.user`: **không thấy cột Lương CB**, không thấy tab/nút mức lương, không thêm được mốc thăng tiến.
- `hr.manager`: đầy đủ.

**Điểm nhấn:** quyền do backend (model) quyết định, không phải ẩn ở giao diện.

---

## 7. Việc cần chuẩn bị / lưu ý khi demo

| # | Vấn đề | Xử lý đề xuất |
|---|---|---|
| 7.1 | **Màn Nhập việc trống** (mọi NV đang "Chính thức") → không có danh sách thử việc để demo luồng end-to-end trên màn này | Đặt 1–2 NV về trạng thái **Thử việc** (vd HB.04/HB.05) trước buổi demo. *Cần xác nhận vì ghi vào DB team.* Hoặc demo cổng trực tiếp từ hồ sơ HB.03 (mục 5.1) |
| 7.2 | HB.03–HB.06 đang "Chính thức" nhưng 2 cổng vẫn "draft" (chưa đánh giá) — hơi mâu thuẫn khi soi kỹ | Nếu set lại trạng thái thử việc (7.1) sẽ nhất quán |
| 7.3 | NPT: tài khoản `hr.user` **chưa** thêm/sửa được người phụ thuộc (chỉ Manager) — nếu demo phần NPT bằng hr.user sẽ báo lỗi quyền | Demo NPT bằng `hr.manager`; hoặc chốt mở quyền cho HR User (1 dòng cấu hình) — xem [Câu hỏi verify](CUSTOMER_VERIFY_QUESTIONS.md) |
| 7.4 | HB.06 (Nguyễn Hoàng Nam, BOD) chưa có chức danh | Bổ sung chức danh nếu cần ảnh đẹp |

---

## 8. Tóm tắt mapping chức năng → màn demo
| Chức năng | Màn / Tab demo | Tài khoản |
|---|---|---|
| F-001 Hồ sơ tổng quan | Nhân viên (list + drawer) | hr.manager |
| F-002 Trường pháp lý | Form Thêm/Sửa · tab Thông tin | hr.manager |
| F-003 Người phụ thuộc | Tab Thông tin → NPT | hr.manager |
| F-004/005 Thử việc 2 cổng + automation | Tab Thử việc (Nhóm B) | hr.manager |
| F-006 Tài sản | Tab Tài sản | hr.manager / hr.user |
| F-007 Thăng tiến | Tab Thăng tiến | hr.manager |
| F-008 Thử giảng | Tab Thử việc (Nhóm A) | hr.manager |
| F-008 Chứng chỉ / skill | Tab Thông tin → Chứng chỉ | hr.manager / hr.user |
| F-009 Cảnh báo hết hạn chứng chỉ | Dashboard (widget) | hr.manager |
| Self-service | Hồ sơ của tôi | nv.test / nv.thuviec |
