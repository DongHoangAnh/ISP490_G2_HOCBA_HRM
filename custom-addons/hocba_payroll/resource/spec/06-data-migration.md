# 06 — Di trú dữ liệu (Excel → Odoo)

> Nguồn: 6 file TSV xuất từ Lark/Excel của Học Bá. Đích: model ở file 03.
> Chiến lược: import master data trước (employee, contract), rồi lịch sử bảng lương (10/2025–04/2026).

---

## 1. Thứ tự import

```
1. res.partner.bank  ← (số TK, ngân hàng từ 2_2)
2. hr.employee       ← 2_2 (lương/phúc lợi) + 2_3 (thuế/BH)   [match theo Mã NV]
3. hr.contract       ← 2_2 (lương, phụ cấp định mức) + 2_3 (lương đóng BH, NPT)
4. hocba.sale.level  ← seed bậc hoa hồng (file 03) — chờ khách chốt
5. hocba.sale.revenue← 5_1 (Doanh thu, Level, %COM) theo từng tháng
6. hr.payslip (history) ← 5_1 (offline) + 5_2 (online) — import kết quả để tra cứu/đối chiếu
```

> Lưu ý: bước 6 import **kết quả lịch sử** (không tính lại) để giữ số đã trả. Từ kỳ go-live trở đi
> hệ thống **tự tính**. Có thể tạo một field `x_imported = True` để phân biệt phiếu nhập tay.

---

## 2. Map `2_2 Thông tin lương/phúc lợi` → hr.employee / hr.contract

| Cột Excel | Đích | Model |
|---|---|---|
| Mã nhân sự | `x_employee_code` (+ `barcode`) | employee |
| Tài khoản Lark | `x_lark_account` | employee |
| Họ tên nhân sự_text | `name` | employee |
| Trạng thái | `x_emp_status` (map giá trị) | employee |
| Phòng ban | `department_id` (tạo nếu chưa có) | employee |
| Hình thức | `x_work_form` (Offline→offline, Online→online) | employee |
| Chức danh | `job_id` / `job_title` | employee |
| Loại vị trí | `x_position_type` (Quản lý→manager, Nhân viên→staff) | employee |
| Ngày thử việc | `x_probation_date` | employee |
| Ngày chính thức | `x_official_date` | employee |
| Thâm niên làm việc | (compute lại, bỏ qua import) | — |
| Lương đóng BHXH | `x_insurance_base` ❓(so với 2_3) | contract |
| Lương cơ bản | `wage` (lương hợp đồng) | contract |
| PC gửi xe | `x_pc_parking` | contract |
| PC xăng xe | `x_pc_fuel` | contract |
| PC chức vụ | `x_pc_position` | contract |
| PC thâm niên | `x_pc_seniority` | contract |
| Hỗ trợ đi lại | `x_sp_transport` | contract |
| Hỗ trợ điện thoại | `x_sp_phone` | contract |
| Hỗ trợ ăn ca | `x_sp_meal` | contract |
| Hỗ trợ trang phục | `x_sp_uniform` | contract |
| Lương KPI | `x_kpi_wage` | contract |
| Số tài khoản | `res.partner.bank.acc_number` | bank |
| Ngân hàng | `res.partner.bank.bank_id` | bank |

**Làm sạch giá trị tiền**: bỏ ký tự `₫`, dấu `,`, khoảng trắng → số. (vd `₫1,200,000` → `1200000`).

---

## 3. Map `2_3 Thông tin thuế/bảo hiểm` → hr.employee / hr.contract

| Cột Excel | Đích | Model |
|---|---|---|
| Mã số thuế TNCN | `x_pit_code` | employee |
| Số căn cước công dân | `identification_id` | employee |
| Ngày cấp | `x_id_issue_date` | employee |
| Nơi cấp | `x_id_issue_place` | employee |
| Số sổ BHXH | `x_social_insurance_no` | employee |
| Số thẻ BHYT | `x_health_insurance_no` | employee |
| Nơi đăng ký BHYT | `x_health_insurance_place` | employee |
| Giảm trừ thuế TNCN | (= 6.2tr × NPT; dùng để verify) | — |
| Người phụ thuộc | `x_dependent_count` | employee + contract |
| Chính sách bảo hiểm | `x_insurance_policy` (map) | contract |
| Mức lương đóng BH | `x_insurance_base` ❓(so với 2_2) | contract |

> ❓ **Xung đột `x_insurance_base`**: 2_2 (7.300.000) ≠ 2_3 (6.500.000) cho HB.01.
> Trong file `5_1` cột "Lương đóng BH" = 7.300.000 và khớp với số BH đã verify → **ưu tiên giá trị từ `5_1`/`2_2`**.
> Đề xuất quy tắc import: lấy `x_insurance_base` từ `5_1` (kỳ gần nhất); nếu thiếu lấy `2_2`; cảnh báo nếu lệch `2_3`.

Map `x_emp_status`: `Chính thức→official`, `Thử việc→probation`, `Parttime→parttime`, `Online→online`, `Nghỉ việc→resigned`.
Map `x_insurance_policy`: `BH theo định mức→standard`, `Đóng 0.5% BH TNLĐ→tnld_0_5`, rỗng→`none`.

---

## 4. Map `5_1 Tính lương offline` → hocba.sale.revenue + hr.payslip (history)

**Sale revenue** (chỉ dòng có Doanh thu): `Mã NV`, `Tháng/Năm tương ứng`, `Doanh thu`→revenue, `Level`, `%COM`.

**Payslip history** — lưu các chỉ tiêu để đối chiếu (map vào payslip lines tương ứng hoặc field phụ):
| Cột Excel | Ý nghĩa |
|---|---|
| Tháng tương ứng / Năm tương ứng | period |
| Công chuẩn / Công tháng / Tăng ca / Tổng công | worked days |
| Lương thời gian | line LUONG_TG |
| COM / Lương sale | line HOA_HONG |
| Tổng phụ cấp | line PHU_CAP |
| Thưởng Lễ / Thưởng khác | line THUONG |
| TỔNG THU NHẬP | line GROSS |
| BHXH/BHYT/BHTN (CT & NV) | lines BH |
| Số người phụ thuộc / Giảm trừ NPT | thông tin thuế |
| TN tính thuế / Thuế TNCN | line TNCN (đối chiếu) |
| Tạm ứng, trừ khác | line ADVANCE |
| THỰC LÃNH | line NET |
| Trạng thái thanh toán | `x_approval_state` (Đã thanh toán→paid) |

> ⚠️ Dùng cột "**Tháng/Năm tương ứng**" (số) làm period, KHÔNG dùng "Tháng/Năm" (text "Tháng 3").
> Dữ liệu phủ: 10/2025, 11/2025, 12/2025, 01/2026, 02/2026, 03/2026, 04/2026.

---

## 5. Map `5_2 Tính lương online` → hr.payslip (history, online)

| Cột | Ý nghĩa |
|---|---|
| Mã NV / Tên / Tháng-Năm tương ứng | key + period |
| Lương | line LUONG |
| Thưởng | line THUONG |
| TỔNG THU NHẬP | line GROSS |
| Tạm ứng, trừ khác | line ADVANCE |
| Thực lãnh | line NET |
| Số TK / Ngân hàng / Email | bank/contact |
| Trạng thái thanh toán | state |

---

## 6. Kỹ thuật import (gợi ý cho AI/Dev)

- Viết script Python dùng `odoo.api.Environment` (chạy qua `odoo shell`) hoặc XML-RPC, đọc TSV bằng `csv.reader(delimiter='\t')`.
- Encoding: UTF-8. Có ký tự `\r` cuối dòng → strip.
- Một NV xuất hiện nhiều dòng (mỗi tháng 1 dòng) ở `5_1`/`5_2` → group theo Mã NV để tạo employee/contract 1 lần.
- Idempotent: dùng `x_employee_code` để upsert, tránh tạo trùng khi chạy lại.
- Validate sau import: đếm số NV/phiếu, tổng NET mỗi tháng so với tổng Excel (xem file 07).
- Lưu file gốc TSV vào `addons/hocba_payroll/data/migration/` để tái lập.

---

## 7. Bảng map giá trị nhanh

```python
EMP_STATUS = {'Chính thức':'official','Thử việc':'probation','Parttime':'parttime',
              'Online':'online','Nghỉ việc':'resigned'}
WORK_FORM  = {'Offline':'offline','Online':'online'}
POS_TYPE   = {'Quản lý':'manager','Nhân viên':'staff'}
INS_POLICY = {'BH theo định mức':'standard','Đóng 0.5% BH TNLĐ':'tnld_0_5','':'none'}

def to_amount(s):
    if not s: return 0.0
    return float(s.replace('₫','').replace(',','').replace(' ','').strip() or 0)
```
