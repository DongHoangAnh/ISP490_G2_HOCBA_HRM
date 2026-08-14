# Spec — User manual module Employee (ISP490_G2), 14/08/2026

Bản hướng dẫn sử dụng cho **module Employee** (owner: Vu/Tân), viết theo đúng khuôn
`ISP490_G2_User_manual_Recruitment_v1.0.docx` của Việt để hai tài liệu bàn giao đồng bộ.

- Thành phẩm: `docs/specs/employees/user_manual/out/ISP490_G2_User_manual_Employee_v1.0.docx`
- Nguồn dựng lại: `docs/specs/employees/user_manual/` (script python-docx + ảnh)
- Đối chiếu nghiệp vụ: 13 FS tại `docs/specs/employees/fs/out/`

## 1. Quyết định đã chốt (user duyệt 14/08/2026)

| Điểm | Chốt |
|---|---|
| Phạm vi | **Chỉ module Employee** — 12 quy trình EMP-BP-01…12. Không đụng Đánh giá/Tuyển dụng/Chấm công/Lương/Nghỉ phép. |
| Ngôn ngữ | **Thân bài tiếng Anh**, giữ nguyên nhãn UI tiếng Việt (Nhân viên, Nhận việc, Gia hạn…) — y hệt bản Recruitment. |
| Ảnh | **Chụp thật** từ app đang chạy bằng Selenium (như đợt UT/BPT), không dùng ảnh giả/placeholder. |
| Kiểu file | Mượn `styles.xml` / numbering / theme / trang bìa của bản Recruitment làm **donor**, dựng body bằng python-docx. |

## 2. Cấu trúc tài liệu

Bìa → Change history → FPT Signature → Table of Contents (field, cập nhật bằng
"Update Field") → 1. OVERVIEW → 2. USER MANUAL → Appendix A → Appendix B.

### 1. OVERVIEW
- **1.1 Process used in guide document** — bảng 12 quy trình EMP-BP-01…12.
- **1.2 The employee lifecycle** — `Thử việc → Chính thức → Nghỉ việc`, cộng 4 trục
  phân loại (loại vị trí / hình thức làm việc / loại nhân sự / phòng ban) quyết định
  quy trình nhận việc nào được gán.
- **1.3 Roles and permissions** — Admin · HR Manager · HR officer (**không** xem lương)
  · Giáo vụ (chỉ giáo viên) · Trưởng phòng (phòng mình + phòng con) · nhân viên thường.
  Bám đúng `_cap_edit_emp` / `_cap_see_salary` / `_cap_edit_salary` / `_cap_manage_account`
  trong `hocba_hrm/controllers/main.py`.
- **1.4 How to open the module** — `/hocba-hrm`, sidebar, lưu ý tài khoản vai trò quản lý
  **không** có mục "Hồ sơ của tôi".

### 2. USER MANUAL — mỗi mục gồm *Content · Navigation · Detail implementation*

| Mã | Nội dung | Màn hình SPA | FS |
|---|---|---|---|
| EMP-BP-01 | Hồ sơ nhân viên: tạo, lọc, drawer 5 tab | Nhân viên | 001, 002 |
| EMP-BP-02 | Người phụ thuộc (giảm trừ thuế TNCN) | drawer ▸ Thông tin | 003 |
| EMP-BP-03 | Chứng chỉ, xác minh, cảnh báo hết hạn | drawer ▸ Thông tin | 008, 009 |
| EMP-BP-04 | Cấp phát tài sản | drawer ▸ Tài sản | 006 |
| EMP-BP-05 | Nhận việc theo bước động (Đạt / Gia hạn / Không đạt) | Nhận việc | 004, 005 |
| EMP-BP-06 | Cấu hình quy trình nhận việc, thứ tự ưu tiên, snapshot | Cấu hình nhận việc | 004 |
| EMP-BP-07 | Thăng tiến & lịch sử lương (chỉ đọc; nhập ở màn Đánh giá) | drawer ▸ Thăng tiến | 007, 011 |
| EMP-BP-08 | Dashboard sự nghiệp + Bảng vinh danh | Lộ trình sự nghiệp | 012 |
| EMP-BP-09 | Tài khoản đăng nhập: tạo, khoá, cấp lại mật khẩu | Tài khoản | 013 |
| EMP-BP-10 | Phòng ban: tạo, gán trưởng phòng, lưu trữ | Phòng ban | — |
| EMP-BP-11 | Nghỉ việc: nộp đơn, duyệt 2 cấp, hoàn tất | Nghỉ việc | 010 |
| EMP-BP-12 | Self-service: Hồ sơ của tôi, đổi ảnh, Lộ trình của tôi | Hồ sơ của tôi | 001 |

### Appendix A — Frequently asked questions
Tối thiểu 6 câu, lấy từ lỗi thật hay gặp: BR-010 (chính thức bắt buộc CCCD 12 số +
MST TNCN + số sổ BHXH), NV không có bước nhận việc (thiếu ngày bắt đầu thử việc hoặc
không khớp trục phân loại), không thấy cột Lương CB (HR officer), không mở khoá được
tài khoản người đã nghỉ, đổi quy trình bỏ bước chưa làm, bước "Không đạt" đẩy sang
nghỉ việc.

### Appendix B — Reference documents
Bảng 13 dòng FS-EMP-001…013 khớp `docs/specs/employees/fs/README.md`.

## 3. Ràng buộc nội dung

- Mọi câu mô tả phải **bám code thật** (`frontend/src/features/*`, `hocba_employees`,
  `hocba_hrm/controllers/main.py`), không chép lại FS cũ đã lệch.
- Không mô tả các field lịch sử đã ngừng dùng (`x_eval_*`, `x_trial_*`).
- Nhắc rõ hai điểm hay sai trong vận hành: sửa template **không** ảnh hưởng NV đang
  chạy (snapshot); thứ tự thẻ ở Cấu hình nhận việc **là** thứ tự giành quyền khi một NV
  khớp nhiều quy trình.

## 4. Quy trình dựng

1. `donor/` ← copy bản Recruitment v1.0 để mượn style.
2. `um_content.py` giữ toàn bộ nội dung; `gen_um_docx.py` dựng file.
3. `shots/capture.py` — Selenium đăng nhập 4 tài khoản test, chụp `img/fig-NN-*.png`.
4. `build.py` ghép ảnh + nội dung → `out/*.docx`.

Ảnh chụp từ app đang chạy; nếu Neon không lên thì báo lại chứ không tự chuyển DB local.
