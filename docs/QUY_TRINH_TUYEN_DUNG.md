# Quy trình tuyển dụng Học Bá — Tài liệu nghiệp vụ & kết quả kiểm thử

> **Mục đích:** Mô tả đầy đủ luồng tuyển dụng trên hệ thống HRM Học Bá để trình bày cho khách hàng.
> **Phạm vi:** Module `hocba_recruitments` + SPA `/hocba-hrm` (tab **Tuyển dụng**) + trang tuyển dụng công khai `/jobs`.
> **Đã kiểm thử end-to-end ngày 16/06/2026** bằng 2 tài khoản thật (xem mục 6). Kết quả: **đạt toàn bộ**.

---

## 1. Hai vai trò trong quy trình

| Vai trò | Tài khoản test | Quyền | Làm gì |
|---|---|---|---|
| **HR Manager** | `hr.manager` (mật khẩu `hocba@123`) | Nhóm tuyển dụng (`group_hr_recruitment_user`) → **xem + tạo + sửa** | Toàn bộ nghiệp vụ tuyển dụng: phiếu yêu cầu, đăng tuyển, lọc CV, phỏng vấn, offer, gửi mail. |
| **Ứng viên** | đóng vai bởi `nv.thuviec` (NV thử việc, **không HR**) | Khách / người dùng thường → **không có quyền tuyển dụng** | Nộp hồ sơ qua **trang công khai `/jobs`**. Không truy cập được màn quản trị tuyển dụng. |

> **Kiểm chứng phân quyền:** Khi `nv.thuviec` gọi API ghi của tuyển dụng → hệ thống trả **403 Forbidden**. Khi đọc → cờ `isRecruiter = false` (chỉ xem, không có nút thao tác).

---

## 2. Hai cửa vào hệ thống

| Đối tượng | Đường vào | Ghi chú |
|---|---|---|
| HR | `http://localhost:8069/hocba-hrm` → tab **Tuyển dụng** | Đăng nhập bằng tài khoản nội bộ. SPA gồm 7 tab (mục 4). |
| Ứng viên | `http://localhost:8069/jobs` | Trang web công khai, **không cần đăng nhập**. Chỉ hiển thị vị trí đã **Đăng tuyển**. |

---

## 3. Sơ đồ luồng tổng thể (10 bước)

Mỗi hồ sơ ứng viên đi qua 10 **giai đoạn (stage)** trong pipeline tuyển dụng:

```
[HR]  1. Yêu cầu tuyển dụng        ──► phiếu YCTU được duyệt
[HR]  2. Đăng tuyển & tổng hợp CV  ──► vị trí publish lên /jobs
 │
[ỨNG VIÊN]  nộp hồ sơ qua /jobs  ──────────────┐
 │                                              ▼
[HR]  3. Lọc CV                    ──► Pass / Fail / Tiềm năng + gọi điện (Đồng ý PV)
[HR]  4. Lên lịch phỏng vấn        ──► khai báo lịch rảnh, hẹn ngày/giờ/người PV
[HR]  5. Hẹn & mời phỏng vấn       ──► gửi MAIL "Thư mời phỏng vấn" (tự điền thông tin UV)
[HR]  6. Phỏng vấn                 ──► tiến hành phỏng vấn
[HR]  7. Kết quả phỏng vấn         ──► Đã đến + Pass/Fail
        │
        ├─ Fail ─► gửi MAIL "Thông báo kết quả" (từ chối)
        │
        └─ Pass ▼
[HR]  8. Gửi Offer                 ──► nhập offer (lương/COM) + ngày nhận việc
                                       gửi MAIL "Thư mời nhận việc"
[HR]  9. Onboarding                ──► gửi MAIL "Chào mừng đến với Học Bá"
[HR] 10. Bàn giao nhân sự          ──► nhận việc chính thức (hired)
```

10 stage này cấu hình sẵn trong hệ thống (model `hr.recruitment.stage`), kèm **tiêu chí hoàn thành** và **người phụ trách** cho từng bước (xem SPEC.md §6.2).

---

## 4. Các màn hình HR (SPA tab Tuyển dụng)

| Tab | Dùng cho bước | Nội dung |
|---|---|---|
| **Danh sách CV** | 3 — Lọc CV | Toàn bộ ứng viên, cột Kết quả lọc (badge), trạng thái gọi điện, ngày/giờ/người PV. HR có nút **Thêm CV** thủ công. |
| **Vị trí tuyển dụng / JD** | 2 — Đăng tuyển | Danh sách vị trí + nút **Đăng tuyển / Ngừng đăng**. Vị trí đã đăng → lên `/jobs`. |
| **Phiếu yêu cầu** | 1 — Yêu cầu tuyển dụng | Phiếu YCTU từ các phòng ban, luồng duyệt: Nháp → Chờ duyệt → Đang tuyển → Đóng. |
| **Danh sách PV** | 4–7 — Phỏng vấn | Lịch rảnh phỏng vấn theo tuần + ứng viên đang phỏng vấn, trạng thái Đã đến/Không đến, kết quả. |
| **Offer & Nhận việc** | 8–10 — Offer/Onboarding | Ứng viên ở bước offer: nội dung offer, ngày nhận việc, xác nhận của UV. |
| **Mail mẫu tuyển dụng** | mọi bước | 4 mẫu mail Học Bá, **xem trước** (tự điền dữ liệu UV) trước khi gửi. |
| **Lịch sử gửi mail** | mọi bước | Toàn bộ mail đã gửi cho ứng viên, kèm trạng thái (Đã gửi / Đang chờ / Lỗi). |

---

## 5. Mail tự động — "tự lấy thông tin ứng viên"

Hệ thống có sẵn **4 mẫu mail**, tự render dữ liệu của đúng ứng viên đang chọn:

| Mẫu | Dùng khi | Tự điền |
|---|---|---|
| Thư mời phỏng vấn | Sau khi UV **Đồng ý PV** (bước 5) | Tên UV, vị trí, **ngày/giờ phỏng vấn**, email người nhận |
| Thông báo kết quả phỏng vấn | Khi **Fail** (bước 7) | Tên UV, vị trí |
| Thư mời nhận việc | Khi **Pass** (bước 8) | Tên UV, vị trí |
| Chào mừng đến với Học Bá | Ngày nhận việc (bước 9) | Tên UV |

Cơ chế: các biến `{{ object.partner_name }}`, `{{ object.email_from }}`, `{{ object.job_id.name }}`, `{{ object.interview_date }}`… được thay bằng dữ liệu thật. **Ô người nhận (To) tự điền email ứng viên.** HR có thể sửa nội dung ngay tại màn xem trước trước khi gửi.

> **Lưu ý gửi mail thật:** Tính năng đã hoàn chỉnh; mail được đẩy vào hàng đợi. Để mail **bay ra ngoài** cần cấu hình **Outgoing Mail Server (SMTP)** một lần (Settings → Technical → Email → Outgoing Mail Servers). Khi chưa cấu hình, mail vẫn được ghi nhận trong "Lịch sử gửi mail" nhưng dừng ở trạng thái chờ gửi.

---

## 6. Kết quả kiểm thử thực tế (16/06/2026)

Chạy đầy đủ một vòng tuyển dụng với ứng viên demo. Mọi bước **đạt**.

| # | Bước | Ai | Thao tác | Kết quả |
|---|---|---|---|---|
| 0 | Phân quyền | `nv.thuviec` | Gọi API ghi tuyển dụng | ✅ Bị chặn **403 Forbidden**; đọc → `isRecruiter=false` |
| 1 | Phiếu yêu cầu | `hr.manager` | Tạo YCTU/2026/06/022 → Gửi duyệt → BP duyệt | ✅ `draft → submitted → recruiting` |
| 2 | Đăng tuyển | `hr.manager` | Tạo vị trí "NV tư vấn tuyển sinh (demo)" + Đăng tuyển | ✅ Hiện công khai tại `/jobs/...-39` |
| 3 | **Ứng viên nộp hồ sơ** | Ứng viên (công khai) | Điền form tại `/jobs/apply/...` | ✅ Tạo hồ sơ **#598**, vào tab Danh sách CV của HR |
| 4 | Lọc CV | `hr.manager` | Đặt Kết quả lọc = **Pass**, Gọi điện = **Đồng ý PV** | ✅ Stage → "Lọc CV" |
| 5 | Lên lịch PV | `hr.manager` | Hẹn 19/06 10h00, người PV; tạo 1 slot lịch rảnh | ✅ Stage → "Lên lịch phỏng vấn", slot tạo OK |
| 6 | Mời PV | `hr.manager` | Xem trước + **gửi mail Thư mời phỏng vấn** | ✅ Tiêu đề tự điền "...VỊ TRÍ Tư vấn tuyển sinh"; To = email UV; gửi 1/1 |
| 7 | Phỏng vấn → Kết quả | `hr.manager` | Đã đến = **present**, Kết quả = **Pass** | ✅ Stage → "Kết quả phỏng vấn" |
| 8 | Offer | `hr.manager` | Nhập offer (lương + COM), ngày nhận việc 01/07, UV xác nhận; gửi **Thư mời nhận việc** | ✅ Stage → "Gửi Offer"; gửi 1/1 |
| 9 | Onboarding | `hr.manager` | Stage → Onboarding; gửi **mail Chào mừng** | ✅ gửi 1/1 |
| 10 | Lịch sử mail | `hr.manager` | Mở tab Lịch sử gửi mail | ✅ Hiện đủ **3 mail** đã gửi cho UV #598 |

**Dữ liệu demo còn lại sau test:** hồ sơ ứng viên #598, phiếu YCTU/2026/06/022, vị trí #39, 1 slot phỏng vấn, 3 bản ghi mail — có thể giữ làm ví dụ demo hoặc xóa.

---

## 7. Lỗi phát hiện & đã sửa trong quá trình test

**Tab "Lịch sử gửi mail" bị lỗi 404** khi tồn tại bản ghi mail trỏ tới một ứng viên đã bị xóa.
- Nguyên nhân: `controllers/main.py` duyệt `mail.message` rồi `browse(res_id)` và đọc field — với hồ sơ đã xóa sẽ ném `MissingError` làm hỏng cả trang.
- Đã sửa: thêm `.exists()` để bỏ qua hồ sơ không còn tồn tại (`a = Applicant.browse(m.res_id).exists()`).
- Sau sửa: tab Lịch sử gửi mail trả về bình thường (HTTP 200), hiển thị đủ các mail.

---

## 8. Cách chạy lại để demo

1. Khởi động hệ thống: `docker compose up -d` (Odoo tại `http://localhost:8069`).
2. **Ứng viên:** mở `/jobs` → chọn vị trí đang đăng → **Apply** → điền form → gửi.
3. **HR:** đăng nhập `hr.manager` / `hocba@123` → vào `/hocba-hrm` → tab **Tuyển dụng** → xử lý hồ sơ theo 10 bước ở mục 3.
4. Xem mail tự điền tại tab **Mail mẫu** (nút Xem trước) và **Lịch sử gửi mail**.

> Chi tiết kỹ thuật (model, field, API) xem `custom-addons/hocba_recruitments/SPEC.md` và `docs/SPEC_API_RECRUITMENT.md`.
