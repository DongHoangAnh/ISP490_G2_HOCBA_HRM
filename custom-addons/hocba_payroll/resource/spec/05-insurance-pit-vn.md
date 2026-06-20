# 05 — Bảo hiểm & Thuế TNCN (VN 2026)

> File này cung cấp tỷ lệ, trần, biểu thuế để code rule BH & TNCN. Đã đối chiếu với dữ liệu Học Bá.

---

## 1. Tỷ lệ Bảo hiểm bắt buộc

Cơ sở tính = `contract.x_insurance_base` (cột "Lương đóng BH"), **không phải** lương hợp đồng.

| Khoản | Người LĐ (NV) | Doanh nghiệp (CT) |
|---|---|---|
| BHXH | **8%** | **17.5%** (gồm 17% hưu trí-tử tuất + 0.5% TNLĐ-BNN) |
| BHYT | **1.5%** | **3%** |
| BHTN | **1%** | **1%** |
| **Tổng** | **10.5%** | **21.5%** |

**Đối chiếu (đã verify)**:
- HB.01 base 7.300.000 → NV: 584.000 + 109.500 + 73.000 = **766.500** (10.5%) ✓; CT: 1.277.500 + 219.000 + 73.000 ✓
- HB.09 base 5.700.000 → NV: 456.000 + 85.500 + 57.000 = **598.500** ✓

### Chính sách BH (`x_insurance_policy`)
| Giá trị | Mô tả | Áp dụng |
|---|---|---|
| `standard` | "BH theo định mức" | Đủ 8/1.5/1% (NV) + 17.5/3/1% (CT) |
| `tnld_0_5` | "Đóng 0.5% BH TNLĐ" | Chỉ phần 0.5% TNLĐ-BNN (CT). NV không đóng ❓ |
| `none` | Không đóng (Online, một số part-time) | 0 |

> ❓ Cần khách làm rõ trường hợp `tnld_0_5` (HB.58) đóng những khoản nào cụ thể.

### Trần đóng BH (validation, chưa chặn cứng)
- BHXH & BHYT: trần = **20 × mức tham chiếu** (mức lương cơ sở/mức tham chiếu theo Luật BHXH 2024).
- BHTN: trần = **20 × lương tối thiểu vùng**.
- Sàn: không thấp hơn lương tối thiểu vùng áp dụng.
> Học Bá lưu `x_insurance_base` thủ công (5.1tr–7.3tr) nên hiện **dưới trần** → chỉ cần cảnh báo nếu vượt.
> ❓ Cập nhật con số trần theo quy định hiệu lực tại kỳ tính (lương cơ sở 2.34tr → trần 46.8tr; lương tối thiểu vùng I 2025/2026 — xác nhận số mới nhất khi go-live).

### Rule python (mẫu)
```python
base = contract.x_insurance_base or 0.0
pol = contract.x_insurance_policy
def r(x): return round(base * x)
if pol == 'standard':
    BHXH_NV, BHYT_NV, BHTN_NV = -r(0.08), -r(0.015), -r(0.01)
    BHXH_CT, BHYT_CT, BHTN_CT =  r(0.175), r(0.03),  r(0.01)
elif pol == 'tnld_0_5':
    BHXH_NV = BHYT_NV = BHTN_NV = 0
    BHXH_CT, BHYT_CT, BHTN_CT = r(0.005), 0, 0     # ❓ xác nhận
else:
    BHXH_NV = BHYT_NV = BHTN_NV = BHXH_CT = BHYT_CT = BHTN_CT = 0
```

---

## 2. Thuế TNCN — VN 2026

### 2.1. Giảm trừ gia cảnh (từ kỳ tính thuế 2026)
> **Nghị quyết 110/2025/UBTVQH15** (hiệu lực kỳ tính thuế 2026):
> - Bản thân người nộp thuế: **15.500.000 đ/tháng** (186tr/năm)
> - Mỗi người phụ thuộc: **6.200.000 đ/tháng**

**Đối chiếu**: Cột "Giảm trừ NPT" Học Bá = 6.200.000/người ✓ (đúng chuẩn 2026). HB.01 (1 NPT) → 6.200.000 ✓.

### 2.2. Thu nhập tính thuế (đã verify công thức)
```
TI = max(0, GROSS − BH_NV(10.5%) − 15.500.000 − 6.200.000×SốNPT − PhụCấpMiễnThuế)
```
**Đối chiếu HB.09**: 29.362.441 − 598.500 − 15.500.000 − 0 − 700.000 = **12.563.941** ✓

### 2.3. Phụ cấp miễn thuế thường gặp (TT 111/2013/TT-BTC)
| Khoản | Mức miễn | Ghi chú |
|---|---|---|
| Ăn giữa ca/ăn trưa | tối đa **730.000/tháng** | Học Bá quan sát dùng 700.000 |
| Điện thoại, công tác phí | theo quy chế công ty | cần quy chế |
| Trang phục | tối đa **5.000.000/năm** (nếu bằng tiền) | |
| Phụ cấp ăn ca/làm thêm đúng quy định | phần vượt quy định mới chịu thuế | |
> Mỗi loại phụ cấp gắn cờ `is_taxable`. Phần miễn thuế cộng vào `NONTAX_ALW`.
> ❓ Khách chốt danh sách + mức miễn áp dụng.

### 2.4. Biểu thuế lũy tiến từng phần (7 bậc — thuế tháng)

| Bậc | TI tháng (đồng) | Thuế suất | Tính nhanh (TI×suất − trừ) |
|---|---|---|---|
| 1 | đến 5.000.000 | 5% | 5%·TI |
| 2 | trên 5tr–10tr | 10% | 10%·TI − 250.000 |
| 3 | trên 10tr–18tr | 15% | 15%·TI − 750.000 |
| 4 | trên 18tr–32tr | 20% | 20%·TI − 1.650.000 |
| 5 | trên 32tr–52tr | 25% | 25%·TI − 3.250.000 |
| 6 | trên 52tr–80tr | 30% | 30%·TI − 5.850.000 |
| 7 | trên 80tr | 35% | 35%·TI − 9.850.000 |

> ❓ **Xác nhận biểu thuế**: dự thảo Luật TNCN sửa đổi có đề xuất rút còn **5 bậc**. Nếu kỳ tính thuế
> áp dụng biểu mới → cập nhật bảng này. Mặc định spec dùng 7 bậc hiện hành.

### 2.5. Hàm tính PIT (lưu bậc trong `pit_brackets_data.xml`, không hardcode)
```python
def _hocba_pit(self, ti):
    ti = max(0.0, ti)
    tax = 0.0
    # brackets = recordset hocba.pit.bracket sắp theo lower_bound
    for b in self.env['hocba.pit.bracket'].search([], order='lower_bound'):
        if ti > b.lower_bound:
            upper = b.upper_bound or float('inf')
            seg = min(ti, upper) - b.lower_bound
            tax += seg * b.rate
        else:
            break
    return round(tax)
```
Model `hocba.pit.bracket`: `lower_bound`, `upper_bound` (0 = ∞), `rate` (float), `quick_deduct` (tham khảo).

**Đối chiếu công thức** (cho TI = 12.563.941, đúng luật):
- Bậc1: 5.000.000×5% = 250.000
- Bậc2: 5.000.000×10% = 500.000
- Bậc3: 2.563.941×15% = 384.591
- **Tổng = 1.134.591** ← số ĐÚNG hệ thống mới sẽ xuất (Excel ghi 756.394 là sai số nhập tay).

---

## 3. Tóm tắt khác biệt Excel ↔ Hệ thống mới (phải nói rõ với khách)

| Hạng mục | Excel Học Bá | Hệ thống mới | Lý do |
|---|---|---|---|
| Net trên dòng thuế=0 | đúng | giống | math sạch |
| Thuế TNCN dòng có thuế | có sai số nhập tay | tính đúng 7 bậc | chuẩn hóa |
| Giảm trừ 2026 | đã dùng 15.5tr/6.2tr | giữ nguyên | đúng luật |
| Phụ cấp miễn thuế | gộp/ẩn | tách qua `is_taxable` | minh bạch |

> Khuyến nghị: chạy song song (parallel run) 1–2 kỳ, đối chiếu, giải thích chênh lệch thuế cho khách trước go-live.
