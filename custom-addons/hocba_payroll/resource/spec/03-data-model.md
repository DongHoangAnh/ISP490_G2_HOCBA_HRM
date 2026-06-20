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
| `x_kpi_wage` | Monetary | Lương KPI | |
| `x_is_sale` | Boolean | (suy từ có doanh thu/Level) | Bật rule hoa hồng sale |

> Mỗi loại phụ cấp nên có cờ `is_taxable` (cấu hình ở category, không per-field) để sau này tách
> phụ cấp miễn thuế (ăn ca, điện thoại, đồng phục…) theo TT111/2013. Giai đoạn này mặc định **gộp** như Excel,
> nhưng giữ chỗ. (❓ xác nhận với khách — file 00 mục 4.6)

---

## 3. Model mới: `hocba.sale.level` (bậc hoa hồng sale)

Dùng để tra cứu %COM + lương cứng theo Level. Suy từ dữ liệu (xác nhận lại với khách):

| Field | Type | Ghi chú |
|---|---|---|
| `name` | Char | "Level 0", "Level 1"… |
| `level` | Integer | 0..n |
| `kpi_threshold` | Monetary | Ngưỡng doanh thu (KPI) để đạt level |
| `commission_rate` | Float | %COM (vd 0.03 = 3%) |
| `base_sale_wage` | Monetary | Lương cứng sale (LC sale) |

Dữ liệu quan sát được (file `5_1`) — **dùng làm seed, khách chốt chính thức**:

| Level | KPI (ngưỡng DT) | %COM | LC sale |
|---|---|---|---|
| 0 | 50.000.000 | 3.00% | 6.200.000 |
| 1 | 90.000.000 | 4.00% | 6.200.000 |
| 2 | 120.000.000 | 4.50% | 7.000.000 |
| 4 | 210.000.000 | 3.50% | 8.500.000 |
| 5 | 270.000.000 | 4.00% | 9.200.000 |
| 6 | 340.000.000 | 4.40% | 10.200.000 |

> ⚠️ Dữ liệu thực có biến động (cùng level đôi khi %COM khác) và thiếu Level 3.
> → Bảng bậc trên **chưa hoàn chỉnh**, BẮT BUỘC khách cung cấp **chính sách hoa hồng chính thức**.
> Engine sẽ: với 1 nhân viên/tháng, lấy `Doanh thu` → tìm level cao nhất có `kpi_threshold <= Doanh thu`
> → lấy `%COM` & `LC sale` của level đó. COM = `Doanh thu × %COM`.

---

## 4. Model mới: `hocba.sale.revenue` (doanh thu sale theo tháng)

Input cho hoa hồng — mỗi NV sale một dòng/tháng.

| Field | Type | Ghi chú |
|---|---|---|
| `employee_id` | Many2one hr.employee | |
| `period_month` | Integer (1..12) | |
| `period_year` | Integer | |
| `revenue` | Monetary | Doanh thu (cột "Doanh thu") |
| `level_id` | Many2one hocba.sale.level | compute hoặc nhập tay |
| `commission` | Monetary (compute) | = revenue × level.commission_rate |
| `sale_wage` | Monetary (compute) | = level.base_sale_wage + commission |

> Đây là nguồn cho biến `SALE_REV`, `SALE_COM`, `SALE_BASE` trong salary rule (file 04).

---

## 5. Worked days / Công (nhập theo tháng)

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

## 6. Bảng lương — tận dụng model chuẩn

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

## 7. ERD rút gọn

```
hr.employee ──1:n── hr.contract ──1:n── hr.payslip ──1:n── hr.payslip.line
     │                   │                   │
     │                   │                   └── worked_days (n)
     │                   └── x_insurance_base, phụ cấp định mức, NPT
     │
     ├──1:n── hocba.sale.revenue ──n:1── hocba.sale.level
     └── res.partner.bank (số TK, NH)

hr.payslip.run (batch tháng) ──1:n── hr.payslip
hr.payroll.structure ──1:n── hr.salary.rule ──n:1── hr.salary.rule.category
```

---

## 8. Index & ràng buộc đề xuất

- `hr.employee.x_employee_code`: `unique`, có index.
- `hocba.sale.revenue`: unique `(employee_id, period_month, period_year)`.
- `hr.contract.x_insurance_base >= 0`; cảnh báo nếu > trần BH (file 05).
- Soft validation: NV `x_work_form = offline` & `Chính thức` mà thiếu `x_insurance_base` → warning (giống Odoo "Employees Without …").
