# Học Bá Education — Payroll System Spec (cho AI Coder)

> **Mục tiêu**: Chuyển nghiệp vụ tính lương đang chạy trên Excel/Lark của Học Bá Education
> sang hệ thống web mới. **Giai đoạn này chỉ build DB + Backend (Odoo)**, test trên Docker.
> Frontend (ReactJS) làm sau khi BE chạy đúng.
>
> **Đối tượng đọc**: AI coding agent + Dev. Đọc các file theo đúng thứ tự bên dưới.

---

## 0. Stack đã chốt

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| Backend | **Odoo 17.0 Community** + module custom `hocba_payroll` | Engine salary rule lấy từ **OCA `payroll`** (backport Community của Odoo SA) |
| Database | **PostgreSQL trên Neon** (serverless) | Odoo trỏ trực tiếp vào Neon qua biến môi trường |
| Frontend | ReactJS (giai đoạn sau) | Giao tiếp BE qua Odoo JSON-RPC / REST controller |
| Triển khai dev | **Docker Compose** | Chỉ container Odoo (web). DB nằm ngoài, trên Neon |

> ⚠️ **CẦN XÁC NHẬN trước khi build** (xem mục 4):
> 1. Odoo **Community** hay **Enterprise**? Spec này viết cho **Community + OCA payroll**.
>    Nếu khách có license Enterprise thì dùng `hr_payroll` gốc, mapping rule tương đương.
> 2. OCA `payroll` cho **branch 17.0** — xác nhận tồn tại/ổn định tại
>    `https://github.com/OCA/payroll` (đã có 13.0/16.0 chắc chắn).
> 3. Biểu thuế TNCN dùng **7 bậc lũy tiến** (xem file 05) — xác nhận chưa áp dụng biểu 5 bậc mới.

---

## 1. Thứ tự đọc & build

| # | File | Nội dung | Dùng để |
|---|---|---|---|
| 1 | `01-business-context-scope.md` | Bối cảnh, quy trình hiện tại, scope in/out | Hiểu nghiệp vụ |
| 2 | `02-architecture-docker-neon.md` | Docker Compose, kết nối Neon, skeleton module | Dựng môi trường |
| 3 | `03-data-model.md` | Models, fields custom, bảng DB sinh ra trên Neon | Tạo schema |
| 4 | `04-salary-structures-rules.md` | 2 cấu trúc lương (Offline/Online) + toàn bộ salary rule + công thức | Code engine tính lương |
| 5 | `05-insurance-pit-vn.md` | BHXH/BHYT/BHTN + Thuế TNCN VN 2026 | Code rule bảo hiểm/thuế |
| 6 | `06-data-migration.md` | Map cột Excel → field Odoo, chiến lược import | Đổ dữ liệu |
| 7 | `07-acceptance-tests.md` | Test case bằng SỐ THẬT từ Excel | Verify đúng/sai |
| 8 | `08-payslip-format-demo.md` | **Format + công thức bảng lương ĐÍCH** (BẢNG_LƯƠNG_DEMO_EDU) + xuất Excel | Output chuẩn |
| 9 | `09-bank-bulk-payment.md` | Quản lý ngân hàng (CRUD) + xuất file CK MB (lọc theo bank) | Đi lương |
| 10 | `10-approval-workflow-employee-confirm.md` | Quy trình duyệt + NV xác nhận qua email link + lịch sử lương | Workflow |
| 11 | `11-salary-rule-config-roles.md` | Config mã phí (CRUD) theo vai trò + tổng hợp từ chấm công | Cấu hình |

**Build order khuyến nghị**: 02 (môi trường) → 03 (schema) → 11 (mã phí/structure theo vai trò) → 05 (BH/thuế) → 08 (công thức NV thường = chuẩn) → 04 (hoa hồng sale) → 11 (nhận công + compute) → 06 (import lịch sử) → 09 (xuất CK) → 10 (duyệt/email/lịch sử) → 07 (test).

> ⚠️ **Quan trọng — ưu tiên công thức**: File **08 (demo)** là công thức ĐÍCH cho NV thường và
> **thay thế** giả định "lương đóng BH là field riêng" trong file 03/04. Theo demo: **cơ sở đóng BH = "Lương cơ bản tháng" (`contract.wage`)** và mọi khoản (base + phụ cấp) đều ×Công/Công chuẩn.
> Khi mâu thuẫn, **file 08 thắng** cho NV thường; file 04 chỉ bổ sung phần hoa hồng sale.

---

## 2. Phạm vi GIAI ĐOẠN NÀY (Payroll – BE/DB)

✅ **In scope**
- Model dữ liệu nhân sự phục vụ tính lương (employee, contract, thông tin BH/thuế, TK ngân hàng)
- 2 cấu trúc lương: **Offline** (full: công, phụ cấp, hoa hồng sale, BH, thuế, net) và **Online** (đơn giản: lương + thưởng − tạm ứng)
- Engine tính: lương thời gian, hoa hồng sale theo Level/KPI, phụ cấp, BHXH/BHYT/BHTN, thuế TNCN, thực lãnh
- Bảng lương theo lô (batch) theo tháng
- Import dữ liệu lịch sử từ Excel
- Bộ test đối chiếu số liệu

❌ **Out of scope giai đoạn này** (làm sau / phase khác)
- Frontend React
- Tích hợp máy chấm công thực tế (giai đoạn này nhận công dạng input/import)
- File chuyển khoản ngân hàng tự động, BHXH điện tử
- Quy trình duyệt đa cấp trên UI (chỉ để state field)
- Gửi email phiếu lương tự động (giai đoạn này: dựng template + token + endpoint; SMTP cấu hình sau)

---

## 2b. Yêu cầu bổ sung của khách (đợt 2) — đã đưa vào spec

| # | Yêu cầu | File |
|---|---|---|
| R1 | **Config mã phí** (thuế/%/BH…) thêm-sửa-xóa, **tùy vai trò** (NV vs CTV/GV online/offline) | `11` |
| R2 | Xem **lịch sử thanh toán lương** theo từng tháng & từng người | `10 §3` |
| R3 | **Quy trình**: HR tạo → Quản lý xác nhận → **email + link web** cho NV xem → NV xác nhận → áp dụng | `10 §1–2` |
| R4 | **Quản lý ngân hàng** thêm-sửa-xóa | `09 §1` |
| R5 | Nhận **chấm công** (công/OT/phép/nghỉ KL) → nhân với công ra lương; xuất **Excel format DEMO** + **file CK MB lọc theo từng ngân hàng** | `11 §3`,`08`,`09` |

---

## 3. Quy ước chung

- **Tiền tệ**: VND, không có phần thập phân khi lưu thành tiền (round tới đồng). Trong Odoo dùng `monetary`/`float` digits phù hợp.
- **Kỳ lương**: theo tháng dương lịch (period = ngày 1 → ngày cuối tháng).
- **Mã NV**: dạng `HB.xx` (vd `HB.01`). Là khóa nghiệp vụ, lưu ở `hr.employee.barcode` hoặc field custom `x_employee_code`.
- **2 nhóm nhân sự**:
  - `Offline` → áp cấu trúc lương đầy đủ (đóng BH, tính thuế).
  - `Online` → cộng tác viên/part-time, KHÔNG đóng BH/thuế trong sheet hiện tại; chỉ lương + thưởng − tạm ứng.
- **Trạng thái nhân sự** (cột "Tình trạng"): `Chính thức`, `Thử việc`, `Parttime`, `Online`, `Nghỉ việc`.
- **Round**: tất cả khoản BH và thuế làm tròn tới đồng (round half-up). Test ở file 07 dựa trên số đã round của Excel.

---

## 4. Việc cần khách/PM xác nhận (đánh dấu ❓ trong các file)

1. **Edition Odoo** (Community/Enterprise) — ảnh hưởng module nền.
2. **Lương đóng BH**: file `2_2` ghi `Lương đóng BHXH = 7.300.000` nhưng file `2_3` ghi `Mức lương đóng BH = 6.500.000` cho cùng HB.01. → Chốt 1 nguồn sự thật.
3. **Mức giảm trừ NPT trong Excel** = 6.200.000/người (đúng chuẩn 2026). Xác nhận tất cả NV dùng chuẩn mới.
4. **Biểu thuế TNCN**: 7 bậc (default) hay biểu 5 bậc mới.
5. **Công thức Level/KPI hoa hồng sale**: spec suy ra từ dữ liệu (xem file 04). Cần khách xác nhận bảng bậc chính thức.
6. **Phụ cấp miễn thuế**: ăn ca, điện thoại, đồng phục… có tách khỏi thu nhập chịu thuế không (Excel hiện gộp). Mặc định spec để cờ `is_taxable` per phụ cấp.
