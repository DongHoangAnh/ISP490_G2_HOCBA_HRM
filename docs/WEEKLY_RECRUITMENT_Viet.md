# WEEKLY REPORT — Module Tuyển dụng (`hocba_recruitments`)

> **Group:** ISP490_G2_HOCBA_HRM
> **Week:** 16/06/2026 – 20/06/2026
> **In-charge:** Việt — nhánh `Viet/Recruitment`
> Nguồn: `custom-addons/hocba_recruitments/SPEC.md` + git log nhánh.

---

## I. Status Report

| # | Project Task | In-charge | Status | Notes (Work Item in Details) |
|---|--------------|-----------|--------|------------------------------|
| 1 | Backend Odoo — models & views (9 màn) | Việt | Done | `hb.recruitment.request` (state machine draft→submitted→recruiting→closed/refused), `hb.interview.slot` + wizard khai báo lịch tuần, inherit `hr.job` / `hr.applicant` / `hr.recruitment.stage`. Seed: 8 vị trí, 10 bước quy trình, 4 mail template. |
| 2 | SPA Tuyển dụng (React) — 7 tab | Việt | Done | Danh sách CV, Vị trí/JD, Phiếu yêu cầu, Danh sách PV, Offer & Nhận việc, Mail mẫu, Lịch sử gửi mail. Build vào `hocba_hrm`. |
| 3 | API domain `recruitment` (`controllers/main.py`) | Việt | Done | REST `/hocba-hrm/api/recruitment/*`: CV/ứng viên (+upload PDF), jobs/JD, phiếu yêu cầu, mail template (preview/send), mail-logs, interview-slots. Hợp đồng tại `docs/SPEC_API_RECRUITMENT.md`. |
| 4 | Sửa inline Danh sách CV + import lịch tuần | Việt | Done | Commit 1ce562a (19/06): sửa chỉnh sửa inline trên bảng CV, import lịch rảnh theo tuần. |
| 5 | Tạo hồ sơ NV từ ứng viên (tab Offer) | Việt | In Progress | Nút tạo `hr.employee` từ ứng viên đã đậu — đã chạy local; còn lỗi 500 trên Neon do DB lệch schema (thiếu bảng `hocba_work_shift`), cần upgrade `hocba_attendance`. |
| 6 | Phân quyền tuyển dụng (HR Manager & Trưởng phòng) | Việt | Done | Commit b0de25c (18/06): gắn nhóm `group_hr_recruitment_user` / `interviewer` cho menu + thao tác ghi. |
| 7 | Gửi mail thật qua SMTP | Việt | Pending | Chưa cấu hình `ir.mail_server`; hiện chạy chế độ soạn + xem trước, mail nằm hàng đợi. |

---

## II. Project Issues

| # | Project Issue | Owner | Status | Notes (Solution, Suggestion, etc.) |
|---|---------------|-------|--------|------------------------------------|
| 1 | DB Neon lệch schema → tạo hồ sơ NV lỗi 500 | Việt | In Progress | Thiếu bảng `hocba_work_shift` trên Neon. Cần chạy `-u hocba_attendance` để đồng bộ schema. |
| 2 | Nút TBP Duyệt và HR Duyệt dùng chung 1 group | Việt | Pending | Cả hai dùng `group_hr_recruitment_user` — chưa tách role riêng cho 2 cấp phê duyệt. |
| 3 | Chưa cấu hình SMTP (`ir.mail_server`) | Việt | Pending | Mail tuyển dụng chưa gửi thật; cần khai báo mail server hoặc xác nhận chạy chế độ xem trước cho demo. |
| 4 | Sample data chưa kiểm tra nội dung | Việt | Pending | `hb_applicant_data*.xml`, `hb_interview_results.xml` cần rà lại; `cv_link` seed đang là tên file, không phải URL. |

---

## III. Next Week Plan

| # | Project Task | In-charge | Deadline | Notes (Task Details, etc.) |
|---|--------------|-----------|----------|----------------------------|
| 1 | Upgrade `hocba_attendance` trên Neon | Việt | 24/06/2026 | Tạo bảng `hocba_work_shift`, kiểm tra lại chức năng tạo hồ sơ NV từ ứng viên end-to-end. |
| 2 | Tách role phê duyệt TBP / HR | Việt | 25/06/2026 | Thêm group riêng + ràng buộc nút duyệt theo cấp. |
| 3 | Cấu hình SMTP & test gửi mail thật | Việt | 26/06/2026 | Khai báo `ir.mail_server`, gửi thử 4 mail template. |
| 4 | Rà soát & hoàn thiện sample data | Việt | 26/06/2026 | Cập nhật `cv_link` thành URL, kiểm tra dữ liệu mẫu ứng viên / kết quả PV. |
| 5 | Test tích hợp toàn module + chuẩn bị demo | Việt | 27/06/2026 | Đi qua đủ 10 bước quy trình, đối chiếu SPEC. |

---

## IV. Other Project Matters / Suggestions

| # | Project Matter/Suggestions | Raised By | Date | Notes |
|---|----------------------------|-----------|------|-------|
| 1 | Đã merge `origin/main` (18 commit payroll) vào nhánh | Việt | 19/06/2026 | Fast-forward, không xung đột; nhánh đang ahead chưa push lên remote. |
| 2 | Thông tin liên hệ hardcode trong mail template | Việt | 19/06/2026 | HR Ms. Ngọc Anh / SĐT / email cố định trong template — cần cập nhật khi thay nhân sự. |
| 3 | `jd_google_link` của các vị trí seed còn trống | Việt | 19/06/2026 | Cần điền URL JD Google Drive thực tế. |
