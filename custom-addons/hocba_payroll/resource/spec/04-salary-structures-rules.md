# 04 — Cấu trúc lương & Salary Rules

> Đây là file lõi để code engine tính lương. Tất cả công thức đã được **đối chiếu ngược từ
> số liệu thật** trong `5_1__Tính_lương_offline` và `5_2__Tính_lương_online`.
> Viết theo phong cách salary rule của Odoo/OCA (`amount_python_compute`: gán `result`).
>
> Quy ước biến (theo OCA payroll):
> - `contract` = `hr.contract` hiện hành (chứa field custom file 03)
> - `worked_days.CODE.number_of_days` = số ngày của loại công CODE
> - `inputs.CODE.amount` = giá trị Other Input
> - `categories.X` = tổng các rule thuộc category X tính trước đó
> - `result` = giá trị rule trả về

---

## 1. Categories (nhóm rule)

| Code | Tên | Vai trò |
|---|---|---|
| `BASIC` | Lương thời gian | Lương theo công |
| `COM` | Hoa hồng sale | COM |
| `ALW` | Phụ cấp | PC + hỗ trợ |
| `BONUS` | Thưởng | Thưởng lễ, thưởng khác |
| `GROSS` | Tổng thu nhập | = BASIC+COM+ALW+BONUS |
| `COMP` | BH phần công ty | Tracking, KHÔNG trừ net |
| `DED` | Khấu trừ NV | BH NV + tạm ứng |
| `TAX` | Thuế TNCN | |
| `NET` | Thực lãnh | |

---

## 2. Đầu vào theo kỳ (Other Inputs / Worked Days)

| Code | Loại | Ý nghĩa | Nguồn |
|---|---|---|---|
| `STD_DAYS` | input | Công chuẩn (mẫu số chia) — quan sát = 24 ❓ | nhập/cấu hình |
| `PAID_DAYS` | worked | Công tháng (công có lương = chấm công + phép) | import |
| `OT_DAYS` | worked | Tăng ca quy đổi ra ngày | import |
| `SALE_REV` | input | Doanh thu sale trong tháng | `hocba.sale.revenue` |
| `BONUS_HOLIDAY` | input | Thưởng Lễ | nhập |
| `BONUS_OTHER` | input | Thưởng khác | nhập |
| `ADVANCE` | input | Tạm ứng / Trừ khác | nhập |
| `NONTAX_ALW` | input | Phụ cấp miễn thuế (ăn ca…) — quan sát 700.000 | cấu hình/contract |

> **Tổng công** = `PAID_DAYS + OT_DAYS`. **Hệ số công** = `Tổng công / STD_DAYS`.

---

## 3. CẤU TRÚC OFFLINE — `STRUCT_OFFLINE`

### Rule 3.1 — `LUONG_TG` (Lương thời gian) · cat BASIC
```python
# Base: nếu là sale (contract.x_is_sale) → dùng LC sale của level đạt được;
# ngược lại dùng lương hợp đồng (contract.wage).
std_days = inputs.STD_DAYS.amount or 24.0
total_days = (worked_days.PAID_DAYS.number_of_days or 0.0) + (worked_days.OT_DAYS.number_of_days or 0.0)
ratio = total_days / std_days if std_days else 0.0

if contract.x_is_sale:
    base = contract._hocba_sale_base(payslip.date_from)   # = level.base_sale_wage (LC sale)
else:
    base = contract.wage                                  # Lương hợp đồng

result = round(base * ratio)
```
**Đối chiếu**:
- HB.01 (non-sale): 20.000.000 × 24/24 = **20.000.000** ✓
- HB.09 (sale, Level 6): 10.200.000 × 28.3125/24 = **12.032.812** ✓

### Rule 3.2 — `HOA_HONG` (COM) · cat COM
```python
# Chỉ áp cho sale. COM = Doanh thu × %COM của level đạt được.
result = 0.0
if contract.x_is_sale:
    rev = inputs.SALE_REV.amount or 0.0
    rate = contract._hocba_sale_rate(payslip.date_from, rev)  # tra hocba.sale.level theo rev
    result = round(rev * rate)
```
**Đối chiếu**: HB.09: 349.537.000 × 4.40% = **15.379.628** ✓
> `_hocba_sale_rate`: tìm level cao nhất có `kpi_threshold <= rev`, trả `commission_rate`.
> `_hocba_sale_base`: tương tự, trả `base_sale_wage`. (Bảng bậc ở file 03 — ❓ khách chốt.)

### Rule 3.3 — `PHU_CAP` (Tổng phụ cấp) · cat ALW
```python
result = (contract.x_pc_seniority + contract.x_pc_parking + contract.x_pc_fuel
          + contract.x_pc_position + contract.x_sp_transport + contract.x_sp_phone
          + contract.x_sp_meal + contract.x_sp_uniform)
```
> Trong dữ liệu nhiều dòng Tổng phụ cấp = 0 (phụ cấp đã gộp vào lương HĐ). Giữ rule để mở rộng.

### Rule 3.4 — `THUONG` (Thưởng) · cat BONUS
```python
result = (inputs.BONUS_HOLIDAY.amount or 0.0) + (inputs.BONUS_OTHER.amount or 0.0)
```
**Đối chiếu**: HB.01: Thưởng khác 150.000 → **150.000** ✓; HB.09: **1.950.000** ✓

### Rule 3.5 — `GROSS` (Tổng thu nhập) · cat GROSS
```python
result = categories.BASIC + categories.COM + categories.ALW + categories.BONUS
```
**Đối chiếu**:
- HB.01: 20.000.000 + 0 + 0 + 150.000 = **20.150.000** ✓
- HB.09: 12.032.812 + 15.379.628 + 0 + 1.950.000 = **29.362.440** ≈ 29.362.441 ✓ (lệch 1đ do round)

### Rule 3.6 → 3.11 — Bảo hiểm (xem file 05 cho tỷ lệ & trần)
Phần công ty (cat COMP, KHÔNG trừ net): `BHXH_CT 17.5%`, `BHYT_CT 3%`, `BHTN_CT 1%`.
Phần NV (cat DED, trừ net): `BHXH_NV 8%`, `BHYT_NV 1.5%`, `BHTN_NV 1%`.
Tất cả nhân với `contract.x_insurance_base` (Lương đóng BH), tùy `x_insurance_policy`.
**Đối chiếu HB.09** (base 5.700.000): BHXH_NV 456.000 ✓, BHYT_NV 85.500 ✓, BHTN_NV 57.000 ✓, tổng NV 598.500 ✓.

### Rule 3.12 — `BH_NV_TOTAL` (Tổng BH NV 10.5%) · cat DED (helper)
```python
result = -(abs(BHXH_NV) + abs(BHYT_NV) + abs(BHTN_NV))   # dấu âm: khấu trừ
```

### Rule 3.13 — `TNCN` (Thuế TNCN) · cat TAX  → công thức ở file 05
```python
gross = categories.GROSS
bh_nv = abs(BHXH_NV) + abs(BHYT_NV) + abs(BHTN_NV)
self_ded = 15_500_000                                  # giảm trừ bản thân 2026
dep_ded  = 6_200_000 * (contract.x_dependent_count or 0)
nontax   = inputs.NONTAX_ALW.amount or 0.0             # ăn ca… miễn thuế (vd 700.000)
taxable = max(0.0, gross - bh_nv - self_ded - dep_ded - nontax)
result = -payslip._hocba_pit(taxable)                  # progressive 7 bậc, dấu âm
```
**Đối chiếu TN tính thuế HB.09**: 29.362.441 − 598.500 − 15.500.000 − 0 − 700.000 = **12.563.941** ✓ (khớp cột "TN tính thuế").
> ⚠️ **Cảnh báo dữ liệu**: ô "Thuế TNCN" của một số dòng Excel KHÔNG nhất quán với TI
> (HB.09 ghi 756.394 trong khi 7 bậc đúng luật cho TI 12.563.941 = 1.134.591). Excel do người
> nhập tay nên có sai số. **Hệ thống mới tính đúng luật** — KHÔNG sao chép số thuế cũ.
> Test (file 07) chỉ hard-assert các dòng thuế = 0 (đã sạch); dòng có thuế để chế độ "review".

### Rule 3.14 — `ADVANCE` (Tạm ứng/Trừ khác) · cat DED
```python
result = -(inputs.ADVANCE.amount or 0.0)
```
**Đối chiếu HB.09**: −1.800.000 ✓

### Rule 3.15 — `NET` (Thực lãnh) · cat NET
```python
result = categories.GROSS + categories.DED + categories.TAX
# DED và TAX đã mang dấu âm
```
**Đối chiếu**:
- HB.01: 20.150.000 − 766.500 − 0 − 0 = **19.383.500** ✓✓ (khớp tuyệt đối)
- HB.09: 29.362.441 − 598.500 − 756.394(Excel) − 1.800.000 = 26.207.547 ✓ (với thuế Excel)
  → Với thuế đúng luật 1.134.591 thì NET mới = 25.829.350 (đây mới là số đúng để go-live).

---

## 4. CẤU TRÚC ONLINE — `STRUCT_ONLINE`

Đơn giản, không công/BH/thuế.

### Rule 4.1 — `LUONG` · cat BASIC
```python
result = inputs.WAGE_ONLINE.amount or contract.wage   # "Lương" nhập theo tháng
```
### Rule 4.2 — `THUONG` · cat BONUS
```python
result = inputs.BONUS_OTHER.amount or 0.0             # "Thưởng"
```
### Rule 4.3 — `GROSS` · cat GROSS
```python
result = categories.BASIC + categories.BONUS
```
### Rule 4.4 — `ADVANCE` · cat DED
```python
result = -(inputs.ADVANCE.amount or 0.0)              # "Tạm ứng, trừ khác"
```
### Rule 4.5 — `NET` · cat NET
```python
result = categories.GROSS + categories.DED
```
**Đối chiếu** (HB.32, T3/2025): Lương 10.000.000 + Thưởng 1.000.000 − 0 = **11.000.000** ✓

---

## 5. Bảng tổng hợp rule (để sinh XML)

### OFFLINE
| Seq | Code | Category | Sign | Công thức tóm tắt |
|---|---|---|---|---|
| 10 | LUONG_TG | BASIC | + | base × tổng_công/STD_DAYS |
| 20 | HOA_HONG | COM | + | DT × %COM |
| 30 | PHU_CAP | ALW | + | Σ phụ cấp định mức |
| 40 | THUONG | BONUS | + | thưởng lễ + khác |
| 50 | GROSS | GROSS | = | BASIC+COM+ALW+BONUS |
| 60 | BHXH_CT | COMP | (track) | base × 17.5% |
| 61 | BHYT_CT | COMP | (track) | base × 3% |
| 62 | BHTN_CT | COMP | (track) | base × 1% |
| 70 | BHXH_NV | DED | − | base × 8% |
| 71 | BHYT_NV | DED | − | base × 1.5% |
| 72 | BHTN_NV | DED | − | base × 1% |
| 80 | TNCN | TAX | − | PIT(taxable) |
| 90 | ADVANCE | DED | − | tạm ứng |
| 99 | NET | NET | = | GROSS+DED+TAX |

### ONLINE
| Seq | Code | Category | Sign | Công thức |
|---|---|---|---|---|
| 10 | LUONG | BASIC | + | lương tháng |
| 40 | THUONG | BONUS | + | thưởng |
| 50 | GROSS | GROSS | = | BASIC+BONUS |
| 90 | ADVANCE | DED | − | tạm ứng |
| 99 | NET | NET | = | GROSS+DED |

---

## 6. Lưu ý implement

1. **Round**: round tới đồng từng rule (như Excel). Chấp nhận lệch ≤1đ ở GROSS do tổng các phần đã round.
2. **`x_is_sale`**: bật khi có dòng `hocba.sale.revenue` cho kỳ HOẶC contract đánh dấu sale. Nếu sale nhưng tháng đó không có doanh thu (DT rỗng như HB.01 vài tháng) → COM=0 và base lương thời gian = lương hợp đồng (fallback). ❓ Xác nhận quy tắc fallback với khách.
3. **STD_DAYS=24**: quan sát cố định 24 trong dữ liệu, nhưng "Công chuẩn của tháng" lại là 25/26. → ❓ Khách xác nhận mẫu số là 24 cố định hay theo tháng.
4. **NONTAX_ALW**: mặc định 700.000 (ăn ca) nếu hợp đồng có HT ăn ca ≥ 700.000; trần miễn thuế ăn ca 730.000 (file 05). Cần khách chốt danh sách phụ cấp miễn thuế.
