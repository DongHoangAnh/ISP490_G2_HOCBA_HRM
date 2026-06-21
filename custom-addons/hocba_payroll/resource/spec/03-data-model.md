# 03 — Mô hình dữ liệu (Models & Bảng DB trên Neon)

> Odoo ORM tự sinh bảng PostgreSQL trên Neon từ model. Dưới đây là field cần thêm/model mới.
> Quy ước: field custom prefix `x_` nếu thêm vào model lõi; model mới đặt `hocba.*`.

---

## 1. `hr.employee` — bổ sung field

| Field | Type | Nguồn Excel | Ghi chú |
|---|---|---|---|
| `x_employee_code` | Char (index, unique) | Mã NV (HB.01) | Khóa nghiệp vụ. Có thể map vào `barcode` |
| `x_lark_account` | Char | Tài khoản Lark | |
| `x_work_form` | Selection `[offline, online]` | Hình thức | Quyết định structure áp dụng |
| `x_position_type` | Selection `[manager, staff]` | Loại vị trí | Quản lý / Nhân viên |
| `x_probation_date` | Date | Ngày thử việc | |
| `x_official_date` | Date | Ngày chính thức | |
| `x_seniority_years` | Integer (compute) | Thâm niên | Tính từ official_date |
| `x_pit_code` | Char | Mã số thuế TNCN | |
| `x_social_insurance_no` | Char | Số sổ BHXH | |
| `x_health_insurance_no` | Char | Số thẻ BHYT | |
| `x_health_insurance_place` | Char | Nơi ĐK BHYT | |
| `x_dependent_count` | Integer | Số người phụ thuộc | Dùng cho giảm trừ NPT |
| `x_emp_status` | Selection | Tình trạng | `official/probation/parttime/online/resigned` |

> CCCD, ngày/nơi cấp → dùng field chuẩn `identification_id` + custom `x_id_issue_date`, `x_id_issue_place`.
> Số TK + ngân hàng → dùng `res.partner.bank` chuẩn (bắt buộc để register payment được — xem `phieu-luong.md`).
> Email cá nhân → `private_email` / `work_email`.

---

## 2. `hr.contract` — bổ sung field

| Field | Type | Nguồn | Ghi chú |
|---|---|---|---|
| `wage` | Monetary (lõi) | Lương cơ bản / Lương hợp đồng | Lương HĐ tháng đủ công |
| `x_insurance_base` | Monetary | Lương đóng BH | **Cơ sở tính BHXH/BHYT/BHTN** (KHÁC wage) |
| `x_insurance_policy` | Selection | Chính sách bảo hiểm | `standard` (BH theo định mức), `tnld_0_5` (chỉ 0.5% TNLĐ), `none` |
| `x_dependent_count` | Integer | Số NPT | Mirror từ employee, cho phép override theo kỳ |
| `x_pc_seniority` | Monetary | PC thâm niên | Phụ cấp định mức |
| `x_pc_parking` | Monetary | PC gửi xe | |
| `x_pc_fuel` | Monetary | PC xăng xe | |
| `x_pc_position` | Monetary | PC chức vụ | |
| `x_sp_transport` | Monetary | Hỗ trợ đi lại | |
| `x_sp_phone` | Monetary | Hỗ trợ điện thoại | |
| `x_sp_meal` | Monetary | Hỗ trợ ăn ca | |
| `x_sp_uniform` | Monetary | Hỗ trợ trang phục | |

> Mỗi loại phụ cấp nên có cờ `is_taxable` (cấu hình ở category, không per-field) để sau này tách
> phụ cấp miễn thuế (ăn ca, điện thoại, đồng phục…) theo TT111/2013. Giai đoạn này mặc định **gộp** như Excel,
> nhưng giữ chỗ. (❓ xác nhận với khách — file 00 mục 4.6)

---

## 3. Worked days / Công (nhập theo tháng)

Tận dụng `hr.payslip.worked_days` của OCA payroll. Các loại cần map:

| Loại công (Excel) | work_entry_type (code) | Ghi chú |
|---|---|---|
| Công chuẩn của tháng | `STANDARD` | Số công chuẩn (mẫu số chia lương thời gian) |
| Công tháng / Tổng công | `WORK100` | Công thực làm |
| Tăng ca | `OT` | Giờ/ngày OT |
| Nghỉ phép năm | `LEAVE_PAID` | |
| Nghỉ phép (không lương) | `LEAVE_UNPAID` | |
| Ngày lễ | `HOLIDAY` | |
| Nghỉ thai sản | `MATERNITY` | |
| Công làm online | `WORK_ONLINE` | (cho NV offline làm online) |

Giai đoạn này: nhận **import** số công/tháng (file 06). Chưa cần tích hợp máy chấm công.
Xem `cong.md` / `work-entry-analysis.md` trong project để biết cơ chế Work Entries chuẩn của Odoo.

---

## 4. Bảng lương — tận dụng model chuẩn

| Model OCA payroll | Vai trò |
|---|---|
| `hr.payslip` | Phiếu lương 1 NV/tháng |
| `hr.payslip.line` | Dòng kết quả từng rule |
| `hr.payslip.run` | Lô bảng lương theo tháng (batch) |
| `hr.salary.rule` / `hr.salary.rule.category` | Định nghĩa rule & nhóm |
| `hr.payroll.structure` | Cấu trúc lương (Offline / Online) |

State bổ sung cho luồng duyệt (file 01 mục 2): thêm field `x_approval_state` trên `hr.payslip.run`
`[draft, computed, tbp_confirmed, sent, director_approved, paid]` + nút chuyển state (chưa cần UI đẹp).

---

## 5. ERD rút gọn

```
hr.employee ──1:n── hr.contract ──1:n── hr.payslip ──1:n── hr.payslip.line
     │                   │                   │
     │                   │                   └── worked_days (n)
     │                   └── x_insurance_base, phụ cấp định mức, NPT
     │
     └── res.partner.bank (số TK, NH)

hr.payslip.run (batch tháng) ──1:n── hr.payslip
hr.payroll.structure ──1:n── hr.salary.rule ──n:1── hr.salary.rule.category
```

---

## 6. Index & ràng buộc đề xuất

- `hr.employee.x_employee_code`: `unique`, có index.
- `hr.contract.x_insurance_base >= 0`; cảnh báo nếu > trần BH (file 05).
- Soft validation: NV `x_work_form = offline` & `Chính thức` mà thiếu `x_insurance_base` → warning (giống Odoo "Employees Without …").
