# 08 — Format & Công thức BẢNG LƯƠNG (chuẩn output)

> Nguồn: `BẢNG_LƯƠNG_DEMO_EDU.xlsx` (sheet `BL4`). **Đây là format + công thức ĐÍCH** khách muốn.
> Khác (và thay thế) công thức cũ trong `5_1` cho nhân sự thường. Hoa hồng sale (file 04) chỉ áp riêng nhóm sale.
> Toàn bộ công thức dưới đây đã **đối chiếu khớp số** từ file demo.

---

## 1. Layout file Excel xuất ra (phải tái lập y hệt)

```
Row1:  A="Tên công ty"     C=CÔNG TY CỔ PHẦN GIÁO DỤC & ĐÀO TẠO HỌC BÁ
Row2:  A="Địa chỉ:"        C=Tầng 2 Tòa nhà HH1 Imperia Plaza, 360 Giải Phóng, Hà Nội
Row3:  A="MST:"            C=0110883975
Row6:  G="<công chuẩn>"    (vd 25) — số ngày công chuẩn của tháng, dùng làm mẫu số
Row7-8: HEADER 2 tầng (merge), xem mục 2
Row9+: dữ liệu, mỗi NV 1 dòng
RowN:  "Tổng" — dòng tổng cộng (sum các cột số)
+2:    "Ngày DD tháng MM năm YYYY" (canh phải, cột X)
+3:    "Lập Biểu" (C) | "Kế Toán Trưởng" (G) | "Giám Đốc" (X)
+4:    "(Ký ghi rõ họ tên)" ...
foot:  "Trả qua MB"  = Σ NET của NV trả qua ngân hàng
       "Trả tiền mặt"= Σ NET của NV trả tiền mặt
```

---

## 2. Cấu trúc cột (header 2 tầng)

| Cột | Tầng 1 (row7) | Tầng 2 (row8) | Field hệ thống |
|---|---|---|---|
| A | STT | | số thứ tự |
| B | Mã NV | | `x_employee_code` |
| C | Họ Và Tên | | `employee.name` |
| D | Chức Vụ | | `job_title` |
| E | Phòng ban | | `department_id` |
| F | Lương cơ bản tháng | | `contract.wage` (= **cơ sở đóng BH**) |
| G | Lương Thời Gian hưởng | Công | `worked.total_days` |
| H | | Ngày nghỉ tính lương | `worked.paid_leave_days` |
| I | | NCTT (ngày công thực tế) | `worked.actual_days` |
| J | Phụ Cấp | Ăn ca | `= 50.000 × Công` |
| K | | Xăng xe | `contract.x_pc_fuel` |
| L | | Điện thoại | `contract.x_sp_phone` |
| M | | Thưởng khác | input `BONUS_OTHER` |
| N | | Hỗ trợ nuôi con nhỏ | `contract.x_sp_childcare` |
| O | Tổng thu nhập | | **công thức (3.1)** |
| P | Thu nhập miễn thuế TNCN | | `= min(Ăn ca, 730.000)` |
| Q | Tổng Thu nhập trước thuế | | `= O − P` |
| R | Các khoản giảm trừ | NPT | `contract.x_dependent_count` |
| S | | số tiền | `= 15.500.000 + 6.200.000 × NPT` |
| T | BH trích từ NV | BHXH (8%) | `= F × 8%` |
| U | | BHYT (1.5%) | `= F × 1.5%` |
| V | | BHTN (1%) | `= F × 1%` |
| W | Tổng thu nhập tính thuế | | **công thức (3.4)** |
| X | Thuế TNCN | | `= PIT(W)` (file 05) |
| Y | Tổng lương thực lĩnh | | **công thức (3.5)** = NET |
| Z | BH do công ty đóng | BHXH (17.5%) | `= F × 17.5%` |
| AA | | BHYT (3%) | `= F × 3%` |
| AB | | BHTN (1%) | `= F × 1%` |
| AC | KÝ NHẬN | | (cột ký, để trống) |

---

## 3. Công thức (đã verify)

Ký hiệu: `CC` = Công (total_days, cột G), `CCh` = Công chuẩn (G6).

### 3.1 — Tổng thu nhập (O)
```
Ăn ca (J)   = 50.000 × CC
O = (F + J + K + L + M + N) × CC / CCh
```
> ⚠️ Lưu ý: ăn ca (J) đã = 50.000×CC, rồi O lại nhân CC/CCh → ăn ca chịu hệ số công 2 lần.
> Đây là đúng theo số liệu demo (HB.40: (5.700.000+1.387.500+1.000.000+1.000.000)×27,75/25 = **10.087.125** ✓).
> ❓ Xác nhận với khách đây là chủ ý hay cần sửa ăn ca thành cố định.

**Đối chiếu**:
- HB.03: (7.300.000+1.200.000+1.000.000+1.000.000)×24/25 = **10.080.000** ✓
- HB.04: (6.000.000+1.200.000+1.000.000+800.000)×24/25 = **8.640.000** ✓

### 3.2 — Miễn thuế (P) & Trước thuế (Q)
```
P = min(Ăn ca thực nhận, 730.000)     # trần ăn ca miễn thuế
Q = O − P
```
**Đối chiếu HB.03**: 10.080.000 − 730.000 = **9.350.000** ✓

### 3.3 — Giảm trừ (S) & Bảo hiểm
```
S = 15.500.000 + 6.200.000 × NPT
BH_NV = F×8% + F×1.5% + F×1%   (T+U+V)
BH_CT = F×17.5% + F×3% + F×1%  (Z+AA+AB)
```
**Đối chiếu**: HB.01 NPT=1 → S=**21.700.000** ✓; HB.58 NPT=2 → S=**27.900.000** ✓.
T/U/V HB.03 (F=7.300.000) = 584.000 / 109.500 / 73.000 ✓.

### 3.4 — Thu nhập tính thuế (W)
```
W = max(0, Q − BH_NV − S)
```
**Đối chiếu HB.03**: 9.350.000 − 766.500 − 15.500.000 < 0 → **0** ✓ (mọi dòng demo W=0 → X=0)

### 3.5 — Thực lĩnh (Y / NET)
```
Y = O − BH_NV − X
```
> Lưu ý: NET tính trên **O** (gồm cả phần ăn ca miễn thuế), KHÔNG phải Q.
**Đối chiếu**:
- HB.03: 10.080.000 − 766.500 − 0 = **9.313.500** ✓
- HB.01: 9.888.000 − 766.500 − 0 = **9.121.500** ✓

---

## 4. Khác biệt so với file 04 (5_1) — cần thống nhất

| Mục | Demo (BL4) — ĐÍCH | 5_1 (cũ) |
|---|---|---|
| Cơ sở đóng BH | = Lương cơ bản tháng (F) | field riêng "Lương đóng BH" |
| Proration | Cả (base+phụ cấp) × CC/CCh | chỉ base × tổng_công/CChuẩn |
| Ăn ca | 50.000 × công | gộp |
| Hoa hồng sale | KHÔNG hiển thị cột (gộp Thưởng khác?) | có cột COM/Lương sale |
| Công chuẩn | G6 theo tháng (25) | quan sát 24 |

> ❗ **Quyết định cần khách chốt**:
> 1. Hệ thống mới dùng công thức **DEMO** làm chuẩn cho NV thường (khuyến nghị).
> 2. Hoa hồng sale (file 04) áp dụng thế nào trong format demo: thêm cột "Hoa hồng" trước O,
>    hay trả riêng bằng phiếu lương hoa hồng (warrant)? → đề xuất **thêm cột Hoa hồng** vào nhóm Phụ Cấp/Thưởng.
> 3. Cơ sở đóng BH = lương cơ bản tháng (F) → cập nhật lại file 03 (`x_insurance_base` = `wage` cho NV thường).

---

## 5. Spec xuất file Excel "Bảng lương" (để soát)

- Tạo từ **một `hr.payslip.run`** (1 tháng). Mỗi payslip → 1 dòng.
- Dùng **openpyxl**, tái lập layout mục 1–2: merge header 2 tầng, freeze panes ở row 9, format số `#,##0`, viền bảng.
- Thứ tự dòng: theo phòng ban hoặc STT (giống demo: theo STT). ❓ xác nhận thứ tự.
- Dòng "Tổng": SUM các cột F,J..N,O,P,Q,S,T..V,W,X,Y,Z..AB.
- Footer "Trả qua MB"/"Trả tiền mặt": tách theo `payment_method` của NV.
- Tên file: `BangLuong_HocBa_T{MM}-{YYYY}.xlsx`.
- Endpoint/nút: action "Xuất bảng lương (Excel)" trên `hr.payslip.run`.

> Đây là file soát NỘI BỘ. File chuyển khoản ngân hàng (định dạng MB) ở **file 09**.
