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
| `luong_co_ban` | Lương thời gian | Lương theo công |
| `phu_cap` | Phụ cấp | PC + hỗ trợ |
| `thuong` | Thưởng | Thưởng lễ, thưởng khác |
| `tong_thu_nhap` | Tổng thu nhập | = luong_co_ban+phu_cap+thuong |
| `bh_cong_ty` | BH phần công ty | Tracking, KHÔNG trừ net |
| `khau_tru` | Khấu trừ NV | BH NV + tạm ứng |
| `thue` | Thuế TNCN | |
| `thuc_lanh` | Thực lãnh | |

---

## 2. Đầu vào theo kỳ (Other Inputs / Worked Days)

| Code | Loại | Ý nghĩa | Nguồn |
|---|---|---|---|
| `STD_DAYS` | input | Công chuẩn (mẫu số chia) — quan sát = 24 ❓ | nhập/cấu hình |
| `PAID_DAYS` | worked | Công tháng (công có lương = chấm công + phép) | import |
| `OT_DAYS` | worked | Tăng ca quy đổi ra ngày | import |
| `BONUS_HOLIDAY` | input | Thưởng Lễ | nhập |
| `BONUS_OTHER` | input | Thưởng khác | nhập |
| `ADVANCE` | input | Tạm ứng / Trừ khác | nhập |
| `NONTAX_ALW` | input | Phụ cấp miễn thuế (ăn ca…) — quan sát 700.000 | cấu hình/contract |

> **Tổng công** = `PAID_DAYS + OT_DAYS`. **Hệ số công** = `Tổng công / STD_DAYS`.

---

## 3. CẤU TRÚC OFFLINE — `STRUCT_OFFLINE`

### Rule 3.1 — `LUONG_TG` (Lương thời gian) · cat luong_co_ban
```python
std_days = inputs.STD_DAYS.amount or 24.0
total_days = (worked_days.PAID_DAYS.number_of_days or 0.0) + (worked_days.OT_DAYS.number_of_days or 0.0)
ratio = total_days / std_days if std_days else 0.0
base = contract.wage   # Lương hợp đồng
result = round(base * ratio)
```
**Đối chiếu**:
- HB.01: 20.000.000 x 24/24 = **20.000.000** ✓

### Rule 3.2 — `PHU_CAP` (Tổng phụ cấp) · cat phu_cap
```python
result = (contract.x_pc_seniority + contract.x_pc_parking + contract.x_pc_fuel
          + contract.x_pc_position + contract.x_sp_transport + contract.x_sp_phone
          + contract.x_sp_meal + contract.x_sp_uniform)
```
> Trong dữ liệu nhiều dòng Tổng phụ cấp = 0 (phụ cấp đã gộp vào lương HĐ). Giữ rule để mở rộng.

### Rule 3.3 — `THUONG` (Thưởng) · cat thuong
```python
result = (inputs.BONUS_HOLIDAY.amount or 0.0) + (inputs.BONUS_OTHER.amount or 0.0)
```
**Đối chiếu**: HB.01: Thưởng khác 150.000 → **150.000** ✓; HB.09: **1.950.000** ✓

### Rule 3.4 — `GROSS` (Tổng thu nhập) · cat tong_thu_nhap
```python
result = categories.luong_co_ban + categories.phu_cap + categories.thuong
```
**Đối chiếu**:
- HB.01: 20.000.000 + 0 + 150.000 = **20.150.000** ✓

### Rule 3.5 -> 3.10 — Bảo hiểm (xem file 05 cho tỷ lệ & trần)
Phần công ty (cat bh_cong_ty, KHÔNG trừ net): `BHXH_CT 17.5%`, `BHYT_CT 3%`, `BHTN_CT 1%`.
Phần NV (cat khau_tru, trừ net): `BHXH_NV 8%`, `BHYT_NV 1.5%`, `BHTN_NV 1%`.
Tất cả nhân với `contract.x_insurance_base` (Lương đóng BH), tùy `x_insurance_policy`.
**Đối chiếu HB.09** (base 5.700.000): BHXH_NV 456.000 ✓, BHYT_NV 85.500 ✓, BHTN_NV 57.000 ✓, tổng NV 598.500 ✓.

### Rule 3.11 — `BH_NV_TOTAL` (Tổng BH NV 10.5%) · cat khau_tru (helper)
```python
result = -(abs(BHXH_NV) + abs(BHYT_NV) + abs(BHTN_NV))   # dấu âm: khấu trừ
```

### Rule 3.12 — `TNCN` (Thuế TNCN) · cat thue  -> công thức ở file 05
```python
gross = categories.tong_thu_nhap
bh_nv = abs(BHXH_NV) + abs(BHYT_NV) + abs(BHTN_NV)
self_ded = 15_500_000                                  # giảm trừ bản thân 2026
dep_ded  = 6_200_000 * (contract.x_dependent_count or 0)
nontax   = inputs.NONTAX_ALW.amount or 0.0             # ăn ca… miễn thuế (vd 700.000)
taxable = max(0.0, gross - bh_nv - self_ded - dep_ded - nontax)
result = -payslip._hocba_pit(taxable)                  # progressive 7 bậc, dấu âm
```
**Đối chiếu**: xem file 07 cho test case cụ thể.
> **Hệ thống tính đúng luật** -- KHÔNG sao chép số thuế cũ từ Excel.
> Test (file 07) chỉ hard-assert các dòng thuế = 0 (đã sạch); dòng có thuế để chế độ "review".

### Rule 3.13 — `ADVANCE` (Tạm ứng/Trừ khác) · cat khau_tru
```python
result = -(inputs.ADVANCE.amount or 0.0)
```
**Đối chiếu HB.09**: −1.800.000 ✓

### Rule 3.14 — `NET` (Thực lãnh) · cat thuc_lanh
```python
result = categories.tong_thu_nhap + categories.khau_tru + categories.thue
# khau_tru và thue đã mang dấu âm
```
**Đối chiếu**:
- HB.01: 20.150.000 - 766.500 - 0 - 0 = **19.383.500** ✓ (khớp tuyệt đối)

---

## 4. CẤU TRÚC ONLINE — `STRUCT_ONLINE`

Đơn giản, không công/BH/thuế.

### Rule 4.1 — `LUONG` · cat luong_co_ban
```python
result = inputs.WAGE_ONLINE.amount or contract.wage   # "Lương" nhập theo tháng
```
### Rule 4.2 — `THUONG` · cat thuong
```python
result = inputs.BONUS_OTHER.amount or 0.0             # "Thưởng"
```
### Rule 4.3 — `GROSS` · cat tong_thu_nhap
```python
result = categories.luong_co_ban + categories.thuong
```
### Rule 4.4 — `ADVANCE` · cat khau_tru
```python
result = -(inputs.ADVANCE.amount or 0.0)              # "Tạm ứng, trừ khác"
```
### Rule 4.5 — `NET` · cat thuc_lanh
```python
result = categories.tong_thu_nhap + categories.khau_tru
```
**Đối chiếu** (HB.32, T3/2025): Lương 10.000.000 + Thưởng 1.000.000 − 0 = **11.000.000** ✓

---

## 5. Bảng tổng hợp rule (để sinh XML)

### OFFLINE
| Seq | Code | Category | Sign | Công thức tóm tắt |
|---|---|---|---|---|
| 10 | LUONG_TG | luong_co_ban | + | wage x tổng_công/STD_DAYS |
| 20 | PHU_CAP | phu_cap | + | Σ phụ cấp định mức |
| 30 | THUONG | thuong | + | thưởng lễ + khác |
| 40 | GROSS | tong_thu_nhap | = | luong_co_ban+phu_cap+thuong |
| 50 | BHXH_CT | bh_cong_ty | (track) | base x 17.5% |
| 51 | BHYT_CT | bh_cong_ty | (track) | base x 3% |
| 52 | BHTN_CT | bh_cong_ty | (track) | base x 1% |
| 60 | BHXH_NV | khau_tru | - | base x 8% |
| 61 | BHYT_NV | khau_tru | - | base x 1.5% |
| 62 | BHTN_NV | khau_tru | - | base x 1% |
| 70 | TNCN | thue | - | PIT(taxable) |
| 80 | ADVANCE | khau_tru | - | tạm ứng |
| 99 | NET | thuc_lanh | = | tong_thu_nhap+khau_tru+thue |

### ONLINE
| Seq | Code | Category | Sign | Công thức |
|---|---|---|---|---|
| 10 | LUONG | luong_co_ban | + | lương tháng |
| 30 | THUONG | thuong | + | thưởng |
| 40 | GROSS | tong_thu_nhap | = | luong_co_ban+thuong |
| 80 | ADVANCE | khau_tru | - | tạm ứng |
| 99 | NET | thuc_lanh | = | tong_thu_nhap+khau_tru |

---

## 6. Lưu ý implement

1. **Round**: round tới đồng từng rule (như Excel). Chấp nhận lệch ≤1đ ở GROSS do tổng các phần đã round.
2. **STD_DAYS=24**: quan sát cố định 24 trong dữ liệu, nhưng "Công chuẩn của tháng" lại là 25/26. -> Khách xác nhận mẫu số là 24 cố định hay theo tháng.
3. **NONTAX_ALW**: mặc định 700.000 (ăn ca) nếu hợp đồng có HT ăn ca >= 700.000; trần miễn thuế ăn ca 730.000 (file 05). Cần khách chốt danh sách phụ cấp miễn thuế.
